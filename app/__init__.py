import json
from collections import deque
from pathlib import Path

from flask import Flask, abort, jsonify, request

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
    def pokemon(name: str):
        entry = by_name.get(name.lower())
        if entry is None:
            abort(404)
        return jsonify(to_card(entry))

    return app
