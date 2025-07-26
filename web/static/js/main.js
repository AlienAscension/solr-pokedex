document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const searchQuery = document.getElementById('searchQuery');
    const resultsGrid = document.getElementById('pokemonGrid');
    const resultsCountDiv = document.getElementById('results-count');
    const spellcheckDiv = document.getElementById('spellcheck');
    const loadingMessage = document.getElementById('loadingMessage');
    const errorMessage = document.getElementById('errorMessage');
    const paginationDiv = document.getElementById('pagination');

    const generationFilter = document.getElementById('generationFilter');
    const typeFilter = document.getElementById('typeFilter');
    const legendaryFilter = document.getElementById('legendaryFilter');
    const sortBy = document.getElementById('sortBy');
    const sortOrder = document.getElementById('sortOrder');

    let currentPage = 0;
    const rowsPerPage = 20;

    // Function to perform a search
    const search = async (query, page = 0) => {
        currentPage = page;
        loadingMessage.style.display = 'block';
        errorMessage.style.display = 'none';
        resultsGrid.innerHTML = '';
        paginationDiv.innerHTML = '';

        const params = new URLSearchParams({
            q: query,
            start: page * rowsPerPage,
            rows: rowsPerPage,
            sort: sortBy.value,
            order: sortOrder.value,
            generation: generationFilter.value,
            type: typeFilter.value,
            legendary: legendaryFilter.value,
        });

        try {
            const response = await fetch(`/api/search?${params.toString()}`);
            const data = await response.json();

            if (data.success) {
                displayResults(data);
                displayPagination(data);
            } else {
                errorMessage.textContent = data.error || 'An unknown error occurred.';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            errorMessage.textContent = 'Failed to fetch search results.';
            errorMessage.style.display = 'block';
        } finally {
            loadingMessage.style.display = 'none';
        }
    };

    // Function to display results
    const displayResults = (data) => {
        resultsCountDiv.textContent = `Found ${data.total} results`;

        if (data.spellcheck && data.spellcheck.collated) {
            spellcheckDiv.innerHTML = `Did you mean: <a href="#" onclick="search('${data.spellcheck.collated}')">${data.spellcheck.collated}</a>?`;
        } else if (data.spellcheck && data.spellcheck.suggestions.length > 0) {
            const suggestionsHtml = data.spellcheck.suggestions.map(s => `<a href="#" onclick="search('${s}')">${s}</a>`).join(', ');
            spellcheckDiv.innerHTML = `Did you mean: ${suggestionsHtml}?`;
        } else {
            spellcheckDiv.innerHTML = '';
        }

        data.results.forEach(pokemon => {
            const card = document.createElement('div');
            card.className = 'pokemon-card';
            card.innerHTML = `
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${pokemon.id}.png" alt="${pokemon.name}">
                <h3>${pokemon.name}</h3>
                <p>#${pokemon.id}</p>
                <p style="display: none;">${pokemon.stat_special_attack}</p>
                <p style="display: none;">${pokemon.stat_special_defense}</p>
            `;
            card.addEventListener('click', () => openModal(pokemon.id));
            resultsGrid.appendChild(card);
        });
    };

    // Function to display pagination
    const displayPagination = (data) => {
        const totalPages = Math.ceil(data.total / rowsPerPage);
        if (totalPages <= 1) return;

        for (let i = 0; i < totalPages; i++) {
            const pageLink = document.createElement('a');
            pageLink.href = '#';
            pageLink.textContent = i + 1;
            if (i === currentPage) {
                pageLink.className = 'active';
            }
            pageLink.addEventListener('click', (e) => {
                e.preventDefault();
                search(searchQuery.value, i);
            });
            paginationDiv.appendChild(pageLink);
        }
    };

    // Event Listeners
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        search(searchQuery.value);
    });

    [generationFilter, typeFilter, legendaryFilter, sortBy, sortOrder].forEach(el => {
        el.addEventListener('change', () => search(searchQuery.value));
    });

    // Initial search
    search('*:*');
});

// Functions for modal
const openModal = async (pokemonId) => {
    const modal = document.getElementById('pokemonModal');
    const modalBody = document.getElementById('modalBody');

    try {
        const response = await fetch(`/api/pokemon/${pokemonId}`);
        const data = await response.json();

        if (data.success) {
            const pokemon = data.pokemon;
            modalBody.innerHTML = `
                <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${pokemon.id}.png" alt="${pokemon.name}" class="modal-pokemon-image">
                <div class="modal-pokemon-header">
                    <h2 class="modal-pokemon-name">${pokemon.name}</h2>
                    <p class="modal-pokemon-id">#${pokemon.id}</p>
                </div>

                <div class="modal-section">
                    <h3 class="modal-section-title">Types</h3>
                    <div class="modal-types">
                        ${pokemon.types.map(type => `<span class="type-badge type-${type.toLowerCase()}">${type}</span>`).join('')}
                    </div>
                </div>

                <div class="modal-section">
                    <h3 class="modal-section-title">Abilities</h3>
                    <p>${pokemon.all_abilities.join(', ')}</p>
                </div>

                <div class="modal-section">
                    <h3 class="modal-section-title">Stats</h3>
                    <div class="modal-stats-grid">
                        <div class="stat-item">
                            <span class="stat-label">HP</span>
                            <span class="stat-value">${pokemon.stat_hp}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Attack</span>
                            <span class="stat-value">${pokemon.stat_attack}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Defense</span>
                            <span class="stat-value">${pokemon.stat_defense}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Speed</span>
                            <span class="stat-value">${pokemon.stat_speed}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Special Attack</span>
                            <span class="stat-value">${pokemon.stat_special_attack}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Special Defense</span>
                            <span class="stat-value">${pokemon.stat_special_defense}</span>
                        </div>
                    </div>
                </div>

                <div class="modal-section">
                    <h3 class="modal-section-title">Flavor Text</h3>
                    <p>${pokemon.flavor_text}</p>
                </div>
            `;
            modal.classList.add('show');
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('Failed to load Pokemon details.');
    }

    const closeBtn = modal.querySelector('.modal-close-btn');
    closeBtn.onclick = () => modal.classList.remove('show');
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.classList.remove('show');
        }
    };
};