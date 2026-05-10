# Pokemon Search App

Aplikacja webowa w Pythonie (Flask) służąca do wyszukiwania Pokémonów na podstawie lokalnej bazy `files/pokedex.json`.

## Wymagania

- Python 3.13 lub nowszy (zalecana wersja zgodna z plikiem `.python-version`)
- `pip`
- System operacyjny: macOS / Linux / Windows

## Uruchomienie w środowisku wirtualnym (venv)

### 1. Sklonuj repozytorium

```bash
git clone <URL-repozytorium>
cd pokemon-search-app
```

### 2. Utwórz środowisko wirtualne

**macOS / Linux:**

```bash
python3 -m venv venv
```

**Windows (PowerShell):**

```powershell
python -m venv venv
```

### 3. Aktywuj środowisko

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (cmd):**

```cmd
venv\Scripts\activate.bat
```

Po aktywacji w terminalu pojawi się prefiks `(venv)`.

### 4. Zaktualizuj pip i zainstaluj zależności

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. (Opcjonalnie) Zainstaluj zależności deweloperskie

Jeśli chcesz uruchamiać testy i lintery:

```bash
pip install pytest pytest-cov ruff pre-commit
```

### 6. Uruchom aplikację

```bash
python run.py
```

Aplikacja domyślnie wystartuje na:

```text
http://127.0.0.1:5001
```

## Uruchamianie testów

```bash
pytest
```

Wynik pokrycia kodu zostanie zapisany do `coverage.xml`.

## Testowanie algorytmu na innym pliku JSON

W `files/` znajdziesz dwa zbiory danych:

- `pokedex.json` — pełna baza (898 Pokémonów, używana domyślnie)
- `pokedex_example.json` — mały zestaw przykładowy (10 Pokémonów, 12 różnych typów) do szybkiego sprawdzenia, czy wyszukiwarka i filtry typów działają poprawnie

Aby uruchomić aplikację na zbiorze przykładowym, otwórz `app/__init__.py` i zmień ścieżkę:

```python
POKEDEX_PATH = BASE_DIR / "files" / "pokedex_example.json"
```

Zrestartuj `python run.py` i wejdź na `http://127.0.0.1:5001/`.

Przykładowe scenariusze testowe na `pokedex_example.json`:

| Co wpisać / wybrać     | Oczekiwany wynik                |
|------------------------|---------------------------------|
| (puste pole)           | 10 kart                         |
| `mud`                  | Mudkip                          |
| `fire` (po typie)      | Torchic                         |
| `psychic` (po typie)   | Ralts                           |
| typ `Dark` z dropdowna | Sableye                         |
| `zzz`                  | 0 wyników, „Brak wyników"       |

Aby wrócić do pełnej bazy, przywróć ścieżkę do `pokedex.json`.

Własny plik JSON musi mieć tę samą strukturę co istniejące zbiory: lista obiektów z polami `id`, `name.english`, `type` (lista), `base` i `image` (z `thumbnail` lub `hires`).

## Linter (ruff)

```bash
ruff check .
```

## Dezaktywacja środowiska

Po zakończonej pracy:

```bash
deactivate
```

## Struktura projektu

```text
pokemon-search-app/
├── run.py              # Punkt startowy aplikacji Flask
├── app/                # Pakiet aplikacji
│   ├── __init__.py
│   └── main.py
├── files/
│   ├── pokedex.json            # Pełna baza Pokémonów (898 wpisów, domyślna)
│   └── pokedex_example.json    # Przykładowy zestaw testowy (10 wpisów)
├── frontend/           # Statyki serwowane przez Flaska (HTML/CSS/JS, logo)
├── tests/              # Testy pytest
├── pyproject.toml      # Konfiguracja projektu (pytest, ruff, coverage)
├── requirements.txt    # Zależności runtime
└── README.md
```

## Licencja

Zobacz plik [LICENSE.md](LICENSE.md).
