import json
import math
from collections import deque
from pathlib import Path

from flask import Flask, abort, jsonify, request

# Attacking type → defending type → damage multiplier (0, 0.5, 1, 2)
TYPE_CHART: dict[str, dict[str, float]] = {
    "Normal":   {"Rock": 0.5, "Ghost": 0.0, "Steel": 0.5},
    "Fire":     {"Grass": 2.0, "Ice": 2.0, "Bug": 2.0, "Steel": 2.0,
                 "Fire": 0.5, "Water": 0.5, "Rock": 0.5, "Dragon": 0.5},
    "Water":    {"Fire": 2.0, "Ground": 2.0, "Rock": 2.0,
                 "Water": 0.5, "Grass": 0.5, "Dragon": 0.5},
    "Electric": {"Water": 2.0, "Flying": 2.0,
                 "Electric": 0.5, "Grass": 0.5, "Ground": 0.0, "Dragon": 0.5},
    "Grass":    {"Water": 2.0, "Ground": 2.0, "Rock": 2.0,
                 "Fire": 0.5, "Grass": 0.5, "Poison": 0.5,
                 "Flying": 0.5, "Bug": 0.5, "Dragon": 0.5, "Steel": 0.5},
    "Ice":      {"Grass": 2.0, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0,
                 "Water": 0.5, "Ice": 0.5, "Steel": 0.5},
    "Fighting": {"Normal": 2.0, "Ice": 2.0, "Rock": 2.0, "Dark": 2.0, "Steel": 2.0,
                 "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5,
                 "Bug": 0.5, "Fairy": 0.5, "Ghost": 0.0},
    "Poison":   {"Grass": 2.0, "Fairy": 2.0,
                 "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0.0},
    "Ground":   {"Fire": 2.0, "Electric": 2.0, "Poison": 2.0, "Rock": 2.0, "Steel": 2.0,
                 "Grass": 0.5, "Bug": 0.5, "Flying": 0.0},
    "Flying":   {"Grass": 2.0, "Fighting": 2.0, "Bug": 2.0,
                 "Electric": 0.5, "Rock": 0.5, "Steel": 0.5},
    "Psychic":  {"Fighting": 2.0, "Poison": 2.0,
                 "Psychic": 0.5, "Dark": 0.0, "Steel": 0.5},
    "Bug":      {"Grass": 2.0, "Psychic": 2.0, "Dark": 2.0,
                 "Fire": 0.5, "Fighting": 0.5, "Flying": 0.5,
                 "Ghost": 0.5, "Steel": 0.5, "Fairy": 0.5},
    "Rock":     {"Fire": 2.0, "Ice": 2.0, "Flying": 2.0, "Bug": 2.0,
                 "Fighting": 0.5, "Ground": 0.5, "Steel": 0.5},
    "Ghost":    {"Psychic": 2.0, "Ghost": 2.0,
                 "Normal": 0.0, "Dark": 0.5},
    "Dragon":   {"Dragon": 2.0, "Steel": 0.5, "Fairy": 0.0},
    "Dark":     {"Psychic": 2.0, "Ghost": 2.0,
                 "Fighting": 0.5, "Dark": 0.5, "Fairy": 0.5},
    "Steel":    {"Ice": 2.0, "Rock": 2.0, "Fairy": 2.0,
                 "Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Steel": 0.5},
    "Fairy":    {"Fighting": 2.0, "Dragon": 2.0, "Dark": 2.0,
                 "Fire": 0.5, "Poison": 0.5, "Steel": 0.5},
}


def get_type_advantage(attacker_types: list[str], defender_types: list[str]) -> float:
    """Return best offensive type multiplier attacker can achieve vs defender."""
    best = 0.0
    for atk_type in attacker_types:
        matchups = TYPE_CHART.get(atk_type, {})
        mult = 1.0
        for def_type in defender_types:
            mult *= matchups.get(def_type, 1.0)
        best = max(best, mult)
    return best


def _move_type_mult(move_type: str, defender_types: list[str]) -> float:
    matchups = TYPE_CHART.get(move_type, {})
    mult = 1.0
    for def_type in defender_types:
        mult *= matchups.get(def_type, 1.0)
    return mult


def best_move_vs(attacker: dict, defender: dict) -> tuple[float, float, str | None]:
    """
    Find the best move the attacker can use against the defender.

    Uses real move data from the 'moves' field when available; falls back to
    the Pokemon's own type if there are no damaging moves on record.

    Returns (effective_dps, type_multiplier, move_name_or_None).
    """
    moves: list[dict] = attacker.get("moves", [])
    a = attacker["base"]
    d = defender["base"]

    if not moves:
        mult = get_type_advantage(attacker["type"], defender["type"])
        dps = (a["Attack"] + a["Sp. Attack"]) / 2 * mult / max((d["Defense"] + d["Sp. Defense"]) / 2, 1.0)
        return dps, mult, None

    best_dps = 0.0
    best_mult = 1.0
    best_name: str | None = None

    for move in moves:
        mult = _move_type_mult(move["type"], defender["type"])
        if move.get("damage_class") == "physical":
            atk_stat = a["Attack"]
            def_stat = d["Defense"]
        else:
            atk_stat = a["Sp. Attack"]
            def_stat = d["Sp. Defense"]

        dps = atk_stat * move["power"] / max(def_stat * 100, 1.0) * mult
        if dps > best_dps:
            best_dps = dps
            best_mult = mult
            best_name = move["name"]

    return best_dps, best_mult, best_name


def battle_score(attacker: dict, defender: dict) -> float:
    """
    Heuristic battle score using a simulated DPS race with real move data.

    Each side's damage output is calculated from their best available move
    (power × type effectiveness × stat) relative to the opponent's defensive
    stat. We compare the resulting KO-turn counts; the log-ratio is the score.
    Speed gives a ±15 % bonus to the faster Pokemon.
    """
    a = attacker["base"]
    d = defender["base"]

    atk_dps, _, _ = best_move_vs(attacker, defender)
    def_dps, def_type_mult, _ = best_move_vs(defender, attacker)

    # Fallback: if move-based DPS is 0, use plain stat ratio
    if atk_dps == 0:
        atk_dps = 0.01
    if def_dps == 0:
        def_dps = 0.01

    atk_turns_to_ko = d["HP"] / atk_dps
    def_turns_to_ko = a["HP"] / def_dps

    ratio = def_turns_to_ko / max(atk_turns_to_ko, 0.001)

    if a["Speed"] > d["Speed"]:
        ratio *= 1.15
    elif a["Speed"] < d["Speed"]:
        ratio *= 0.85

    return math.log(ratio)


def score_to_probability(score: float) -> float:
    return 1.0 / (1.0 + math.exp(-score))


def build_battle_reason(attacker: dict, defender: dict) -> str:
    a = attacker["base"]
    d = defender["base"]

    _, atk_type_mult, best_move = best_move_vs(attacker, defender)
    def_type_mult = get_type_advantage(defender["type"], attacker["type"])

    parts: list[str] = []

    if best_move and atk_type_mult >= 4:
        parts.append(f"podwójna przewaga {best_move} (x{atk_type_mult:.0f})")
    elif best_move and atk_type_mult >= 2:
        parts.append(f"przewaga {best_move} (x{atk_type_mult:.0f} vs {'/'.join(defender['type'])})")
    elif atk_type_mult >= 2:
        parts.append(f"przewaga typów ({'/'.join(attacker['type'])} → {'/'.join(defender['type'])})")

    if def_type_mult == 0:
        parts.append(f"odporność na ataki {'/'.join(defender['type'])}")
    elif def_type_mult <= 0.5:
        parts.append("odporność na ataki oponenta")

    atk_total = a["Attack"] + a["Sp. Attack"]
    def_total = d["Attack"] + d["Sp. Attack"]
    if atk_total > def_total * 1.2:
        parts.append(f"wyższy atak ({atk_total} vs {def_total})")

    if a["Speed"] > d["Speed"] * 1.1:
        parts.append(f"wyższa prędkość ({a['Speed']} vs {d['Speed']})")

    if a["HP"] > d["HP"] * 1.2:
        parts.append(f"więcej HP ({a['HP']} vs {d['HP']})")

    return ", ".join(parts) if parts else "ogólna przewaga statystyk"

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
POKEDEX_PATH = BASE_DIR / "files" / "pokedex.json"


def build_adjacency(pokedex: list[dict]) -> list[set[int]]:
    id_to_index = {p["id"]: i for i, p in enumerate(pokedex)}
    adjacency: list[set[int]] = [set() for _ in pokedex]
    for i, p in enumerate(pokedex):
        evolution = p.get("evolution") or {}
        related: list[str] = [nxt[0] for nxt in evolution.get("next", [])]
        if evolution.get("prev"):
            related.append(evolution["prev"][0])
        for raw_id in related:
            try:
                j = id_to_index[int(raw_id)]
            except (KeyError, ValueError):
                continue
            if j != i:
                adjacency[i].add(j)
                adjacency[j].add(i)
    return adjacency


def find_start_nodes(pokedex: list[dict], query: str, type_filter: str) -> list[int]:
    seeds: list[int] = []
    for i, p in enumerate(pokedex):
        if query and query not in p["name"]["english"].lower():
            continue
        if type_filter and type_filter not in p["type"]:
            continue
        seeds.append(i)
    return seeds


def bfs_search(
    pokedex: list[dict],
    adjacency: list[set[int]],
    query: str,
    type_filter: str,
) -> list[dict]:
    visited = [False] * len(pokedex)
    queue: deque[int] = deque()
    for start in find_start_nodes(pokedex, query, type_filter):
        if not visited[start]:
            visited[start] = True
            queue.append(start)

    order: list[int] = []
    while queue:
        i = queue.popleft()
        order.append(i)
        for j in sorted(adjacency[i]):
            if not visited[j]:
                visited[j] = True
                queue.append(j)

    return [pokedex[i] for i in order]


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


def _make_battle_results(attacker: dict, by_name: dict, limit: int) -> dict:
    results = []
    atk_key = attacker["name"]["english"].lower()
    for pname, defender in by_name.items():
        if pname == atk_key:
            continue
        score = battle_score(attacker, defender)
        prob = score_to_probability(score)
        results.append({
            "pokemon": to_card(defender),
            "win_probability": round(prob * 100, 1),
            "reason": build_battle_reason(attacker, defender),
            "_score": score,
        })
    results.sort(key=lambda x: x["_score"], reverse=True)
    top = results[:limit]
    for r in top:
        del r["_score"]
    return {"attacker": to_card(attacker), "top_opponents": top}


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path="",
    )

    with POKEDEX_PATH.open(encoding="utf-8") as fh:
        pokedex = json.load(fh)

    by_name = {p["name"]["english"].lower(): p for p in pokedex}
    sorted_types = sorted({t for p in pokedex for t in p["type"]})
    adjacency = build_adjacency(pokedex)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/types")
    def list_types():
        return jsonify(sorted_types)

    @app.route("/pokemons")
    def list_pokemons():
        query = request.args.get("q", "").strip().lower()
        type_filter = request.args.get("type", "").strip()
        results = bfs_search(pokedex, adjacency, query, type_filter)
        return jsonify([to_card(p) for p in results])

    @app.route("/pokemon/<name>")
    def get_pokemon(name: str):
        entry = by_name.get(name.lower())
        if entry is None:
            abort(404)
        return jsonify(to_card(entry))

    @app.route("/pokemon/<name>/battle-analysis")
    def get_battle_analysis(name: str):
        attacker = by_name.get(name.lower())
        if attacker is None:
            abort(404)
        limit = request.args.get("limit", 5, type=int)
        return jsonify(_make_battle_results(attacker, by_name, limit))

    return app
