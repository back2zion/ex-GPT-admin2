#!/usr/bin/env python3
"""
Fix column mapping for 302 government organization records
"""
import requests

API_BASE = "http://localhost:8010/api/v1/admin"

def fix_all_records():
    """Fix mapping for all records in dictionary 2"""

    # Get all terms
    response = requests.get(f"{API_BASE}/dictionaries/2")
    if response.status_code != 200:
        print(f"❌ Failed to fetch dictionary: {response.status_code}")
        return

    data = response.json()
    terms = data['terms']
    print(f"📄 Found {len(terms)} terms to fix\n")

    fixed_count = 0
    error_count = 0

    for idx, term in enumerate(terms, start=1):
        # Current wrong mapping:
        # alias_3 has english name (full)
        # english_name has english abbreviation
        # english_alias has category
        # category is None

        # Correct mapping:
        corrected_data = {
            "dict_id": term['dict_id'],
            "main_term": term['main_term'],
            "main_alias": term['main_alias'],
            "alias_1": term['alias_1'],
            "alias_2": term['alias_2'],
            "alias_3": None,  # Should be empty (currently has English name)
            "english_name": term['alias_3'],  # Move full English name here
            "english_alias": term['english_name'],  # Move English abbreviation here
            "category": term['english_alias'],  # Move category here
            "use_yn": term['use_yn']
        }

        # Debug first 5 records
        if idx <= 5:
            print(f"{idx}. {term['main_term']}")
            print(f"   영문명: {term['alias_3']} → {corrected_data['english_name']}")
            print(f"   영문약칭: {term['english_name']} → {corrected_data['english_alias']}")
            print(f"   분류: {term['english_alias']} → {corrected_data['category']}")
            print()

        # Update via API
        try:
            response = requests.put(
                f"{API_BASE}/dictionaries/terms/{term['term_id']}",
                json=corrected_data
            )

            if response.status_code == 200:
                fixed_count += 1
                if idx % 50 == 0:
                    print(f"✅ Progress: {fixed_count} records fixed")
            else:
                print(f"❌ Failed to update term_id {term['term_id']}: {response.status_code}")
                error_count += 1

        except Exception as e:
            print(f"❌ Exception updating term_id {term['term_id']}: {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Successfully fixed: {fixed_count} records")
    print(f"❌ Errors: {error_count} records")

if __name__ == "__main__":
    print("🚀 Starting column mapping fix for government organizations\n")
    fix_all_records()
