class PokemonSearchApp {
            constructor() {
                this.currentPage = 0;
                this.resultsPerPage = 20;
                this.totalResults = 0;
                this.isLoading = false;
                
                this.modal = document.getElementById('pokemonModal');
                this.modalBody = document.getElementById('modalBody');
                this.modalCloseBtn = document.querySelector('.modal-close-btn');

                this.initializeEventListeners();
                this.performSearch(); // Load initial results
            }

            initializeEventListeners() {
                // Search form submission
                document.getElementById('searchForm').addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.currentPage = 0;
                    this.performSearch();
                });

                // Filter changes
                ['generationFilter', 'typeFilter', 'legendaryFilter', 'sortBy', 'sortOrder'].forEach(id => {
                    document.getElementById(id).addEventListener('change', () => {
                        this.currentPage = 0;
                        this.performSearch();
                    });
                });

                // Real-time search (debounced)
                let searchTimeout;
                document.getElementById('searchQuery').addEventListener('input', () => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        this.currentPage = 0;
                        this.performSearch();
                    }, 500);
                });
                
                // Modal closing events
                this.modalCloseBtn.addEventListener('click', () => this.hidePokemonDetails());
                this.modal.addEventListener('click', (e) => {
                    if (e.target === this.modal) {
                        this.hidePokemonDetails();
                    }
                });
            }

            async performSearch() {
                if (this.isLoading) return;
                
                this.isLoading = true;
                this.showLoading(true);
                this.hideError();

                try {
                    const params = this.buildSearchParams();
                    const response = await fetch(`/api/search?${params}`);
                    const data = await response.json();

                    if (data.success) {
                        this.displayResults(data);
                        this.updatePagination(data);
                    } else {
                        this.showError(data.error || 'Search failed');
                    }
                } catch (error) {
                    this.showError('Network error: ' + error.message);
                } finally {
                    this.showLoading(false);
                    this.isLoading = false;
                }
            }

            buildSearchParams() {
                const params = new URLSearchParams();
                
                const query = document.getElementById('searchQuery').value.trim();
                if (query) params.append('q', query);
                
                params.append('start', this.currentPage * this.resultsPerPage);
                params.append('rows', this.resultsPerPage);
                
                const generation = document.getElementById('generationFilter').value;
                if (generation) params.append('generation', generation);
                
                const type = document.getElementById('typeFilter').value;
                if (type) params.append('type', type);
                
                const legendary = document.getElementById('legendaryFilter').value;
                if (legendary) params.append('legendary', legendary);
                
                params.append('sort', document.getElementById('sortBy').value);
                params.append('order', document.getElementById('sortOrder').value);
                
                return params.toString();
            }

            displayResults(data) {
                const grid = document.getElementById('pokemonGrid');
                const resultsCount = document.getElementById('resultsCount');
                
                this.totalResults = data.total;
                
                // Update results count
                resultsCount.textContent = `Found ${data.total} Pokemon`;
                
                // Clear previous results
                grid.innerHTML = '';
                
                // Display Pokemon cards
                data.results.forEach(pokemon => {
                    const card = this.createPokemonCard(pokemon);
                    grid.appendChild(card);
                });
            }

            createPokemonCard(pokemon) {
                const card = document.createElement('div');
                card.className = 'pokemon-card';
                card.onclick = () => this.showPokemonDetails(pokemon);
                
                const types = pokemon.types || [];
                
                card.innerHTML = `
                    <div class="pokemon-header">
                        <div class="pokemon-name">${pokemon.name}</div>
                        <div class="pokemon-id">#${String(pokemon.pokemon_id).padStart(3, '0')}</div>
                    </div>
                    
                    <div class="pokemon-types">
                        ${types.map(type => 
                            `<span class="type-badge type-${type}">${type}</span>`
                        ).join('')}
                    </div>
                `;
                
                return card;
            }

            showPokemonDetails(pokemon) {
                const imageUrl = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${pokemon.pokemon_id}.png`;
                
                const types = pokemon.types || [];
                const abilities = pokemon.abilities || [];
                const flavorText = pokemon.flavor_text || 'No description available.';
                const levelupMoves = pokemon.levelup_moves || [];

                this.modalBody.innerHTML = `

                    <div class="split-modal">
                        <div>
                        
                            <img src="${imageUrl}" alt="${pokemon.name}" class="modal-pokemon-image" onerror="this.style.display='none'">
                            <div class="modal-pokemon-header">
                                <div class="modal-pokemon-name">${pokemon.name}</div>
                                <div class="modal-pokemon-id">#${String(pokemon.pokemon_id).padStart(3, '0')}</div>
                            </div>
                            <div class="modal-types">
                                ${types.map(type => `<span class="type-badge type-${type}">${type}</span>`).join('')}
                            </div>
                            <div class="modal-section">
                                <div class="modal-section-title">Stats</div>
                                <div class="pokemon-stats modal-stats-grid">
                                    <div class="stat-item"><div class="stat-label">HP</div><div class="stat-value">${pokemon.stat_hp || 0}</div></div>
                                    <div class="stat-item"><div class="stat-label">Attack</div><div class="stat-value">${pokemon.stat_attack || 0}</div></div>
                                    <div class="stat-item"><div class="stat-label">Defense</div><div class="stat-value">${pokemon.stat_defense || 0}</div></div>
                                    <div class="stat-item"><div class="stat-label">Sp. Atk</div><div class="stat-value">${pokemon['stat_special-attack'] || 0}</div></div>
                                    <div class="stat-item"><div class="stat-label">Sp. Def</div><div class="stat-value">${pokemon['stat_special-defense'] || 0}</div></div>
                                    <div class="stat-item"><div class="stat-label">Speed</div><div class="stat-value">${pokemon.stat_speed || 0}</div></div>
                                </div>
                            </div>
                        </div>
                            <div>
                            ${abilities.length > 0 ? `
                            <div class="modal-section">
                                <div class="modal-section-title">Abilities</div>
                                <div class="ability-list">
                                    ${abilities.map(ability => `<span class="ability-tag">${ability}</span>`).join('')}
                                </div>
                            </div>` : ''}

                            ${levelupMoves.length > 0 ? `
                            <div class="modal-section">
                                <div class="modal-section-title">Level-Up Moves</div>
                                <div class="ability-list">
                                    ${levelupMoves.map(move => `<span class="ability-tag move-tag">${move}</span>`).join('')}
                                </div>
                            </div>` : ''}

                            <div class="modal-section">
                                <div class="modal-section-title">Description</div>
                                <div class="pokemon-flavor">${flavorText}</div>
                            </div>
                        </div>
                    </div>
                `;

                this.modal.classList.add('show');
                document.body.style.overflow = 'hidden'; // Prevent background scrolling
            }
            
            hidePokemonDetails() {
                this.modal.classList.remove('show');
                document.body.style.overflow = ''; // Restore background scrolling
            }

            updatePagination(data) {
                const pagination = document.getElementById('pagination');
                pagination.innerHTML = '';
                
                const totalPages = Math.ceil(data.total / this.resultsPerPage);
                const currentPage = this.currentPage;
                
                if (totalPages <= 1) return;
                
                // Previous button
                if (currentPage > 0) {
                    const prevBtn = this.createPageButton('Previous', currentPage - 1);
                    pagination.appendChild(prevBtn);
                }
                
                // Page numbers
                const startPage = Math.max(0, currentPage - 2);
                const endPage = Math.min(totalPages - 1, currentPage + 2);
                
                for (let i = startPage; i <= endPage; i++) {
                    const pageBtn = this.createPageButton(i + 1, i);
                    if (i === currentPage) {
                        pageBtn.classList.add('active');
                    }
                    pagination.appendChild(pageBtn);
                }
                
                // Next button
                if (currentPage < totalPages - 1) {
                    const nextBtn = this.createPageButton('Next', currentPage + 1);
                    pagination.appendChild(nextBtn);
                }
            }

            createPageButton(text, page) {
                const btn = document.createElement('button');
                btn.className = 'page-btn';
                btn.textContent = text;
                btn.onclick = () => {
                    this.currentPage = page;
                    this.performSearch();
                };
                return btn;
            }

            showLoading(show) {
                document.getElementById('loadingMessage').style.display = show ? 'block' : 'none';
            }

            showError(message) {
                const errorDiv = document.getElementById('errorMessage');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
            }

            hideError() {
                document.getElementById('errorMessage').style.display = 'none';
            }
        }

        // Initialize the app when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new PokemonSearchApp();
        });