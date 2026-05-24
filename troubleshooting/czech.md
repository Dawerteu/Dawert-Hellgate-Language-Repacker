# Troubleshooting - Čeština

## Windows

- Když setup selže, nainstaluj Python 3.8+ ručně z `https://www.python.org/downloads/windows/`.
- Při instalaci zaškrtni `Add python.exe to PATH`.
- Otevři `cmd` ve složce `dawert-language repacker` a otestuj:

```bat
py -3 --version
python --version
```

- Spusť:

```bat
start-windows.bat
```

- Když PowerShell blokuje skripty, použij `.bat`, ne `.ps1`.
- Když chybí `py`, ale funguje `python`, BAT launcher použije `python`.
- Když `Launcher.exe` nechce běžet se změněnými daty nebo stahuje originální lokalizaci zpět, používej pro hraní `play-windows.bat`.

## Linux

- Když setup selže, nainstaluj Python ručně přes package manager:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Pak spusť:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

- Když launcher přepisuje přeložené soubory, spusť hru přes:

```bash
chmod +x play-linux.sh
./play-linux.sh
```

`play-*` skript má režim pro normální hraní a režim pro oficiální update. Update režim nejdřív obnoví čistá data, spustí `Launcher.exe`, po zavření obnoví clean backup a pak může znovu aplikovat překlad.

## Logy a restore

- Logy jsou v `Data/dawertrepacker/logs/`.
- Zálohy jsou v `Data/dawertrepacker/backup/`.
- Restore jde z menu nebo příkazem:

```bash
python3 repacker.py --auto-find --action restore
```

Nástroj drží `Data/language.dat` jako `Language=English`.
