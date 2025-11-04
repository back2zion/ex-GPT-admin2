#!/usr/bin/env python3
"""
Re-upload 302 government organization records with correct column mapping
"""
import csv
import requests

API_BASE = "http://localhost:8010/api/v1/admin"

def reload_all_records():
    """Delete all existing records and re-upload with correct mapping"""

    # 1. Get all existing terms
    response = requests.get(f"{API_BASE}/dictionaries/2")
    if response.status_code != 200:
        print(f"❌ Failed to fetch dictionary: {response.status_code}")
        return

    data = response.json()
    existing_terms = data['terms']
    print(f"📄 Found {len(existing_terms)} existing terms")

    # 2. Delete all existing terms
    print("\n🗑️  Deleting existing terms...")
    deleted = 0
    for term in existing_terms:
        try:
            response = requests.delete(f"{API_BASE}/dictionaries/terms/{term['term_id']}")
            if response.status_code == 200:
                deleted += 1
                if deleted % 50 == 0:
                    print(f"   Deleted {deleted} terms...")
        except Exception as e:
            print(f"❌ Failed to delete term_id {term['term_id']}: {e}")

    print(f"✅ Deleted {deleted} terms\n")

    # 3. Read 302 CSV file
    print("📂 Reading 302 government organizations CSV...")
    with open('/home/aigen/정부기관_전체_302개.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    print(f"📄 Loaded {len(rows)-1} rows from CSV\n")

    # 4. Upload with correct column mapping
    print("📤 Uploading with correct mapping...\n")
    success_count = 0
    error_count = 0

    for idx, row in enumerate(rows[1:], start=2):  # Skip header
        if len(row) < 7 or not row[0].strip():
            continue

        # Correct mapping for 302 CSV (7 columns in data rows):
        # [0] = 정식명칭 → main_term
        # [1] = 주요약칭 → main_alias
        # [2] = 추가약칭1 → alias_1
        # [3] = 추가약칭2 → alias_2
        # [4] = 영문명 → english_name
        # [5] = 영문약칭 → english_alias
        # [6] = 분류 → category
        # alias_3 is always None (missing column in CSV)

        data = {
            "dict_id": 2,
            "main_term": row[0].strip(),
            "main_alias": row[1].strip() if row[1].strip() else None,
            "alias_1": row[2].strip() if row[2].strip() else None,
            "alias_2": row[3].strip() if row[3].strip() else None,
            "alias_3": None,  # Not in CSV
            "english_name": row[4].strip() if row[4].strip() else None,
            "english_alias": row[5].strip() if row[5].strip() else None,
            "category": row[6].strip() if len(row) > 6 and row[6].strip() else None,
            "use_yn": True
        }

        # Debug first 10 records
        if success_count < 10:
            print(f"{success_count+1}. {data['main_term']}")
            print(f"   주요약칭: {data['main_alias']}")
            if data['alias_1']:
                print(f"   추가약칭1: {data['alias_1']}")
            if data['alias_2']:
                print(f"   추가약칭2: {data['alias_2']}")
            if data['alias_3']:
                print(f"   추가약칭3: {data['alias_3']}")
            print(f"   영문명: {data['english_name']}")
            print(f"   영문약칭: {data['english_alias']}")
            print(f"   분류: {data['category']}")
            print()

        try:
            response = requests.post(f"{API_BASE}/dictionaries/terms", json=data)
            if response.status_code == 200:
                success_count += 1
                if success_count % 50 == 0:
                    print(f"✅ Progress: {success_count} records uploaded")
            else:
                print(f"❌ Failed to upload '{data['main_term']}': {response.status_code}")
                error_count += 1
        except Exception as e:
            print(f"❌ Exception uploading '{data['main_term']}': {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"✅ Successfully uploaded: {success_count} records")
    print(f"❌ Errors: {error_count} records")

if __name__ == "__main__":
    print("🚀 Re-uploading government organizations with correct column mapping\n")
    reload_all_records()
