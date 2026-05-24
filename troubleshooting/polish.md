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
- Jeśli `Launcher.exe` nie działa ze zmienionymi plikami albo pobiera oryginalną lokalizację ponownie, użyj do grania `play-windows.bat`.

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

- Jeśli launcher nadpisuje przetłumaczone pliki, uruchom grę przez:

```bash
chmod +x play-linux.sh
./play-linux.sh
```

Skrypt `play-*` ma tryb normalnej gry i tryb oficjalnej aktualizacji. Tryb aktualizacji najpierw przywraca czyste dane, uruchamia `Launcher.exe`, po zamknięciu odświeża czysty backup i może ponownie zastosować tłumaczenie.

## Logi i restore

- Logi są w `Data/dawertrepacker/logs/`.
- Backupy są w `Data/dawertrepacker/backup/`.
- Restore z menu albo komendą:

```bash
python3 repacker.py --auto-find --action restore
```

Narzędzie utrzymuje `Data/language.dat` jako `Language=English`.
