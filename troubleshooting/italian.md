# Troubleshooting - Italiano

## Windows

- Se il setup non funziona, installa Python 3.8+ manualmente da `https://www.python.org/downloads/windows/`.
- Durante l'installazione abilita `Add python.exe to PATH`.
- Apri `cmd` nella cartella `dawert-language repacker` e verifica:

```bat
py -3 --version
python --version
```

- Avvia:

```bat
start-windows.bat
```

- Se PowerShell blocca gli script, usa `.bat` invece di `.ps1`.
- Se manca `py` ma funziona `python`, il BAT launcher userà `python`.

## Linux

- Se il setup non funziona, installa Python manualmente:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Poi esegui:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

## Log e restore

- Log: `Data/dawertrepacker/logs/`.
- Backup: `Data/dawertrepacker/backup/`.
- Restore dal menu o con:

```bash
python3 repacker.py --auto-find --action restore
```

Lo strumento mantiene `Data/language.dat` come `Language=English`.
