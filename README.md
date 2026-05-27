# Pokemon Search App

Aplikacja webowa w Pythonie (Flask) służąca do wyszukiwania Pokémonów na podstawie lokalnej bazy `files/pokedex.json`.

## Wymagania

- Python 3.13 lub nowszy
- [`uv`](https://docs.astral.sh/uv/)

## Uruchomienie

```bash
uv sync
uv run python run.py
```

Aplikacja wystartuje na `http://127.0.0.1:5001`.

## Testy

```bash
uv run pytest
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
├── pyproject.toml      # Konfiguracja projektu i zależności (uv, pytest, ruff, coverage)
├── uv.lock             # Zablokowane wersje zależności (uv)
└── README.md
```

## Licencja

Zobacz plik [LICENSE.md](LICENSE.md).
