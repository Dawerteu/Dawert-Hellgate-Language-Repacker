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
- Se `Launcher.exe` non funziona con dati modificati o scarica di nuovo la localizzazione originale, usa `play-windows.bat` per giocare.

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

- Se il launcher sovrascrive i file tradotti, avvia il gioco con:

```bash
chmod +x play-linux.sh
./play-linux.sh
```

Lo script `play-*` ha una modalità di gioco normale e una modalità update ufficiale. La modalità update ripristina prima i dati puliti, avvia `Launcher.exe`, aggiorna il backup pulito dopo la chiusura e poi può applicare di nuovo la traduzione.

## Log e restore

- Log: `Data/dawertrepacker/logs/`.
- Backup: `Data/dawertrepacker/backup/`.
- Restore dal menu o con:

```bash
python3 repacker.py --auto-find --action restore
```

Lo strumento mantiene `Data/language.dat` come `Language=English`.
