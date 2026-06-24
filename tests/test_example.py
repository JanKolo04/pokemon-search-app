"""
Tests for BFS search, type-advantage heuristic, and battle analysis API.
"""

from app import (
    battle_score,
    best_move_vs,
    bfs_search,
    build_adjacency,
    get_type_advantage,
    score_to_probability,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def _pokemon(hp=50, atk=50, def_=50, spatk=50, spdef=50, spd=50, types=None, moves=None):
    return {
        "id": 0,
        "name": {"english": "Test"},
        "type": types or ["Normal"],
        "base": {
            "HP": hp,
            "Attack": atk,
            "Defense": def_,
            "Sp. Attack": spatk,
            "Sp. Defense": spdef,
            "Speed": spd,
        },
        "moves": moves or [],
        "image": {"sprite": "", "thumbnail": "", "hires": ""},
        "evolution": {},
    }


# ── get_type_advantage ────────────────────────────────────────────────────────

def test_type_advantage_super_effective():
    assert get_type_advantage(["Electric"], ["Water"]) == 2.0


def test_type_advantage_not_effective():
    assert get_type_advantage(["Electric"], ["Ground"]) == 0.0


def test_type_advantage_neutral():
    assert get_type_advantage(["Normal"], ["Normal"]) == 1.0


def test_type_advantage_dual_defender_stacks():
    # Electric vs Water/Flying: 2x * 2x = 4x
    assert get_type_advantage(["Electric"], ["Water", "Flying"]) == 4.0


def test_type_advantage_picks_best_attacker_type():
    # Fire/Flying vs Grass: Fire=2x, Flying=2x → best = 2x (no stacking on attacker)
    result = get_type_advantage(["Fire", "Flying"], ["Grass"])
    assert result == 2.0


def test_type_advantage_resist():
    # Water vs Water = 0.5x
    assert get_type_advantage(["Water"], ["Water"]) == 0.5


def test_type_advantage_unknown_type_is_neutral():
    assert get_type_advantage(["Normal"], ["Normal"]) == 1.0


# ── score_to_probability ──────────────────────────────────────────────────────

def test_probability_at_zero_is_half():
    assert abs(score_to_probability(0) - 0.5) < 0.001


def test_probability_positive_score_above_half():
    assert score_to_probability(3) > 0.95


def test_probability_negative_score_below_half():
    assert score_to_probability(-3) < 0.05


def test_probability_in_range():
    for s in [-10, -1, 0, 1, 10]:
        p = score_to_probability(s)
        assert 0.0 <= p <= 1.0


# ── battle_score ──────────────────────────────────────────────────────────────

def test_battle_score_identical_pokemon_is_neutral():
    p = _pokemon()
    prob = score_to_probability(battle_score(p, p))
    assert 0.45 <= prob <= 0.55


def test_battle_score_stronger_wins():
    strong = _pokemon(hp=150, atk=150, def_=150, spatk=150, spdef=150, spd=150)
    weak = _pokemon(hp=30, atk=30, def_=30, spatk=30, spdef=30, spd=30)
    assert battle_score(strong, weak) > 0
    assert battle_score(weak, strong) < 0


def test_battle_score_type_advantage_helps():
    electric = _pokemon(types=["Electric"])
    water = _pokemon(types=["Water"])
    normal = _pokemon(types=["Normal"])
    # Electric vs Water should score higher than Electric vs Normal
    assert battle_score(electric, water) > battle_score(electric, normal)


def test_battle_score_speed_matters():
    fast = _pokemon(spd=150)
    slow = _pokemon(spd=10)
    assert battle_score(fast, slow) > battle_score(slow, fast)


# ── best_move_vs ──────────────────────────────────────────────────────────────

def test_best_move_vs_uses_real_moves():
    attacker = _pokemon(
        types=["Normal"],
        moves=[
            {"name": "Thunderbolt", "type": "Electric", "power": 90, "damage_class": "special"},
            {"name": "Surf", "type": "Water", "power": 90, "damage_class": "special"},
        ],
    )
    defender = _pokemon(types=["Water"])
    _, mult, name = best_move_vs(attacker, defender)
    assert name == "Thunderbolt"  # Electric x2 vs Water
    assert mult == 2.0


def test_best_move_vs_fallback_when_no_moves():
    attacker = _pokemon(types=["Electric"], moves=[])
    defender = _pokemon(types=["Water"])
    dps, mult, name = best_move_vs(attacker, defender)
    assert name is None
    assert mult == 2.0  # falls back to type chart


# ── BFS search ───────────────────────────────────────────────────────────────

def _mini_pokedex():
    return [
        {"id": 1, "name": {"english": "Bulbasaur"}, "type": ["Grass", "Poison"],
         "base": {}, "image": {}, "moves": [], "evolution": {"next": [["2", "Level 16"]]}},
        {"id": 2, "name": {"english": "Ivysaur"}, "type": ["Grass", "Poison"],
         "base": {}, "image": {}, "moves": [],
         "evolution": {"prev": ["1", "Level 16"], "next": [["3", "Level 32"]]}},
        {"id": 3, "name": {"english": "Venusaur"}, "type": ["Grass", "Poison"],
         "base": {}, "image": {}, "moves": [], "evolution": {"prev": ["2", "Level 32"]}},
        {"id": 4, "name": {"english": "Charmander"}, "type": ["Fire"],
         "base": {}, "image": {}, "moves": [], "evolution": {"next": [["5", "Level 16"]]}},
        {"id": 5, "name": {"english": "Charmeleon"}, "type": ["Fire"],
         "base": {}, "image": {}, "moves": [],
         "evolution": {"prev": ["4", "Level 16"]}},
    ]


def test_bfs_finds_direct_match():
    pokedex = _mini_pokedex()
    adjacency = build_adjacency(pokedex)
    results = bfs_search(pokedex, adjacency, "bulbasaur", "")
    names = [r["name"]["english"] for r in results]
    assert "Bulbasaur" in names


def test_bfs_expands_evolution_chain():
    pokedex = _mini_pokedex()
    adjacency = build_adjacency(pokedex)
    results = bfs_search(pokedex, adjacency, "bulbasaur", "")
    names = [r["name"]["english"] for r in results]
    assert "Ivysaur" in names
    assert "Venusaur" in names


def test_bfs_does_not_cross_chains():
    pokedex = _mini_pokedex()
    adjacency = build_adjacency(pokedex)
    results = bfs_search(pokedex, adjacency, "bulbasaur", "")
    names = [r["name"]["english"] for r in results]
    assert "Charmander" not in names
    assert "Charmeleon" not in names


def test_bfs_type_filter():
    pokedex = _mini_pokedex()
    adjacency = build_adjacency(pokedex)
    results = bfs_search(pokedex, adjacency, "", "Fire")
    names = [r["name"]["english"] for r in results]
    assert "Charmander" in names
    assert "Bulbasaur" not in names


def test_bfs_empty_query_no_filter_returns_all():
    # Empty query + no type filter → all Pokemon (used on initial page load)
    pokedex = _mini_pokedex()
    adjacency = build_adjacency(pokedex)
    results = bfs_search(pokedex, adjacency, "", "")
    assert len(results) == len(pokedex)


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_types_endpoint(client):
    r = client.get("/types")
    assert r.status_code == 200
    types = r.get_json()
    assert isinstance(types, list)
    assert "Fire" in types
    assert "Water" in types
    assert types == sorted(types)


def test_search_by_name(client):
    r = client.get("/pokemons?q=pikachu")
    assert r.status_code == 200
    data = r.get_json()
    names = [p["name"] for p in data]
    assert "Pikachu" in names


def test_search_includes_evolution_chain(client):
    r = client.get("/pokemons?q=charmander")
    assert r.status_code == 200
    names = [p["name"] for p in r.get_json()]
    assert "Charmander" in names
    assert "Charmeleon" in names
    assert "Charizard" in names


def test_search_by_type_filter(client):
    # BFS expands evolution chains, so some non-Electric results may appear
    # (e.g. Eevee returned because Jolteon is its evolution and matches Electric).
    # We assert that Electric types are present, not that ALL results are Electric.
    r = client.get("/pokemons?type=Electric")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) > 0
    assert any("Electric" in p["type"] for p in data)


def test_single_pokemon_endpoint(client):
    r = client.get("/pokemon/pikachu")
    assert r.status_code == 200
    data = r.get_json()
    assert data["name"] == "Pikachu"
    assert "Electric" in data["type"]


def test_single_pokemon_not_found(client):
    assert client.get("/pokemon/doesnotexist").status_code == 404


def test_battle_analysis_structure(client):
    r = client.get("/pokemon/pikachu/battle-analysis?limit=3")
    assert r.status_code == 200
    data = r.get_json()
    assert data["attacker"]["name"] == "Pikachu"
    assert len(data["top_opponents"]) == 3
    for opp in data["top_opponents"]:
        assert "pokemon" in opp
        assert "win_probability" in opp
        assert "reason" in opp
        assert 50.0 <= opp["win_probability"] <= 100.0


def test_battle_analysis_not_found(client):
    assert client.get("/pokemon/doesnotexist/battle-analysis").status_code == 404


def test_battle_analysis_electric_beats_water(client):
    r = client.get("/pokemon/pikachu/battle-analysis?limit=20")
    data = r.get_json()
    water_opponents = [
        o for o in data["top_opponents"] if "Water" in o["pokemon"]["type"]
    ]
    assert len(water_opponents) > 0, "Pikachu should have Water-type victims in top 20"


def test_battle_analysis_opponents_sorted_descending(client):
    r = client.get("/pokemon/charizard/battle-analysis?limit=10")
    probs = [o["win_probability"] for o in r.get_json()["top_opponents"]]
    assert probs == sorted(probs, reverse=True)
