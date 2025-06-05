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
    
    def search_pokemon(self) -> Dict[str, Any]:
        """
        Search Pokemon based on query parameters
        
        Returns:
            JSON response with search results
        """
        try:
            # Get search parameters
            query = request.args.get('q', '*:*')
            start = int(request.args.get('start', 0))
            rows = min(int(request.args.get('rows', 20)), 100)  # Max 100 results
            sort_field = request.args.get('sort', 'pokemon_id')
            sort_order = request.args.get('order', 'asc')
            
            # Filters
            generation = request.args.get('generation')
            pokemon_type = request.args.get('type')
            ability = request.args.get('ability')
            is_legendary = request.args.get('legendary')
            
            # Build Solr query
            solr_query = self.build_solr_query(
                query, generation, pokemon_type, ability, is_legendary
            )
            
            # Build sort parameter
            sort_param = f"{sort_field} {sort_order}"
            
            # Execute search
            results = self.solr.search(
                solr_query,
                start=start,
                rows=rows,
                sort=sort_param,
                facet='true',
                facet_field=['generation', 'primary_type', 'color', 'habitat'],
                facet_mincount=1
            )
            
            # Format response
            response = {
                'success': True,
                'total': results.hits,
                'start': start,
                'rows': rows,
                'results': [dict(doc) for doc in results.docs],
                'facets': self.format_facets(results.facets) if hasattr(results, 'facets') else {},
                'query': query,
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
    
    def build_solr_query(self, query: str, generation: Optional[str], 
                        pokemon_type: Optional[str], ability: Optional[str],
                        is_legendary: Optional[str]) -> str:
        """
        Build Solr query string with filters
        
        Args:
            query: Main search query
            generation: Generation filter
            pokemon_type: Type filter
            ability: Ability filter
            is_legendary: Legendary filter
            
        Returns:
            Complete Solr query string
        """
        # Start with main query
        if not query or query.strip() == '':
            query = '*:*'
        
        # Handle full-text search
        if query != '*:*' and not ':' in query:
            # Search across name, types, abilities, and flavor text
            query = f'(name:*{query}* OR types:*{query}* OR all_abilities:*{query}* OR flavor_text:{query})'
        
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
        
        # Combine query and filters
        if filters:
            filter_string = ' AND '.join(filters)
            return f'({query}) AND ({filter_string})'
        
        return query
    
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