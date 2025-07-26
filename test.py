#!/usr/bin/env python3
"""
Pokemon Search Engine Test Suite

Comprehensive testing script for evaluating the Pokemon search functionality.
Tests various search scenarios and measures performance metrics.

Usage:
    python test_pokemon_search.py
    python test_pokemon_search.py --url http://localhost:5000 --output results.json

Author: Pokemon Search Engine Project
"""

import requests
import time
import json
import argparse
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import statistics

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

class PokemonSearchTester:
    """Test suite for Pokemon search functionality"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[TestResult] = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and return comprehensive results"""
        print("🧪 Starting Pokemon Search Engine Test Suite")
        print("=" * 50)
        
        # Test suites
        self.test_exact_name_search()
        self.test_partial_name_search()
        self.test_type_search()
        self.test_ability_search()
        self.test_autocomplete_functionality()
        self.test_spellcheck_functionality()
        self.test_filter_combinations()
        self.test_performance_metrics()
        self.test_edge_cases()
        
        return self.generate_summary_report()
    
    def test_exact_name_search(self):
        """Test exact Pokemon name searches"""
        print("\n📍 Testing Exact Name Search...")
        
        test_cases = [
            ("Pikachu", "Pikachu"),
            ("Charizard", "Charizard"), 
            ("Bulbasaur", "Bulbasaur"),
            ("Mewtwo", "Mewtwo"),
            ("Mew", "Mew"),
            ("Alakazam", "Alakazam")
        ]
        
        for query, expected in test_cases:
            result = self._perform_search_test(
                f"Exact Name: {query}",
                {"q": query},
                expected_first=expected
            )
            print(f"  ✓ {query}: {result.response_time:.3f}s, Position: {result.position_of_expected}")
    
    def test_partial_name_search(self):
        """Test partial/substring name searches"""
        print("\n🔍 Testing Partial Name Search...")
        
        test_cases = [
            ("pika", ["Pikachu"]),
            ("char", ["Charmander", "Charmeleon", "Charizard"]),
            ("saur", ["Bulbasaur", "Ivysaur", "Venusaur"]),
            ("squirt", ["Squirtle"]),
            ("bell", ["Bellsprout"])
        ]
        
        for query, expected_names in test_cases:
            result = self._perform_search_test(
                f"Partial Name: {query}",
                {"q": query},
                expected_contains=expected_names
            )
            print(f"  ✓ {query}: {result.response_time:.3f}s, Found: {result.total_results}")
    
    def test_type_search(self):
        """Test Pokemon type-based searches"""
        print("\n🔥 Testing Type Search...")
        
        # Test both text search and filter approach
        test_cases = [
            ("fire", ["Charmander", "Charmeleon", "Charizard"]),
            ("water", ["Squirtle", "Wartortle", "Blastoise"]),
            ("grass", ["Bulbasaur", "Ivysaur", "Venusaur"]),
            ("electric", ["Pikachu", "Raichu"]),
            ("psychic", ["Abra", "Kadabra", "Alakazam"])
        ]
        
        for type_name, expected_pokemon in test_cases:
            # Test as text search (what we were doing before)
            result_text = self._perform_search_test(
                f"Type Text Search: {type_name}",
                {"q": type_name},
                expected_contains=expected_pokemon
            )
            
            # Test as type filter (how web app actually works)
            result_filter = self._perform_search_test(
                f"Type Filter: {type_name}",
                {"q": "", "type": type_name},
                expected_contains=expected_pokemon
            )
            
            print(f"  ✓ {type_name} (text): {result_text.response_time:.3f}s, Found: {result_text.total_results}")
            print(f"  ✓ {type_name} (filter): {result_filter.response_time:.3f}s, Found: {result_filter.total_results}")
    
    def test_ability_search(self):
        """Test ability-based searches"""
        print("\n⚡ Testing Ability Search...")
        
        test_cases = [
            ("overgrow", ["Bulbasaur"]),
            ("blaze", ["Charmander"]),
            ("torrent", ["Squirtle"]),
            ("static", ["Pikachu"])
        ]
        
        for query, expected_pokemon in test_cases:
            result = self._perform_search_test(
                f"Ability Search: {query}",
                {"q": query},
                expected_contains=expected_pokemon
            )
            print(f"  ✓ {query}: {result.response_time:.3f}s, Found: {result.total_results}")
    
    def test_autocomplete_functionality(self):
        """Test autocomplete suggestions"""
        print("\n💡 Testing Autocomplete...")
        
        test_cases = [
            ("pika", ["Pikachu"]),
            ("char", ["Charmander", "Charmeleon", "Charizard"]),
            ("bulb", ["Bulbasaur"]),
            ("saur", ["Bulbasaur", "Ivysaur", "Venusaur"])
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
                    print(f"  ✓ {query}: {response_time:.3f}s, Suggestions: {len(suggestions)}, Relevance: {relevance:.2f}")
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
            ("squirtl", "squirtle")
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
                          f"{response_time:.3f}s, Suggested: {collated or 'None'}")
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
            ({"generation": "1", "legendary": "true"}, "Gen 1 + Legendary"),
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
        
        # Response time tests
        quick_queries = ["Pikachu", "fire", "generation:1", "*:*"]
        response_times = []
        
        for query in quick_queries:
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
                print(f"  ✓ '{query}': {avg_time:.3f}s avg ({min(times):.3f}-{max(times):.3f}s)")
        
        if response_times:
            overall_avg = statistics.mean(response_times)
            print(f"  📊 Overall average: {overall_avg:.3f}s")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔧 Testing Edge Cases...")
        
        edge_cases = [
            ("", "Empty query"),
            ("   ", "Whitespace only"),
            ("xyz123nonexistent", "Non-existent Pokemon"),
            ("a", "Single character"),
            ("pokemonwithverylongnamethatshouldnotexist", "Very long query"),
            ("!@#$%", "Special characters only")
        ]
        
        for query, description in edge_cases:
            result = self._perform_search_test(
                f"Edge Case: {description}",
                {"q": query}
            )
            print(f"  ✓ {description}: {result.response_time:.3f}s, Results: {result.total_results}")
    
    def _perform_search_test(self, test_name: str, params: Dict[str, str], 
                           expected_first: str = None, expected_contains: List[str] = None) -> TestResult:
        """Perform a single search test"""
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
                            relevance_score = 1.0 if i == 0 else 0.5
                            break
                
                elif expected_contains:
                    found_count = 0
                    for expected in expected_contains:
                        for i, result in enumerate(results):
                            if expected.lower() in result.get('name', '').lower():
                                found_count += 1
                                if position == -1:
                                    position = i + 1
                                break
                    relevance_score = found_count / len(expected_contains) if expected_contains else 0
                
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
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        if not self.results:
            return {"error": "No test results available"}
        
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        response_times = [r.response_time for r in successful_tests]
        relevance_scores = [r.relevance_score for r in successful_tests]
        
        summary = {
            "test_summary": {
                "total_tests": len(self.results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.results) * 100,
            },
            "performance_metrics": {
                "average_response_time": statistics.mean(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
            },
            "relevance_metrics": {
                "average_relevance_score": statistics.mean(relevance_scores) if relevance_scores else 0,
                "perfect_relevance_rate": sum(1 for r in relevance_scores if r >= 1.0) / len(relevance_scores) * 100 if relevance_scores else 0,
            },
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
                    "error_message": r.error_message
                }
                for r in self.results
            ]
        }
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 50)
        print(f"Total Tests: {summary['test_summary']['total_tests']}")
        print(f"Success Rate: {summary['test_summary']['success_rate']:.1f}%")
        print(f"Average Response Time: {summary['performance_metrics']['average_response_time']:.3f}s")
        print(f"Average Relevance Score: {summary['relevance_metrics']['average_relevance_score']:.2f}")
        print(f"Perfect Relevance Rate: {summary['relevance_metrics']['perfect_relevance_rate']:.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test.test_name}: {test.error_message}")
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='Pokemon Search Engine Test Suite')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the Pokemon search application')
    parser.add_argument('--output', help='Output file for test results (JSON)')
    
    args = parser.parse_args()
    
    tester = PokemonSearchTester(args.url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {args.output}")

if __name__ == "__main__":
    main()