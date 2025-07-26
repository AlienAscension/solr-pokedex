#!/usr/bin/env python3
"""
Pokemon Search Engine Test Suite

Comprehensive testing script for evaluating the Pokemon search functionality.
Tests various search scenarios and measures performance metrics including
Information Retrieval metrics (Precision, Recall, F-Measure, Top-K ranking).

Usage:
    python test_pokemon_search.py
    python test_pokemon_search.py --url http://localhost:5000 --output results.json

Author: Pokemon Search Engine Project
"""

import requests
import time
import json
import argparse
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
import statistics
import math

@dataclass
class TestResult:
    """Container for individual test results"""
    test_name: str
    query: str
    success: bool
    response_time: float
    total_results: int
    first_result: str
    position_of_expected: int
    relevance_score: float
    error_message: str = ""
    # New IR metrics
    precision: float = 0.0
    recall: float = 0.0
    f_measure: float = 0.0
    precision_at_k: Dict[int, float] = None
    recall_at_k: Dict[int, float] = None
    f_measure_at_k: Dict[int, float] = None
    ndcg_at_k: Dict[int, float] = None
    mean_reciprocal_rank: float = 0.0
    average_precision: float = 0.0

    def __post_init__(self):
        if self.precision_at_k is None:
            self.precision_at_k = {}
        if self.recall_at_k is None:
            self.recall_at_k = {}
        if self.f_measure_at_k is None:
            self.f_measure_at_k = {}
        if self.ndcg_at_k is None:
            self.ndcg_at_k = {}

@dataclass
class GroundTruthSet:
    """Ground truth data for evaluation"""
    query: str
    relevant_pokemon: Set[str]  # Set of relevant Pokemon names
    highly_relevant: Set[str] = None  # Highly relevant (for NDCG)
    
    def __post_init__(self):
        if self.highly_relevant is None:
            self.highly_relevant = set()

class PokemonSearchTester:
    """Test suite for Pokemon search functionality with IR metrics"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
        self.k_values = [1, 3, 5, 10, 20]  # Top-K values to evaluate
        
        # Ground truth sets for different query types
        self.ground_truth_sets = self._initialize_ground_truth()
        
    def _initialize_ground_truth(self) -> Dict[str, GroundTruthSet]:
        """Initialize ground truth sets for evaluation"""
        return {
            # Exact name searches
            "pikachu": GroundTruthSet(
                query="pikachu",
                relevant_pokemon={"Pikachu"},
                highly_relevant={"Pikachu"}
            ),
            "charizard": GroundTruthSet(
                query="charizard", 
                relevant_pokemon={"Charizard"},
                highly_relevant={"Charizard"}
            ),
            
            # Partial name searches
            "char": GroundTruthSet(
                query="char",
                relevant_pokemon={"Charmander", "Charmeleon", "Charizard"},
                highly_relevant={"Charizard", "Charmander"}
            ),
            "saur": GroundTruthSet(
                query="saur",
                relevant_pokemon={"Bulbasaur", "Ivysaur", "Venusaur"},
                highly_relevant={"Bulbasaur", "Venusaur"}
            ),
            
            # Type searches
            "fire": GroundTruthSet(
                query="fire",
                relevant_pokemon={
                    "Charmander", "Charmeleon", "Charizard", "Vulpix", "Ninetales",
                    "Growlithe", "Arcanine", "Ponyta", "Rapidash", "Magmar",
                    "Flareon", "Moltres"
                },
                highly_relevant={"Charizard", "Arcanine", "Moltres"}
            ),
            "water": GroundTruthSet(
                query="water",
                relevant_pokemon={
                    "Squirtle", "Wartortle", "Blastoise", "Psyduck", "Golduck",
                    "Poliwag", "Poliwhirl", "Poliwrath", "Tentacool", "Tentacruel",
                    "Slowpoke", "Slowbro", "Seel", "Dewgong", "Shellder", "Cloyster",
                    "Krabby", "Kingler", "Horsea", "Seadra", "Goldeen", "Seaking",
                    "Staryu", "Starmie", "Magikarp", "Gyarados", "Lapras", "Vaporeon"
                },
                highly_relevant={"Blastoise", "Gyarados", "Lapras"}
            ),
            "electric": GroundTruthSet(
                query="electric",
                relevant_pokemon={
                    "Pikachu", "Raichu", "Magnemite", "Magneton", "Voltorb",
                    "Electrode", "Electabuzz", "Jolteon", "Zapdos"
                },
                highly_relevant={"Pikachu", "Zapdos"}
            ),
            
            # Ability searches
            "overgrow": GroundTruthSet(
                query="overgrow",
                relevant_pokemon={"Bulbasaur", "Ivysaur", "Venusaur"},
                highly_relevant={"Bulbasaur"}
            ),
            "blaze": GroundTruthSet(
                query="blaze",
                relevant_pokemon={"Charmander", "Charmeleon", "Charizard"},
                highly_relevant={"Charmander"}
            ),
            "torrent": GroundTruthSet(
                query="torrent",
                relevant_pokemon={"Squirtle", "Wartortle", "Blastoise"},
                highly_relevant={"Squirtle"}
            ),
            
            # Generation searches
            "generation 1": GroundTruthSet(
                query="generation 1",
                relevant_pokemon={f"Pokemon_{i}" for i in range(1, 152)},  # Gen 1: 1-151
                highly_relevant={"Pikachu", "Charizard", "Blastoise", "Venusaur", "Mewtwo", "Mew"}
            )
        }
    
    def calculate_ir_metrics(self, query: str, retrieved_results: List[Dict], 
                            ground_truth: GroundTruthSet) -> Dict[str, Any]:
        """Calculate Information Retrieval metrics"""
        if not retrieved_results:
            return {
                'precision': 0.0, 'recall': 0.0, 'f_measure': 0.0,
                'precision_at_k': {k: 0.0 for k in self.k_values},
                'recall_at_k': {k: 0.0 for k in self.k_values},
                'f_measure_at_k': {k: 0.0 for k in self.k_values},
                'ndcg_at_k': {k: 0.0 for k in self.k_values},
                'mean_reciprocal_rank': 0.0,
                'average_precision': 0.0
            }
        
        # Extract retrieved Pokemon names
        retrieved_names = {result.get('name', '').lower() for result in retrieved_results}
        relevant_names = {name.lower() for name in ground_truth.relevant_pokemon}
        highly_relevant_names = {name.lower() for name in ground_truth.highly_relevant}
        
        # Basic metrics
        true_positives = len(retrieved_names & relevant_names)
        false_positives = len(retrieved_names - relevant_names)
        false_negatives = len(relevant_names - retrieved_names)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f_measure = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Precision@K, Recall@K, F-Measure@K
        precision_at_k = {}
        recall_at_k = {}
        f_measure_at_k = {}
        
        for k in self.k_values:
            top_k_names = {retrieved_results[i].get('name', '').lower() 
                          for i in range(min(k, len(retrieved_results)))}
            
            tp_k = len(top_k_names & relevant_names)
            precision_k = tp_k / k if k > 0 else 0.0
            recall_k = tp_k / len(relevant_names) if len(relevant_names) > 0 else 0.0
            f_measure_k = 2 * (precision_k * recall_k) / (precision_k + recall_k) if (precision_k + recall_k) > 0 else 0.0
            
            precision_at_k[k] = precision_k
            recall_at_k[k] = recall_k
            f_measure_at_k[k] = f_measure_k
        
        # NDCG@K (Normalized Discounted Cumulative Gain)
        ndcg_at_k = {}
        for k in self.k_values:
            dcg = self._calculate_dcg(retrieved_results[:k], relevant_names, highly_relevant_names)
            idcg = self._calculate_ideal_dcg(k, relevant_names, highly_relevant_names)
            ndcg_at_k[k] = dcg / idcg if idcg > 0 else 0.0
        
        # Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for i, result in enumerate(retrieved_results):
            if result.get('name', '').lower() in relevant_names:
                mrr = 1.0 / (i + 1)
                break
        
        # Average Precision (AP)
        ap = self._calculate_average_precision(retrieved_results, relevant_names)
        
        return {
            'precision': precision,
            'recall': recall,
            'f_measure': f_measure,
            'precision_at_k': precision_at_k,
            'recall_at_k': recall_at_k,
            'f_measure_at_k': f_measure_at_k,
            'ndcg_at_k': ndcg_at_k,
            'mean_reciprocal_rank': mrr,
            'average_precision': ap
        }
    
    def _calculate_dcg(self, results: List[Dict], relevant: Set[str], highly_relevant: Set[str]) -> float:
        """Calculate Discounted Cumulative Gain"""
        dcg = 0.0
        for i, result in enumerate(results):
            name = result.get('name', '').lower()
            if name in highly_relevant:
                relevance = 3  # Highly relevant
            elif name in relevant:
                relevance = 1  # Relevant
            else:
                relevance = 0  # Not relevant
            
            if relevance > 0:
                dcg += (2**relevance - 1) / math.log2(i + 2)
        
        return dcg
    
    def _calculate_ideal_dcg(self, k: int, relevant: Set[str], highly_relevant: Set[str]) -> float:
        """Calculate Ideal Discounted Cumulative Gain"""
        # Create ideal ranking: highly relevant first, then relevant
        ideal_relevances = ([3] * len(highly_relevant) + [1] * (len(relevant) - len(highly_relevant)))[:k]
        
        idcg = 0.0
        for i, relevance in enumerate(ideal_relevances):
            idcg += (2**relevance - 1) / math.log2(i + 2)
        
        return idcg
    
    def _calculate_average_precision(self, results: List[Dict], relevant: Set[str]) -> float:
        """Calculate Average Precision"""
        if not relevant:
            return 0.0
        
        precisions = []
        relevant_found = 0
        
        for i, result in enumerate(results):
            if result.get('name', '').lower() in relevant:
                relevant_found += 1
                precision_at_i = relevant_found / (i + 1)
                precisions.append(precision_at_i)
        
        return sum(precisions) / len(relevant) if precisions else 0.0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and return comprehensive results"""
        print("🧪 Starting Pokemon Search Engine Test Suite with IR Metrics")
        print("=" * 60)
        
        # Test suites
        self.test_exact_name_search()
        self.test_partial_name_search()
        self.test_type_search()
        self.test_ability_search()
        self.test_dynamic_ability_type_detection()
        self.test_autocomplete_functionality()
        self.test_spellcheck_functionality()
        self.test_filter_combinations()
        self.test_performance_metrics()
        self.test_edge_cases()
        
        # New IR-focused tests
        self.test_ranking_quality()
        self.test_top_k_performance()
        
        return self.generate_summary_report()
    
    def test_exact_name_search(self):
        """Test exact Pokemon name searches with IR metrics"""
        print("\n📍 Testing Exact Name Search...")
        
        test_cases = [
            ("pikachu", "Pikachu"),
            ("charizard", "Charizard"), 
            ("bulbasaur", "Bulbasaur"),
            ("mewtwo", "Mewtwo"),
            ("mew", "Mew"),
            ("alakazam", "Alakazam")
        ]
        
        for query, expected in test_cases:
            result = self._perform_search_test_with_ir(
                f"Exact Name: {query}",
                {"q": query},
                expected_first=expected,
                ground_truth_key=query.lower()
            )
            print(f"  ✓ {query}: {result.response_time:.3f}s, P={result.precision:.2f}, "
                  f"R={result.recall:.2f}, F1={result.f_measure:.2f}, MRR={result.mean_reciprocal_rank:.2f}")
    
    def test_partial_name_search(self):
        """Test partial/substring name searches"""
        print("\n🔍 Testing Partial Name Search...")
        
        test_cases = [
            ("char", ["Charmander", "Charmeleon", "Charizard"]),
            ("saur", ["Bulbasaur", "Ivysaur", "Venusaur"]),
        ]
        
        for query, expected_names in test_cases:
            result = self._perform_search_test_with_ir(
                f"Partial Name: {query}",
                {"q": query},
                expected_contains=expected_names,
                ground_truth_key=query.lower()
            )
            print(f"  ✓ {query}: {result.response_time:.3f}s, P={result.precision:.2f}, "
                  f"R={result.recall:.2f}, F1={result.f_measure:.2f}, NDCG@5={result.ndcg_at_k.get(5, 0):.2f}")
    
    def test_type_search(self):
        """Test Pokemon type-based searches"""
        print("\n🔥 Testing Type Search...")
        
        test_cases = [
            ("fire", ["Charmander", "Charmeleon", "Charizard"]),
            ("water", ["Squirtle", "Wartortle", "Blastoise"]),
            ("electric", ["Pikachu", "Raichu"]),
        ]
        
        for type_name, expected_pokemon in test_cases:
            # Test as text search (our improved dynamic type detection)
            result_text = self._perform_search_test_with_ir(
                f"Type Text Search: {type_name}",
                {"q": type_name},
                expected_contains=expected_pokemon,
                ground_truth_key=type_name.lower()
            )
            
            print(f"  ✓ {type_name}: P@10={result_text.precision_at_k.get(10, 0):.2f}, "
                  f"R@10={result_text.recall_at_k.get(10, 0):.2f}, "
                  f"NDCG@10={result_text.ndcg_at_k.get(10, 0):.2f}")
    
    def test_ability_search(self):
        """Test ability-based searches with improved dynamic detection"""
        print("\n⚡ Testing Ability Search...")
        
        test_cases = [
            ("overgrow", ["Bulbasaur"]),
            ("blaze", ["Charmander"]),
            ("torrent", ["Squirtle"]),
        ]
        
        for ability, expected_pokemon in test_cases:
            result = self._perform_search_test_with_ir(
                f"Ability Search: {ability}",
                {"q": ability},
                expected_contains=expected_pokemon,
                ground_truth_key=ability.lower()
            )
            
            print(f"  ✓ {ability}: P={result.precision:.2f}, R={result.recall:.2f}, "
                  f"F1={result.f_measure:.2f}, AP={result.average_precision:.2f}")
    
    def test_ranking_quality(self):
        """Test ranking quality using IR metrics"""
        print("\n🏆 Testing Ranking Quality...")
        
        ranking_test_cases = [
            ("fire type pokemon", "fire"),
            ("water type pokemon", "water"), 
            ("electric pokemon", "electric"),
            ("starter pokemon char", "char"),
        ]
        
        for query, ground_truth_key in ranking_test_cases:
            if ground_truth_key in self.ground_truth_sets:
                result = self._perform_search_test_with_ir(
                    f"Ranking Quality: {query}",
                    {"q": query},
                    ground_truth_key=ground_truth_key
                )
                
                print(f"  ✓ '{query}':")
                print(f"    NDCG@5: {result.ndcg_at_k.get(5, 0):.3f}, NDCG@10: {result.ndcg_at_k.get(10, 0):.3f}")
                print(f"    P@5: {result.precision_at_k.get(5, 0):.3f}, R@5: {result.recall_at_k.get(5, 0):.3f}")
                print(f"    MRR: {result.mean_reciprocal_rank:.3f}, AP: {result.average_precision:.3f}")
    
    def test_top_k_performance(self):
        """Test Top-K performance across different K values"""
        print("\n📊 Testing Top-K Performance...")
        
        test_queries = ["fire", "water", "char", "overgrow"]
        
        # Aggregate metrics across all queries
        k_metrics = {k: {'precision': [], 'recall': [], 'f_measure': [], 'ndcg': []} 
                    for k in self.k_values}
        
        for query in test_queries:
            if query in self.ground_truth_sets:
                result = self._perform_search_test_with_ir(
                    f"Top-K: {query}",
                    {"q": query},
                    ground_truth_key=query
                )
                
                for k in self.k_values:
                    k_metrics[k]['precision'].append(result.precision_at_k.get(k, 0))
                    k_metrics[k]['recall'].append(result.recall_at_k.get(k, 0))
                    k_metrics[k]['f_measure'].append(result.f_measure_at_k.get(k, 0))
                    k_metrics[k]['ndcg'].append(result.ndcg_at_k.get(k, 0))
        
        print("  📈 Average metrics by K:")
        print("  K    |  P@K   |  R@K   |  F1@K  | NDCG@K")
        print("  -----|--------|--------|--------|--------")
        for k in self.k_values:
            metrics = k_metrics[k]
            avg_p = statistics.mean(metrics['precision']) if metrics['precision'] else 0
            avg_r = statistics.mean(metrics['recall']) if metrics['recall'] else 0
            avg_f = statistics.mean(metrics['f_measure']) if metrics['f_measure'] else 0
            avg_n = statistics.mean(metrics['ndcg']) if metrics['ndcg'] else 0
            print(f"  {k:2d}   | {avg_p:6.3f} | {avg_r:6.3f} | {avg_f:6.3f} | {avg_n:6.3f}")
    
    def test_dynamic_ability_type_detection(self):
        """Test the new dynamic ability and type detection system"""
        print("\n🎯 Testing Dynamic Detection System...")
        
        # Test cases that should trigger dynamic ability detection
        ability_test_cases = [
            ("overgrow", "Should detect as ability (lowercase)"),
            ("BLAZE", "Should detect as ability (uppercase)"),
        ]
        
        # Test cases that should trigger dynamic type detection  
        type_test_cases = [
            ("fire", "Should detect as type (lowercase)"),
            ("WATER", "Should detect as type (uppercase)"),
        ]
        
        for query, description in ability_test_cases + type_test_cases:
            ground_truth_key = query.lower()
            if ground_truth_key in self.ground_truth_sets:
                result = self._perform_search_test_with_ir(
                    f"Dynamic Detection: {query}",
                    {"q": query},
                    ground_truth_key=ground_truth_key
                )
                print(f"  ✓ {query}: P={result.precision:.2f}, R={result.recall:.2f}, "
                      f"Found: {result.total_results}")
            else:
                result = self._perform_search_test(
                    f"Dynamic Detection: {query}",
                    {"q": query}
                )
                print(f"  ✓ {query}: {result.response_time:.3f}s, Found: {result.total_results}")
    
    def test_autocomplete_functionality(self):
        """Test autocomplete suggestions"""
        print("\n💡 Testing Autocomplete...")
        
        test_cases = [
            ("pika", ["Pikachu"]),
            ("char", ["Charmander", "Charmeleon", "Charizard"]),
            ("bulb", ["Bulbasaur"]),
            ("over", ["Overgrow"]),  # Should suggest abilities too
            ("fi", ["fire"])         # Should suggest types
        ]
        
        for query, expected_suggestions in test_cases:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/autocomplete", 
                                      params={"q": query}, timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    suggestions = data.get('suggestions', [])
                    
                    found_expected = sum(1 for exp in expected_suggestions 
                                       if any(exp.lower() in sug.lower() for sug in suggestions))
                    relevance = found_expected / len(expected_suggestions) if expected_suggestions else 0
                    
                    result = TestResult(
                        test_name=f"Autocomplete: {query}",
                        query=query,
                        success=True,
                        response_time=response_time,
                        total_results=len(suggestions),
                        first_result=suggestions[0] if suggestions else "",
                        position_of_expected=1 if suggestions and any(exp.lower() in suggestions[0].lower() 
                                                                   for exp in expected_suggestions) else -1,
                        relevance_score=relevance
                    )
                    print(f"  ✓ {query}: {response_time:.3f}s, Suggestions: {len(suggestions)}, "
                          f"Relevance: {relevance:.2f}")
                else:
                    result = TestResult(
                        test_name=f"Autocomplete: {query}",
                        query=query,
                        success=False,
                        response_time=response_time,
                        total_results=0,
                        first_result="",
                        position_of_expected=-1,
                        relevance_score=0,
                        error_message=f"HTTP {response.status_code}"
                    )
                    print(f"  ❌ {query}: Failed - HTTP {response.status_code}")
                
                self.results.append(result)
                
            except Exception as e:
                response_time = time.time() - start_time
                result = TestResult(
                    test_name=f"Autocomplete: {query}",
                    query=query,
                    success=False,
                    response_time=response_time,
                    total_results=0,
                    first_result="",
                    position_of_expected=-1,
                    relevance_score=0,
                    error_message=str(e)
                )
                self.results.append(result)
                print(f"  ❌ {query}: Error - {e}")
    
    def test_spellcheck_functionality(self):
        """Test spell check suggestions"""
        print("\n🔤 Testing Spell Check...")
        
        test_cases = [
            ("piakchu", "pikachu"),
            ("charizrd", "charizard"),
            ("bulbasr", "bulbasaur"),
            ("squirtl", "squirtle"),
        ]
        
        for wrong_query, expected_correction in test_cases:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/search", 
                                      params={"q": wrong_query}, timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    spellcheck = data.get('spellcheck', {})
                    suggestions = spellcheck.get('suggestions', [])
                    collated = spellcheck.get('collated', '')
                    
                    has_correction = (expected_correction.lower() in [s.lower() for s in suggestions] or
                                    expected_correction.lower() in collated.lower())
                    
                    result = TestResult(
                        test_name=f"Spellcheck: {wrong_query}",
                        query=wrong_query,
                        success=has_correction,
                        response_time=response_time,
                        total_results=len(suggestions),
                        first_result=collated or (suggestions[0] if suggestions else ""),
                        position_of_expected=1 if has_correction else -1,
                        relevance_score=1.0 if has_correction else 0.0
                    )
                    print(f"  {'✓' if has_correction else '❌'} {wrong_query} → {expected_correction}: "
                          f"{response_time:.3f}s")
                else:
                    result = TestResult(
                        test_name=f"Spellcheck: {wrong_query}",
                        query=wrong_query,
                        success=False,
                        response_time=response_time,
                        total_results=0,
                        first_result="",
                        position_of_expected=-1,
                        relevance_score=0,
                        error_message=f"HTTP {response.status_code}"
                    )
                    print(f"  ❌ {wrong_query}: Failed - HTTP {response.status_code}")
                
                self.results.append(result)
                
            except Exception as e:
                response_time = time.time() - start_time
                result = TestResult(
                    test_name=f"Spellcheck: {wrong_query}",
                    query=wrong_query,
                    success=False,
                    response_time=response_time,
                    total_results=0,
                    first_result="",
                    position_of_expected=-1,
                    relevance_score=0,
                    error_message=str(e)
                )
                self.results.append(result)
                print(f"  ❌ {wrong_query}: Error - {e}")
    
    def test_filter_combinations(self):
        """Test filter combinations"""
        print("\n🎛️ Testing Filter Combinations...")
        
        test_cases = [
            ({"generation": "1"}, "Generation 1 filter"),
            ({"type": "fire"}, "Fire type filter"),
            ({"legendary": "true"}, "Legendary filter"),
            ({"generation": "1", "type": "fire"}, "Gen 1 + Fire type"),
            ({"q": "char", "type": "fire"}, "Text search + Type filter"),
        ]
        
        for filters, description in test_cases:
            params = {"q": "*:*"}
            params.update(filters)
            
            result = self._perform_search_test(
                f"Filter: {description}",
                params
            )
            print(f"  ✓ {description}: {result.response_time:.3f}s, Found: {result.total_results}")
    
    def test_performance_metrics(self):
        """Test performance under various conditions"""
        print("\n⚡ Testing Performance...")
        
        # Response time tests with different query types
        quick_queries = [
            ("Pikachu", "Exact name"),
            ("fire", "Type search"),
            ("Overgrow", "Ability search"),
            ("char", "Partial name"),
            ("*:*", "All results")
        ]
        response_times = []
        
        for query, query_type in quick_queries:
            times = []
            for _ in range(5):  # 5 runs each
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}/api/search", 
                                          params={"q": query}, timeout=5)
                    if response.status_code == 200:
                        times.append(time.time() - start_time)
                except:
                    pass
            
            if times:
                avg_time = statistics.mean(times)
                response_times.extend(times)
                print(f"  ✓ '{query}' ({query_type}): {avg_time:.3f}s avg ({min(times):.3f}-{max(times):.3f}s)")
        
        if response_times:
            overall_avg = statistics.mean(response_times)
            print(f"  📊 Overall average: {overall_avg:.3f}s")
            
            # Performance thresholds
            fast_responses = sum(1 for t in response_times if t < 0.1)
            acceptable_responses = sum(1 for t in response_times if t < 0.5)
            print(f"  🚀 Fast responses (<100ms): {fast_responses}/{len(response_times)} ({fast_responses/len(response_times)*100:.1f}%)")
            print(f"  ✅ Acceptable responses (<500ms): {acceptable_responses}/{len(response_times)} ({acceptable_responses/len(response_times)*100:.1f}%)")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔧 Testing Edge Cases...")
        
        edge_cases = [
            ("", "Empty query"),
            ("   ", "Whitespace only"),
            ("xyz123nonexistent", "Non-existent Pokemon"),
            ("a", "Single character"),
            ("pokemonwithverylongnamethatshouldnotexist", "Very long query"),
            ("!@#$%", "Special characters only"),
            ("pikachu AND charizard", "Boolean query"),
            ("name:Pikachu", "Field-specific query"),
        ]
        
        for query, description in edge_cases:
            result = self._perform_search_test(
                f"Edge Case: {description}",
                {"q": query}
            )
            status = "✓" if result.success else "❌"
            print(f"  {status} {description}: {result.response_time:.3f}s, Results: {result.total_results}")
            if not result.success and result.error_message:
                print(f"    Error: {result.error_message}")
    
    def _perform_search_test(self, test_name: str, params: Dict[str, str], 
                           expected_first: str = None, expected_contains: List[str] = None) -> TestResult:
        """Perform a single search test without IR metrics"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/search", params=params, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total = data.get('total', 0)
                
                first_result = results[0].get('name', '') if results else ''
                
                # Calculate position of expected result
                position = -1
                relevance_score = 0.0
                
                if expected_first:
                    for i, result in enumerate(results):
                        if result.get('name', '').lower() == expected_first.lower():
                            position = i + 1
                            relevance_score = 1.0 if i == 0 else max(0.1, 1.0 - (i * 0.1))
                            break
                
                elif expected_contains:
                    found_count = 0
                    positions = []
                    for expected in expected_contains:
                        for i, result in enumerate(results):
                            if expected.lower() in result.get('name', '').lower():
                                found_count += 1
                                positions.append(i + 1)
                                if position == -1:
                                    position = i + 1
                                break
                    relevance_score = found_count / len(expected_contains) if expected_contains else 0
                    # Bonus for finding expected results early
                    if positions:
                        avg_position = sum(positions) / len(positions)
                        position_bonus = max(0, 1.0 - (avg_position - 1) * 0.1)
                        relevance_score = min(1.0, relevance_score * position_bonus)
                
                result = TestResult(
                    test_name=test_name,
                    query=params.get('q', ''),
                    success=True,
                    response_time=response_time,
                    total_results=total,
                    first_result=first_result,
                    position_of_expected=position,
                    relevance_score=relevance_score
                )
            else:
                result = TestResult(
                    test_name=test_name,
                    query=params.get('q', ''),
                    success=False,
                    response_time=response_time,
                    total_results=0,
                    first_result="",
                    position_of_expected=-1,
                    relevance_score=0,
                    error_message=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                test_name=test_name,
                query=params.get('q', ''),
                success=False,
                response_time=response_time,
                total_results=0,
                first_result="",
                position_of_expected=-1,
                relevance_score=0,
                error_message=str(e)
            )
        
        self.results.append(result)
        return result
    
    def _perform_search_test_with_ir(self, test_name: str, params: Dict[str, str], 
                                   expected_first: str = None, expected_contains: List[str] = None,
                                   ground_truth_key: str = None) -> TestResult:
        """Perform a search test with IR metrics calculation"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/api/search", params=params, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total = data.get('total', 0)
                
                first_result = results[0].get('name', '') if results else ''
                
                # Calculate position of expected result
                position = -1
                relevance_score = 0.0
                
                if expected_first:
                    for i, result in enumerate(results):
                        if result.get('name', '').lower() == expected_first.lower():
                            position = i + 1
                            relevance_score = 1.0 if i == 0 else max(0.1, 1.0 - (i * 0.1))
                            break
                
                elif expected_contains:
                    found_count = 0
                    positions = []
                    for expected in expected_contains:
                        for i, result in enumerate(results):
                            if expected.lower() in result.get('name', '').lower():
                                found_count += 1
                                positions.append(i + 1)
                                if position == -1:
                                    position = i + 1
                                break
                    relevance_score = found_count / len(expected_contains) if expected_contains else 0
                    # Bonus for finding expected results early
                    if positions:
                        avg_position = sum(positions) / len(positions)
                        position_bonus = max(0, 1.0 - (avg_position - 1) * 0.1)
                        relevance_score = min(1.0, relevance_score * position_bonus)
                
                # Calculate IR metrics if ground truth is available
                ir_metrics = {}
                if ground_truth_key and ground_truth_key in self.ground_truth_sets:
                    ground_truth = self.ground_truth_sets[ground_truth_key]
                    ir_metrics = self.calculate_ir_metrics(params.get('q', ''), results, ground_truth)
                
                result = TestResult(
                    test_name=test_name,
                    query=params.get('q', ''),
                    success=True,
                    response_time=response_time,
                    total_results=total,
                    first_result=first_result,
                    position_of_expected=position,
                    relevance_score=relevance_score,
                    precision=ir_metrics.get('precision', 0.0),
                    recall=ir_metrics.get('recall', 0.0),
                    f_measure=ir_metrics.get('f_measure', 0.0),
                    precision_at_k=ir_metrics.get('precision_at_k', {}),
                    recall_at_k=ir_metrics.get('recall_at_k', {}),
                    f_measure_at_k=ir_metrics.get('f_measure_at_k', {}),
                    ndcg_at_k=ir_metrics.get('ndcg_at_k', {}),
                    mean_reciprocal_rank=ir_metrics.get('mean_reciprocal_rank', 0.0),
                    average_precision=ir_metrics.get('average_precision', 0.0)
                )
            else:
                result = TestResult(
                    test_name=test_name,
                    query=params.get('q', ''),
                    success=False,
                    response_time=response_time,
                    total_results=0,
                    first_result="",
                    position_of_expected=-1,
                    relevance_score=0,
                    error_message=f"HTTP {response.status_code}"
                )
        
        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                test_name=test_name,
                query=params.get('q', ''),
                success=False,
                response_time=response_time,
                total_results=0,
                first_result="",
                position_of_expected=-1,
                relevance_score=0,
                error_message=str(e)
            )
        
        self.results.append(result)
        return result
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive test summary with IR metrics"""
        if not self.results:
            return {"error": "No test results available"}
        
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        response_times = [r.response_time for r in successful_tests]
        relevance_scores = [r.relevance_score for r in successful_tests if r.relevance_score > 0]
        
        # IR metrics for tests that have them
        ir_tests = [r for r in successful_tests if r.precision > 0 or r.recall > 0 or r.f_measure > 0]
        
        # Categorize tests by type
        test_categories = {}
        for result in self.results:
            category = result.test_name.split(':')[0]
            if category not in test_categories:
                test_categories[category] = []
            test_categories[category].append(result)
        
        category_stats = {}
        for category, tests in test_categories.items():
            successful = [t for t in tests if t.success]
            ir_tests_cat = [t for t in successful if t.precision > 0 or t.recall > 0 or t.f_measure > 0]
            relevance_scores = [t.relevance_score for t in successful if t.relevance_score > 0]
            
            category_stats[category] = {
                "total": len(tests),
                "successful": len(successful),
                "success_rate": len(successful) / len(tests) * 100 if tests else 0,
                "avg_response_time": statistics.mean([t.response_time for t in successful]) if successful else 0,
                "avg_relevance": statistics.mean(relevance_scores) if relevance_scores else 0,
                "avg_precision": statistics.mean([t.precision for t in ir_tests_cat]) if ir_tests_cat else 0,
                "avg_recall": statistics.mean([t.recall for t in ir_tests_cat]) if ir_tests_cat else 0,
                "avg_f_measure": statistics.mean([t.f_measure for t in ir_tests_cat]) if ir_tests_cat else 0,
                "avg_mrr": statistics.mean([t.mean_reciprocal_rank for t in ir_tests_cat]) if ir_tests_cat else 0,
                "avg_ap": statistics.mean([t.average_precision for t in ir_tests_cat]) if ir_tests_cat else 0
            }
        
        # Calculate aggregate IR metrics
        ir_metrics_summary = {}
        if ir_tests:
            ir_metrics_summary = {
                "average_precision": statistics.mean([t.precision for t in ir_tests]),
                "average_recall": statistics.mean([t.recall for t in ir_tests]),
                "average_f_measure": statistics.mean([t.f_measure for t in ir_tests]),
                "average_mrr": statistics.mean([t.mean_reciprocal_rank for t in ir_tests]),
                "average_ap": statistics.mean([t.average_precision for t in ir_tests]),
            }
            
            # Aggregate Top-K metrics
            for k in self.k_values:
                precision_k = [t.precision_at_k.get(k, 0) for t in ir_tests if t.precision_at_k]
                recall_k = [t.recall_at_k.get(k, 0) for t in ir_tests if t.recall_at_k]
                f_measure_k = [t.f_measure_at_k.get(k, 0) for t in ir_tests if t.f_measure_at_k]
                ndcg_k = [t.ndcg_at_k.get(k, 0) for t in ir_tests if t.ndcg_at_k]
                
                ir_metrics_summary[f"average_precision_at_{k}"] = statistics.mean(precision_k) if precision_k else 0
                ir_metrics_summary[f"average_recall_at_{k}"] = statistics.mean(recall_k) if recall_k else 0
                ir_metrics_summary[f"average_f_measure_at_{k}"] = statistics.mean(f_measure_k) if f_measure_k else 0
                ir_metrics_summary[f"average_ndcg_at_{k}"] = statistics.mean(ndcg_k) if ndcg_k else 0
        
        summary = {
            "test_summary": {
                "total_tests": len(self.results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.results) * 100,
                "tests_with_ir_metrics": len(ir_tests)
            },
            "performance_metrics": {
                "average_response_time": statistics.mean(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "fast_responses_pct": sum(1 for t in response_times if t < 0.1) / len(response_times) * 100 if response_times else 0,
                "acceptable_responses_pct": sum(1 for t in response_times if t < 0.5) / len(response_times) * 100 if response_times else 0,
            },
            "relevance_metrics": {
                "average_relevance_score": statistics.mean(relevance_scores) if relevance_scores else 0,
                "perfect_relevance_rate": sum(1 for r in relevance_scores if r >= 1.0) / len(relevance_scores) * 100 if relevance_scores else 0,
                "good_relevance_rate": sum(1 for r in relevance_scores if r >= 0.7) / len(relevance_scores) * 100 if relevance_scores else 0,
            },
            "information_retrieval_metrics": ir_metrics_summary,
            "category_breakdown": category_stats,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "query": r.query,
                    "success": r.success,
                    "response_time": round(r.response_time, 3),
                    "total_results": r.total_results,
                    "first_result": r.first_result,
                    "position_of_expected": r.position_of_expected,
                    "relevance_score": round(r.relevance_score, 2),
                    "precision": round(r.precision, 3),
                    "recall": round(r.recall, 3),
                    "f_measure": round(r.f_measure, 3),
                    "mean_reciprocal_rank": round(r.mean_reciprocal_rank, 3),
                    "average_precision": round(r.average_precision, 3),
                    "precision_at_k": {k: round(v, 3) for k, v in r.precision_at_k.items()} if r.precision_at_k else {},
                    "recall_at_k": {k: round(v, 3) for k, v in r.recall_at_k.items()} if r.recall_at_k else {},
                    "f_measure_at_k": {k: round(v, 3) for k, v in r.f_measure_at_k.items()} if r.f_measure_at_k else {},
                    "ndcg_at_k": {k: round(v, 3) for k, v in r.ndcg_at_k.items()} if r.ndcg_at_k else {},
                    "error_message": r.error_message
                }
                for r in self.results
            ]
        }
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY REPORT")
        print("=" * 60)
        print(f"Total Tests: {summary['test_summary']['total_tests']}")
        print(f"Success Rate: {summary['test_summary']['success_rate']:.1f}%")
        print(f"Tests with IR Metrics: {summary['test_summary']['tests_with_ir_metrics']}")
        
        print(f"\n⚡ Performance Metrics:")
        print(f"Average Response Time: {summary['performance_metrics']['average_response_time']:.3f}s")
        print(f"Fast Responses (<100ms): {summary['performance_metrics']['fast_responses_pct']:.1f}%")
        print(f"Acceptable Responses (<500ms): {summary['performance_metrics']['acceptable_responses_pct']:.1f}%")
        
        if ir_metrics_summary:
            print(f"\n🎯 Information Retrieval Metrics:")
            print(f"Average Precision: {ir_metrics_summary['average_precision']:.3f}")
            print(f"Average Recall: {ir_metrics_summary['average_recall']:.3f}")
            print(f"Average F-Measure: {ir_metrics_summary['average_f_measure']:.3f}")
            print(f"Average MRR: {ir_metrics_summary['average_mrr']:.3f}")
            print(f"Average AP: {ir_metrics_summary['average_ap']:.3f}")
            
            print(f"\n📈 Top-K Performance:")
            print("K    | P@K   | R@K   | F1@K  | NDCG@K")
            print("-----|-------|-------|-------|-------")
            for k in self.k_values:
                p_k = ir_metrics_summary.get(f'average_precision_at_{k}', 0)
                r_k = ir_metrics_summary.get(f'average_recall_at_{k}', 0)
                f_k = ir_metrics_summary.get(f'average_f_measure_at_{k}', 0)
                n_k = ir_metrics_summary.get(f'average_ndcg_at_{k}', 0)
                print(f"{k:2d}   | {p_k:.3f} | {r_k:.3f} | {f_k:.3f} | {n_k:.3f}")
        
        print(f"\n📈 Test Category Breakdown:")
        for category, stats in category_stats.items():
            print(f"  {category}:")
            print(f"    Success Rate: {stats['success_rate']:.1f}%")
            print(f"    Avg Response Time: {stats['avg_response_time']:.3f}s")
            if stats['avg_precision'] > 0:
                print(f"    Avg Precision: {stats['avg_precision']:.3f}")
                print(f"    Avg Recall: {stats['avg_recall']:.3f}")
                print(f"    Avg F-Measure: {stats['avg_f_measure']:.3f}")
        
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test.test_name}: {test.error_message}")
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='Pokemon Search Engine Test Suite with IR Metrics')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the Pokemon search application')
    parser.add_argument('--output', help='Output file for test results (JSON)')
    
    args = parser.parse_args()
    
    print("🧪 Enhanced Pokemon Search Engine Test Suite")
    print("Features: Precision, Recall, F-Measure, Top-K ranking, NDCG, MRR, Average Precision")
    print("-" * 60)
    
    tester = PokemonSearchTester(args.url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {args.output}")
    
    print(f"\n🎯 Key IR Metrics Summary:")
    ir_metrics = results.get('information_retrieval_metrics', {})
    if ir_metrics:
        print(f"Overall Precision: {ir_metrics.get('average_precision', 0):.3f}")
        print(f"Overall Recall: {ir_metrics.get('average_recall', 0):.3f}")
        print(f"Overall F-Measure: {ir_metrics.get('average_f_measure', 0):.3f}")
        print(f"Mean Reciprocal Rank: {ir_metrics.get('average_mrr', 0):.3f}")
        print(f"Mean Average Precision: {ir_metrics.get('average_ap', 0):.3f}")
        print(f"NDCG@5: {ir_metrics.get('average_ndcg_at_5', 0):.3f}")
        print(f"NDCG@10: {ir_metrics.get('average_ndcg_at_10', 0):.3f}")

if __name__ == "__main__":
    main()