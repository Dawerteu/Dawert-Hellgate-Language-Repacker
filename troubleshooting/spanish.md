# Troubleshooting - Español

## Windows

- Si el setup falla, instala Python 3.8+ manualmente desde `https://www.python.org/downloads/windows/`.
- Durante la instalación activa `Add python.exe to PATH`.
- Abre `cmd` en la carpeta `dawert-language repacker` y prueba:

```bat
py -3 --version
python --version
```

- Inicia:

```bat
start-windows.bat
```

- Si PowerShell bloquea scripts, usa `.bat` en vez de `.ps1`.
- Si falta `py` pero funciona `python`, el BAT launcher usará `python`.

## Linux

- Si el setup falla, instala Python manualmente:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Luego ejecuta:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

## Logs y restore

- Logs: `Data/dawertrepacker/logs/`.
- Backups: `Data/dawertrepacker/backup/`.
- Restore desde el menú o con:

```bash
python3 repacker.py --auto-find --action restore
```

La herramienta mantiene `Data/language.dat` como `Language=English`.
