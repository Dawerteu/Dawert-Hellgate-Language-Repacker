#!/usr/bin/env python3
"""
Dawert language repacker for Hellgate London / London2038.

The game is kept on Language=English for London2038 stability. This tool
copies/merges another localized string set into the English string tables,
then appends the rebuilt cooked string files to the existing DAT archives and
patches the IDX offsets.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import os
import shutil
import struct
import sys
import time
import unicodedata
import zlib
from dataclasses import dataclass
from pathlib import Path


ARCHIVE_GLOB = "*localized*.idx"
TARGET_LANGUAGE_DIR = "english"
DEFAULT_EXCLUDES: set[str] = set()
FONT_ARCHIVE_BASE = "hellgate000"
REPACKER_DIR_NAME = "dawertrepacker"
LANGUAGE_DAT_TEXT = "Language=English"
DETAILED_DECRYPT_LOG = True
DEFAULT_CSV_NAME = "hellgate-english-strings.csv"
LONDON2038_CSV_NAME = "london2038-english-strings.csv"
LONDON2038_UNTRANSLATED_CSV_NAME = "london2038-untranslated-english-strings.csv"
CSV_FIELDS = ("Archive", "Table", "StringID", "English", "Translation", "Directory", "Attributes")
FONT_ATLAS_TARGET = r"data\uix\xml\fonts_atlas.xml"
FONT_ATLAS_BY_LANGUAGE = {
    "czech": r"data\uix\xml\czech_fonts_atlas.xml",
    "french": r"data\uix\xml\french_fonts_atlas.xml",
    "german": r"data\uix\xml\german_fonts_atlas.xml",
    "hungarian": r"data\uix\xml\hungarian_fonts_atlas.xml",
    "italian": r"data\uix\xml\italian_fonts_atlas.xml",
    "polish": r"data\uix\xml\polish_fonts_atlas.xml",
    "russian": r"data\uix\xml\russian_fonts_atlas.xml",
    "spanish": r"data\uix\xml\spanish_fonts_atlas.xml",
}
FONT_SAFE_TRANSLATION = str.maketrans(
    {
        "ß": "ss",
        "ẞ": "SS",
        "Æ": "AE",
        "æ": "ae",
        "Œ": "OE",
        "œ": "oe",
        "Ø": "O",
        "ø": "o",
        "Đ": "D",
        "đ": "d",
        "Ł": "L",
        "ł": "l",
        "Þ": "Th",
        "þ": "th",
        "Ð": "D",
        "ð": "d",
        "–": "-",
        "—": "-",
        "―": "-",
        "…": "...",
        "“": '"',
        "”": '"',
        "„": '"',
        "«": '"',
        "»": '"',
        "‘": "'",
        "’": "'",
        "‚": "'",
        "′": "'",
        "″": '"',
        "•": "*",
        "×": "x",
    }
)

LANGUAGE_ALIASES = {
    "cz": "czech",
    "cesky": "czech",
    "česky": "czech",
    "cestina": "czech",
    "čeština": "czech",
    "czech": "czech",
    "fr": "french",
    "french": "french",
    "es": "spanish",
    "spanish": "spanish",
    "it": "italian",
    "italian": "italian",
    "pl": "polish",
    "polish": "polish",
    "ru": "russian",
    "russian": "russian",
    "hu": "hungarian",
    "hungarian": "hungarian",
    "de": "german",
    "german": "german",
}

UI_LANG = "en"
UI = {
    "en": {
        "script_language": "Script language",
        "english": "English",
        "czech_ui": "Czech",
        "choose_number": "Choose a number from {minimum} to {maximum}.",
        "found_folders": "Found Hellgate folders:",
        "custom_path": "Type custom path",
        "game_folder": "Game folder",
        "game_folder_manual": "Hellgate game folder (folder containing Data)",
        "languages": "Languages:",
        "custom_language": "Type custom language",
        "install_language": "Install language",
        "language_name": "Language name",
        "font_atlas": "Font atlas for real font fix:",
        "no_font_atlas": "No font atlas patch",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "CSV export scope:",
        "csv_missing": "London2038 untranslated only",
        "csv_london": "London2038 all",
        "csv_all": "Everything",
        "csv_scope_prompt": "CSV scope",
        "toggle_title": "Toggle tables you do NOT want translated:",
        "done": "Done",
        "toggle_hint": "Selected [X] = keep this table in English.",
        "toggle_prompt": "Toggle number(s), comma-separated, or 0 when done",
        "ignored_toggle": "Ignored invalid toggle: {item}",
        "menu_title": "Main Menu:",
        "menu_install": "Install",
        "menu_csv": "Manual CSV Translation",
        "menu_maintenance": "Maintenance",
        "menu_1": "Install language, normal mode + real font fix + loading tips",
        "menu_2": "Custom install, toggle what NOT to translate",
        "menu_3": "Install language with ASCII/font-safe fallback",
        "menu_4": "Export only London2038 strings not translated automatically",
        "menu_5": "Export all London2038 strings",
        "menu_6": "Export every English string",
        "menu_7": "Import translated CSV",
        "menu_8": "List available source languages",
        "menu_9": "Restore original files",
        "menu_10": "Dry run normal install",
        "menu_0": "Exit",
        "choose_action": "Choose action",
        "csv_output": "CSV output path",
        "csv_input": "CSV input path",
    },
    "cs": {
        "script_language": "Jazyk scriptu",
        "english": "Anglictina",
        "czech_ui": "Cestina",
        "choose_number": "Vyber cislo od {minimum} do {maximum}.",
        "found_folders": "Nalezene Hellgate slozky:",
        "custom_path": "Zadat vlastni cestu",
        "game_folder": "Slozka hry",
        "game_folder_manual": "Hellgate slozka hry (slozka obsahujici Data)",
        "languages": "Jazyky:",
        "custom_language": "Zadat vlastni jazyk",
        "install_language": "Instalovat jazyk",
        "language_name": "Nazev jazyka",
        "font_atlas": "Font atlas pro skutecnou opravu fontu:",
        "no_font_atlas": "Bez font atlas patche",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "Rozsah CSV exportu:",
        "csv_missing": "Jen London2038 texty bez automatickeho prekladu",
        "csv_london": "Vsechny London2038 texty",
        "csv_all": "Vsechno",
        "csv_scope_prompt": "Rozsah CSV",
        "toggle_title": "Prepinani tabulek, ktere NECHCES prelozit:",
        "done": "Hotovo",
        "toggle_hint": "Vybrane [X] = nechat tuto tabulku anglicky.",
        "toggle_prompt": "Cislo/cisla oddelena carkou, nebo 0 pro hotovo",
        "ignored_toggle": "Ignoruju neplatnou volbu: {item}",
        "menu_title": "Hlavni menu:",
        "menu_install": "Instalace",
        "menu_csv": "Rucni CSV preklady",
        "menu_maintenance": "Udrzba",
        "menu_1": "Instalovat jazyk normalne + oprava fontu + loading tips",
        "menu_2": "Vlastni instalace, vyber co NEprekladat",
        "menu_3": "Instalovat jazyk s ASCII/font-safe fallbackem",
        "menu_4": "Exportovat jen London2038 texty bez automatickeho prekladu",
        "menu_5": "Exportovat vsechny London2038 texty",
        "menu_6": "Exportovat vsechny anglicke texty",
        "menu_7": "Importovat prelozene CSV",
        "menu_8": "Vypsat dostupne zdrojove jazyky",
        "menu_9": "Obnovit originalni soubory",
        "menu_10": "Dry run normalni instalace",
        "menu_0": "Konec",
        "choose_action": "Vyber akci",
        "csv_output": "Cesta pro CSV export",
        "csv_input": "Cesta k CSV importu",
    },
    "ru": {
        "script_language": "Язык скрипта",
        "english": "Английский",
        "czech_ui": "Чешский",
        "choose_number": "Выберите число от {minimum} до {maximum}.",
        "found_folders": "Найденные папки Hellgate:",
        "custom_path": "Указать свой путь",
        "game_folder": "Папка игры",
        "game_folder_manual": "Папка Hellgate с папкой Data",
        "languages": "Языки:",
        "custom_language": "Указать другой язык",
        "install_language": "Установить язык",
        "language_name": "Название языка",
        "font_atlas": "Font atlas для исправления шрифта:",
        "no_font_atlas": "Без патча font atlas",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "Область CSV экспорта:",
        "csv_missing": "Только London2038 без автоматического перевода",
        "csv_london": "Все строки London2038",
        "csv_all": "Все строки",
        "csv_scope_prompt": "Область CSV",
        "toggle_title": "Отметьте таблицы, которые НЕ переводить:",
        "done": "Готово",
        "toggle_hint": "Выбрано [X] = оставить эту таблицу на английском.",
        "toggle_prompt": "Номер/номера через запятую или 0 для завершения",
        "ignored_toggle": "Пропущен неверный выбор: {item}",
        "menu_title": "Главное меню:",
        "menu_install": "Установка",
        "menu_csv": "Ручной CSV перевод",
        "menu_maintenance": "Обслуживание",
        "menu_1": "Установить язык: обычный режим + исправление шрифта + loading tips",
        "menu_2": "Выборочная установка: выбрать, что НЕ переводить",
        "menu_3": "Установить язык с ASCII/font-safe fallback",
        "menu_4": "Экспортировать только London2038 без автоматического перевода",
        "menu_5": "Экспортировать все строки London2038",
        "menu_6": "Экспортировать все английские строки",
        "menu_7": "Импортировать переведенный CSV",
        "menu_8": "Показать доступные исходные языки",
        "menu_9": "Восстановить оригинальные файлы",
        "menu_10": "Dry run обычной установки",
        "menu_0": "Выход",
        "choose_action": "Выберите действие",
        "csv_output": "Путь для CSV экспорта",
        "csv_input": "Путь к CSV импорту",
    },
    "pl": {
        "script_language": "Język skryptu",
        "english": "Angielski",
        "czech_ui": "Czeski",
        "choose_number": "Wybierz liczbę od {minimum} do {maximum}.",
        "found_folders": "Znalezione foldery Hellgate:",
        "custom_path": "Podaj własną ścieżkę",
        "game_folder": "Folder gry",
        "game_folder_manual": "Folder Hellgate zawierający Data",
        "languages": "Języki:",
        "custom_language": "Podaj inny język",
        "install_language": "Zainstaluj język",
        "language_name": "Nazwa języka",
        "font_atlas": "Font atlas do naprawy czcionki:",
        "no_font_atlas": "Bez patcha font atlas",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "Zakres eksportu CSV:",
        "csv_missing": "Tylko London2038 bez automatycznego tłumaczenia",
        "csv_london": "Wszystkie teksty London2038",
        "csv_all": "Wszystko",
        "csv_scope_prompt": "Zakres CSV",
        "toggle_title": "Zaznacz tabele, których NIE tłumaczyć:",
        "done": "Gotowe",
        "toggle_hint": "Wybrane [X] = zostaw tę tabelę po angielsku.",
        "toggle_prompt": "Numer(y) po przecinku albo 0 aby zakończyć",
        "ignored_toggle": "Pominięto nieprawidłowy wybór: {item}",
        "menu_title": "Menu główne:",
        "menu_install": "Instalacja",
        "menu_csv": "Ręczne tłumaczenie CSV",
        "menu_maintenance": "Utrzymanie",
        "menu_1": "Zainstaluj język: normalnie + naprawa fontu + loading tips",
        "menu_2": "Instalacja własna: wybierz, czego NIE tłumaczyć",
        "menu_3": "Zainstaluj język z ASCII/font-safe fallback",
        "menu_4": "Eksportuj tylko London2038 bez automatycznego tłumaczenia",
        "menu_5": "Eksportuj wszystkie teksty London2038",
        "menu_6": "Eksportuj wszystkie angielskie teksty",
        "menu_7": "Importuj przetłumaczony CSV",
        "menu_8": "Pokaż dostępne języki źródłowe",
        "menu_9": "Przywróć oryginalne pliki",
        "menu_10": "Dry run normalnej instalacji",
        "menu_0": "Wyjście",
        "choose_action": "Wybierz akcję",
        "csv_output": "Ścieżka eksportu CSV",
        "csv_input": "Ścieżka importu CSV",
    },
    "hu": {
        "script_language": "Szkript nyelve",
        "english": "Angol",
        "czech_ui": "Cseh",
        "choose_number": "Válassz számot {minimum} és {maximum} között.",
        "found_folders": "Talált Hellgate mappák:",
        "custom_path": "Egyéni útvonal megadása",
        "game_folder": "Játék mappa",
        "game_folder_manual": "Hellgate mappa, amely tartalmazza a Data mappát",
        "languages": "Nyelvek:",
        "custom_language": "Egyéni nyelv megadása",
        "install_language": "Nyelv telepítése",
        "language_name": "Nyelv neve",
        "font_atlas": "Font atlas a betűk javításához:",
        "no_font_atlas": "Font atlas patch nélkül",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "CSV export tartomány:",
        "csv_missing": "Csak London2038 automatikus fordítás nélkül",
        "csv_london": "Minden London2038 szöveg",
        "csv_all": "Minden",
        "csv_scope_prompt": "CSV tartomány",
        "toggle_title": "Kapcsold be, amit NEM akarsz fordítani:",
        "done": "Kész",
        "toggle_hint": "Kijelölt [X] = maradjon angolul ez a tábla.",
        "toggle_prompt": "Szám(ok) vesszővel, vagy 0 ha kész",
        "ignored_toggle": "Érvénytelen választás kihagyva: {item}",
        "menu_title": "Főmenü:",
        "menu_install": "Telepítés",
        "menu_csv": "Kézi CSV fordítás",
        "menu_maintenance": "Karbantartás",
        "menu_1": "Nyelv telepítése: normál mód + font javítás + loading tips",
        "menu_2": "Egyéni telepítés: válaszd ki, mit NE fordítson",
        "menu_3": "Nyelv telepítése ASCII/font-safe fallback móddal",
        "menu_4": "Csak automatikusan nem fordított London2038 export",
        "menu_5": "Minden London2038 szöveg exportálása",
        "menu_6": "Minden angol szöveg exportálása",
        "menu_7": "Lefordított CSV importálása",
        "menu_8": "Elérhető forrásnyelvek listája",
        "menu_9": "Eredeti fájlok visszaállítása",
        "menu_10": "Normál telepítés dry run",
        "menu_0": "Kilépés",
        "choose_action": "Válassz műveletet",
        "csv_output": "CSV export útvonala",
        "csv_input": "CSV import útvonala",
    },
    "it": {
        "script_language": "Lingua dello script",
        "english": "Inglese",
        "czech_ui": "Ceco",
        "choose_number": "Scegli un numero da {minimum} a {maximum}.",
        "found_folders": "Cartelle Hellgate trovate:",
        "custom_path": "Inserisci percorso personalizzato",
        "game_folder": "Cartella del gioco",
        "game_folder_manual": "Cartella Hellgate che contiene Data",
        "languages": "Lingue:",
        "custom_language": "Inserisci lingua personalizzata",
        "install_language": "Installa lingua",
        "language_name": "Nome lingua",
        "font_atlas": "Font atlas per correggere i font:",
        "no_font_atlas": "Nessun patch font atlas",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "Ambito esportazione CSV:",
        "csv_missing": "Solo London2038 non tradotto automaticamente",
        "csv_london": "Tutti i testi London2038",
        "csv_all": "Tutto",
        "csv_scope_prompt": "Ambito CSV",
        "toggle_title": "Seleziona le tabelle da NON tradurre:",
        "done": "Fatto",
        "toggle_hint": "Selezionato [X] = lascia questa tabella in inglese.",
        "toggle_prompt": "Numero/i separati da virgola, oppure 0 per finire",
        "ignored_toggle": "Scelta non valida ignorata: {item}",
        "menu_title": "Menu principale:",
        "menu_install": "Installazione",
        "menu_csv": "Traduzione CSV manuale",
        "menu_maintenance": "Manutenzione",
        "menu_1": "Installa lingua: normale + fix font + loading tips",
        "menu_2": "Installazione custom: scegli cosa NON tradurre",
        "menu_3": "Installa lingua con fallback ASCII/font-safe",
        "menu_4": "Esporta solo London2038 non tradotto automaticamente",
        "menu_5": "Esporta tutti i testi London2038",
        "menu_6": "Esporta tutti i testi inglesi",
        "menu_7": "Importa CSV tradotto",
        "menu_8": "Mostra lingue sorgenti disponibili",
        "menu_9": "Ripristina file originali",
        "menu_10": "Dry run installazione normale",
        "menu_0": "Esci",
        "choose_action": "Scegli azione",
        "csv_output": "Percorso export CSV",
        "csv_input": "Percorso import CSV",
    },
    "fr": {
        "script_language": "Langue du script",
        "english": "Anglais",
        "czech_ui": "Tchèque",
        "choose_number": "Choisis un nombre de {minimum} à {maximum}.",
        "found_folders": "Dossiers Hellgate trouvés :",
        "custom_path": "Entrer un chemin personnalisé",
        "game_folder": "Dossier du jeu",
        "game_folder_manual": "Dossier Hellgate contenant Data",
        "languages": "Langues :",
        "custom_language": "Entrer une autre langue",
        "install_language": "Installer la langue",
        "language_name": "Nom de la langue",
        "font_atlas": "Font atlas pour corriger la police :",
        "no_font_atlas": "Pas de patch font atlas",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "Portée de l'export CSV :",
        "csv_missing": "Seulement London2038 non traduit automatiquement",
        "csv_london": "Tous les textes London2038",
        "csv_all": "Tout",
        "csv_scope_prompt": "Portée CSV",
        "toggle_title": "Sélectionne les tables à NE PAS traduire :",
        "done": "Terminé",
        "toggle_hint": "Sélectionné [X] = garder cette table en anglais.",
        "toggle_prompt": "Numéro(s) séparés par virgule, ou 0 pour terminer",
        "ignored_toggle": "Choix invalide ignoré : {item}",
        "menu_title": "Menu principal :",
        "menu_install": "Installation",
        "menu_csv": "Traduction CSV manuelle",
        "menu_maintenance": "Maintenance",
        "menu_1": "Installer la langue : normal + correction police + loading tips",
        "menu_2": "Installation personnalisée : choisir quoi NE PAS traduire",
        "menu_3": "Installer la langue avec fallback ASCII/font-safe",
        "menu_4": "Exporter seulement London2038 non traduit automatiquement",
        "menu_5": "Exporter tous les textes London2038",
        "menu_6": "Exporter tous les textes anglais",
        "menu_7": "Importer le CSV traduit",
        "menu_8": "Lister les langues source disponibles",
        "menu_9": "Restaurer les fichiers originaux",
        "menu_10": "Dry run installation normale",
        "menu_0": "Quitter",
        "choose_action": "Choisir une action",
        "csv_output": "Chemin export CSV",
        "csv_input": "Chemin import CSV",
    },
    "es": {
        "script_language": "Idioma del script",
        "english": "Inglés",
        "czech_ui": "Checo",
        "choose_number": "Elige un número de {minimum} a {maximum}.",
        "found_folders": "Carpetas Hellgate encontradas:",
        "custom_path": "Introducir ruta personalizada",
        "game_folder": "Carpeta del juego",
        "game_folder_manual": "Carpeta Hellgate que contiene Data",
        "languages": "Idiomas:",
        "custom_language": "Introducir otro idioma",
        "install_language": "Instalar idioma",
        "language_name": "Nombre del idioma",
        "font_atlas": "Font atlas para corregir la fuente:",
        "no_font_atlas": "Sin parche font atlas",
        "font_atlas_prompt": "Font atlas",
        "csv_scope": "Alcance de exportación CSV:",
        "csv_missing": "Solo London2038 sin traducción automática",
        "csv_london": "Todos los textos London2038",
        "csv_all": "Todo",
        "csv_scope_prompt": "Alcance CSV",
        "toggle_title": "Selecciona tablas que NO quieres traducir:",
        "done": "Listo",
        "toggle_hint": "Seleccionado [X] = mantener esta tabla en inglés.",
        "toggle_prompt": "Número(s) separados por coma, o 0 para terminar",
        "ignored_toggle": "Opción inválida ignorada: {item}",
        "menu_title": "Menú principal:",
        "menu_install": "Instalación",
        "menu_csv": "Traducción CSV manual",
        "menu_maintenance": "Mantenimiento",
        "menu_1": "Instalar idioma: normal + arreglo de fuente + loading tips",
        "menu_2": "Instalación personalizada: elegir qué NO traducir",
        "menu_3": "Instalar idioma con fallback ASCII/font-safe",
        "menu_4": "Exportar solo London2038 sin traducción automática",
        "menu_5": "Exportar todos los textos London2038",
        "menu_6": "Exportar todos los textos ingleses",
        "menu_7": "Importar CSV traducido",
        "menu_8": "Listar idiomas fuente disponibles",
        "menu_9": "Restaurar archivos originales",
        "menu_10": "Dry run instalación normal",
        "menu_0": "Salir",
        "choose_action": "Elegir acción",
        "csv_output": "Ruta de exportación CSV",
        "csv_input": "Ruta de importación CSV",
    },
}

SCRIPT_UI_LANGUAGES = [
    ("en", "English"),
    ("cs", "Čeština"),
    ("ru", "Русский"),
    ("pl", "Polski"),
    ("hu", "Magyar"),
    ("it", "Italiano"),
    ("fr", "Français"),
    ("es", "Español"),
]

UI_UPDATES = {
    "en": {"menu_1": "Install language", "done_play": "Done. You can play the game."},
    "cs": {"menu_1": "Instalovat jazyk", "done_play": "Hotovo. Muzes hrat hru."},
    "ru": {"menu_1": "Установить язык", "done_play": "Готово. Можно играть."},
    "pl": {"menu_1": "Zainstaluj język", "done_play": "Gotowe. Możesz grać."},
    "hu": {"menu_1": "Nyelv telepítése", "done_play": "Kész. Játszhatsz a játékkal."},
    "it": {"menu_1": "Installa lingua", "done_play": "Fatto. Puoi giocare."},
    "fr": {"menu_1": "Installer la langue", "done_play": "Terminé. Tu peux jouer."},
    "es": {"menu_1": "Instalar idioma", "done_play": "Listo. Puedes jugar."},
}

for _lang, _values in UI_UPDATES.items():
    UI.setdefault(_lang, {}).update(_values)


@dataclass
class CryptVariant:
    name: str
    key1: int
    key2: int
    key3: int = 0x29A


CRYPT_OLD = CryptVariant("old", 0x00010DCD, 0x0F4559D5)
CRYPT_L2038 = CryptVariant("l2038", 0x000007F6, 0x1017D017)
CRYPT_VARIANTS = (CRYPT_OLD, CRYPT_L2038)


def log_detail(message: str) -> None:
    if DETAILED_DECRYPT_LOG:
        print(f"[detail] {message}")


@dataclass
class Entry:
    entry_offset: int
    directory: str
    name: str
    data_offset: int
    size_uncompressed: int
    size_compressed: int

    @property
    def path(self) -> str:
        return f"{self.directory}{self.name}"


@dataclass
class Archive:
    base: str
    dat_path: Path
    idx_path: Path
    idx_plain: bytearray
    crypt: CryptVariant
    strings: list[str]
    entries: list[Entry]


def u32(buf: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def put_u32(buf: bytearray, off: int, value: int) -> None:
    struct.pack_into("<I", buf, off, value & 0xFFFFFFFF)


def crypt_idx(data: bytes | bytearray, variant: CryptVariant, encrypt: bool) -> bytearray:
    out = bytearray(data)
    table_count = 0x20
    table_size = table_count * 4
    cached_block = -1
    table = b""

    for off in range(len(out)):
        block = (off // table_size) * table_size
        if block != cached_block:
            cached_block = block
            v = (block + variant.key3) & 0xFFFFFFFF
            parts = []
            for _ in range(table_count):
                v = ((v * variant.key1) + variant.key2) & 0xFFFFFFFF
                parts.append(struct.pack("<I", v))
            table = b"".join(parts)

        key = table[off - block]
        out[off] = (out[off] + key) & 0xFF if encrypt else (out[off] - key) & 0xFF

    return out


def valid_plain_idx(buf: bytes | bytearray) -> bool:
    if len(buf) < 32 or bytes(buf[:4]) != b"nigh":
        return False
    version = u32(buf, 4)
    file_count = u32(buf, 8)
    return version in (4, 5) and 0 < file_count < 100000 and buf.find(b"spgh") >= 0


def decrypt_idx_file(path: Path) -> tuple[bytearray, CryptVariant]:
    raw = path.read_bytes()
    log_detail(f"IDX decrypt start: {path.name} bytes={len(raw)}")
    for variant in CRYPT_VARIANTS:
        log_detail(
            f"  try crypt={variant.name} key1=0x{variant.key1:08X} "
            f"key2=0x{variant.key2:08X} key3=0x{variant.key3:08X}"
        )
        plain = crypt_idx(raw, variant, encrypt=False)
        if valid_plain_idx(plain):
            first = plain.find(b"spgh")
            second = plain.find(b"spgh", first + 4)
            third = plain.find(b"spgh", second + 4)
            log_detail(
                f"  success crypt={variant.name} header=nigh "
                f"version={u32(plain, 4)} file_count={u32(plain, 8)} "
                f"spgh=[0x{first:X},0x{second:X},0x{third:X}]"
            )
            return plain, variant
        header = bytes(plain[:4]).decode("latin-1", errors="replace")
        log_detail(f"  reject crypt={variant.name} decrypted_header={header!r}")
    log_detail(f"IDX decrypt failed: {path.name}")
    raise RuntimeError(f"Cannot decrypt IDX: {path}")


def norm_dir(value: str) -> str:
    value = value.replace("/", "\\").lower()
    if value and not value.endswith("\\"):
        value += "\\"
    return value


def path_language_dir(directory: str) -> str | None:
    d = norm_dir(directory)
    marker = "\\excel\\strings\\"
    pos = d.find(marker)
    if pos < 0:
        return None
    rest = d[pos + len(marker) :]
    return rest.split("\\", 1)[0] if rest else None


def parse_idx_strings(idx: bytes | bytearray) -> list[str]:
    first = idx.find(b"spgh")
    second = idx.find(b"spgh", first + 4)
    if first < 0 or second < 0:
        raise RuntimeError("IDX missing string sections")
    area = bytes(idx[first + 12 : second])
    if area.endswith(b"\x00"):
        area = area[:-1]
    if not area:
        return []
    strings = [part.decode("latin-1") for part in area.split(b"\x00")]
    log_detail(f"  string table parsed: count={len(strings)} bytes={len(area)}")
    return strings


def parse_entries(idx: bytes | bytearray, strings: list[str], dat_size: int) -> list[Entry]:
    entries: list[Entry] = []
    first = idx.find(b"spgh")
    second = idx.find(b"spgh", first + 4)
    third = idx.find(b"spgh", second + 4)
    if first < 0 or second < 0 or third < 0:
        return entries

    record_count = u32(idx, 8)
    start = third + 4
    record_size = 80
    skipped_bad_token = 0
    skipped_bad_bounds = 0

    for index in range(record_count):
        entry = start + (index * record_size)
        if entry + 76 > len(idx):
            break
        if bytes(idx[entry : entry + 4]) != b"oigh":
            skipped_bad_token += 1
            continue

        data_offset = u32(idx, entry + 12)
        size_uncompressed = u32(idx, entry + 20)
        size_compressed = u32(idx, entry + 24)
        dir_index = u32(idx, entry + 32)
        name_index = u32(idx, entry + 36)
        if (
            data_offset >= dat_size
            or size_compressed == 0
            or size_compressed > dat_size
            or dir_index >= len(strings)
            or name_index >= len(strings)
        ):
            skipped_bad_bounds += 1
            continue

        entries.append(
            Entry(
                entry_offset=entry,
                directory=strings[dir_index],
                name=strings[name_index],
                data_offset=data_offset,
                size_uncompressed=size_uncompressed,
                size_compressed=size_compressed,
            )
        )
    log_detail(
        f"  entries parsed: records={record_count} valid={len(entries)} "
        f"skipped_token={skipped_bad_token} skipped_bounds={skipped_bad_bounds} "
        f"dat_size={dat_size}"
    )
    return entries


def load_archive(data_dir: Path, idx_path: Path) -> Archive:
    dat_path = idx_path.with_suffix(".dat")
    if not dat_path.exists():
        raise RuntimeError(f"DAT missing for {idx_path.name}")
    log_detail(f"Archive load: idx={idx_path.name} dat={dat_path.name} dat_bytes={dat_path.stat().st_size}")
    idx_plain, crypt = decrypt_idx_file(idx_path)
    strings = parse_idx_strings(idx_plain)
    entries = parse_entries(idx_plain, strings, dat_path.stat().st_size)
    archive = Archive(
        base=idx_path.stem,
        dat_path=dat_path,
        idx_path=idx_path,
        idx_plain=idx_plain,
        crypt=crypt,
        strings=strings,
        entries=entries,
    )
    log_detail(
        f"Archive ready: base={archive.base} crypt={archive.crypt.name} "
        f"strings={len(archive.strings)} entries={len(archive.entries)}"
    )
    return archive


def read_entry_plain(dat_path: Path, entry: Entry) -> bytes:
    with dat_path.open("rb") as fh:
        fh.seek(entry.data_offset)
        compressed = fh.read(entry.size_compressed)
    if len(compressed) != entry.size_compressed:
        raise RuntimeError(f"Short read: {dat_path.name}:{entry.path}")
    plain = zlib.decompress(compressed)
    if len(plain) != entry.size_uncompressed:
        raise RuntimeError(f"Size mismatch after decompress: {dat_path.name}:{entry.path}")
    return plain


@dataclass
class StringRow:
    ref: int
    unknown: int
    string_id: str
    reserved: int
    text: str
    attrs: list[str]


def parse_cooked_strings(data: bytes) -> tuple[int, list[StringRow]]:
    if len(data) < 12 or u32(data, 0) != 0x68667374:
        raise ValueError("Not a cooked string file")
    version = u32(data, 4)
    count = u32(data, 8)
    off = 12
    rows: list[StringRow] = []

    for _ in range(count):
        ref = u32(data, off)
        off += 4
        unknown = u32(data, off)
        off += 4
        id_len = u32(data, off)
        off += 4
        string_id = data[off : off + id_len].decode("latin-1")
        off += id_len + 1
        reserved = u32(data, off)
        off += 4
        byte_count = u32(data, off)
        off += 4
        raw_text = data[off : off + byte_count]
        off += byte_count
        if len(raw_text) >= 2:
            raw_text = raw_text[:-2]
        text = raw_text.decode("utf-16le", errors="replace")
        attr_count = u32(data, off)
        off += 4
        attrs: list[str] = []
        for _ in range(attr_count):
            chars = u32(data, off)
            off += 4
            raw_attr = data[off : off + ((chars + 1) * 2)]
            off += (chars + 1) * 2
            if len(raw_attr) >= 2:
                raw_attr = raw_attr[:-2]
            attrs.append(raw_attr.decode("utf-16le", errors="replace"))
        rows.append(StringRow(ref, unknown, string_id, reserved, text, attrs))

    if off != len(data):
        raise ValueError(f"Cooked parse ended at {off}, file size is {len(data)}")
    return version, rows


def write_utf16z_with_byte_count(out: bytearray, text: str) -> None:
    raw = text.encode("utf-16le")
    out.extend(struct.pack("<I", len(raw) + 2))
    out.extend(raw)
    out.extend(b"\x00\x00")


def write_utf16z_with_char_count(out: bytearray, text: str) -> None:
    raw = text.encode("utf-16le")
    out.extend(struct.pack("<I", len(text)))
    out.extend(raw)
    out.extend(b"\x00\x00")


def build_cooked_strings(version: int, rows: list[StringRow]) -> bytes:
    out = bytearray()
    out.extend(struct.pack("<III", 0x68667374, version, len(rows)))
    for row in rows:
        out.extend(struct.pack("<II", row.ref, row.unknown))
        raw_id = row.string_id.encode("latin-1")
        out.extend(struct.pack("<I", len(raw_id)))
        out.extend(raw_id)
        out.append(0)
        out.extend(struct.pack("<I", row.reserved))
        write_utf16z_with_byte_count(out, row.text or "")
        attrs = [a for a in row.attrs if a]
        out.extend(struct.pack("<I", len(attrs)))
        for attr in attrs:
            write_utf16z_with_char_count(out, attr)
    return bytes(out)


def source_score(row: StringRow, language_dir: str) -> int:
    if not row.text:
        return -1
    if row.text.isdigit() and not row.attrs:
        return -1
    attrs = "\n".join(row.attrs).lower()
    lang_name = language_dir.lower()
    score = 10
    if lang_name in attrs:
        score += 70
    if "default" in attrs:
        score += 20
    if "masculine" in attrs:
        score += 10
    return score


def best_source_by_id(rows: list[StringRow], language_dir: str) -> dict[str, StringRow]:
    best: dict[str, tuple[int, StringRow]] = {}
    for row in rows:
        if not row.string_id:
            continue
        score = source_score(row, language_dir)
        if score < 0:
            continue
        old = best.get(row.string_id)
        if old is None or score > old[0]:
            best[row.string_id] = (score, row)
    return {key: value for key, (_, value) in best.items()}


def font_safe_text(text: str) -> str:
    text = text.translate(FONT_SAFE_TRANSLATION)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def merge_strings(
    target_data: bytes,
    source_rows: list[StringRow],
    language_dir: str,
    font_safe: bool,
) -> tuple[bytes, int, int]:
    version, target_rows = parse_cooked_strings(target_data)
    source_by_id = best_source_by_id(source_rows, language_dir)
    changed = 0
    for row in target_rows:
        source = source_by_id.get(row.string_id)
        if source:
            new_text = font_safe_text(source.text) if font_safe else source.text
            if row.text == new_text:
                continue
            row.text = new_text
            # Keep English attributes. The client is still running with Language=English.
            changed += 1
    return build_cooked_strings(version, target_rows), changed, len(target_rows)


def string_entries_by_language(archive: Archive, language_dir: str) -> dict[str, Entry]:
    result: dict[str, Entry] = {}
    for entry in archive.entries:
        if not entry.name.startswith("strings_") or not entry.name.endswith(".xls.uni.cooked"):
            continue
        if path_language_dir(entry.directory) == language_dir:
            result[entry.name] = entry
    return result


def discover_archives(data_dir: Path) -> list[Archive]:
    archives = []
    log_detail(f"Discover archives: {data_dir}")
    for idx_path in sorted(data_dir.glob(ARCHIVE_GLOB)):
        if idx_path.name.endswith(".dec") or ".bak" in idx_path.name:
            log_detail(f"  skip helper/bak idx: {idx_path.name}")
            continue
        dat_path = idx_path.with_suffix(".dat")
        if dat_path.exists():
            archives.append(load_archive(data_dir, idx_path))
        else:
            log_detail(f"  skip idx without dat: {idx_path.name}")
    log_detail(f"Discover archives done: count={len(archives)}")
    return archives


def discover_languages(archives: list[Archive]) -> list[str]:
    languages = set()
    for archive in archives:
        for entry in archive.entries:
            lang = path_language_dir(entry.directory)
            if lang and lang != TARGET_LANGUAGE_DIR:
                languages.add(lang)
    return sorted(languages)


def resolve_game_dir(value: str) -> Path:
    path = Path(value).expanduser()
    if (path / "Data").is_dir():
        return path
    if path.name.lower() == "data" and path.is_dir():
        return path.parent
    raise SystemExit(f"Game folder not found or missing Data/: {path}")


def is_game_dir(path: Path) -> bool:
    return (path / "Data").is_dir() and (
        (path / "Launcher.exe").exists()
        or (path / "MP_x64").is_dir()
        or (path / "MP_x86").is_dir()
        or any((path / "Data").glob("*localized*.idx"))
    )


def candidate_game_dirs() -> list[Path]:
    here = Path(__file__).resolve().parent
    candidates: list[Path] = []
    env_names = ("HELLGATE_DIR", "GAME_DIR", "LONDON2038_DIR")
    for name in env_names:
        value = os.environ.get(name)
        if value:
            candidates.append(Path(value).expanduser())

    candidates.extend(
        [
            here,
            here.parent,
            here.parent / "london2038" / "wineprefix" / "drive_c" / "Program Files" / "Flagship Studios" / "Hellgate London",
            Path.cwd(),
            Path.cwd() / "london2038" / "wineprefix" / "drive_c" / "Program Files" / "Flagship Studios" / "Hellgate London",
            Path.home() / ".local" / "share" / "london2038" / "wineprefix" / "drive_c" / "London2038",
            Path.home() / ".local" / "share" / "london2038" / "wineprefix" / "drive_c" / "Program Files" / "Flagship Studios" / "Hellgate London",
            Path("C:/London2038"),
            Path("C:/Program Files/Flagship Studios/Hellgate London"),
            Path("C:/Program Files (x86)/Flagship Studios/Hellgate London"),
            Path("D:/London2038"),
            Path("D:/Program Files/Flagship Studios/Hellgate London"),
            Path("D:/Program Files (x86)/Flagship Studios/Hellgate London"),
        ]
    )

    found: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if is_game_dir(resolved):
            found.append(resolved)
    return found


def auto_find_game_dir() -> Path | None:
    found = candidate_game_dirs()
    return found[0] if found else None


def repacker_root(data_dir: Path) -> Path:
    return data_dir / REPACKER_DIR_NAME


class Tee:
    def __init__(self, *streams: object) -> None:
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def setup_run_logging(data_dir: Path, action: str) -> Path:
    log_dir = repacker_root(data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    log_path = log_dir / f"{stamp}-{action}.log"
    log_fh = log_path.open("w", encoding="utf-8")
    sys.stdout = Tee(sys.stdout, log_fh)  # type: ignore[assignment]
    sys.stderr = Tee(sys.stderr, log_fh)  # type: ignore[assignment]
    print(f"Run log: {log_path}")
    print(f"Started: {_dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"Action: {action}")
    return log_path


def ensure_language_backup(data_dir: Path) -> Path:
    backup_dir = repacker_root(data_dir) / "backup" / "original"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_lang = backup_dir / "language.dat"
    current_lang = data_dir / "language.dat"
    if not backup_lang.exists():
        if current_lang.exists() and current_lang.read_text(errors="ignore").strip() == LANGUAGE_DAT_TEXT:
            shutil.copy2(current_lang, backup_lang)
        else:
            backup_lang.write_text(LANGUAGE_DAT_TEXT, encoding="ascii")
    return backup_lang


def fix_language_dat(data_dir: Path, reason: str) -> None:
    ensure_language_backup(data_dir)
    lang = data_dir / "language.dat"
    old = lang.read_text(errors="ignore").strip() if lang.exists() else "(missing)"
    if old != LANGUAGE_DAT_TEXT:
        print(f"Fixing language.dat ({reason}): {old!r} -> {LANGUAGE_DAT_TEXT!r}")
    else:
        print(f"language.dat OK ({reason}): {LANGUAGE_DAT_TEXT}")
    lang.write_text(LANGUAGE_DAT_TEXT, encoding="ascii")


def backup_originals(data_dir: Path, archive_names: list[str]) -> Path:
    backup_dir = repacker_root(data_dir) / "backup" / "original"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ensure_language_backup(data_dir)

    legacy_backups = [
        data_dir / "czech-repack-original-backup",
        data_dir / "dawert-language-repacker-backup" / "original",
    ]
    for base in archive_names:
        for ext in ("dat", "idx"):
            target = backup_dir / f"{base}.{ext}"
            if target.exists():
                continue
            current = data_dir / f"{base}.{ext}"
            source = current
            for legacy_backup in legacy_backups:
                legacy = legacy_backup / f"{base}.{ext}"
                if legacy.exists():
                    source = legacy
                    break
            if not source.exists():
                raise RuntimeError(f"Missing archive file for backup: {base}.{ext}")
            shutil.copy2(source, target)
    return backup_dir


def copy_current_snapshot(data_dir: Path, archive_names: list[str]) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot = repacker_root(data_dir) / "backup" / f"before-install-{stamp}"
    snapshot.mkdir(parents=True, exist_ok=True)
    for base in archive_names:
        for ext in ("dat", "idx"):
            source = data_dir / f"{base}.{ext}"
            if source.exists():
                shutil.copy2(source, snapshot / source.name)
    lang = data_dir / "language.dat"
    if lang.exists():
        shutil.copy2(lang, snapshot / "language.dat")
    return snapshot


def restore_originals(game_dir: Path) -> None:
    data_dir = game_dir / "Data"
    backup_dir = repacker_root(data_dir) / "backup" / "original"
    if not backup_dir.is_dir():
        raise SystemExit(f"Backup folder not found: {backup_dir}")
    for file in backup_dir.glob("*.dat"):
        shutil.copy2(file, data_dir / file.name)
    for file in backup_dir.glob("*.idx"):
        shutil.copy2(file, data_dir / file.name)
    backup_lang = ensure_language_backup(data_dir)
    shutil.copy2(backup_lang, data_dir / "language.dat")
    fix_language_dat(data_dir, "restore")
    print(f"Restored original archives from: {backup_dir}")
    print(color_text(tr("done_play"), "green", bold=True))


def append_patch_archive(
    original_archive: Archive,
    source_same_archive: dict[str, list[StringRow]],
    global_source: dict[str, list[StringRow]],
    language_dir: str,
    excludes: set[str],
    output_dir: Path,
    font_safe: bool,
) -> tuple[Path, Path, list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_dat = output_dir / original_archive.dat_path.name
    out_idx = output_dir / original_archive.idx_path.name
    shutil.copy2(original_archive.dat_path, out_dat)
    idx = bytearray(original_archive.idx_plain)
    changed_log: list[str] = []

    target_entries = string_entries_by_language(original_archive, TARGET_LANGUAGE_DIR)
    with out_dat.open("r+b") as dfh:
        for name, entry in sorted(target_entries.items()):
            if name in excludes:
                changed_log.append(f"SKIP excluded {original_archive.base}:{name}")
                continue

            source_rows = source_same_archive.get(name) or global_source.get(name)
            if not source_rows:
                changed_log.append(f"SKIP no source {original_archive.base}:{name}")
                continue

            target_plain = read_entry_plain(original_archive.dat_path, entry)
            merged, changed, total = merge_strings(target_plain, source_rows, language_dir, font_safe)
            if changed == 0:
                changed_log.append(f"UNCHANGED {original_archive.base}:{name} total={total}")
                continue

            compressed = zlib.compress(merged, 9)
            dfh.seek(0, os.SEEK_END)
            off = dfh.tell()
            pad = (0x200 - (off % 0x200)) % 0x200
            if pad:
                dfh.write(b"\x00" * pad)
                off += pad
            dfh.write(compressed)

            put_u32(idx, entry.entry_offset + 12, off)
            put_u32(idx, entry.entry_offset + 20, len(merged))
            put_u32(idx, entry.entry_offset + 24, len(compressed))
            changed_log.append(
                f"PATCH {original_archive.base}:{name} changed={changed}/{total} "
                f"off=0x{off:X} usz={len(merged)} csz={len(compressed)}"
            )

    encrypted = crypt_idx(idx, original_archive.crypt, encrypt=True)
    out_idx.write_bytes(encrypted)
    return out_dat, out_idx, changed_log


def normalize_archive_path(value: str) -> str:
    return value.replace("/", "\\").lower()


def find_entry_by_path(archive: Archive, path: str) -> Entry | None:
    wanted = normalize_archive_path(path)
    for entry in archive.entries:
        if normalize_archive_path(entry.path) == wanted:
            return entry
    return None


def append_patch_raw_entry(
    original_archive: Archive,
    target_entry: Entry,
    replacement_plain: bytes,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_dat = output_dir / original_archive.dat_path.name
    out_idx = output_dir / original_archive.idx_path.name
    shutil.copy2(original_archive.dat_path, out_dat)
    idx = bytearray(original_archive.idx_plain)

    compressed = zlib.compress(replacement_plain, 9)
    with out_dat.open("r+b") as dfh:
        dfh.seek(0, os.SEEK_END)
        off = dfh.tell()
        pad = (0x200 - (off % 0x200)) % 0x200
        if pad:
            dfh.write(b"\x00" * pad)
            off += pad
        dfh.write(compressed)

    put_u32(idx, target_entry.entry_offset + 12, off)
    put_u32(idx, target_entry.entry_offset + 20, len(replacement_plain))
    put_u32(idx, target_entry.entry_offset + 24, len(compressed))
    out_idx.write_bytes(crypt_idx(idx, original_archive.crypt, encrypt=True))
    return out_dat, out_idx


def patch_font_atlas(original_dir: Path, language_dir: str, output_dir: Path) -> list[str]:
    idx_path = original_dir / f"{FONT_ARCHIVE_BASE}.idx"
    if not idx_path.exists():
        return [f"SKIP font atlas: {idx_path.name} not found"]

    archive = load_archive(original_dir, idx_path)
    target_entry = find_entry_by_path(archive, FONT_ATLAS_TARGET)
    if not target_entry:
        return [f"SKIP font atlas: target not found: {FONT_ATLAS_TARGET}"]

    source_path = FONT_ATLAS_BY_LANGUAGE.get(language_dir)
    if not source_path:
        return [f"SKIP font atlas: no known atlas for language '{language_dir}'"]

    source_entry = find_entry_by_path(archive, source_path)
    if not source_entry:
        return [f"SKIP font atlas: source not found: {source_path}"]

    replacement_plain = read_entry_plain(archive.dat_path, source_entry)
    append_patch_raw_entry(archive, target_entry, replacement_plain, output_dir)
    return [
        f"PATCH {FONT_ARCHIVE_BASE}:{FONT_ATLAS_TARGET} <- {source_path} "
        f"usz={len(replacement_plain)}"
    ]


def normalize_language(value: str) -> str:
    key = value.strip().lower()
    return LANGUAGE_ALIASES.get(key, key)


def tr(key: str, **kwargs: object) -> str:
    text = UI.get(UI_LANG, UI["en"]).get(key, UI["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "blue": "\033[34m",
}


def supports_color() -> bool:
    return os.environ.get("NO_COLOR") is None and bool(getattr(sys.stdout, "isatty", lambda: False)())


def color_text(text: str, color_name: str, bold: bool = False) -> str:
    if not supports_color():
        return text
    prefix = ANSI["bold"] if bold else ""
    prefix += ANSI.get(color_name, "")
    return f"{prefix}{text}{ANSI['reset']}"


def prompt_script_language() -> None:
    global UI_LANG
    print("Script language / Jazyk scriptu:")
    for index, (_, label) in enumerate(SCRIPT_UI_LANGUAGES, start=1):
        print(f"  {index}. {label}")
    while True:
        raw = input("Choose / Vyber [1]: ").strip()
        if not raw:
            UI_LANG = "en"
            return
        if raw.isdigit() and 1 <= int(raw) <= len(SCRIPT_UI_LANGUAGES):
            UI_LANG = SCRIPT_UI_LANGUAGES[int(raw) - 1][0]
            return
        print(f"Choose 1-{len(SCRIPT_UI_LANGUAGES)}. / Vyber 1-{len(SCRIPT_UI_LANGUAGES)}.")


def print_banner() -> None:
    banner = r"""
 ____      _    __        _______ ____ _____
|  _ \    / \   \ \      / / ____|  _ \_   _|
| | | |  / _ \   \ \ /\ / /|  _| | |_) || |
| |_| | / ___ \   \ V  V / | |___|  _ < | |
|____/ /_/   \_\   \_/\_/  |_____|_| \_\|_|

Hellgate London / London2038 Language Repacker
""".strip("\n").splitlines()
    palette = ("cyan", "blue", "magenta", "yellow", "green")
    if supports_color():
        for index, line in enumerate(banner):
            print(color_text(line, palette[index % len(palette)], bold=index < 5))
            time.sleep(0.035)
    else:
        print("\n".join(banner))


def prompt_number(label: str, minimum: int, maximum: int, default: int | None = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        if raw.isdigit():
            value = int(raw)
            if minimum <= value <= maximum:
                return value
        print(tr("choose_number", minimum=minimum, maximum=maximum))


def prompt_game_dir() -> str:
    found = candidate_game_dirs()
    if found:
        print(tr("found_folders"))
        for index, path in enumerate(found, start=1):
            print(f"  {index}. {path}")
        print(f"  {len(found) + 1}. {tr('custom_path')}")
        choice = prompt_number(tr("game_folder"), 1, len(found) + 1, 1)
        if choice <= len(found):
            return str(found[choice - 1])
    return input(f"{tr('game_folder_manual')}: ").strip().strip('"')


def available_languages_for_game(game_dir: str) -> list[str]:
    try:
        archives = discover_archives(resolve_game_dir(game_dir) / "Data")
        return discover_languages(archives)
    except Exception:
        return []


def prompt_language(game_dir: str) -> str:
    languages = available_languages_for_game(game_dir)
    if not languages:
        languages = ["czech", "polish", "russian", "french", "spanish", "italian", "hungarian"]

    print(f"\n{tr('languages')}")
    for index, language in enumerate(languages, start=1):
        print(f"  {index}. {language}")
    print(f"  {len(languages) + 1}. {tr('custom_language')}")
    choice = prompt_number(tr("install_language"), 1, len(languages) + 1, 1)
    if choice <= len(languages):
        return languages[choice - 1]
    return input(f"{tr('language_name')}: ").strip()


def prompt_font_atlas_language(game_dir: str) -> str:
    languages = [lang for lang in available_languages_for_game(game_dir) if lang in FONT_ATLAS_BY_LANGUAGE]
    if not languages:
        languages = sorted(FONT_ATLAS_BY_LANGUAGE)

    print(f"\n{tr('font_atlas')}")
    print(f"  0. {tr('no_font_atlas')}")
    for index, language in enumerate(languages, start=1):
        print(f"  {index}. {language}")
    choice = prompt_number(tr("font_atlas_prompt"), 0, len(languages), 1)
    if choice == 0:
        return ""
    return languages[choice - 1]


def prompt_csv_scope() -> str:
    print(f"\n{tr('csv_scope')}")
    print(f"  1. {tr('csv_missing')}")
    print(f"  2. {tr('csv_london')}")
    print(f"  3. {tr('csv_all')}")
    choice = prompt_number(tr("csv_scope_prompt"), 1, 3, 1)
    if choice == 1:
        return "london2038-untranslated"
    if choice == 2:
        return "london2038"
    return "all"


def english_string_table_names(game_dir: str) -> list[str]:
    try:
        archives = discover_archives(resolve_game_dir(game_dir) / "Data")
    except Exception:
        return sorted(DEFAULT_EXCLUDES)

    names: set[str] = set()
    for archive in archives:
        names.update(string_entries_by_language(archive, TARGET_LANGUAGE_DIR).keys())
    return sorted(names)


def prompt_excludes(game_dir: str, include_loadingtips: bool) -> list[str] | None:
    tables = english_string_table_names(game_dir)
    selected = set() if include_loadingtips else set(DEFAULT_EXCLUDES)

    def short_name(table: str) -> str:
        if table.startswith("strings_") and table.endswith(".xls.uni.cooked"):
            return table[len("strings_") : -len(".xls.uni.cooked")]
        return table

    while True:
        print(f"\n{tr('toggle_title')}")
        print(f"  0. {tr('done')}")
        for index, table in enumerate(tables, start=1):
            mark = "X" if table in selected else " "
            print(f"  {index}. [{mark}] {short_name(table)}")
        print(tr("toggle_hint"))
        raw = input(f"{tr('toggle_prompt')}: ").strip().lower()
        if not raw or raw == "0" or raw in ("done", "d"):
            break
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            if not item.isdigit() or not (1 <= int(item) <= len(tables)):
                print(tr("ignored_toggle", item=item))
                continue
            table = tables[int(item) - 1]
            if table in selected:
                selected.remove(table)
            else:
                selected.add(table)

    return sorted(selected) if selected else ["none"]


def parse_excludes(values: list[str] | None) -> set[str]:
    excludes = set(DEFAULT_EXCLUDES)
    if not values:
        return excludes
    for raw in values:
        for item in raw.split(","):
            item = item.strip().lower()
            if not item:
                continue
            if item in ("none", "no", "empty"):
                excludes.clear()
                continue
            if item.startswith("strings_") and item.endswith(".xls.uni.cooked"):
                excludes.add(item)
            else:
                excludes.add(f"strings_{item}.xls.uni.cooked")
    return excludes


def build_install(
    game_dir: Path,
    language_dir: str,
    excludes: set[str],
    dry_run: bool,
    font_safe: bool,
    patch_fonts: bool,
) -> None:
    data_dir = game_dir / "Data"
    current_archives = discover_archives(data_dir)
    if not current_archives:
        raise SystemExit(f"No localized archives found in {data_dir}")

    archive_names = [archive.base for archive in current_archives]
    if patch_fonts and (data_dir / f"{FONT_ARCHIVE_BASE}.idx").exists():
        archive_names.append(FONT_ARCHIVE_BASE)
    original_dir = backup_originals(data_dir, archive_names)
    original_archives = discover_archives(original_dir)
    available = discover_languages(original_archives)
    if language_dir not in available:
        raise SystemExit(
            f"Language '{language_dir}' not found in original archives.\n"
            f"Available: {', '.join(available) or '(none)'}"
        )

    print(f"Game: {game_dir}")
    print(f"Language source: {language_dir}")
    print(f"Target runtime language: English")
    print(f"Excluding: {', '.join(sorted(excludes)) or '(nothing)'}")
    print(f"Real font fix, language atlas patch: {'yes' if patch_fonts else 'no'}")
    print(f"ASCII/font-safe fallback: {'yes' if font_safe else 'no'}")
    print(f"Original backup: {original_dir}")

    per_archive_source: dict[str, dict[str, list[StringRow]]] = {}
    global_source: dict[str, list[StringRow]] = {}
    global_source_counts: dict[str, int] = {}

    for archive in original_archives:
        source_entries = string_entries_by_language(archive, language_dir)
        archive_map: dict[str, list[StringRow]] = {}
        for name, entry in source_entries.items():
            try:
                _, rows = parse_cooked_strings(read_entry_plain(archive.dat_path, entry))
            except Exception as exc:
                print(f"WARN source parse failed {archive.base}:{name}: {exc}")
                continue
            archive_map[name] = rows
            if len(rows) > global_source_counts.get(name, -1):
                global_source[name] = rows
                global_source_counts[name] = len(rows)
        per_archive_source[archive.base] = archive_map

    out_dir = repacker_root(data_dir) / "output" / language_dir
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_logs: list[str] = []
    for archive in original_archives:
        _, _, logs = append_patch_archive(
            archive,
            per_archive_source.get(archive.base, {}),
            global_source,
            language_dir,
            excludes,
            out_dir,
            font_safe,
        )
        all_logs.extend(logs)

    if patch_fonts:
        all_logs.extend(patch_font_atlas(original_dir, language_dir, out_dir))

    log_file = out_dir / "repack.log"
    log_file.write_text("\n".join(all_logs) + "\n", encoding="utf-8")
    print(f"Built repack: {out_dir}")
    print(f"Log: {log_file}")

    patched_count = sum(1 for line in all_logs if line.startswith("PATCH "))
    print(f"Patched tables: {patched_count}")

    if dry_run:
        print("Dry run requested; not installing files.")
        return

    snapshot = copy_current_snapshot(data_dir, archive_names)
    for base in archive_names:
        for ext in ("dat", "idx"):
            file = out_dir / f"{base}.{ext}"
            if file.exists():
                shutil.copy2(file, data_dir / file.name)
    fix_language_dat(data_dir, "install")
    print(f"Installed repack. Previous current files snapshot: {snapshot}")
    print(color_text(tr("done_play"), "green", bold=True))


def clean_original_archives(data_dir: Path, include_fonts: bool = False) -> tuple[Path, list[Archive], list[str]]:
    current_archives = discover_archives(data_dir)
    if not current_archives:
        raise SystemExit(f"No localized archives found in {data_dir}")
    archive_names = [archive.base for archive in current_archives]
    if include_fonts and (data_dir / f"{FONT_ARCHIVE_BASE}.idx").exists():
        archive_names.append(FONT_ARCHIVE_BASE)
    original_dir = backup_originals(data_dir, archive_names)
    return original_dir, discover_archives(original_dir), archive_names


def resolve_csv_path(game_dir: Path, value: str | None, default_name: str = DEFAULT_CSV_NAME) -> Path:
    if value:
        return Path(value).expanduser()
    return repacker_root(game_dir / "Data") / "exports" / default_name


def normalize_csv_scope(value: str | None) -> str:
    if not value:
        return "all"
    value = value.strip().lower().replace("-", "").replace("_", "")
    if value in ("all", "everything", "full"):
        return "all"
    if value in ("london2038", "2038", "l2038", "london"):
        return "london2038"
    if value in ("london2038untranslated", "2038untranslated", "l2038untranslated", "untranslated2038"):
        return "london2038-untranslated"
    raise SystemExit("CSV scope must be 'all', 'london2038', or 'london2038-untranslated'")


def archive_in_csv_scope(archive: Archive, scope: str) -> bool:
    if scope == "all":
        return True
    if scope in ("london2038", "london2038-untranslated"):
        return "2038" in archive.base.lower()
    return False


def source_rows_by_table(
    archives: list[Archive],
    language_dir: str,
) -> dict[str, dict[str, StringRow]]:
    best_rows: dict[str, dict[str, StringRow]] = {}
    best_counts: dict[str, int] = {}
    for archive in archives:
        for table, entry in string_entries_by_language(archive, language_dir).items():
            try:
                _, rows = parse_cooked_strings(read_entry_plain(archive.dat_path, entry))
            except Exception as exc:
                print(f"WARN source parse failed {archive.base}:{table}: {exc}")
                continue
            if len(rows) <= best_counts.get(table, -1):
                continue
            best_rows[table] = best_source_by_id(rows, language_dir)
            best_counts[table] = len(rows)
    return best_rows


def row_is_untranslated_by_language(
    row: StringRow,
    table: str,
    source_by_table: dict[str, dict[str, StringRow]],
) -> bool:
    if not row.string_id:
        return False
    source = source_by_table.get(table, {}).get(row.string_id)
    return source is None or not source.text


def export_english_csv(
    game_dir: Path,
    csv_path: Path,
    scope: str = "all",
    language_dir: str | None = None,
) -> None:
    data_dir = game_dir / "Data"
    original_dir, original_archives, _ = clean_original_archives(data_dir)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    scope = normalize_csv_scope(scope)
    if scope == "london2038-untranslated":
        if not language_dir:
            raise SystemExit("--language is required for --csv-scope london2038-untranslated")
        language_dir = normalize_language(language_dir)
        source_by_table = source_rows_by_table(original_archives, language_dir)
    else:
        source_by_table = {}

    row_count = 0
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for archive in original_archives:
            if not archive_in_csv_scope(archive, scope):
                continue
            for table, entry in sorted(string_entries_by_language(archive, TARGET_LANGUAGE_DIR).items()):
                try:
                    _, rows = parse_cooked_strings(read_entry_plain(archive.dat_path, entry))
                except Exception as exc:
                    print(f"WARN export skipped {archive.base}:{table}: {exc}")
                    continue
                for row in rows:
                    if scope == "london2038-untranslated" and not row_is_untranslated_by_language(
                        row,
                        table,
                        source_by_table,
                    ):
                        continue
                    writer.writerow(
                        {
                            "Archive": archive.base,
                            "Table": table,
                            "StringID": row.string_id,
                            "English": row.text or "",
                            "Translation": "",
                            "Directory": entry.directory,
                            "Attributes": "|".join(row.attrs),
                        }
                    )
                    row_count += 1

    print(f"Exported English strings: {csv_path}")
    print(f"Scope: {scope}")
    if language_dir:
        print(f"Compared language: {language_dir}")
    print(f"Rows: {row_count}")
    print(f"Source archives: {original_dir}")


def csv_get(row: dict[str, str], name: str) -> str:
    for key, value in row.items():
        if key.strip().lower() == name.lower():
            return value or ""
    return ""


def load_csv_translations(csv_path: Path) -> tuple[dict[tuple[str, str, str], str], dict[tuple[str, str], str]]:
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    by_archive: dict[tuple[str, str, str], str] = {}
    by_table: dict[tuple[str, str], str] = {}
    with csv_path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            archive = csv_get(raw, "Archive").strip()
            table = csv_get(raw, "Table").strip()
            string_id = csv_get(raw, "StringID").strip()
            translation = csv_get(raw, "Translation")
            if not table or not string_id or not translation.strip():
                continue
            translation = translation.rstrip("\r\n")
            if archive:
                by_archive[(archive, table, string_id)] = translation
            by_table[(table, string_id)] = translation
    return by_archive, by_table


def merge_strings_from_csv(
    archive_base: str,
    table: str,
    target_data: bytes,
    by_archive: dict[tuple[str, str, str], str],
    by_table: dict[tuple[str, str], str],
) -> tuple[bytes, int, int]:
    version, rows = parse_cooked_strings(target_data)
    changed = 0
    for row in rows:
        translation = by_archive.get((archive_base, table, row.string_id))
        if translation is None:
            translation = by_table.get((table, row.string_id))
        if translation is None or row.text == translation:
            continue
        row.text = translation
        changed += 1
    return build_cooked_strings(version, rows), changed, len(rows)


def apply_csv_to_cooked_data(
    archive_base: str,
    table: str,
    target_data: bytes,
    by_archive: dict[tuple[str, str, str], str],
    by_table: dict[tuple[str, str], str],
) -> tuple[bytes, int, int]:
    return merge_strings_from_csv(archive_base, table, target_data, by_archive, by_table)


def append_patch_archive_from_csv(
    original_archive: Archive,
    by_archive: dict[tuple[str, str, str], str],
    by_table: dict[tuple[str, str], str],
    excludes: set[str],
    output_dir: Path,
    source_same_archive: dict[str, list[StringRow]] | None = None,
    global_source: dict[str, list[StringRow]] | None = None,
    language_dir: str | None = None,
    font_safe: bool = False,
) -> tuple[Path, Path, list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_dat = output_dir / original_archive.dat_path.name
    out_idx = output_dir / original_archive.idx_path.name
    shutil.copy2(original_archive.dat_path, out_dat)
    idx = bytearray(original_archive.idx_plain)
    changed_log: list[str] = []

    with out_dat.open("r+b") as dfh:
        for table, entry in sorted(string_entries_by_language(original_archive, TARGET_LANGUAGE_DIR).items()):
            if table in excludes:
                changed_log.append(f"SKIP excluded {original_archive.base}:{table}")
                continue

            working = read_entry_plain(original_archive.dat_path, entry)
            base_changed = 0
            if language_dir:
                source_rows = (source_same_archive or {}).get(table) or (global_source or {}).get(table)
                if source_rows:
                    working, base_changed, total = merge_strings(working, source_rows, language_dir, font_safe)

            merged, csv_changed, total = apply_csv_to_cooked_data(
                original_archive.base,
                table,
                working,
                by_archive,
                by_table,
            )
            changed = base_changed + csv_changed
            if changed == 0:
                changed_log.append(f"UNCHANGED {original_archive.base}:{table} total={total}")
                continue

            compressed = zlib.compress(merged, 9)
            dfh.seek(0, os.SEEK_END)
            off = dfh.tell()
            pad = (0x200 - (off % 0x200)) % 0x200
            if pad:
                dfh.write(b"\x00" * pad)
                off += pad
            dfh.write(compressed)

            put_u32(idx, entry.entry_offset + 12, off)
            put_u32(idx, entry.entry_offset + 20, len(merged))
            put_u32(idx, entry.entry_offset + 24, len(compressed))
            changed_log.append(
                f"PATCH {original_archive.base}:{table} changed={changed}/{total} "
                f"base={base_changed} csv={csv_changed} "
                f"off=0x{off:X} usz={len(merged)} csz={len(compressed)}"
            )

    out_idx.write_bytes(crypt_idx(idx, original_archive.crypt, encrypt=True))
    return out_dat, out_idx, changed_log


def import_csv_translations(
    game_dir: Path,
    csv_path: Path,
    excludes: set[str],
    dry_run: bool,
    patch_font_language: str | None,
    base_language: str | None,
    font_safe: bool,
) -> None:
    data_dir = game_dir / "Data"
    patch_fonts = bool(patch_font_language)
    original_dir, original_archives, archive_names = clean_original_archives(data_dir, include_fonts=patch_fonts)
    by_archive, by_table = load_csv_translations(csv_path)
    if not by_archive and not by_table:
        raise SystemExit(f"No filled Translation values found in CSV: {csv_path}")

    if base_language:
        base_language = normalize_language(base_language)
        available = discover_languages(original_archives)
        if base_language not in available:
            raise SystemExit(
                f"Language '{base_language}' not found in original archives.\n"
                f"Available: {', '.join(available) or '(none)'}"
            )

        per_archive_source: dict[str, dict[str, list[StringRow]]] = {}
        global_source_rows: dict[str, list[StringRow]] = {}
        global_source_counts: dict[str, int] = {}
        for archive in original_archives:
            archive_map: dict[str, list[StringRow]] = {}
            for table, entry in string_entries_by_language(archive, base_language).items():
                try:
                    _, rows = parse_cooked_strings(read_entry_plain(archive.dat_path, entry))
                except Exception as exc:
                    print(f"WARN source parse failed {archive.base}:{table}: {exc}")
                    continue
                archive_map[table] = rows
                if len(rows) > global_source_counts.get(table, -1):
                    global_source_rows[table] = rows
                    global_source_counts[table] = len(rows)
            per_archive_source[archive.base] = archive_map
    else:
        per_archive_source = {}
        global_source_rows = {}

    out_dir = repacker_root(data_dir) / "output" / "csv-import"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Game: {game_dir}")
    print(f"CSV: {csv_path}")
    print(f"Target runtime language: English")
    print(f"Base automatic language merge: {base_language or 'no'}")
    print(f"Excluding: {', '.join(sorted(excludes)) or '(nothing)'}")
    print(f"Real font fix, language atlas patch: {patch_font_language or 'no'}")
    print(f"Original backup: {original_dir}")

    all_logs: list[str] = []
    for archive in original_archives:
        _, _, logs = append_patch_archive_from_csv(
            archive,
            by_archive,
            by_table,
            excludes,
            out_dir,
            per_archive_source.get(archive.base, {}),
            global_source_rows,
            base_language,
            font_safe,
        )
        all_logs.extend(logs)

    if patch_font_language:
        all_logs.extend(patch_font_atlas(original_dir, patch_font_language, out_dir))

    log_file = out_dir / "repack.log"
    log_file.write_text("\n".join(all_logs) + "\n", encoding="utf-8")
    print(f"Built CSV import repack: {out_dir}")
    print(f"Log: {log_file}")
    print(f"Patched tables: {sum(1 for line in all_logs if line.startswith('PATCH '))}")

    if dry_run:
        print("Dry run requested; not installing files.")
        return

    snapshot = copy_current_snapshot(data_dir, archive_names)
    for base in archive_names:
        for ext in ("dat", "idx"):
            file = out_dir / f"{base}.{ext}"
            if file.exists():
                shutil.copy2(file, data_dir / file.name)
    fix_language_dat(data_dir, "csv-import")
    print(f"Installed CSV import. Previous current files snapshot: {snapshot}")
    print(color_text(tr("done_play"), "green", bold=True))


def interactive_args() -> argparse.Namespace:
    prompt_script_language()
    print_banner()
    game = prompt_game_dir()

    print(color_text(f"\n{tr('menu_title')}", "green", bold=True))
    print(color_text(f"== {tr('menu_install')} ==", "cyan", bold=True))
    print(f"  1. {tr('menu_1')}")
    print(f"  2. {tr('menu_2')}")
    print(f"  3. {tr('menu_3')}")
    print(color_text(f"\n== {tr('menu_csv')} ==", "magenta", bold=True))
    print(f"  4. {tr('menu_4')}")
    print(f"  5. {tr('menu_5')}")
    print(f"  6. {tr('menu_6')}")
    print(f"  7. {tr('menu_7')}")
    print(color_text(f"\n== {tr('menu_maintenance')} ==", "yellow", bold=True))
    print(f"  8. {tr('menu_8')}")
    print(f"  9. {tr('menu_9')}")
    print(f"  10. {tr('menu_10')}")
    print(f"  0. {tr('menu_0')}")
    choice = prompt_number(tr("choose_action"), 0, 10, 1)
    if choice == 0:
        raise SystemExit(0)

    action = "install"
    language = ""
    font_safe = False
    patch_fonts = True
    dry = False
    include_loadingtips = True
    exclude: list[str] | None = None
    csv_path = ""
    csv_scope = "all"
    font_atlas_language = ""

    if choice in (4, 5, 6):
        action = "export-csv"
        if choice == 4:
            csv_scope = "london2038-untranslated"
            language = prompt_language(game)
            default_name = LONDON2038_UNTRANSLATED_CSV_NAME
        elif choice == 5:
            csv_scope = "london2038"
            default_name = LONDON2038_CSV_NAME
        else:
            csv_scope = "all"
            default_name = DEFAULT_CSV_NAME
        csv_path = input(f"{tr('csv_output')} [Data/{REPACKER_DIR_NAME}/exports/{default_name}]: ").strip().strip('"')
    elif choice == 7:
        action = "import-csv"
        csv_path = input(f"{tr('csv_input')} [Data/{REPACKER_DIR_NAME}/exports/{LONDON2038_UNTRANSLATED_CSV_NAME}]: ").strip().strip('"')
        language = prompt_language(game)
        font_atlas_language = language
        exclude = prompt_excludes(game, include_loadingtips=True)
    elif choice == 8:
        action = "list"
    elif choice == 9:
        action = "restore"
    else:
        language = prompt_language(game)
        if choice == 2:
            exclude = prompt_excludes(game, include_loadingtips=True)
        elif choice == 3:
            font_safe = True
        elif choice == 10:
            dry = True

    if exclude is None and include_loadingtips:
        exclude = ["none"]

    return argparse.Namespace(
        game_dir=game,
        language=language,
        action="install" if action == "dry-run" else action,
        dry_run=dry,
        exclude=exclude,
        font_safe=font_safe,
        no_font_patch=not patch_fonts,
        csv=csv_path or None,
        csv_scope=csv_scope,
        font_atlas_language=font_atlas_language or None,
        interactive=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Hellgate London / London2038 language repacker")
    parser.add_argument("--interactive", action="store_true", help="Prompt for game folder and language")
    parser.add_argument("--game-dir", help="Hellgate folder containing Data/")
    parser.add_argument("--auto-find", action="store_true", help="Try to find the Hellgate folder automatically")
    parser.add_argument("--language", help="Source language to merge into English")
    parser.add_argument("--action", choices=("install", "list", "restore", "export-csv", "import-csv"), default="install")
    parser.add_argument("--dry-run", action="store_true", help="Build output but do not install")
    parser.add_argument("--csv", help="CSV path for export-csv or import-csv")
    parser.add_argument(
        "--csv-scope",
        choices=("all", "london2038", "london2038-untranslated"),
        default="all",
        help=(
            "CSV export scope. Use london2038 for mp_hellgate_localized_2038* "
            "or london2038-untranslated for only rows missing in --language."
        ),
    )
    parser.add_argument(
        "--font-atlas-language",
        help="Language atlas to patch during CSV import, for example czech, polish, russian",
    )
    parser.add_argument(
        "--font-safe",
        action="store_true",
        help="Strip accents and replace common unsupported Latin glyphs for safer in-game fonts",
    )
    parser.add_argument(
        "--no-font-patch",
        action="store_true",
        help="Do not replace English fonts_atlas.xml with the selected language's font atlas",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="String table(s) to exclude/keep English. Default: nothing. Use 'none' for full.",
    )
    parser.add_argument(
        "--quiet-decrypt-log",
        action="store_true",
        help="Disable detailed IDX decrypt/archive parse console logging.",
    )
    args = parser.parse_args()
    global DETAILED_DECRYPT_LOG
    if args.quiet_decrypt_log:
        DETAILED_DECRYPT_LOG = False
    if args.interactive or not args.game_dir:
        if args.auto_find and not args.game_dir:
            found = auto_find_game_dir()
            if found:
                args.game_dir = str(found)
            else:
                args = interactive_args()
        else:
            args = interactive_args()

    game_dir = resolve_game_dir(args.game_dir)
    data_dir = game_dir / "Data"
    setup_run_logging(data_dir, args.action)
    print(f"Game directory: {game_dir}")
    print(f"Repacker data: {repacker_root(data_dir)}")

    if args.action == "restore":
        restore_originals(game_dir)
        return 0

    if args.action == "export-csv":
        if args.csv_scope == "london2038-untranslated":
            default_csv_name = LONDON2038_UNTRANSLATED_CSV_NAME
        elif args.csv_scope == "london2038":
            default_csv_name = LONDON2038_CSV_NAME
        else:
            default_csv_name = DEFAULT_CSV_NAME
        export_english_csv(
            game_dir,
            resolve_csv_path(game_dir, args.csv, default_csv_name),
            args.csv_scope,
            args.language,
        )
        return 0

    if args.action == "import-csv":
        base_language = normalize_language(args.language) if args.language else None
        patch_font_language = args.font_atlas_language or base_language or ""
        patch_font_language = normalize_language(patch_font_language) if patch_font_language else None
        import_csv_translations(
            game_dir,
            resolve_csv_path(game_dir, args.csv, LONDON2038_UNTRANSLATED_CSV_NAME),
            parse_excludes(args.exclude),
            args.dry_run,
            patch_font_language,
            base_language,
            args.font_safe,
        )
        return 0

    if args.action == "list":
        archives = discover_archives(data_dir)
        print("Available source languages:")
        for lang in discover_languages(archives):
            print(f"  {lang}")
        print("\nLocalized archives:")
        for archive in archives:
            print(f"  {archive.idx_path.name} ({archive.crypt.name}, files={len(archive.entries)})")
        return 0

    if not args.language:
        raise SystemExit("--language is required for install")
    language_dir = normalize_language(args.language)
    build_install(
        game_dir,
        language_dir,
        parse_excludes(args.exclude),
        args.dry_run,
        args.font_safe,
        not args.no_font_patch,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
