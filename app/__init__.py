import json
from pathlib import Path

from flask import Flask, abort, jsonify, request

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
POKEDEX_PATH = BASE_DIR / "files" / "pokedex.json"


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR),
        static_url_path="",
    )

    with POKEDEX_PATH.open(encoding="utf-8") as fh:
        pokedex = json.load(fh)

    by_name = {p["name"]["english"].lower(): p for p in pokedex}

    types: set[str] = set()
    for p in pokedex:
        types.update(p["type"])
    sorted_types = sorted(types)

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

    @app.route("/pokemon/<name>")
    def pokemon(name: str):
        entry = by_name.get(name.lower())
        if entry is None:
            abort(404)
        return jsonify(to_card(entry))

    return app
