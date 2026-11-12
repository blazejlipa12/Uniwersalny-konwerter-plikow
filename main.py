
import csv
import json
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk

from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# ============================================================
# FUNKCJE POMOCNICZE
# ============================================================

def bezpieczna_sciezka(katalog, nazwa_pliku):
    """
    Sprawdza, czy plik o podanej nazwie już istnieje.
    Jeśli tak, dodaje kolejny numer, np. wynik_1.pdf.
    Dzięki temu nie nadpisujemy istniejących plików.
    """
    sciezka = Path(katalog) / nazwa_pliku

    if not sciezka.exists():
        return sciezka

    nazwa = sciezka.stem
    rozszerzenie = sciezka.suffix
    licznik = 1

    while True:
        nowa_sciezka = Path(katalog) / f"{nazwa}_{licznik}{rozszerzenie}"

        if not nowa_sciezka.exists():
            return nowa_sciezka

        licznik += 1


def znajdz_libreoffice():
    """
    Szuka programu LibreOffice potrzebnego do konwersji dokumentów.
    """
    program = shutil.which("soffice")

    if program:
        return program

    # Typowe lokalizacje LibreOffice w systemie Windows
    mozliwe_sciezki = [
        "C:/Program Files/LibreOffice/program/soffice.exe",
        "C:/Program Files (x86)/LibreOffice/program/soffice.exe"
    ]

    for sciezka in mozliwe_sciezki:
        if Path(sciezka).exists():
            return sciezka

    raise FileNotFoundError(
        "Nie znaleziono LibreOffice. Zainstaluj program "
        "lub sprawdź jego lokalizację."
    )


def sprawdz_dane_wejsciowe(plik_wejsciowy, katalog_wyjsciowy):
    """
    Sprawdza, czy plik wejściowy i katalog wyjściowy istnieją.
    """
    plik = Path(plik_wejsciowy)
    katalog = Path(katalog_wyjsciowy)

    if not plik.exists():
        raise FileNotFoundError("Wybrany plik wejściowy nie istnieje.")

    if not plik.is_file():
        raise ValueError("Wybrana ścieżka nie wskazuje na plik.")

    if not katalog.exists():
        raise FileNotFoundError("Wybrany katalog wyjściowy nie istnieje.")

    if not katalog.is_dir():
        raise ValueError("Wybrana ścieżka wyjściowa nie jest katalogiem.")

    return plik, katalog


# ============================================================
# GRUPA A - KONWERSJA CSV <-> JSON
# ============================================================

def csv_na_json(plik_wejsciowy, katalog_wyjsciowy):
    """
    Zamienia plik CSV na JSON.
    """
    plik, katalog = sprawdz_dane_wejsciowe(
        plik_wejsciowy, katalog_wyjsciowy
    )

    if plik.suffix.lower() != ".csv":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie CSV.")

    try:
        with open(plik, "r", encoding="utf-8-sig", newline="") as plik_csv:
            czytnik = csv.DictReader(plik_csv)

            if not czytnik.fieldnames:
                raise ValueError("Plik CSV nie zawiera nagłówków kolumn.")

            if any(not naglowek for naglowek in czytnik.fieldnames):
                raise ValueError("Plik CSV zawiera pusty nagłówek kolumny.")

            dane = list(czytnik)

            if not dane:
                raise ValueError("Plik CSV nie zawiera żadnych danych.")

            if any(None in rekord for rekord in dane):
                raise ValueError(
                    "Niektóre wiersze CSV zawierają więcej wartości "
                    "niż nagłówków."
                )

    except UnicodeDecodeError:
        raise ValueError("Nie udało się odczytać pliku CSV.")

    sciezka_wyjsciowa = bezpieczna_sciezka(
        katalog, plik.stem + ".json"
    )

    with open(sciezka_wyjsciowa, "w", encoding="utf-8") as plik_json:
        json.dump(dane, plik_json, ensure_ascii=False, indent=4)

    return sciezka_wyjsciowa


def json_na_csv(plik_wejsciowy, katalog_wyjsciowy):
    """
    Zamienia plik JSON na CSV.
    """
    plik, katalog = sprawdz_dane_wejsciowe(
        plik_wejsciowy, katalog_wyjsciowy
    )

    if plik.suffix.lower() != ".json":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie JSON.")

    try:
        with open(plik, "r", encoding="utf-8-sig") as plik_json:
            dane = json.load(plik_json)

    except json.JSONDecodeError as blad:
        raise ValueError(
            f"Niepoprawny plik JSON. Błąd w linii {blad.lineno}, "
            f"kolumna {blad.colno}."
        )

    except UnicodeDecodeError:
        raise ValueError("Nie udało się odczytać pliku JSON.")

    if not isinstance(dane, list) or len(dane) == 0:
        raise ValueError("JSON musi zawierać niepustą listę obiektów.")

    if not all(isinstance(rekord, dict) for rekord in dane):
        raise ValueError("Każdy element listy JSON musi być obiektem.")

    naglowki = list(dane[0].keys())

    if not naglowki:
        raise ValueError("Obiekty JSON nie zawierają żadnych pól.")

    for rekord in dane:
        if list(rekord.keys()) != naglowki:
            raise ValueError(
                "Wszystkie obiekty JSON muszą zawierać te same pola "
                "w tej samej kolejności."
            )

    sciezka_wyjsciowa = bezpieczna_sciezka(
        katalog, plik.stem + ".csv"
    )

    with open(
        sciezka_wyjsciowa,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as plik_csv:

        zapis = csv.DictWriter(plik_csv, fieldnames=naglowki)
        zapis.writeheader()
        zapis.writerows(dane)

    return sciezka_wyjsciowa


# ============================================================
# GRUPA B I C - KONWERSJE DOKUMENTÓW
# ============================================================

def dokument_na_pdf(plik_wejsciowy, katalog_wyjsciowy):
    """
    Zamienia dokument DOCX lub ODT na PDF przy użyciu LibreOffice.
    """
    plik, katalog = sprawdz_dane_wejsciowe(
        plik_wejsciowy, katalog_wyjsciowy
    )

    if plik.suffix.lower() not in [".docx", ".odt"]:
        raise ValueError("Obsługiwane formaty wejściowe to DOCX i ODT.")

    return konwertuj_libreoffice(plik, katalog, "pdf")


def tekst_na_format(plik_wejsciowy, katalog_wyjsciowy, format_docelowy):
    """
    Zamienia plik TXT na wybrany format: PDF lub ODT.
    """
    plik, katalog = sprawdz_dane_wejsciowe(
        plik_wejsciowy, katalog_wyjsciowy
    )

    if plik.suffix.lower() != ".txt":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie TXT.")

    if format_docelowy not in ["pdf", "odt"]:
        raise ValueError("Nieobsługiwany format docelowy.")

    return konwertuj_libreoffice(plik, katalog, format_docelowy)


def konwertuj_libreoffice(plik, katalog, format_docelowy):
    """
    Wspólna funkcja konwertująca dokumenty za pomocą LibreOffice.
    """
    libreoffice = znajdz_libreoffice()

    # Tworzymy tymczasowy katalog na wynik konwersji
    with tempfile.TemporaryDirectory() as katalog_tymczasowy:

        polecenie = [
            libreoffice,
            "--headless",
            "--convert-to",
            format_docelowy,
            "--outdir",
            katalog_tymczasowy,
            str(plik)
        ]

        try:
            wynik = subprocess.run(
                polecenie,
                capture_output=True,
                text=True,
                timeout=120
            )

        except subprocess.TimeoutExpired:
            raise TimeoutError(
                "Konwersja przekroczyła limit czasu 120 sekund."
            )

        except OSError as blad:
            raise RuntimeError(
                f"Nie udało się uruchomić LibreOffice: {blad}"
            )

        if wynik.returncode != 0:
            szczegoly = wynik.stderr.strip() or wynik.stdout.strip()

            raise RuntimeError(
                "LibreOffice nie mógł przekonwertować dokumentu.\n"
                + szczegoly
            )

        plik_wynikowy = (
            Path(katalog_tymczasowy) /
            f"{plik.stem}.{format_docelowy}"
        )

        if not plik_wynikowy.exists():
            raise RuntimeError(
                "LibreOffice nie utworzył pliku wynikowego."
            )

        # Tworzymy bezpieczną nazwę pliku wynikowego
        sciezka_docelowa = bezpieczna_sciezka(
            katalog, plik.stem + "." + format_docelowy
        )

        shutil.move(str(plik_wynikowy), str(sciezka_docelowa))

    return sciezka_docelowa


# ============================================================
# REJESTR DOSTĘPNYCH KONWERSJI
# ============================================================

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
    },

    ".txt": {
        "PDF": lambda plik, katalog: tekst_na_format(
            plik, katalog, "pdf"
        ),

        "ODT": lambda plik, katalog: tekst_na_format(
            plik, katalog, "odt"
        )
    }
}


# ============================================================
# INTERFEJS GRAFICZNY - TKINTER
# ============================================================

okno = tk.Tk()
okno.title("Uniwersalny konwerter plików")
okno.geometry("680x470")
okno.minsize(580, 430)

plik_wejsciowy = tk.StringVar()
katalog_wyjsciowy = tk.StringVar()
format_docelowy = tk.StringVar()
status = tk.StringVar(value="Wybierz plik wejściowy, aby rozpocząć.")

konwersja_w_trakcie = False


def wybierz_plik():
    """
    Otwiera okno wyboru pliku wejściowego.
    """
    sciezka = filedialog.askopenfilename(
        title="Wybierz plik do konwersji",
        filetypes=[
            ("Obsługiwane pliki", "*.csv *.json *.docx *.odt *.txt"),
            ("Pliki CSV", "*.csv"),
            ("Pliki JSON", "*.json"),
            ("Dokumenty Word", "*.docx"),
            ("Dokumenty OpenDocument", "*.odt"),
            ("Pliki tekstowe", "*.txt"),
            ("Wszystkie pliki", "*.*")
        ]
    )

    if sciezka:
        plik_wejsciowy.set(sciezka)
        aktualizuj_formaty()


def wybierz_katalog():
    """
    Otwiera okno wyboru katalogu wyjściowego.
    """
    sciezka = filedialog.askdirectory(
        title="Wybierz katalog wyjściowy"
    )

    if sciezka:
        katalog_wyjsciowy.set(sciezka)
        aktualizuj_przycisk()


def aktualizuj_formaty(*args):
    """
    Aktualizuje listę formatów docelowych na podstawie pliku wejściowego.
    """
    sciezka = plik_wejsciowy.get()

    if not sciezka:
        lista_formatow["values"] = []
        format_docelowy.set("")
        aktualizuj_przycisk()
        return

    rozszerzenie = Path(sciezka).suffix.lower()

    dostepne_formaty = KONWERTERY.get(rozszerzenie, {})

    formaty = list(dostepne_formaty.keys())

    lista_formatow["values"] = formaty

    if formaty:
        format_docelowy.set(formaty[0])
        status.set("Wybierz katalog wyjściowy.")
    else:
        format_docelowy.set("")
        status.set("Ten format pliku nie jest obsługiwany.")

    aktualizuj_przycisk()


def aktualizuj_przycisk(*args):
    """
    Sprawdza, czy użytkownik uzupełnił wymagane pola.
    """
    if (
        plik_wejsciowy.get()
        and katalog_wyjsciowy.get()
        and format_docelowy.get()
        and not konwersja_w_trakcie
    ):
        przycisk_konwertuj.config(state="normal")
    else:
        przycisk_konwertuj.config(state="disabled")


def zakoncz_konwersje(sciezka_wynikowa):
    """
    Wyświetla komunikat po poprawnym zakończeniu konwersji.
    Funkcja jest wywoływana w głównym wątku GUI.
    """
    global konwersja_w_trakcie

    konwersja_w_trakcie = False
    przycisk_konwertuj.config(text="Konwertuj")
    aktualizuj_przycisk()

    status.set("Konwersja zakończona pomyślnie.")

    messagebox.showinfo(
        "Sukces",
        f"Plik został przekonwertowany.\n\n"
        f"Zapisano jako:\n{sciezka_wynikowa}"
    )


def blad_konwersji(komunikat):
    """
    Wyświetla komunikat o błędzie.
    Funkcja jest wywoływana w głównym wątku GUI.
    """
    global konwersja_w_trakcie

    konwersja_w_trakcie = False
    przycisk_konwertuj.config(text="Konwertuj")
    aktualizuj_przycisk()

    status.set("Wystąpił błąd podczas konwersji.")

    messagebox.showerror(
        "Błąd konwersji",
        komunikat
    )


def wykonaj_konwersje():
    """
    Uruchamia konwersję w osobnym wątku, aby GUI nie przestawało odpowiadać.
    """
    global konwersja_w_trakcie

    if konwersja_w_trakcie:
        return

    sciezka_pliku = plik_wejsciowy.get()
    sciezka_katalogu = katalog_wyjsciowy.get()
    wybrany_format = format_docelowy.get()

    if not sciezka_pliku or not sciezka_katalogu or not wybrany_format:
        messagebox.showwarning(
            "Brak danych",
            "Wybierz plik, katalog wyjściowy i format docelowy."
        )
        return

    rozszerzenie = Path(sciezka_pliku).suffix.lower()

    dostepne_formaty = KONWERTERY.get(rozszerzenie, {})

    funkcja = dostepne_formaty.get(wybrany_format)

    if funkcja is None:
        messagebox.showerror(
            "Błąd",
            "Wybrana konwersja nie jest obsługiwana."
        )
        return

    # Sprawdzamy, czy plik wynikowy już istnieje.
    # Jeśli tak, pytamy użytkownika o utworzenie kolejnej kopii.
    rozszerzenie_wyjsciowe = "." + wybrany_format.lower()

    nazwa_wynikowa = (
        Path(sciezka_pliku).stem + rozszerzenie_wyjsciowe
    )

    przewidywana_sciezka = (
        Path(sciezka_katalogu) / nazwa_wynikowa
    )

    if przewidywana_sciezka.exists():
        decyzja = messagebox.askyesno(
            "Plik już istnieje",
            "Plik o takiej nazwie już istnieje.\n\n"
            "Czy chcesz utworzyć kolejną kopię z numerem "
            "zamiast nadpisywać istniejący plik?"
        )

        if not decyzja:
            return

    konwersja_w_trakcie = True
    przycisk_konwertuj.config(
        state="disabled",
        text="Konwertowanie..."
    )

    status.set("Trwa konwersja pliku...")

    # Funkcja wykonywana w osobnym wątku
    def zadanie():
        try:
            wynik = funkcja(
                sciezka_pliku,
                sciezka_katalogu
            )

            okno.after(
                0,
                lambda: zakoncz_konwersje(wynik)
            )

        except Exception as blad:
            komunikat = str(blad)

            okno.after(
                0,
                lambda: blad_konwersji(komunikat)
            )

    watek = threading.Thread(
        target=zadanie,
        daemon=True
    )

    watek.start()


# ============================================================
# BUDOWA INTERFEJSU
# ============================================================

glowna_ramka = ttk.Frame(okno, padding=25)
glowna_ramka.pack(fill="both", expand=True)

tytul = ttk.Label(
    glowna_ramka,
    text="Uniwersalny konwerter plików",
    font=("Arial", 18, "bold")
)
tytul.pack(pady=(0, 10))

opis = ttk.Label(
    glowna_ramka,
    text="Wybierz plik, katalog docelowy i format konwersji.",
    font=("Arial", 10)
)
opis.pack(pady=(0, 25))


# Wybór pliku wejściowego

etykieta_pliku = ttk.Label(
    glowna_ramka,
    text="Plik wejściowy:"
)
etykieta_pliku.pack(anchor="w")

ramka_pliku = ttk.Frame(glowna_ramka)
ramka_pliku.pack(fill="x", pady=(5, 15))

pole_pliku = ttk.Entry(
    ramka_pliku,
    textvariable=plik_wejsciowy,
    state="readonly"
)
pole_pliku.pack(side="left", fill="x", expand=True, padx=(0, 10))

przycisk_pliku = ttk.Button(
    ramka_pliku,
    text="Wybierz plik",
    command=wybierz_plik
)
przycisk_pliku.pack(side="right")


# Wybór katalogu wyjściowego

etykieta_katalogu = ttk.Label(
    glowna_ramka,
    text="Katalog wyjściowy:"
)
etykieta_katalogu.pack(anchor="w")

ramka_katalogu = ttk.Frame(glowna_ramka)
ramka_katalogu.pack(fill="x", pady=(5, 15))

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


# Wybór formatu docelowego

etykieta_formatu = ttk.Label(
    glowna_ramka,
    text="Format docelowy:"
)
etykieta_formatu.pack(anchor="w")

lista_formatow = ttk.Combobox(
    glowna_ramka,
    textvariable=format_docelowy,
    state="readonly"
)
lista_formatow.pack(fill="x", pady=(5, 20))


# Przycisk konwersji

przycisk_konwertuj = ttk.Button(
    glowna_ramka,
    text="Konwertuj",
    command=wykonaj_konwersje,
    state="disabled"
)
przycisk_konwertuj.pack(pady=10, ipadx=20, ipady=5)


# Informacja o aktualnym stanie aplikacji

etykieta_statusu = ttk.Label(
    glowna_ramka,
    textvariable=status,
    font=("Arial", 9),
    wraplength=580
)
etykieta_statusu.pack(pady=15)


# Reagowanie na zmianę danych
plik_wejsciowy.trace_add("write", aktualizuj_formaty)
katalog_wyjsciowy.trace_add("write", aktualizuj_przycisk)
format_docelowy.trace_add("write", aktualizuj_przycisk)


# Uruchomienie aplikacji
okno.mainloop()
