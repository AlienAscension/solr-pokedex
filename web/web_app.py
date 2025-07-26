#!/usr/bin/env python3
"""
Pokemon Search Web Frontend

Flask web application providing a user-friendly interface for searching Pokemon
using the Solr backend. Supports full-text search, filtering, and sorting.

Features:
- Full-text search across all Pokemon data
- Filter by generation, type, abilities
- Sort by various stats and attributes
- Responsive web design
- RESTful API endpoints

Requirements:
- flask
- pysolr
- requests

Usage:
    python web_app.py

Author: Generated for Pokemon Search Engine Project
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import pysolr
import os
import logging
from typing import Dict, List, Any, Optional
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PokemonSearchApp:
    """
    Flask application for Pokemon search interface
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'pokemon-search-secret-key'
        
        # Solr configuration
        solr_url = os.environ.get('SOLR_URL', 'http://localhost:8983/solr/pokemon')
        self.solr = pysolr.Solr(solr_url, always_commit=True, timeout=10)
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main search page"""
            return render_template('index.html')
        
        @self.app.route('/api/search')
        def api_search():
            """API endpoint for Pokemon search"""
            return self.search_pokemon()
        
        @self.app.route('/api/pokemon/<int:pokemon_id>')
        def api_pokemon_detail(pokemon_id):
            """API endpoint for individual Pokemon details"""
            return self.get_pokemon_detail(pokemon_id)
        
        @self.app.route('/api/stats')
        def api_stats():
            """API endpoint for search statistics"""
            return self.get_search_stats()
        
        @self.app.route('/api/autocomplete')
        def api_autocomplete():
            """API endpoint for search autocomplete suggestions"""
            return self.get_autocomplete_suggestions()
    
    def search_pokemon(self) -> Dict[str, Any]:
        """
        Search Pokemon based on query parameters
        
        Returns:
            JSON response with search results
        """
        try:
            # Get search parameters
            query = request.args.get('q', '') # Default to empty string
            if not query.strip():
                query = '*:*' # If query is empty or just whitespace, search all
            
            start = int(request.args.get('start', 0))
            rows = min(int(request.args.get('rows', 20)), 100)  # Max 100 results
            sort_field = request.args.get('sort', 'pokemon_id')
            sort_order = request.args.get('order', 'asc')
            
            # Filters
            generation = request.args.get('generation')
            pokemon_type = request.args.get('type')
            ability = request.args.get('ability')
            is_legendary = request.args.get('legendary')
            
            # Build Solr filters
            filters = self.build_solr_filters(
                generation, pokemon_type, ability, is_legendary
            )
            
            # Build sort parameter
            sort_param = f"{sort_field} {sort_order}"
            
            # Execute main search with enhanced substring matching
            # If it's a simple term search, try wildcard matching first
            if query and query != '*:*' and ' ' not in query and len(query) > 2:
                # Try wildcard search for partial matches
                wildcard_query = f'name:*{query}* OR name:*{query.capitalize()}*'
                params = {
                    'q': wildcard_query,
                    'start': start,
                    'rows': rows,
                    'sort': sort_param,
                    'facet': 'true',
                    'facet.field': ['generation', 'primary_type', 'color', 'habitat'],
                    'facet.mincount': 1,
                }
            else:
                # Use edismax for complex queries
                params = {
                    'q': query,
                    'start': start,
                    'rows': rows,
                    'sort': sort_param,
                    'facet': 'true',
                    'facet.field': ['generation', 'primary_type', 'color', 'habitat'],
                    'facet.mincount': 1,
                    'defType': 'edismax',
                    'qf': 'name^5 types^2 all_abilities^2 flavor_text^1',
                    'mm': '1',
                    'qs': '2',
                    'ps': '2', 
                    'tie': '0.1',
                }
            
            if filters:
                params['fq'] = filters # Add filters to the fq parameter
                
            results = self.solr.search(**params)

            # Fetch spellcheck suggestions separately
            suggestions = []
            collated_suggestion = None
            if query.strip() and query != '*:*': # Only request spellcheck if there's a real query
                spellcheck_params = {
                    'q': query,
                    'spellcheck': 'true',
                    'spellcheck.build': 'true', # This was the missing piece!
                    'spellcheck.collate': 'true',
                    'spellcheck.maxCollations': 5,
                    'spellcheck.dictionary': 'default',
                    'spellcheck.extendedResults': 'true',
                    'wt': 'json' # Ensure JSON response
                }
                try:
                    spellcheck_response = requests.get(f"{self.solr.url.rstrip('/')}/spell", params=spellcheck_params)
                    spellcheck_response.raise_for_status()
                    spellcheck_data = spellcheck_response.json()
                    logger.info(f"Raw spellcheck response: {spellcheck_data}")

                    if spellcheck_data.get('spellcheck') and spellcheck_data['spellcheck'].get('suggestions'):
                        # Solr's spellcheck suggestions can be an array with the term and then the suggestion object
                        # We need to iterate through them to find the actual suggestions
                        for item in spellcheck_data['spellcheck']['suggestions']:
                            if isinstance(item, dict) and item.get('suggestion'):
                                suggestions.extend([s['word'] for s in item['suggestion']])
                        
                        if spellcheck_data['spellcheck'].get('collations'):
                            collations_list = spellcheck_data['spellcheck']['collations']
                            # Collations can be a list of [original, corrected] or just [corrected]
                            # We want the corrected one, which is usually the second element if both are present
                            # or the first if only one is present.
                            if len(collations_list) > 1 and isinstance(collations_list[1], str):
                                collated_suggestion = collations_list[1]
                            elif len(collations_list) > 0 and isinstance(collations_list[0], str):
                                collated_suggestion = collations_list[0]
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching spellcheck suggestions: {e}")

            
            # Format response
            response = {
                'success': True,
                'total': results.hits,
                'start': start,
                'rows': rows,
                'results': [dict(doc) for doc in results.docs],
                'facets': self.format_facets(results.facets) if hasattr(results, 'facets') else {},
                'query': query,
                'spellcheck': {
                    'suggestions': suggestions,
                    'collated': collated_suggestion,
                },
                'filters': {
                    'generation': generation,
                    'type': pokemon_type,
                    'ability': ability,
                    'legendary': is_legendary
                }
            }
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'total': 0,
                'results': []
            }), 500
    
    def build_solr_filters(self, generation: Optional[str], 
                        pokemon_type: Optional[str], ability: Optional[str],
                        is_legendary: Optional[str]) -> List[str]:
        """
        Build Solr filter query strings
        
        Args:
            generation: Generation filter
            pokemon_type: Type filter
            ability: Ability filter
            is_legendary: Legendary filter
            
        Returns:
            List of Solr filter query strings
        """
        filters = []
        
        # Add filters
        if generation:
            filters.append(f'generation:{generation}')
        
        if pokemon_type:
            filters.append(f'(primary_type:{pokemon_type} OR secondary_type:{pokemon_type})')
        
        if ability:
            filters.append(f'all_abilities:*{ability}*')
        
        if is_legendary:
            if is_legendary.lower() in ['true', '1', 'yes']:
                filters.append('(is_legendary:true OR is_mythical:true)')
            else:
                filters.append('(is_legendary:false AND is_mythical:false)')
        
        return filters
    
    def format_facets(self, facets: Dict) -> Dict[str, List[Dict]]:
        """
        Format Solr facets for JSON response
        
        Args:
            facets: Raw facets from Solr
            
        Returns:
            Formatted facets dictionary
        """
        formatted = {}
        
        for field, values in facets.items():
            if field.endswith('_facet') or not isinstance(values, list):
                continue
            
            formatted[field] = []
            # Facet values come as [value1, count1, value2, count2, ...]
            for i in range(0, len(values), 2):
                if i + 1 < len(values):
                    formatted[field].append({
                        'value': values[i],
                        'count': values[i + 1]
                    })
        
        return formatted
    
    def get_pokemon_detail(self, pokemon_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific Pokemon
        
        Args:
            pokemon_id: Pokemon ID
            
        Returns:
            JSON response with Pokemon details
        """
        try:
            results = self.solr.search(f'pokemon_id:{pokemon_id}')
            
            if results.hits > 0:
                pokemon = dict(results.docs[0])
                return jsonify({
                    'success': True,
                    'pokemon': pokemon
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Pokemon not found'
                }), 404
                
        except Exception as e:
            logger.error(f"Detail error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get general statistics about the Pokemon collection
        
        Returns:
            JSON response with stats
        """
        try:
            # Total count
            total_results = self.solr.search('*:*', rows=0)
            total_count = total_results.hits
            
            # Generation counts
            gen_stats = {}
            for gen in [1, 2, 3]:
                gen_results = self.solr.search(f'generation:{gen}', rows=0)
                gen_stats[f'generation_{gen}'] = gen_results.hits
            
            # Type distribution
            type_results = self.solr.search(
                '*:*', 
                rows=0, 
                facet='true', 
                facet_field='primary_type',
                facet_mincount=1
            )
            
            type_stats = {}
            if hasattr(type_results, 'facets') and 'primary_type' in type_results.facets:
                types = type_results.facets['primary_type']
                for i in range(0, len(types), 2):
                    if i + 1 < len(types):
                        type_stats[types[i]] = types[i + 1]
            
            return jsonify({
                'success': True,
                'total_pokemon': total_count,
                'generation_stats': gen_stats,
                'type_distribution': type_stats
            })
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def get_autocomplete_suggestions(self) -> Dict[str, Any]:
        """
        Get autocomplete suggestions based on partial query
        
        Returns:
            JSON response with suggestions
        """
        try:
            query = request.args.get('q', '').strip()
            if not query or len(query) < 2:
                return jsonify({
                    'success': True,
                    'suggestions': []
                })
            
            suggestions = []
            
            # Get term suggestions from Solr using terms component
            try:
                terms_params = {
                    'terms': 'true',
                    'terms.fl': 'name,name_spell,types,all_abilities',
                    'terms.prefix': query.lower(),
                    'terms.limit': 15,
                    'wt': 'json'
                }
                
                terms_response = requests.get(f"{self.solr.url.rstrip('/')}/terms", params=terms_params)
                terms_response.raise_for_status()
                terms_data = terms_response.json()
                
                logger.info(f"Terms component returned: {len(terms_data.get('terms', {}))} fields")
                
                if terms_data.get('terms'):
                    for field, terms_list in terms_data['terms'].items():
                        if isinstance(terms_list, list):
                            # Terms come as [term1, count1, term2, count2, ...]
                            field_suggestions = 0
                            for i in range(0, len(terms_list), 2):
                                if i < len(terms_list):
                                    term = terms_list[i]
                                    # Case-insensitive matching for terms
                                    if term.lower().startswith(query.lower()) and term not in suggestions:
                                        suggestions.append(term)
                                        field_suggestions += 1
                            logger.info(f"Field '{field}' contributed {field_suggestions} suggestions")
                                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"Terms request failed: {e}")
            
            # Get Pokemon name suggestions using simple wildcard matching
            try:
                # Use the same successful wildcard approach as main search
                wildcard_query = f'name:*{query}* OR name:*{query.capitalize()}*'
                
                name_params = {
                    'q': wildcard_query,
                    'rows': 15,  # Limit for autocomplete
                    'fl': 'name',
                    'wt': 'json'
                }
                
                name_response = requests.get(f"{self.solr.url.rstrip('/')}/select", params=name_params)
                name_response.raise_for_status()
                name_data = name_response.json()
                
                logger.info(f"Autocomplete wildcard search returned {name_data.get('response', {}).get('numFound', 0)} results")
                
                if name_data.get('response', {}).get('docs'):
                    # Separate prefix matches and substring matches for better ordering
                    prefix_matches = []
                    substring_matches = []
                    
                    for doc in name_data['response']['docs']:
                        name = doc.get('name', '')
                        if name and query.lower() in name.lower() and name not in suggestions:
                            if name.lower().startswith(query.lower()):
                                prefix_matches.append(name)
                            else:
                                substring_matches.append(name)
                    
                    # Add prefix matches first (higher priority), then substring matches
                    suggestions.extend(prefix_matches)
                    suggestions.extend(substring_matches)
                    
                    logger.info(f"Added {len(prefix_matches)} prefix matches and {len(substring_matches)} substring matches")
                            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Name search failed: {e}")
            
            # Remove duplicates and limit results
            unique_suggestions = list(dict.fromkeys(suggestions))[:8]
            
            return jsonify({
                'success': True,
                'suggestions': unique_suggestions
            })
            
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'suggestions': []
            }), 500

# Create Flask app instance
pokemon_app = PokemonSearchApp()
app = pokemon_app.app

if __name__ == '__main__':
    # Check Solr connection
    try:
        pokemon_app.solr.ping()
        logger.info("Connected to Solr successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Solr: {e}")
        logger.error("Make sure Solr is running and the pokemon core exists")
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)