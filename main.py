
import csv
import json
import shutil
import subprocess
import tempfile
import tkinter as tk

from pathlib import Path
from tkinter import ttk, filedialog, messagebox


# --------------------------------------------------
# WYSZUKIWANIE LIBREOFFICE
# --------------------------------------------------

def znajdz_libreoffice():
    """Sprawdza, czy LibreOffice jest zainstalowany."""

    program = shutil.which("soffice")

    if program:
        return program

    mozliwe_sciezki = [
        Path("C:/Program Files/LibreOffice/program/soffice.exe"),
        Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe")
    ]

    for sciezka in mozliwe_sciezki:
        if sciezka.is_file():
            return str(sciezka)

    return None


# --------------------------------------------------
# OBSŁUGA PLIKÓW
# --------------------------------------------------

def bezpieczna_sciezka(katalog, nazwa):
    """Tworzy ścieżkę wynikową, nie nadpisując istniejących plików."""

    katalog = Path(katalog)
    katalog.mkdir(parents=True, exist_ok=True)

    sciezka = katalog / nazwa

    if not sciezka.exists():
        return sciezka

    numer = 1
    rozszerzenie = sciezka.suffix
    nazwa_pliku = sciezka.stem

    while True:
        nowa_nazwa = f"{nazwa_pliku}_{numer}{rozszerzenie}"
        nowa_sciezka = katalog / nowa_nazwa

        if not nowa_sciezka.exists():
            return nowa_sciezka

        numer += 1


# --------------------------------------------------
# CSV -> JSON
# --------------------------------------------------

def csv_na_json(plik_wejsciowy, katalog_wyjsciowy):
    """Konwertuje plik CSV do JSON."""

    plik_wejsciowy = Path(plik_wejsciowy)

    if not plik_wejsciowy.is_file():
        raise FileNotFoundError("Nie znaleziono pliku wejściowego.")

    if plik_wejsciowy.suffix.lower() != ".csv":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie CSV.")

    with plik_wejsciowy.open(
        "r", encoding="utf-8-sig", newline=""
    ) as plik:
        reader = csv.DictReader(plik)

        if not reader.fieldnames:
            raise ValueError("Plik CSV nie zawiera nagłówków.")

        dane = list(reader)

    sciezka_wynikowa = bezpieczna_sciezka(
        katalog_wyjsciowy,
        plik_wejsciowy.stem + ".json"
    )

    with sciezka_wynikowa.open("w", encoding="utf-8") as plik:
        json.dump(dane, plik, ensure_ascii=False, indent=4)

    return sciezka_wynikowa


# --------------------------------------------------
# JSON -> CSV
# --------------------------------------------------

def json_na_csv(plik_wejsciowy, katalog_wyjsciowy):
    """Konwertuje plik JSON do CSV."""

    plik_wejsciowy = Path(plik_wejsciowy)

    if not plik_wejsciowy.is_file():
        raise FileNotFoundError("Nie znaleziono pliku wejściowego.")

    if plik_wejsciowy.suffix.lower() != ".json":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie JSON.")

    try:
        with plik_wejsciowy.open("r", encoding="utf-8-sig") as plik:
            dane = json.load(plik)
    except json.JSONDecodeError as blad:
        raise ValueError(
            f"Niepoprawny JSON. Linia: {blad.lineno}, "
            f"kolumna: {blad.colno}."
        )

    if not isinstance(dane, list) or not dane:
        raise ValueError("JSON musi zawierać niepustą listę obiektów.")

    if not all(isinstance(element, dict) for element in dane):
        raise ValueError("Każdy element JSON musi być obiektem.")

    naglowki = list(dane[0].keys())

    if not naglowki:
        raise ValueError("Obiekty JSON muszą zawierać pola.")

    for element in dane:
        if list(element.keys()) != naglowki:
            raise ValueError(
                "Wszystkie obiekty JSON muszą mieć takie same pola "
                "w tej samej kolejności."
            )

    sciezka_wynikowa = bezpieczna_sciezka(
        katalog_wyjsciowy,
        plik_wejsciowy.stem + ".csv"
    )

    with sciezka_wynikowa.open(
        "w", encoding="utf-8-sig", newline=""
    ) as plik:
        writer = csv.DictWriter(plik, fieldnames=naglowki)
        writer.writeheader()
        writer.writerows(dane)

    return sciezka_wynikowa


# --------------------------------------------------
# DOCX / ODT -> PDF
# --------------------------------------------------

def dokument_na_pdf(plik_wejsciowy, katalog_wyjsciowy):
    """Konwertuje dokument DOCX lub ODT do PDF za pomocą LibreOffice."""

    plik_wejsciowy = Path(plik_wejsciowy)
    katalog_wyjsciowy = Path(katalog_wyjsciowy)

    if not plik_wejsciowy.is_file():
        raise FileNotFoundError("Nie znaleziono pliku wejściowego.")

    if plik_wejsciowy.suffix.lower() not in [".docx", ".odt"]:
        raise ValueError("Obsługiwane są tylko pliki DOCX i ODT.")

    libreoffice = znajdz_libreoffice()

    if not libreoffice:
        raise FileNotFoundError(
            "Nie znaleziono LibreOffice. Zainstaluj program "
            "lub dodaj jego katalog do zmiennej PATH."
        )

    katalog_wyjsciowy.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as katalog_tymczasowy:

        polecenie = [
            libreoffice,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", katalog_tymczasowy,
            str(plik_wejsciowy)
        ]

        wynik = subprocess.run(
            polecenie,
            capture_output=True,
            text=True,
            timeout=120
        )

        if wynik.returncode != 0:
            komunikat = wynik.stderr.strip() or wynik.stdout.strip()
            raise RuntimeError(
                komunikat or "Konwersja dokumentu nie powiodła się."
            )

        plik_pdf = Path(katalog_tymczasowy) / (
            plik_wejsciowy.stem + ".pdf"
        )

        if not plik_pdf.is_file():
            raise RuntimeError(
                "LibreOffice nie utworzył oczekiwanego pliku PDF."
            )

        sciezka_wynikowa = bezpieczna_sciezka(
            katalog_wyjsciowy,
            plik_wejsciowy.stem + ".pdf"
        )

        shutil.move(str(plik_pdf), str(sciezka_wynikowa))

    return sciezka_wynikowa


# --------------------------------------------------
# DOSTĘPNE KONWERTERY
# --------------------------------------------------

KONWERTERY = {
    ".csv": {
        "JSON": csv_na_json
    },
    ".json": {
        "CSV": json_na_csv
    },
    ".docx": {
        "PDF": dokument_na_pdf
    },
    ".odt": {
        "PDF": dokument_na_pdf
    }
}


# --------------------------------------------------
# FUNKCJE INTERFEJSU GRAFICZNEGO
# --------------------------------------------------

def wybierz_plik():
    """Otwiera okno wyboru pliku."""

    plik = filedialog.askopenfilename(
        title="Wybierz plik do konwersji",
        filetypes=[
            ("Obsługiwane pliki", "*.csv *.json *.docx *.odt"),
            ("Pliki CSV", "*.csv"),
            ("Pliki JSON", "*.json"),
            ("Pliki DOCX", "*.docx"),
            ("Pliki ODT", "*.odt"),
            ("Wszystkie pliki", "*.*")
        ]
    )

    if plik:
        plik_wejsciowy.set(plik)
        aktualizuj_formaty()


def wybierz_katalog():
    """Otwiera okno wyboru katalogu wynikowego."""

    katalog = filedialog.askdirectory(
        title="Wybierz katalog zapisu"
    )

    if katalog:
        katalog_wyjsciowy.set(katalog)
        aktualizuj_przycisk()


def aktualizuj_formaty():
    """Ustawia formaty docelowe zależnie od rozszerzenia pliku."""

    plik = plik_wejsciowy.get()

    if not plik:
        dostepne_formaty = []
    else:
        rozszerzenie = Path(plik).suffix.lower()
        dostepne_formaty = list(
            KONWERTERY.get(rozszerzenie, {}).keys()
        )

    wybor_formatu["values"] = dostepne_formaty
    format_docelowy.set("")

    if dostepne_formaty:
        wybor_formatu.current(0)
        status.set("Wybrano plik. Można rozpocząć konwersję.")
    else:
        status.set("Nieobsługiwany format pliku.")

    aktualizuj_przycisk()


def aktualizuj_przycisk(*args):
    """Sprawdza, czy można uruchomić konwersję."""

    if (
        plik_wejsciowy.get()
        and katalog_wyjsciowy.get()
        and format_docelowy.get()
    ):
        przycisk_konwersji.config(state="normal")
    else:
        przycisk_konwersji.config(state="disabled")


def wykonaj_konwersje():
    """Uruchamia wybraną konwersję."""

    plik = plik_wejsciowy.get()
    katalog = katalog_wyjsciowy.get()
    format_doc = format_docelowy.get()

    if not plik or not katalog or not format_doc:
        messagebox.showwarning(
            "Brak danych",
            "Wybierz plik, katalog i format docelowy."
        )
        return

    rozszerzenie = Path(plik).suffix.lower()

    konwertery = KONWERTERY.get(rozszerzenie, {})
    funkcja = konwertery.get(format_doc)

    if funkcja is None:
        messagebox.showerror(
            "Błąd",
            "Wybrana para formatów nie jest obsługiwana."
        )
        return

    try:
        status.set("Trwa konwersja...")
        okno.update_idletasks()

        wynik = funkcja(plik, katalog)

        status.set("Konwersja zakończona pomyślnie!")

        messagebox.showinfo(
            "Sukces",
            f"Konwersja zakończona pomyślnie!\n\n"
            f"Plik wynikowy:\n{wynik}"
        )

    except (
        OSError,
        ValueError,
        RuntimeError,
        TypeError,
        subprocess.TimeoutExpired
    ) as blad:

        status.set("Wystąpił błąd podczas konwersji.")

        messagebox.showerror(
            "Błąd konwersji",
            str(blad)
        )


# --------------------------------------------------
# TWORZENIE OKNA PROGRAMU
# --------------------------------------------------

okno = tk.Tk()
okno.title("Uniwersalny konwerter plików")
okno.geometry("650x440")
okno.minsize(550, 400)

# Zmienne przechowujące wybory użytkownika
plik_wejsciowy = tk.StringVar()
katalog_wyjsciowy = tk.StringVar()
format_docelowy = tk.StringVar()
status = tk.StringVar(value="Oczekiwanie na wybór pliku...")

# Główny kontener
ramka = ttk.Frame(okno, padding=25)
ramka.pack(fill="both", expand=True)

# Tytuł
tytul = ttk.Label(
    ramka,
    text="UNIWERSALNY KONWERTER PLIKÓW",
    font=("Arial", 18, "bold")
)
tytul.pack(pady=(5, 25))

# Wybór pliku
etykieta_pliku = ttk.Label(
    ramka,
    text="Plik wejściowy:"
)
etykieta_pliku.pack(anchor="w")

ramka_pliku = ttk.Frame(ramka)
ramka_pliku.pack(fill="x", pady=(5, 20))

pole_pliku = ttk.Entry(
    ramka_pliku,
    textvariable=plik_wejsciowy,
    state="readonly"
)
pole_pliku.pack(side="left", fill="x", expand=True, padx=(0, 10))

przycisk_pliku = ttk.Button(
    ramka_pliku,
    text="Przeglądaj",
    command=wybierz_plik
)
przycisk_pliku.pack(side="right")

# Wybór katalogu
etykieta_katalogu = ttk.Label(
    ramka,
    text="Katalog wyjściowy:"
)
etykieta_katalogu.pack(anchor="w")

ramka_katalogu = ttk.Frame(ramka)
ramka_katalogu.pack(fill="x", pady=(5, 20))

pole_katalogu = ttk.Entry(
    ramka_katalogu,
    textvariable=katalog_wyjsciowy,
    state="readonly"
)
pole_katalogu.pack(side="left", fill="x", expand=True, padx=(0, 10))

przycisk_katalogu = ttk.Button(
    ramka_katalogu,
    text="Wybierz katalog",
    command=wybierz_katalog
)
przycisk_katalogu.pack(side="right")

# Wybór formatu
etykieta_formatu = ttk.Label(
    ramka,
    text="Format docelowy:"
)
etykieta_formatu.pack(anchor="w")

wybor_formatu = ttk.Combobox(
    ramka,
    textvariable=format_docelowy,
    state="readonly"
)
wybor_formatu.pack(fill="x", pady=(5, 25))

# Przycisk konwersji
przycisk_konwersji = ttk.Button(
    ramka,
    text="KONWERTUJ PLIK",
    command=wykonaj_konwersje,
    state="disabled"
)
przycisk_konwersji.pack(fill="x", ipady=8)

# Status programu
etykieta_statusu = ttk.Label(
    ramka,
    textvariable=status,
    wraplength=580
)
etykieta_statusu.pack(pady=(25, 5))

# Reagowanie na zmianę wyboru formatu
format_docelowy.trace_add(
    "write",
    aktualizuj_przycisk
)

# Uruchomienie programu
okno.mainloop()
