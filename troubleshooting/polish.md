# Troubleshooting - Polski

## Windows

- Jeśli setup nie działa, zainstaluj Python 3.8+ ręcznie z `https://www.python.org/downloads/windows/`.
- Podczas instalacji zaznacz `Add python.exe to PATH`.
- Otwórz `cmd` w folderze `dawert-language repacker` i sprawdź:

```bat
py -3 --version
python --version
```

- Uruchom:

```bat
start-windows.bat
```

- Jeśli PowerShell blokuje skrypty, użyj `.bat` zamiast `.ps1`.
- Jeśli brakuje `py`, ale działa `python`, BAT launcher użyje `python`.

## Linux

- Jeśli setup nie działa, zainstaluj Python ręcznie:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Potem uruchom:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

## Logi i restore

- Logi są w `Data/dawertrepacker/logs/`.
- Backupy są w `Data/dawertrepacker/backup/`.
- Restore z menu albo komendą:

```bash
python3 repacker.py --auto-find --action restore
```

Narzędzie utrzymuje `Data/language.dat` jako `Language=English`.
