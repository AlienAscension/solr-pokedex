"""
Debug and fix spellcheck component configuration issues
"""

import requests
import json

def debug_spellcheck_component():
    solr_url = "http://localhost:8983/solr/pokemon"
    
    print("🔧 Debugging Spellcheck Component Configuration\n")
    
    # Test 1: Check what spellcheck field is being used
    print("1. Testing different spellcheck field configurations...")
    
    test_params = [
        {
            'name': 'Default configuration',
            'params': {
                'q': 'bulbasr',
                'spellcheck': 'true',
                'spellcheck.build': 'true'
            }
        },
        {
            'name': 'Force specific field (name_spell)',
            'params': {
                'q': 'bulbasr',
                'spellcheck': 'true',
                'spellcheck.dictionary': 'default',
                'spellcheck.build': 'true'
            }
        },
        {
            'name': 'Use name field directly',
            'params': {
                'q': 'bulbasr',
                'spellcheck': 'true',
                'spellcheck.q': 'name:bulbasr',
                'spellcheck.build': 'true'
            }
        }
    ]
    
    for test in test_params:
        print(f"\n  Testing: {test['name']}")
        
        try:
            response = requests.get(f"{solr_url}/spell", params=test['params'])
            if response.status_code == 200:
                data = response.json()
                spellcheck = data.get('spellcheck', {})
                print(f"    Result: {spellcheck}")
                
                if spellcheck.get('suggestions') or spellcheck.get('collations'):
                    print("    ✅ SUCCESS! This configuration works!")
                    return test['params']
            else:
                print(f"    ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test 2: Check if the issue is with field analysis
    print("\n2. Testing field analysis...")
    
    analysis_tests = [
        {
            'field': 'name_spell',
            'text': 'Bulbasaur'
        },
        {
            'field': 'name',
            'text': 'Bulbasaur'
        }
    ]
    
    for test in analysis_tests:
        try:
            response = requests.get(f"{solr_url}/analysis/field", params={
                'analysis.fieldname': test['field'],
                'analysis.fieldvalue': test['text'],
                'wt': 'json'
            })
            
            if response.status_code == 200:
                print(f"  ✓ Field '{test['field']}' analysis successful")
                # Could parse and show tokens, but keeping it simple
            else:
                print(f"  ❌ Field '{test['field']}' analysis failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Analysis error for '{test['field']}': {e}")
    
    # Test 3: Check document frequency for terms
    print("\n3. Checking term frequencies...")
    
    try:
        # Check if 'bulbasaur' exists in name_spell field
        response = requests.get(f"{solr_url}/select", params={
            'q': 'name_spell:Bulbasaur',
            'rows': 0
        })
        
        if response.status_code == 200:
            count = response.json()['response']['numFound']
            print(f"  ✓ Documents with 'Bulbasaur' in name_spell: {count}")
            
            if count == 0:
                print("  ❌ No documents found! This is the problem.")
                print("     The spellcheck field doesn't contain the expected terms.")
            else:
                print("  ✓ Terms exist in spellcheck field")
        
        # Also check case-insensitive
        response2 = requests.get(f"{solr_url}/select", params={
            'q': 'name_spell:bulbasaur',  # lowercase
            'rows': 0
        })
        
        if response2.status_code == 200:
            count2 = response2.json()['response']['numFound']
            print(f"  ✓ Documents with 'bulbasaur' (lowercase) in name_spell: {count2}")
            
    except Exception as e:
        print(f"  ❌ Error checking term frequencies: {e}")
    
    return None

def fix_spellcheck_configuration():
    """Apply fixes to make spellcheck work"""
    solr_url = "http://solr:8983/solr/pokemon"
    
    print("\n🛠️ Applying Spellcheck Fixes\n")
    
    # Fix 1: Clean up duplicate name_spell values
    print("1. Cleaning up duplicate name_spell values...")
    
    try:
        # Get all documents
        response = requests.get(f"{solr_url}/select", params={
            'q': '*:*',
            'fl': 'id,name,name_spell',
            'rows': 1000
        })
        
        if response.status_code == 200:
            docs = response.json()['response']['docs']
            updates = []
            
            for doc in docs:
                name_spell = doc.get('name_spell', [])
                name = doc.get('name')
                
                if isinstance(name_spell, list) and len(name_spell) > 1:
                    # Remove duplicates but keep original case
                    unique_values = list(dict.fromkeys(name_spell))  # Preserves order
                    if len(unique_values) != len(name_spell):
                        updates.append({
                            'id': doc['id'],
                            'name_spell': {'set': unique_values}
                        })
                elif name and not name_spell:
                    updates.append({
                        'id': doc['id'],
                        'name_spell': {'set': [name]}
                    })
            
            if updates:
                print(f"   Updating {len(updates)} documents...")
                headers = {'Content-type': 'application/json'}
                
                # Apply updates
                response = requests.post(f"{solr_url}/update", 
                                       headers=headers, 
                                       data=json.dumps(updates))
                
                if response.status_code == 200:
                    # Commit
                    requests.post(f"{solr_url}/update", 
                                headers=headers,
                                data=json.dumps({"commit": {}}))
                    print("   ✅ Duplicates cleaned up")
                else:
                    print(f"   ❌ Update failed: {response.status_code}")
            else:
                print("   ✓ No duplicates to fix")
    except Exception as e:
        print(f"   ❌ Error cleaning duplicates: {e}")
    
    # Fix 2: Force spellcheck dictionary rebuild with specific parameters
    print("\n2. Rebuilding spellcheck dictionary with different methods...")
    
    rebuild_methods = [
        {
            'name': 'Standard rebuild',
            'url': f"{solr_url}/spell",
            'params': {
                'spellcheck.build': 'true',
                'spellcheck.reload': 'true'
            }
        },
        {
            'name': 'Rebuild with query',
            'url': f"{solr_url}/spell", 
            'params': {
                'q': '*:*',
                'spellcheck.build': 'true',
                'spellcheck.reload': 'true'
            }
        },
        {
            'name': 'Select handler rebuild',
            'url': f"{solr_url}/select",
            'params': {
                'q': 'name_spell:*',
                'rows': 0,
                'spellcheck.build': 'true',
                'spellcheck.reload': 'true'
            }
        }
    ]
    
    for method in rebuild_methods:
        try:
            print(f"   Trying: {method['name']}")
            response = requests.get(method['url'], params=method['params'])
            
            if response.status_code == 200:
                result = response.json()
                print(f"     ✓ Success: {result.get('responseHeader', {}).get('status', 'unknown')}")
                
                # Test immediately
                test_response = requests.get(f"{solr_url}/spell", params={
                    'q': 'bulbasr',
                    'spellcheck': 'true'
                })
                
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    spellcheck = test_data.get('spellcheck', {})
                    if spellcheck.get('suggestions') or spellcheck.get('collations'):
                        print(f"     🎉 SPELLCHECK NOW WORKING! Method: {method['name']}")
                        print(f"     Result: {spellcheck}")
                        return True
            else:
                print(f"     ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Fix 3: Try alternative spellcheck approach
    print("\n3. Testing alternative spellcheck configuration...")
    
    alternative_tests = [
        {
            'name': 'Lowercase query',
            'params': {
                'q': 'bulbasaur',  # exact lowercase
                'spellcheck': 'true',
                'spellcheck.q': 'bulbasr'  # misspelled version
            }
        },
        {
            'name': 'Direct field query',
            'params': {
                'q': 'bulbasr',
                'spellcheck': 'true',
                'spellcheck.dictionary': 'default'
            }
        },
        {
            'name': 'Extended results',
            'params': {
                'q': 'bulbasr',
                'spellcheck': 'true',
                'spellcheck.extendedResults': 'true',
                'spellcheck.collate': 'true',
                'spellcheck.maxCollations': 5
            }
        }
    ]
    
    for test in alternative_tests:
        try:
            print(f"   Testing: {test['name']}")
            response = requests.get(f"{solr_url}/spell", params=test['params'])
            
            if response.status_code == 200:
                data = response.json()
                spellcheck = data.get('spellcheck', {})
                
                if spellcheck.get('suggestions') or spellcheck.get('collations'):
                    print(f"     🎉 SUCCESS with {test['name']}!")
                    print(f"     Result: {spellcheck}")
                    return True
                else:
                    print(f"     Still empty: {spellcheck}")
            else:
                print(f"     HTTP error: {response.status_code}")
                
        except Exception as e:
            print(f"     Error: {e}")
    
    return False

def create_working_spellcheck_test():
    """Create a minimal test to verify spellcheck should work"""
    solr_url = "http://localhost:8983/solr/pokemon"
    
    print("\n🧪 Creating Working Spellcheck Test\n")
    
    # Add a simple test document with known spellcheck data
    test_doc = {
        'id': 'spellcheck_test',
        'name': 'TestPokemon',
        'name_spell': ['TestPokemon'],
        'pokemon_id': 999
    }
    
    headers = {'Content-type': 'application/json'}
    
    try:
        # Add test document
        print("1. Adding test document...")
        response = requests.post(f"{solr_url}/update", 
                               headers=headers,
                               data=json.dumps([test_doc]))
        
        if response.status_code == 200:
            # Commit
            requests.post(f"{solr_url}/update", 
                        headers=headers,
                        data=json.dumps({"commit": {}}))
            print("   ✓ Test document added")
            
            # Rebuild spellcheck
            print("2. Rebuilding spellcheck with test data...")
            requests.get(f"{solr_url}/spell", params={
                'spellcheck.build': 'true',
                'spellcheck.reload': 'true'
            })
            
            # Test spellcheck
            print("3. Testing spellcheck with known misspelling...")
            test_response = requests.get(f"{solr_url}/spell", params={
                'q': 'TestPokemn',  # intentional misspelling
                'spellcheck': 'true'
            })
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                spellcheck = test_data.get('spellcheck', {})
                print(f"   Test result: {spellcheck}")
                
                if spellcheck.get('suggestions') or spellcheck.get('collations'):
                    print("   🎉 SPELLCHECK IS WORKING!")
                    print("   The issue might be with your specific data or terms")
                else:
                    print("   ❌ Even test document doesn't work")
                    print("   This indicates a deeper configuration issue")
            
            # Clean up test document
            print("4. Cleaning up test document...")
            requests.post(f"{solr_url}/update", 
                        headers=headers,
                        data=json.dumps({"delete": {"id": "spellcheck_test"}}))
            requests.post(f"{solr_url}/update", 
                        headers=headers,
                        data=json.dumps({"commit": {}}))
            
        else:
            print("   ❌ Failed to add test document")
            
    except Exception as e:
        print(f"   ❌ Error in test: {e}")

def main():
    """Run complete spellcheck debugging and fixing"""
    
    print("🚀 Starting Complete Spellcheck Debug & Fix\n")
    
    # Step 1: Debug current configuration
    working_config = debug_spellcheck_component()
    
    if working_config:
        print(f"\n✅ Found working configuration: {working_config}")
        return
    
    # Step 2: Apply fixes
    if fix_spellcheck_configuration():
        print("\n✅ Spellcheck fixed!")
        return
    
    # Step 3: Test with controlled data
    create_working_spellcheck_test()
    
    print("\n" + "="*60)
    print("🎯 FINAL RECOMMENDATIONS:")
    print()
    print("If spellcheck still doesn't work, the issue is likely:")
    print("1. Case sensitivity - spellcheck might be case-sensitive")
    print("2. Field analyzer - name_spell field might not be analyzed properly")
    print("3. Minimum term frequency - spellcheck might ignore single-occurrence terms")
    print("4. Query analyzer mismatch - different analysis for indexing vs querying")
    print()
    print("Try these manual tests in Solr Admin:")
    print("1. Go to Analysis tab")
    print("2. Test field 'name_spell' with text 'Bulbasaur'")
    print("3. Check if tokens are generated correctly")
    print()
    print("Also try this URL directly:")
    print("http://localhost:8983/solr/pokemon/spell?q=bulbasr&spellcheck=true&spellcheck.build=true")

if __name__ == "__main__":
    main()