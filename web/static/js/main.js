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
    let autocompleteTimeout;
    let currentSuggestionIndex = -1;

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

    window.search = search; // Make search function globally accessible

    window.search = search; // Make search function globally accessible

    // Function to display results
    const displayResults = (data) => {
        resultsCountDiv.textContent = `Found ${data.total} results`;

        if (data.spellcheck && data.spellcheck.collated) {
            const collatedLink = document.createElement('a');
            collatedLink.href = '#';
            collatedLink.textContent = data.spellcheck.collated;
            collatedLink.addEventListener('click', (e) => {
                e.preventDefault();
                search(data.spellcheck.collated);
            });
            spellcheckDiv.innerHTML = 'Did you mean: ';
            spellcheckDiv.appendChild(collatedLink);
            spellcheckDiv.append('?');
        } else if (data.spellcheck && data.spellcheck.suggestions.length > 0) {
            const suggestionsHtml = document.createElement('span');
            suggestionsHtml.textContent = 'Did you mean: ';
            data.spellcheck.suggestions.forEach((s, index) => {
                const suggestionLink = document.createElement('a');
                suggestionLink.href = '#';
                suggestionLink.textContent = s;
                suggestionLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    search(s);
                });
                suggestionsHtml.appendChild(suggestionLink);
                if (index < data.spellcheck.suggestions.length - 1) {
                    suggestionsHtml.append(', ');
                }
            });
            suggestionsHtml.append('?');
            spellcheckDiv.innerHTML = '';
            spellcheckDiv.appendChild(suggestionsHtml);
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

        const maxVisiblePages = 10;
        const currentPageGroup = Math.floor(currentPage / maxVisiblePages);
        const startPage = currentPageGroup * maxVisiblePages;
        const endPage = Math.min(startPage + maxVisiblePages, totalPages);

        // Previous group button
        if (startPage > 0) {
            const prevGroupBtn = document.createElement('a');
            prevGroupBtn.href = '#';
            prevGroupBtn.textContent = '« Previous 10';
            prevGroupBtn.className = 'pagination-nav';
            prevGroupBtn.addEventListener('click', (e) => {
                e.preventDefault();
                search(searchQuery.value, startPage - 1);
            });
            paginationDiv.appendChild(prevGroupBtn);
        }

        // Page numbers
        for (let i = startPage; i < endPage; i++) {
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

        // Next group button
        if (endPage < totalPages) {
            const nextGroupBtn = document.createElement('a');
            nextGroupBtn.href = '#';
            nextGroupBtn.textContent = 'Next 10 »';
            nextGroupBtn.className = 'pagination-nav';
            nextGroupBtn.addEventListener('click', (e) => {
                e.preventDefault();
                search(searchQuery.value, endPage);
            });
            paginationDiv.appendChild(nextGroupBtn);
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

    // Autocomplete functionality
    const setupAutocomplete = () => {
        const autocompleteContainer = document.createElement('div');
        autocompleteContainer.className = 'autocomplete-suggestions';
        autocompleteContainer.style.display = 'none';
        searchQuery.parentNode.appendChild(autocompleteContainer);

        const showSuggestions = (suggestions) => {
            autocompleteContainer.innerHTML = '';
            currentSuggestionIndex = -1;
            
            if (suggestions.length === 0) {
                autocompleteContainer.style.display = 'none';
                return;
            }

            suggestions.forEach((suggestion, index) => {
                const suggestionItem = document.createElement('div');
                suggestionItem.className = 'autocomplete-item';
                
                // Highlight the matching part anywhere in the suggestion (case-insensitive)
                const queryLower = searchQuery.value.toLowerCase();
                const suggestionLower = suggestion.toLowerCase();
                const matchIndex = suggestionLower.indexOf(queryLower);
                
                if (matchIndex >= 0) {
                    // Highlight the matching part wherever it appears
                    const beforeMatch = suggestion.substring(0, matchIndex);
                    const matchedPart = suggestion.substring(matchIndex, matchIndex + queryLower.length);
                    const afterMatch = suggestion.substring(matchIndex + queryLower.length);
                    suggestionItem.innerHTML = `${beforeMatch}<strong>${matchedPart}</strong>${afterMatch}`;
                } else {
                    suggestionItem.textContent = suggestion;
                }
                
                suggestionItem.addEventListener('click', () => {
                    searchQuery.value = suggestion;
                    autocompleteContainer.style.display = 'none';
                    search(suggestion);
                });
                autocompleteContainer.appendChild(suggestionItem);
            });

            autocompleteContainer.style.display = 'block';
        };

        const fetchSuggestions = async (query) => {
            if (query.length < 2) {
                autocompleteContainer.style.display = 'none';
                return;
            }

            try {
                const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success && data.suggestions.length > 0) {
                    showSuggestions(data.suggestions);
                } else {
                    autocompleteContainer.style.display = 'none';
                }
            } catch (error) {
                console.error('Autocomplete error:', error);
                autocompleteContainer.style.display = 'none';
            }
        };

        searchQuery.addEventListener('input', (e) => {
            clearTimeout(autocompleteTimeout);
            const query = e.target.value.trim();
            
            if (query.length >= 2) {
                autocompleteTimeout = setTimeout(() => fetchSuggestions(query), 300);
            } else {
                autocompleteContainer.style.display = 'none';
            }
        });

        searchQuery.addEventListener('keydown', (e) => {
            const suggestions = autocompleteContainer.querySelectorAll('.autocomplete-item');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentSuggestionIndex = Math.min(currentSuggestionIndex + 1, suggestions.length - 1);
                updateSuggestionHighlight(suggestions);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentSuggestionIndex = Math.max(currentSuggestionIndex - 1, -1);
                updateSuggestionHighlight(suggestions);
            } else if (e.key === 'Enter') {
                if (currentSuggestionIndex >= 0 && suggestions[currentSuggestionIndex]) {
                    e.preventDefault();
                    const selectedSuggestion = suggestions[currentSuggestionIndex].textContent;
                    searchQuery.value = selectedSuggestion;
                    autocompleteContainer.style.display = 'none';
                    search(selectedSuggestion);
                }
            } else if (e.key === 'Escape') {
                autocompleteContainer.style.display = 'none';
                currentSuggestionIndex = -1;
            }
        });

        const updateSuggestionHighlight = (suggestions) => {
            suggestions.forEach((item, index) => {
                if (index === currentSuggestionIndex) {
                    item.classList.add('highlighted');
                } else {
                    item.classList.remove('highlighted');
                }
            });
        };

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchQuery.contains(e.target) && !autocompleteContainer.contains(e.target)) {
                autocompleteContainer.style.display = 'none';
            }
        });
    };

    setupAutocomplete();

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