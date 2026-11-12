# Krótki raport z testów – Uniwersalny konwerter plików

## 1. Cel testów
Celem testów jest sprawdzenie poprawności obsługiwanych konwersji, walidacji danych wejściowych, komunikatów o błędach oraz zabezpieczenia przed nadpisywaniem istniejących plików.

## 2. Środowisko testowe
- System operacyjny: Windows 11
- Wersja Pythona: Python 3.15.2
- Wersja LibreOffice: LibreOffice 26.8.2
- Data przeprowadzenia testów: 12.11.2026
- Osoba przeprowadzająca testy: Błażej Lipa

## 3. Przypadki testowe

Status „Do wykonania” oznacza, że test należy przeprowadzić i wpisać rzeczywisty wynik. Nie oznacza on, że test został już zaliczony.

| Lp. | Przypadek testowy | Oczekiwany rezultat | Wynik rzeczywisty / status |
|---:|---|---|---|
| 1 | Poprawny CSV → JSON | Powstaje JSON zawierający dane z CSV. | Działa |
| 2 | Poprawny JSON → CSV | Powstaje CSV z nagłówkami i danymi. | Działa |
| 3 | Poprawny DOCX → PDF | Powstaje dokument PDF. | Działa |
| 4 | Poprawny ODT → PDF | Powstaje dokument PDF. | Działa |
| 5 | Poprawny TXT → PDF | Powstaje dokument PDF. | Działa |
| 6 | Poprawny TXT → ODT | Powstaje dokument ODT. | Działa |
| 7 | Nieobsługiwane rozszerzenie | Niedozwolona konwersja nie jest dostępna. | Działa |
| 8 | Istniejący plik wynikowy | Aplikacja pyta o utworzenie kopii i nie nadpisuje pliku. | Działa |
| 9 | Polskie znaki w danych | Znaki ą, ć, ę, ł, ń, ó, ś, ź, ż zostają zachowane. | Działa |
| 10 | Pusty plik TXT | Wynik konwersji jest poprawnym pustym dokumentem albo aplikacja pokazuje czytelny błąd. | Działa |