import csv
import json
from pathlib import Path


def bezpieczna_sciezka(katalog, nazwa):
    """Tworzy katalog i dobiera wolną nazwę pliku."""
    katalog.mkdir(parents=True, exist_ok=True)
    sciezka = katalog / nazwa

    if not sciezka.exists():
        return sciezka

    numer = 1

    while True:
        nowa_sciezka = katalog / f"{sciezka.stem}_{numer}{sciezka.suffix}"

        if not nowa_sciezka.exists():
            return nowa_sciezka

        numer += 1


def csv_na_json(plik_wejsciowy, katalog_wyjsciowy):
    """Konwertuje plik CSV na JSON."""

    if not plik_wejsciowy.is_file():
        raise FileNotFoundError("Nie znaleziono pliku wejściowego.")

    if plik_wejsciowy.suffix.lower() != ".csv":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie .csv.")

    with plik_wejsciowy.open(
        "r", encoding="utf-8-sig", newline=""
    ) as plik:
        czytnik = csv.DictReader(plik)

        if not czytnik.fieldnames:
            raise ValueError("Plik CSV jest pusty lub nie ma nagłówków.")

        if any(
            not naglowek or not naglowek.strip()
            for naglowek in czytnik.fieldnames
        ):
            raise ValueError("Każda kolumna CSV musi mieć nazwę.")

        dane = list(czytnik)

    plik_wyjsciowy = bezpieczna_sciezka(
        katalog_wyjsciowy,
        f"{plik_wejsciowy.stem}.json"
    )

    with plik_wyjsciowy.open("w", encoding="utf-8") as plik:
        json.dump(dane, plik, ensure_ascii=False, indent=4)

    return plik_wyjsciowy


def json_na_csv(plik_wejsciowy, katalog_wyjsciowy):
    """Konwertuje listę obiektów JSON na plik CSV."""

    if not plik_wejsciowy.is_file():
        raise FileNotFoundError("Nie znaleziono pliku wejściowego.")

    if plik_wejsciowy.suffix.lower() != ".json":
        raise ValueError("Plik wejściowy musi mieć rozszerzenie .json.")

    try:
        with plik_wejsciowy.open("r", encoding="utf-8-sig") as plik:
            dane = json.load(plik)
    except json.JSONDecodeError as blad:
        raise ValueError(
            f"Błędny JSON w linii {blad.lineno}, "
            f"kolumna {blad.colno}: {blad.msg}"
        ) from blad

    if not isinstance(dane, list) or not dane:
        raise ValueError("JSON musi zawierać niepustą listę obiektów.")

    if not all(isinstance(wiersz, dict) for wiersz in dane):
        raise ValueError("Każdy element listy JSON musi być obiektem.")

    naglowki = list(dane[0].keys())

    if not naglowki:
        raise ValueError("Obiekty JSON muszą zawierać przynajmniej jedno pole.")

    zestaw_naglowkow = set(naglowki)

    for numer, wiersz in enumerate(dane, start=1):
        if set(wiersz.keys()) != zestaw_naglowkow:
            raise ValueError(
                f"Obiekt nr {numer} ma inne pola niż pierwszy obiekt."
            )

    plik_wyjsciowy = bezpieczna_sciezka(
        katalog_wyjsciowy,
        f"{plik_wejsciowy.stem}.csv"
    )

    with plik_wyjsciowy.open(
        "w", encoding="utf-8", newline=""
    ) as plik:
        zapis = csv.DictWriter(plik, fieldnames=naglowki)
        zapis.writeheader()

        for wiersz in dane:
            zapis.writerow({
                klucz: "" if wiersz[klucz] is None
                else str(wiersz[klucz])
                for klucz in naglowki
            })

    return plik_wyjsciowy


def main():
    print("===================================")
    print("     UNIWERSALNY KONWERTER PLIKÓW")
    print("===================================")
    print("1. CSV -> JSON")
    print("2. JSON -> CSV")
    print("0. Zakończ program")

    while True:
        wybor = input("\nWybierz opcję: ").strip()

        if wybor == "0":
            print("Zamykanie programu.")
            break

        if wybor not in ("1", "2"):
            print("Błąd: wybierz 1, 2 albo 0.")
            continue

        sciezka = input(
            "Podaj ścieżkę do pliku wejściowego: "
        ).strip().strip('"')

        katalog = input(
            "Podaj katalog zapisu (Enter = wyniki): "
        ).strip().strip('"')

        if not katalog:
            katalog = "wyniki"

        plik_wejsciowy = Path(sciezka)
        katalog_wyjsciowy = Path(katalog)

        try:
            if wybor == "1":
                wynik = csv_na_json(
                    plik_wejsciowy,
                    katalog_wyjsciowy
                )
            else:
                wynik = json_na_csv(
                    plik_wejsciowy,
                    katalog_wyjsciowy
                )

            print("\nKonwersja zakończona powodzeniem!")
            print(f"Zapisano plik: {wynik}")

        except (OSError, ValueError, TypeError) as blad:
            print(f"\nBłąd: {blad}")


if __name__ == "__main__":
    main()
