# Troubleshooting - Magyar

## Windows

- Ha a setup nem működik, telepítsd kézzel a Python 3.8+ verziót innen: `https://www.python.org/downloads/windows/`.
- Telepítéskor pipáld be: `Add python.exe to PATH`.
- Nyisd meg a `cmd`-t a `dawert-language repacker` mappában és teszteld:

```bat
py -3 --version
python --version
```

- Indítás:

```bat
start-windows.bat
```

- Ha a PowerShell blokkolja a szkripteket, használd a `.bat` fájlt.
- Ha nincs `py`, de a `python` működik, a BAT launcher a `python` parancsot használja.

## Linux

- Ha a setup nem működik, telepítsd kézzel a Pythont:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Ezután:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

## Logok és visszaállítás

- Logok: `Data/dawertrepacker/logs/`.
- Backupok: `Data/dawertrepacker/backup/`.
- Restore menüből vagy paranccsal:

```bash
python3 repacker.py --auto-find --action restore
```

Az eszköz a `Data/language.dat` fájlt `Language=English` értéken tartja.
