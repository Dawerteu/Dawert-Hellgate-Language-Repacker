# Troubleshooting - Русский

## Windows

- Если setup не работает, установите Python 3.8+ вручную с `https://www.python.org/downloads/windows/`.
- Во время установки включите `Add python.exe to PATH`.
- Откройте `cmd` в папке `dawert-language repacker` и проверьте:

```bat
py -3 --version
python --version
```

- Запуск:

```bat
start-windows.bat
```

- Если PowerShell блокирует скрипты, используйте `.bat`, а не `.ps1`.
- Если `py` отсутствует, но работает `python`, BAT launcher использует `python`.

## Linux

- Если setup не работает, установите Python вручную:

```bash
sudo apt install python3
sudo dnf install python3
sudo pacman -S python
sudo zypper install python3
```

- Потом запустите:

```bash
chmod +x setup-linux.sh start-linux.sh
./start-linux.sh
```

## Логи и восстановление

- Логи: `Data/dawertrepacker/logs/`.
- Резервные копии: `Data/dawertrepacker/backup/`.
- Restore через меню или командой:

```bash
python3 repacker.py --auto-find --action restore
```

Инструмент держит `Data/language.dat` как `Language=English`.
