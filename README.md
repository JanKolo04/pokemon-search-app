# Pokemon Search App

Aplikacja webowa w Pythonie (Flask) do wyszukiwania Pokémonów z modułem analizy walk opartym na algorytmach AI.

## Wymagania

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/)

## Uruchomienie

```bash
uv sync
uv run python run.py
```

Aplikacja działa na `http://127.0.0.1:5001`.

## Testy

```bash
uv run pytest
```

## Jakość kodu

```bash
uvx ruff check .
```

## Struktura projektu

```text
pokemon-search-app/
├── run.py                   # Punkt startowy
├── app/
│   ├── __init__.py          # Logika: BFS, heurystyka walki, endpointy REST
│   └── main.py              # Punkt wejścia pakietu
├── files/
│   ├── pokedex.json         # Baza 898 Pokémonów z ruchami (PokéAPI)
│   └── pokedex_example.json # Przykładowy zestaw 10 Pokémonów
├── frontend/                # Istniejący UI wyszukiwarki (HTML/CSS/JS)
├── scripts/
│   └── enrich_moves.py      # Jednorazowy skrypt pobierający ruchy z PokéAPI
├── tests/
│   ├── conftest.py
│   └── test_example.py      # 32 testy jednostkowe i integracyjne
├── pyproject.toml
└── uv.lock
```

## Algorytmy AI

- **BFS** na grafie ewolucji — wyszukiwanie rozszerza wyniki o cały łańcuch ewolucji
- **Heurystyczna funkcja oceny** — symulacja DPS z macierzą 18 typów i rzeczywistymi danymi ruchów z PokéAPI

## Licencja

Zobacz [LICENSE.md](LICENSE.md).
