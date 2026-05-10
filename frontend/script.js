const searchInput = document.getElementById("search");
const typeSelect = document.getElementById("type-filter");
const grid = document.getElementById("grid");
const status = document.getElementById("status");

let debounceId = null;

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
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
    debounceId = setTimeout(loadPokemons, 200);
});
typeSelect.addEventListener("change", loadPokemons);

loadTypes();
loadPokemons();
