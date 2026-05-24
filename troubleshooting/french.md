# Troubleshooting - Français

## Windows

- Si le setup échoue, installe Python 3.8+ manuellement depuis `https://www.python.org/downloads/windows/`.
- Pendant l'installation, coche `Add python.exe to PATH`.
- Ouvre `cmd` dans le dossier `dawert-language repacker` et teste:

```bat
py -3 --version
python --version
```

- Lance:

```bat
start-windows.bat
```

- Si PowerShell bloque les scripts, utilise `.bat` au lieu de `.ps1`.
- Si `py` manque mais `python` fonctionne, le launcher BAT utilisera `python`.
- Si `Launcher.exe` refuse les données modifiées ou retélécharge la localisation originale, utilise `play-windows.bat` pour jouer.

## Linux

- Si le setup échoue, installe Python manuellement:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Puis lance:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

- Si le launcher écrase les fichiers traduits, lance le jeu avec:

```bash
chmod +x play-linux.sh
./play-linux.sh
```

Le script `play-*` a un mode de jeu normal et un mode update officiel. Le mode update restaure d'abord les données propres, lance `Launcher.exe`, rafraîchit le backup propre après sa fermeture, puis peut appliquer de nouveau la traduction.

## Logs et restauration

- Logs: `Data/dawertrepacker/logs/`.
- Backups: `Data/dawertrepacker/backup/`.
- Restore depuis le menu ou avec:

```bash
python3 repacker.py --auto-find --action restore
```

L'outil garde `Data/language.dat` en `Language=English`.
