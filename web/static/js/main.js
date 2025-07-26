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
                <h2>${pokemon.name}</h2>
                <p><b>ID:</b> ${pokemon.id}</p>
                <p><b>Type:</b> ${pokemon.types.join(', ')}</p>
                <p><b>Abilities:</b> ${pokemon.all_abilities.join(', ')}</p>
                <p><b>Stats:</b></p>
                <ul>
                    <li>HP: ${pokemon.stat_hp}</li>
                    <li>Attack: ${pokemon.stat_attack}</li>
                    <li>Defense: ${pokemon.stat_defense}</li>
                    <li>Speed: ${pokemon.stat_speed}</li>
                </ul>
                <p>${pokemon.flavor_text}</p>
            `;
            modal.style.display = 'block';
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('Failed to load Pokemon details.');
    }

    const closeBtn = modal.querySelector('.modal-close-btn');
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
};