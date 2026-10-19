# Automatická kontrola WordPress DEV

GitHub Actions pravidelně kontrolují verzi nainstalovaného pluginu na DEV oproti latest.json. Kontrola je jen pro čtení a nezískává přístup k databázi ani administraci.

Kontrolní endpoint: https://jpcontrol.cz/dev/wp-json/portal-platform/v1/dev/build

Plán: každé dvě hodiny nebo manuálně přes Actions. Nové verzi dáváme 26 hodin na automatickou instalaci přes WP-Cron. Pokud je po 26 hodinách na DEV stále starší plugin, CI hlásí chybu. Nesoulad jiné povahy a chybné odpovědi se také považují za chybu. Dokud WordPress v prvních 26 hodinách čeká na plánovanou aktualizaci, je stav jen pending.

Kontrola neinstaluje ZIP, nespouští PHP kód vzdáleně, nemění UAT/PROD a nevyžaduje další GitHub token.
