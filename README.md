# Uniwersalny konwerter plików

## Opis projektu
Aplikacja desktopowa napisana w Pythonie z wykorzystaniem Tkinter. Umożliwia konwersję plików pomiędzy formatami CSV, JSON, DOCX, ODT, TXT i PDF.

## Obsługiwane konwersje

| Format wejściowy | Format wyjściowy |
|---|---|
| CSV | JSON |
| JSON | CSV |
| DOCX | PDF |
| ODT | PDF |
| TXT | PDF |
| TXT | ODT |

Konwersje DOCX, ODT i TXT wykorzystują LibreOffice uruchamiany w trybie headless.

## Wymagania
- Python 3.9 lub nowszy.
- LibreOffice – wymagany do konwersji dokumentów DOCX, ODT i TXT.
- Tkinter – zwykle dołączony do instalacji Pythona; w niektórych dystrybucjach Linux może wymagać osobnej instalacji systemowego pakietu Tkinter.

Projekt korzysta wyłącznie z bibliotek standardowych Pythona. Nie wymaga dodatkowych pakietów instalowanych przez pip.

## Instalacja i uruchomienie
1. Zainstaluj Python 3.
2. Zainstaluj LibreOffice, jeśli chcesz konwertować dokumenty.
3. Umieść `main.py` w katalogu projektu.
4. Uruchom terminal w tym katalogu.
5. Wykonaj polecenie:

```bash
python main.py
```

W niektórych systemach użyj `python3 main.py`.

## Korzystanie z aplikacji
1. Wybierz plik wejściowy.
2. Wybierz katalog wyjściowy.
3. Wybierz format docelowy z listy.
4. Kliknij „Konwertuj”.
5. Po zakończeniu aplikacja pokaże lokalizację pliku wynikowego.

Lista formatów jest dostosowywana do rozszerzenia pliku wejściowego. Jeśli plik wynikowy już istnieje, aplikacja pyta o utworzenie kolejnej kopii. Nowa kopia otrzymuje numer w nazwie, np. `dokument_1.pdf`.

## Walidacja i obsługa błędów
Aplikacja sprawdza m.in. istnienie pliku i katalogu, obsługiwane rozszerzenie, strukturę CSV i JSON, dostępność LibreOffice oraz poprawność utworzenia pliku wynikowego. Dłuższe konwersje są wykonywane w osobnym wątku, aby interfejs pozostał responsywny.

## Ograniczenia
- Konwersje DOCX → PDF, ODT → PDF, TXT → PDF i TXT → ODT wymagają LibreOffice.
- Program obsługuje wyłącznie kierunki konwersji wymienione w tabeli.
- JSON przeznaczony do konwersji na CSV musi zawierać niepustą listę obiektów z identycznymi polami w tej samej kolejności.
- CSV musi zawierać wiersz nagłówkowy.
- Wygląd dokumentu wynikowego zależy od pliku źródłowego i możliwości LibreOffice.

## Struktura projektu

```
Uniwersalny-konwerter-plikow/
├── dane_wejsciowe/
├── wyniki/
├── main.py
└── README.md
```

## Technologie
- Python 3
- Tkinter / ttk
- LibreOffice
- Moduły standardowe: `csv`, `json`, `pathlib`, `shutil`, `subprocess`, `tempfile`, `threading`

## Autor
Błażej Lipa