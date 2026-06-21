const searchInput = document.getElementById("search");
const typeSelect = document.getElementById("type-filter");
const grid = document.getElementById("grid");
const status = document.getElementById("status");
const battleAnalysis = document.getElementById("battle-analysis");
const modalOverlay = document.getElementById("modal-overlay");
const modalClose = document.getElementById("modal-close");

modalClose.addEventListener("click", () => {
    modalOverlay.classList.add("hidden");
    battleAnalysis.innerHTML = "";
});

modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.add("hidden");
        battleAnalysis.innerHTML = "";
    }
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        modalOverlay.classList.add("hidden");
        battleAnalysis.innerHTML = "";
    }
});

let debounceId = null;

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[c]));
}

function renderCards(items) {
    if (items.length === 0) {
        status.textContent = "Brak wyników";
        grid.innerHTML = "";
        return;
    }

    status.textContent = `Znaleziono: ${items.length}`;

    grid.innerHTML = items.map(p => `
        <div class="card" data-name="${escapeHtml(p.name.toLowerCase())}">
            <img src="${escapeHtml(p.thumbnail)}" alt="${escapeHtml(p.name)}" loading="lazy">
            <div class="card-id">#${String(p.id).padStart(3, "0")}</div>
            <div class="card-name">${escapeHtml(p.name)}</div>
            <div class="card-types">
                ${p.type.map(t =>
                    `<span class="type type-${escapeHtml(t.toLowerCase())}">
                        ${escapeHtml(t)}
                    </span>`
                ).join("")}
            </div>
        </div>
    `).join("");

    document.querySelectorAll(".card").forEach(card => {
        card.addEventListener("click", () => {
            const pokemonName = card.dataset.name;
            loadBattleAnalysis(pokemonName);
        });
    });
}

async function loadBattleAnalysis(name) {
    battleAnalysis.innerHTML = "<p>Ładowanie analizy walk...</p>";
    modalOverlay.classList.remove("hidden");

    try {
        const response = await fetch(
            `/pokemon/${name}/battle-analysis?limit=5`
        );

        if (!response.ok) {
            throw new Error("Błąd pobierania danych");
        }

        const data = await response.json();

        renderBattleAnalysis(data);

    } catch (error) {
        battleAnalysis.innerHTML = `
            <div class="battle-box">
                <h2>Błąd</h2>
                <p>Nie udało się pobrać analizy walk.</p>
            </div>
        `;
    }
}

function renderBattleAnalysis(data) {

    const attacker = data.attacker;
    const opponents = data.top_opponents;

    battleAnalysis.innerHTML = `
        <div class="battle-box">

            <h2>Analiza walk AI</h2>

            <div class="attacker-box">
                <img
                    src="${escapeHtml(attacker.thumbnail)}"
                    alt="${escapeHtml(attacker.name)}"
                >

                <div>
                    <h3>${escapeHtml(attacker.name)}</h3>

                    <div class="card-types">
                        ${attacker.type.map(t =>
                            `<span class="type type-${escapeHtml(t.toLowerCase())}">
                                ${escapeHtml(t)}
                            </span>`
                        ).join("")}
                    </div>

                    <p>
                        HP: ${attacker.base.HP}
                        |
                        Attack: ${attacker.base.Attack}
                        |
                        Defense: ${attacker.base.Defense}
                        |
                        Speed: ${attacker.base.Speed}
                    </p>
                </div>
            </div>

            <h3>Pokémony które może pokonać</h3>

            <div class="opponents-list">

                ${opponents.map(item => `
                    <div class="opponent-card">

                        <img
                            src="${escapeHtml(item.pokemon.thumbnail)}"
                            alt="${escapeHtml(item.pokemon.name)}"
                        >

                        <div class="opponent-info">

                            <strong>
                                ${escapeHtml(item.pokemon.name)}
                            </strong>

                            <div class="card-types">
                                ${item.pokemon.type.map(t =>
                                    `<span class="type type-${escapeHtml(t.toLowerCase())}">
                                        ${escapeHtml(t)}
                                    </span>`
                                ).join("")}
                            </div>

                            <p class="win-rate">
                                ${Number(item.win_probability).toFixed(1)}%
                                szans na wygraną
                            </p>

                            <p>
                                ${escapeHtml(item.reason)}
                            </p>

                        </div>

                    </div>
                `).join("")}

            </div>

        </div>
    `;

}

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
        .catch(() => {
            status.textContent = "Błąd ładowania danych";
        });
}

function loadTypes() {

    fetch("/types")
        .then(res => res.json())
        .then(types => {

            for (const t of types) {

                const opt = document.createElement("option");

                opt.value = t;
                opt.textContent = t;

                typeSelect.appendChild(opt);
            }
        });
}

searchInput.addEventListener("input", () => {

    clearTimeout(debounceId);

    debounceId = setTimeout(
        loadPokemons,
        200
    );
});

typeSelect.addEventListener(
    "change",
    loadPokemons
);

loadTypes();
loadPokemons();