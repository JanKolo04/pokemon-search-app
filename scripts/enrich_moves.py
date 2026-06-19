#!/usr/bin/env python3
"""
Fetches real move data from PokéAPI and enriches files/pokedex.json.

Each Pokemon entry gets a 'moves' field: up to 5 damaging moves
(best power, one per type) with {name, type, power, damage_class}.

Run from project root:  uv run python scripts/enrich_moves.py
"""
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_URL = "https://pokeapi.co/api/v2"
POKEDEX_PATH = Path("files/pokedex.json")
PROGRESS_PATH = Path("files/.enrich_progress.json")
HEADERS = {"User-Agent": "pokemon-search-app/1.0"}
WORKERS = 25
MAX_MOVES_PER_POKEMON = 5


def fetch_json(url: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            if attempt == retries - 1:
                raise
            time.sleep(1.5 ** attempt)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 ** attempt)
    return {}


def fetch_pokemon_move_names(pokemon_id: int) -> list[str]:
    data = fetch_json(f"{BASE_URL}/pokemon/{pokemon_id}")
    return [m["move"]["name"] for m in data.get("moves", [])]


def fetch_move_details(move_name: str) -> dict | None:
    data = fetch_json(f"{BASE_URL}/move/{move_name}")
    if not data:
        return None
    power = data.get("power")
    if not power:
        return None
    damage_class = data.get("damage_class", {}).get("name", "special")
    return {
        "name": move_name.replace("-", " ").title(),
        "type": data["type"]["name"].title(),
        "power": power,
        "damage_class": damage_class,
    }


def select_top_moves(all_moves: list[dict]) -> list[dict]:
    """Pick best-power move per type, return top MAX_MOVES_PER_POKEMON overall."""
    by_type: dict[str, dict] = {}
    for m in all_moves:
        t = m["type"]
        if t not in by_type or m["power"] > by_type[t]["power"]:
            by_type[t] = m

    top = sorted(by_type.values(), key=lambda m: m["power"], reverse=True)
    return top[:MAX_MOVES_PER_POKEMON]


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        with PROGRESS_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {"pokemon_moves": {}, "move_cache": {}}


def save_progress(progress: dict) -> None:
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(progress, f)


def _fetch_all_pokemon_moves(id_to_entry: dict, progress: dict) -> dict[str, list[str]]:
    pokemon_moves: dict[str, list[str]] = progress["pokemon_moves"]
    missing_ids = [pid for pid in id_to_entry if str(pid) not in pokemon_moves]
    if not missing_ids:
        return pokemon_moves
    print(f"Fetching move lists for {len(missing_ids)} Pokemon…")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_pokemon_move_names, pid): pid for pid in missing_ids}
        for future in as_completed(futures):
            pid = futures[future]
            try:
                pokemon_moves[str(pid)] = future.result()
            except Exception as e:
                print(f"  ⚠ Pokemon #{pid}: {e}")
                pokemon_moves[str(pid)] = []
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(missing_ids)}")
                save_progress({"pokemon_moves": pokemon_moves, "move_cache": progress["move_cache"]})
    save_progress({"pokemon_moves": pokemon_moves, "move_cache": progress["move_cache"]})
    print("  Done.")
    return pokemon_moves


def _fetch_all_move_details(pokemon_moves: dict, progress: dict) -> dict[str, dict | None]:
    move_cache: dict[str, dict | None] = progress["move_cache"]
    all_move_names = {m for moves in pokemon_moves.values() for m in moves}
    missing_moves = [n for n in all_move_names if n not in move_cache]
    if not missing_moves:
        return move_cache
    print(f"Fetching details for {len(missing_moves)} unique moves…")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_move_details, name): name for name in missing_moves}
        for future in as_completed(futures):
            name = futures[future]
            try:
                move_cache[name] = future.result()
            except Exception:
                move_cache[name] = None
            done += 1
            if done % 300 == 0:
                print(f"  {done}/{len(missing_moves)}")
                save_progress({"pokemon_moves": pokemon_moves, "move_cache": move_cache})
    save_progress({"pokemon_moves": pokemon_moves, "move_cache": move_cache})
    print("  Done.")
    return move_cache


def main() -> None:
    print("Loading pokedex.json…")
    with POKEDEX_PATH.open(encoding="utf-8") as f:
        pokedex: list[dict] = json.load(f)
    id_to_entry = {p["id"]: p for p in pokedex}

    progress = load_progress()
    pokemon_moves = _fetch_all_pokemon_moves(id_to_entry, progress)
    progress["pokemon_moves"] = pokemon_moves
    move_cache = _fetch_all_move_details(pokemon_moves, progress)

    print("Building move lists per Pokemon…")
    for pid, entry in id_to_entry.items():
        move_names = pokemon_moves.get(str(pid), [])
        damaging = [move_cache[n] for n in move_names if move_cache.get(n)]
        entry["moves"] = select_top_moves(damaging)

    print("Saving enriched pokedex.json…")
    with POKEDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(pokedex, f, ensure_ascii=False, indent=2)

    PROGRESS_PATH.unlink(missing_ok=True)
    print(f"\nDone! {len(pokedex)} Pokemon enriched.\n")

    sample = next(p for p in pokedex if p["id"] == 25)  # Pikachu
    print(f"Sample – {sample['name']['english']}:")
    for m in sample.get("moves", []):
        print(f"  {m['name']:20s}  type={m['type']:10s}  power={m['power']:3d}  class={m['damage_class']}")


if __name__ == "__main__":
    main()
