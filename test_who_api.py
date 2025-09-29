# test_who_api.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.who_icd_api import WHOICDAPI
from app.config import settings

def test_who_api():
    print("🧪 Testing WHO ICD-API Integration")
    
    try:
        # Test API initialization
        who_api = WHOICDAPI()
        print("✅ WHO ICD-API initialized successfully")
        
        # Test search functionality
        print("🔍 Testing search for 'diabetes'...")
        results = who_api.search_icd_entities('diabetes')
        print(f"✅ Found {len(results)} results for 'diabetes'")
        
        for i, result in enumerate(results[:3]):  # Show first 3 results
            print(f"  {i+1}. {result.get('display', 'N/A')} (Code: {result.get('code', 'N/A')})")
        
        # Test TM2 codes
        print("🌿 Fetching TM2 codes...")
        tm2_codes = who_api.get_tm2_codes()
        print(f"✅ Found {len(tm2_codes)} TM2 codes")
        
        # Test biomedical codes
        print("🏥 Fetching biomedical codes...")
        bio_codes = who_api.get_biomedicine_codes(limit=10)
        print(f"✅ Found {len(bio_codes)} biomedical codes")
        
        print("\n🎉 WHO ICD-API test completed successfully!")
        
    except Exception as e:
        print(f"❌ WHO ICD-API test failed: {e}")

if __name__ == "__main__":
    test_who_api()