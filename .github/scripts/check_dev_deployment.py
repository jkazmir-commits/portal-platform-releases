#!/usr/bin/env python3
"""Read-only acceptance check: published GitHub release versus installed WP DEV."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib import request

DEV_URL = "https://jpcontrol.cz/dev/wp-json/portal-platform/v1/dev/build"
RELEASE_ROOT = "https://github.com/jkazmir-commits/portal-platform-releases/releases/download/"
VERSION = re.compile(r"0[.]8[.]0-dev([0-9]+)\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
GRACE_SECONDS = 26 * 3600


def number(v):
    if not isinstance(v, str) or not VERSION.fullmatch(v):
        raise ValueError("Unsupported DEV version")
    return int(VERSION.fullmatch(v).group(1))


def manifest(v):
    if not isinstance(v, dict):
        raise ValueError("Not a release object")
    version = v.get("version")
    number(version)
    expected = RELEASE_ROOT + version + "/portal-platform-" + version + ".zip"
    if v.get("package") != expected:
        raise ValueError("Untrusted release package")
    digest = v.get("sha256")
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        raise ValueError("Invalid SHA-256")
    return v


def installed(v):
    if not isinstance(v, dict) or set(v) != {"environment", "version"} or v["environment"] != "dev":
        raise ValueError("Non-DEV or unexpected REST reply")
    number(v["version"])
    return v["version"]


def verdict(expected, actual, age):
    e, a = number(expected), number(actual)
    if e == a:
        return ("current", 0)
    if a > e:
        return ("ahead_of_release", 1)
    if age <= GRACE_SECONDS:
        return ("pending_wordpress_auto_update", 0)
    return ("overdue_wordpress_auto_update", 1)


def get_live():
    req = request.Request(DEV_URL + "?monitor=" + str(int(time.time())), headers={
        "Accept": "application/json", "User-Agent": "Portal-Platform-DEV-CI/1",
    })
    with request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError("Unexpected DEV HTTP status")
        data = response.read(4097)
    if len(data) > 4096:
        raise ValueError("Oversized DEV reply")
    return installed(json.loads(data.decode("utf-8")))


def release_age():
    stamp = subprocess.check_output(
        ["git", "log", "-1", "--format=%ct", "--", "latest.json"],
        text=True, timeout=10,
    ).strip()
    if not stamp.isdigit():
        raise ValueError("Missing latest.json commit timestamp")
    return max(0, int(time.time()) - int(stamp))


def report(message):
    print(message)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write("## WP DEV deployment acceptance\n\n" + message + "\n")


def main():
    try:
        expected = manifest(json.loads(Path("latest.json").read_text(encoding="utf-8")))["version"]
        actual = get_live()
        age = release_age()
        result, code = verdict(expected, actual, age)
        report(result.upper() + ": latest " + expected + ", WP DEV " + actual + ", age " + str(age // 3600) + "h")
        return code
    except (OSError, ValueError, KeyError, UnicodeError, subprocess.SubprocessError) as exc:
        report("VERIFICATION ERROR: " + str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
