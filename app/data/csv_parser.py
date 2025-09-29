# app/data/csv_parser.py
import csv
import pandas as pd
from typing import List, Dict, Any
from io import StringIO
import requests
from datetime import datetime

class CSVProcessor:
    """Process NAMASTE CSV exports with WHO API integration"""
    
    def __init__(self, who_api_service=None):
        self.who_api = who_api_service
    
    @staticmethod
    def parse_namaste_csv(csv_content: str) -> List[Dict[str, Any]]:
        """Parse NAMASTE CSV export format"""
        namaste_data = []
        reader = csv.DictReader(StringIO(csv_content))
        
        for row in reader:
            namaste_data.append({
                "id": f"NAMASTE_{row['code']}",
                "code": row['code'],
                "display": row['display_name'],
                "definition": row.get('definition', ''),
                "dosha": row.get('dosha', ''),
                "system": row.get('system', ''),
                "synonyms": row.get('synonyms', '').split(';') if row.get('synonyms') else [],
                "icd11_tm2_code": row.get('icd11_tm2_code', ''),
                "icd11_bio_code": row.get('icd11_bio_code', ''),
                "mapping_confidence": float(row.get('mapping_confidence', 0.8)),
                "version": "1.0.0",
                "effective_date": datetime.now().isoformat(),
                "mapping_source": "manual" if row.get('icd11_tm2_code') else "unmapped"
            })
        
        return namaste_data
    
    def enhance_with_who_mappings(self, namaste_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance NAMASTE data with automatic WHO API mappings"""
        if not self.who_api:
            print("⚠️ WHO API not available for automatic mapping")
            return namaste_data
        
        enhanced_data = []
        mapped_count = 0
        
        for item in namaste_data:
            enhanced_item = item.copy()
            
            # Only try to map if not already mapped
            if not item.get('icd11_tm2_code'):
                try:
                    mapping_result = self.who_api.auto_map_namaste_to_icd(
                        item['code'], 
                        item['display']
                    )
                    
                    if mapping_result.get('suggested_tm2_mapping'):
                        enhanced_item.update({
                            'icd11_tm2_code': mapping_result['suggested_tm2_mapping']['code'],
                            'icd11_tm2_display': mapping_result['suggested_tm2_mapping']['display'],
                            'mapping_confidence': mapping_result['suggested_tm2_mapping']['mapping_confidence'],
                            'mapping_source': 'who_api_auto'
                        })
                        mapped_count += 1
                        
                except Exception as e:
                    print(f"⚠️ Mapping failed for {item['code']}: {e}")
            
            enhanced_data.append(enhanced_item)
        
        print(f"✅ Automatically mapped {mapped_count} terms using WHO API")
        return enhanced_data