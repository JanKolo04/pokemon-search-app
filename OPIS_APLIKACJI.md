# Pokemon Search App — pełny opis aplikacji

## Co to za aplikacja?

To prosta aplikacja webowa do przeglądania i wyszukiwania Pokémonów. Działa w przeglądarce — pokazuje karty z obrazkami, numerami, nazwami i typami Pokémonów. Można:

- **wyszukiwać** Pokémony po fragmencie nazwy (np. `char` → Charmander, Charmeleon, Charizard),
- **wyszukiwać** po typie wpisanym w pole tekstowe (np. `fire`),
- **filtrować** Pokémony wybierając typ z listy rozwijanej.

Aplikacja składa się z dwóch części:

1. **Backend** (Python + Flask) — serwuje dane z pliku JSON.
2. **Frontend** (HTML + CSS + JavaScript) — wyświetla karty i obsługuje wyszukiwanie.

Dane Pokémonów pochodzą z lokalnego pliku `files/pokedex.json` (~1.2 MB).

---

## Struktura projektu

```
pokemon-search-app/
├── app/
│   ├── __init__.py      ← cały backend (Flask + endpointy)
│   └── main.py
├── frontend/
│   ├── index.html       ← struktura strony
│   ├── style.css        ← style (ciemny motyw + kolory typów)
│   ├── script.js        ← logika wyszukiwania w przeglądarce
│   └── logo.png
├── files/
│   └── pokedex.json     ← baza Pokémonów
├── run.py               ← uruchamia serwer
└── pyproject.toml
```

---

## Jak działa krok po kroku

### 1. Uruchomienie — `run.py`

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
```

To plik startowy. Wywołuje `create_app()`, która tworzy aplikację Flask, i uruchamia ją na porcie **5001** w trybie debug. Po starcie wystarczy wejść na `http://localhost:5001`.

### 2. Backend — `app/__init__.py`

To serce aplikacji. Wszystko dzieje się w funkcji `create_app()`.

#### Wczytanie danych przy starcie

```python
with POKEDEX_PATH.open(encoding="utf-8") as fh:
    pokedex = json.load(fh)

by_name = {p["name"]["english"].lower(): p for p in pokedex}

types: set[str] = set()
for p in pokedex:
    types.update(p["type"])
sorted_types = sorted(types)
```

Co się tutaj dzieje:

- Plik `pokedex.json` jest wczytywany **raz** przy starcie serwera (szybko, bez bazy danych).
- Tworzony jest słownik `by_name` — klucz to nazwa Pokémona małymi literami, wartość to cały obiekt. Dzięki temu wyszukanie po nazwie jest natychmiastowe.
- Zbierane są wszystkie unikalne typy (Fire, Water, Grass...) i sortowane — używane do listy rozwijanej w przeglądarce.

#### Funkcja `to_card` — uproszczenie danych

```python
def to_card(entry: dict) -> dict:
    img = entry["image"]
    thumb = img.get("thumbnail") or img.get("sprite") or img.get("hires", "")
    hires = img.get("hires") or thumb
    return {
        "id": entry["id"],
        "name": entry["name"]["english"],
        "type": entry["type"],
        "base": entry["base"],
        "image": hires,
        "thumbnail": thumb,
    }
```

Surowy JSON ma dużo zbędnych pól (nazwy japońskie, chińskie, francuskie, opis itd.). Ta funkcja wyciąga tylko to, co potrzebne do wyświetlenia karty: id, angielska nazwa, typy, statystyki i obrazki. Dodatkowo zabezpiecza się przed brakującymi obrazkami — bierze co jest dostępne (`thumbnail` → `sprite` → `hires`).

#### Endpointy (adresy URL serwera)

**`/`** — wyświetla stronę główną (plik `index.html`):

```python
@app.route("/")
def index():
    return app.send_static_file("index.html")
```

**`/types`** — zwraca listę wszystkich typów w formacie JSON:

```python
@app.route("/types")
def list_types():
    return jsonify(sorted_types)
```

**`/pokemons`** — najważniejszy endpoint, robi wyszukiwanie:

```python
@app.route("/pokemons")
def list_pokemons():
    query = request.args.get("q", "").strip().lower()
    type_filter = request.args.get("type", "").strip()

    results = pokedex
    if query:
        results = [
            p for p in results
            if query in p["name"]["english"].lower()
            or any(query in t.lower() for t in p["type"])
        ]
    if type_filter:
        results = [p for p in results if type_filter in p["type"]]

    return jsonify([to_card(p) for p in results])
```

Jak to działa:

- Czyta dwa parametry z URL: `q` (fragment tekstu) i `type` (konkretny typ).
- Jeśli podano `q`, filtruje Pokémony — zostawia tylko te, których **nazwa zawiera** wpisany fragment, **lub** którykolwiek z **typów zawiera** ten fragment.
- Jeśli podano `type`, dodatkowo zawęża do Pokémonów z tym typem.
- Zwraca wynik jako JSON, przepuszczając każdy element przez `to_card`.

**`/pokemon/<name>`** — pobiera jednego Pokémona po nazwie:

```python
@app.route("/pokemon/<name>")
def pokemon(name: str):
    entry = by_name.get(name.lower())
    if entry is None:
        abort(404)
    return jsonify(to_card(entry))
```

Korzysta z wcześniej przygotowanego słownika `by_name` — szybkie wyszukanie po kluczu. Jeśli nazwa nie istnieje, zwraca 404.

### 3. Frontend — `frontend/index.html`

Bardzo prosty HTML — pole tekstowe do wyszukiwania, lista rozwijana z typami i dwa puste kontenery (`#status` i `#grid`), które JavaScript wypełnia danymi.

```html
<input type="text" id="search" placeholder="Wpisz fragment nazwy lub typu...">
<select id="type-filter">
    <option value="">Wszystkie typy</option>
</select>
<div id="status" class="status"></div>
<div id="grid" class="grid"></div>
```

### 4. JavaScript — `frontend/script.js`

#### Funkcja `loadPokemons` — pobranie wyników z serwera

```javascript
function loadPokemons() {
    const params = new URLSearchParams();
    const q = searchInput.value.trim();
    const t = typeSelect.value;
    if (q) params.set("q", q);
    if (t) params.set("type", t);

    status.textContent = "Ładowanie...";
    fetch(`/pokemons?${params.toString()}`)
        .then(res => res.json())
        .then(renderCards)
        .catch(() => { status.textContent = "Błąd ładowania danych"; });
}
```

Buduje URL typu `/pokemons?q=char&type=Fire`, wysyła zapytanie do serwera (`fetch`), a wynik (JSON) przekazuje do `renderCards`, która rysuje karty.

#### Debouncing — żeby nie pytać serwera przy każdej literze

```javascript
searchInput.addEventListener("input", () => {
    clearTimeout(debounceId);
    debounceId = setTimeout(loadPokemons, 200);
});
```

Po każdym wciśniętym klawiszu czeka **200 ms**. Jeśli w tym czasie użytkownik wpisze coś jeszcze, poprzedni timer jest kasowany. Dzięki temu zapytanie do serwera leci dopiero, gdy użytkownik przestanie pisać — mniej obciążenia.

#### Rysowanie kart — `renderCards`

```javascript
function renderCards(items) {
    if (items.length === 0) {
        status.textContent = "Brak wyników";
        grid.innerHTML = "";
        return;
    }
    status.textContent = `Znaleziono: ${items.length}`;
    grid.innerHTML = items.map(p => `
        <div class="card">
            <img src="${escapeHtml(p.thumbnail)}" alt="${escapeHtml(p.name)}" loading="lazy">
            <div class="card-id">#${String(p.id).padStart(3, "0")}</div>
            <div class="card-name">${escapeHtml(p.name)}</div>
            <div class="card-types">
                ${p.type.map(t => `<span class="type type-${escapeHtml(t.toLowerCase())}">${escapeHtml(t)}</span>`).join("")}
            </div>
        </div>
    `).join("");
}
```

- Buduje HTML dla każdej karty (obrazek + numer typu `#001` + nazwa + kolorowe odznaki typów).
- Używa `escapeHtml`, żeby zabezpieczyć się przed XSS (znaki specjalne zamienia na encje).
- `loading="lazy"` — obrazki ładują się dopiero gdy są widoczne (szybciej i mniej danych).

### 5. Style — `frontend/style.css`

Ciemny motyw (`background: #111`), karty w siatce CSS Grid, która sama dopasowuje liczbę kolumn:

```css
.grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
}
```

Każdy typ Pokémona ma swój **firmowy kolor** (Fire = pomarańczowy, Water = niebieski, Grass = zielony itd.):

```css
.type-fire { background: #f08030; }
.type-water { background: #6890f0; }
.type-grass { background: #78c850; }
```

---

## Przepływ danych — przykład

1. Użytkownik wpisuje `char` w pole wyszukiwania.
2. JavaScript czeka 200 ms, potem wysyła zapytanie do `GET /pokemons?q=char`.
3. Flask filtruje listę Pokémonów — szuka tych, których nazwa lub typ zawiera `char`.
4. Serwer zwraca JSON z trzema Pokémonami (Charmander, Charmeleon, Charizard).
5. JavaScript dostaje odpowiedź i `renderCards` rysuje trzy karty z obrazkami i kolorowymi typami.

---

## Podsumowanie

To **bardzo prosta** aplikacja klient-serwer:

- **Backend** to ~70 linii Pythona — Flask z 4 endpointami, dane trzymane w pamięci jako lista i słownik.
- **Frontend** to czysty HTML/CSS/JS bez żadnych frameworków (brak React, Vue itd.).
- **Brak bazy danych** — wszystko ładuje się z jednego pliku JSON przy starcie.
- **Brak autoryzacji** — to typowa aplikacja edukacyjna / demo.

Mocne strony kodu: zwięzłość, debouncing wyszukiwania, escape'owanie HTML (zabezpieczenie przed XSS), lazy loading obrazków, szybki słownikowy lookup po nazwie.
