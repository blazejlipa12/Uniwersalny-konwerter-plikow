
import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


# --------------------------------------------------
# WYSZUKIWANIE LIBREOFFICE
# --------------------------------------------------

def znajdz_libreoffice():
    """Sprawdza, czy LibreOffice jest zainstalowany."""

    # Sprawdzenie, czy LibreOffice znajduje się w PATH
    program = shutil.which("soffice")

    if program:
        return program

    # Typowe lokalizacje LibreOffice w Windows
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

    # Tymczasowy katalog zapobiega nadpisywaniu plików
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

        # Sprawdzenie kodu zakończenia LibreOffice
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

        # Bezpieczna nazwa pliku wynikowego
        sciezka_wynikowa = bezpieczna_sciezka(
            katalog_wyjsciowy,
            plik_wejsciowy.stem + ".pdf"
        )

        shutil.move(str(plik_pdf), str(sciezka_wynikowa))

    return sciezka_wynikowa


# --------------------------------------------------
# MENU GŁÓWNE
# --------------------------------------------------

def main():
    print("===================================")
    print("     UNIWERSALNY KONWERTER PLIKÓW")
    print("===================================")

    print("1. CSV -> JSON")
    print("2. JSON -> CSV")
    print("3. DOCX -> PDF")
    print("4. ODT -> PDF")
    print("0. Zakończ")

    wybor = input("\nWybierz opcję: ").strip()

    if wybor == "0":
        print("Zakończono program.")
        return

    if wybor == "1":
        funkcja = csv_na_json

    elif wybor == "2":
        funkcja = json_na_csv

    elif wybor == "3":
        funkcja = dokument_na_pdf

    elif wybor == "4":
        funkcja = dokument_na_pdf

    else:
        print("Niepoprawna opcja.")
        return

    plik = input("Podaj ścieżkę do pliku wejściowego: ").strip()
    plik = plik.strip('"')

    katalog = input(
        "Podaj ścieżkę do katalogu wynikowego: "
    ).strip()
    katalog = katalog.strip('"')

    try:
        wynik = funkcja(plik, katalog)
        print("\nKonwersja zakończona pomyślnie!")
        print(f"Plik wynikowy: {wynik}")

    except (
        OSError,
        ValueError,
        RuntimeError,
        TypeError,
        subprocess.TimeoutExpired
    ) as blad:
        print(f"\nWystąpił błąd: {blad}")


if __name__ == "__main__":
    main()
