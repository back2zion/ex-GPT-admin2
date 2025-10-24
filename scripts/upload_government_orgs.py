#!/usr/bin/env python3
"""
Upload 302 government organization records to dictionary database
"""
import csv
import requests
import sys
from pathlib import Path

API_BASE = "http://localhost:8010/api/v1/admin"

def upload_csv_to_dictionary(csv_file_path: str, dict_id: int):
    """Upload CSV records to specified dictionary"""

    # Read CSV file
    with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📄 Loaded {len(rows)} rows from CSV")
    print(f"📋 Columns: {reader.fieldnames}")

    # Verify expected columns
    expected_columns = ['정식명칭', '주요약칭', '추가약칭1', '추가약칭2', '추가약칭3', '영문명', '영문약칭', '분류']
    if reader.fieldnames != expected_columns:
        print(f"❌ Column mismatch!")
        print(f"   Expected: {expected_columns}")
        print(f"   Got: {reader.fieldnames}")
        return

    # Upload each row
    success_count = 0
    error_count = 0
    errors = []

    for idx, row in enumerate(rows, start=2):  # Start at 2 to account for header line
        # Skip empty rows
        main_term_value = row.get('정식명칭')
        if not main_term_value or not main_term_value.strip():
            print(f"⏭️  Line {idx}: Skipping empty row")
            continue

        # Prepare data (handle None and empty strings)
        def clean_field(value):
            if value is None or not value.strip():
                return None
            return value.strip()

        data = {
            "dict_id": dict_id,
            "main_term": clean_field(row['정식명칭']),
            "main_alias": clean_field(row.get('주요약칭')),
            "alias_1": clean_field(row.get('추가약칭1')),
            "alias_2": clean_field(row.get('추가약칭2')),
            "alias_3": clean_field(row.get('추가약칭3')),
            "english_name": clean_field(row.get('영문명')),
            "english_alias": clean_field(row.get('영문약칭')),
            "category": clean_field(row.get('분류')),
            "use_yn": True
        }

        # Debug first few rows
        if idx <= 5:
            print(f"\n📝 Line {idx}: {data['main_term']}")
            print(f"   main_alias: {data['main_alias']}")
            print(f"   english_name: {data['english_name']}")
            print(f"   english_alias: {data['english_alias']}")
            print(f"   category: {data['category']}")

        try:
            response = requests.post(
                f"{API_BASE}/dictionaries/terms",
                json=data,
                verify=False
            )

            if response.status_code == 200:
                success_count += 1
                if idx % 50 == 0:
                    print(f"✅ Progress: {success_count} records uploaded")
            elif response.status_code == 400 and "이미 존재하는 용어" in response.text:
                print(f"⚠️  Line {idx}: Duplicate term '{data['main_term']}'")
                error_count += 1
                errors.append((idx, data['main_term'], "Duplicate"))
            else:
                print(f"❌ Line {idx}: Failed to upload '{data['main_term']}'")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                error_count += 1
                errors.append((idx, data['main_term'], response.text[:100]))

        except Exception as e:
            print(f"❌ Line {idx}: Exception for '{data['main_term']}': {e}")
            error_count += 1
            errors.append((idx, data['main_term'], str(e)))

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Successfully uploaded: {success_count} records")
    print(f"❌ Errors: {error_count} records")

    if errors:
        print(f"\n⚠️  Error details:")
        for line, term, err in errors[:10]:  # Show first 10 errors
            print(f"   Line {line}: {term} - {err}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")

    return success_count, error_count


if __name__ == "__main__":
    csv_file = "/home/aigen/정부기관_전체_302개.csv"
    dict_id = 2  # Government organization synonym dictionary

    if not Path(csv_file).exists():
        print(f"❌ CSV file not found: {csv_file}")
        sys.exit(1)

    print(f"🚀 Starting upload to dictionary ID {dict_id}")
    print(f"📂 CSV file: {csv_file}")
    print(f"🔗 API: {API_BASE}\n")

    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    upload_csv_to_dictionary(csv_file, dict_id)
