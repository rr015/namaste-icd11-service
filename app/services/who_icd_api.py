# app/services/who_icd_api.py
import requests
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import settings

logger = logging.getLogger(__name__)

class WHOICDAPI:
    """Service to interact with the real WHO ICD-API"""
    
    def __init__(self):
        if not settings.who_api_configured:
            raise ValueError("WHO ICD-API credentials not configured")
        
        self.client_id = settings.WHO_ICD_CLIENT_ID
        self.client_secret = settings.WHO_ICD_CLIENT_SECRET
        self.base_url = "https://id.who.int/icd"
        self.token_url = "https://icdaccessmanagement.who.int/connect/token"
        
        print(f"🔌 Initializing WHO ICD-API with Client ID: {self.client_id[:10]}...")
        
        
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.access_token = None
        self.token_expiry = None
        
        
        self._test_connection()
    
    def _test_connection(self):
        """Test API connection on initialization"""
        try:
            token = self.get_access_token()
            print("✅ WHO ICD-API connection test: SUCCESS")
        except Exception as e:
            print(f"❌ WHO ICD-API connection test failed: {e}")
            raise
    
    def get_access_token(self) -> str:
        """Get OAuth2 access token from WHO API"""
        if self.access_token and self.token_expiry and datetime.now().timestamp() < self.token_expiry:
            return self.access_token
        
        try:
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'icdapi_access',
                'grant_type': 'client_credentials'
            }
            
            print("🔑 Requesting WHO ICD-API access token...")
            response = self.session.post(self.token_url, data=payload, verify=True)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            
            self.token_expiry = datetime.now().timestamp() + (50 * 60)
            
            print("✅ Successfully obtained WHO ICD-API access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            error_msg = f"WHO ICD-API token request failed: {e}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Status: {e.response.status_code} - Response: {e.response.text}"
            logger.error(error_msg)
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting WHO API token: {e}")
            raise
    
    def make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to WHO ICD-API"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'API-Version': 'v2'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            print(f"🌐 Calling WHO ICD-API: {endpoint} with params: {params}")
            response = self.session.get(url, headers=headers, params=params, verify=True)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ WHO API call successful: {endpoint}")
            return result
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"WHO API HTTP error for {endpoint}: {e}"
            if e.response.status_code == 404:
                error_msg += " - Endpoint not found"
            elif e.response.status_code == 401:
                error_msg += " - Authentication failed"
            logger.error(error_msg)
           
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"WHO API request failed for {endpoint}: {e}")
            return {}
    
    def search_icd_entities(self, query: str, chapter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search ICD-11 entities using the correct endpoint"""
        
        params = {
            'q': query,
            'useFlexisearch': 'true',
            'flat': 'true'
        }
        if chapter:
            params['chapterFilter'] = chapter
            
        try:
            
            result = self.make_api_request('release/11/2024-01/mms/search', params)
            
            
            if result and 'destinationEntities' in result:
                return result['destinationEntities']
            else:
                print(f"⚠️ Unexpected API response structure: {result.keys() if result else 'Empty response'}")
                return []
                
        except Exception as e:
            print(f"⚠️ Search failed: {e}")
            return self._get_mock_search_results(query, chapter)
    
    def _get_mock_search_results(self, query: str, chapter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Provide mock search results when API is not available or fails"""
        
        mock_data = {
            'fever': [
                {
                    "@id": "http://id.who.int/icd/entity/123456789",
                    "code": "MG26",
                    "title": {"@value": "Fever in traditional medicine"},
                    "definition": {"@value": "Elevated body temperature in traditional medicine context"},
                    "chapter": "26",
                    "isTm2": True
                }
            ],
            'diabetes': [
                {
                    "@id": "http://id.who.int/icd/entity/555555555",
                    "code": "5A10",
                    "title": {"@value": "Type 2 diabetes mellitus"},
                    "definition": {"@value": "Diabetes mellitus characterized by insulin resistance"},
                    "chapter": "5",
                    "isTm2": False
                }
            ],
            'arthritis': [
                {
                    "@id": "http://id.who.int/icd/entity/777777777",
                    "code": "FA20",
                    "title": {"@value": "Rheumatoid arthritis"},
                    "definition": {"@value": "Chronic inflammatory joint disease"},
                    "chapter": "15",
                    "isTm2": False
                }
            ]
        }
        
        query_lower = query.lower()
        results = []
        
      
        for key, items in mock_data.items():
            if key in query_lower:
                results.extend(items)
        
        
        if chapter:
            results = [item for item in results if item.get('chapter') == chapter]
        
        return results[:10]
    
    def get_tm2_codes(self) -> List[Dict[str, Any]]:
        """Get Traditional Medicine Module 2 (TM2) codes - Chapter 26"""
        try:
            
            params = {
                'linearization': 'mms',
                'chapter': '26'
            }
            
            result = self.make_api_request('release/11/2024-01', params)
            
            parsed_results = []
            if result and 'child' in result:
                
                parsed_results = self._extract_entities_from_chapter(result['child'])
            
            if parsed_results:
                print(f"✅ Fetched {len(parsed_results)} TM2 codes from WHO API")
                return parsed_results
            else:
                print("⚠️ No TM2 data received from WHO API, using demo data")
                raise Exception("No TM2 data received")
                
        except Exception as e:
            print(f"⚠️ Failed to fetch TM2 codes: {e}")
           
            return self._get_enhanced_tm2_demo_data()
    
    def _extract_entities_from_chapter(self, children: List[Dict]) -> List[Dict[str, Any]]:
        """Recursively extract entities from chapter structure"""
        entities = []
        for child in children:
            if child.get('classKind') == 'category':
                
                entity = {
                    "id": child.get('@id', '').replace('http://id.who.int/icd/entity/', ''),
                    "code": child.get('code', ''),
                    "display": child.get('title', {}).get('@value', ''),
                    "definition": child.get('definition', {}).get('@value', ''),
                    "chapter": child.get('chapter', ''),
                    "is_tm2": child.get('chapter') == '26',
                    "source": "WHO ICD-API TM2"
                }
                entities.append(entity)
            
            
            if 'child' in child:
                entities.extend(self._extract_entities_from_chapter(child['child']))
        
        return entities
    
    def _get_enhanced_tm2_demo_data(self) -> List[Dict[str, Any]]:
        """Enhanced demo TM2 data"""
        return [
            {
                "id": "TM2_001",
                "code": "TM26.0",
                "display": "Traditional medicine disorder of Jwara (fever)",
                "definition": "Fever conditions in traditional medicine",
                "chapter": "26",
                "is_tm2": True,
                "source": "WHO ICD-API TM2 (Demo)"
            },
            {
                "id": "TM2_002", 
                "code": "TM26.1",
                "display": "Traditional medicine disorder of Atisara (diarrhea)",
                "definition": "Diarrhea conditions in traditional medicine",
                "chapter": "26",
                "is_tm2": True,
                "source": "WHO ICD-API TM2 (Demo)"
            }
        ]
    
    def get_biomedicine_codes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get biomedical ICD-11 codes (excluding TM2)"""
        try:
            
            common_codes = ['1A00', '5A10', 'FA20', 'CA23', 'BA00']  # Common ICD-11 codes
            
            all_results = []
            for code in common_codes:
                entity = self.get_entity_details(f"http://id.who.int/icd/entity/{hash(code) % 1000000}")
                if entity and entity.get('chapter') != '26':  # Exclude TM2
                    parsed = self._parse_entity(entity)
                    if parsed:
                        all_results.append(parsed)
                
                if len(all_results) >= limit:
                    break
            
            if all_results:
                print(f"✅ Fetched {len(all_results)} biomedical codes from WHO API")
                return all_results
            else:
                print("⚠️ No biomedical data received from WHO API, using demo data")
                raise Exception("No biomedical data received")
                
        except Exception as e:
            print(f"⚠️ Failed to fetch biomedical codes: {e}")
            return self._get_enhanced_bio_demo_data()
    
    def _get_enhanced_bio_demo_data(self) -> List[Dict[str, Any]]:
        """Enhanced demo biomedical data"""
        return [
            {
                "id": "BIO_001",
                "code": "1A00",
                "display": "Fever of unknown origin",
                "definition": "Fever without known cause",
                "chapter": "1",
                "is_tm2": False,
                "source": "WHO ICD-API (Demo)"
            },
            {
                "id": "BIO_002",
                "code": "5A10", 
                "display": "Type 2 diabetes mellitus",
                "definition": "Diabetes mellitus type 2",
                "chapter": "5",
                "is_tm2": False,
                "source": "WHO ICD-API (Demo)"
            }
        ]
    
    def get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific ICD-11 entity"""
        try:
            
            if entity_id.startswith('http://id.who.int/icd/entity/'):
                entity_id = entity_id.replace('http://id.who.int/icd/entity/', '')
            
            return self.make_api_request(f'entity/{entity_id}')
        except:
            return None
    
    def _parse_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Parse WHO API entity into our standardized format"""
        try:
            entity_id = entity.get('@id', '')
            if entity_id.startswith('http://id.who.int/icd/entity/'):
                entity_id = entity_id.replace('http://id.who.int/icd/entity/', '')
            
            return {
                'id': entity_id,
                'code': entity.get('code', ''),
                'display': entity.get('title', {}).get('@value', ''),
                'definition': entity.get('definition', {}).get('@value', ''),
                'chapter': entity.get('chapter', ''),
                'chapter_name': entity.get('chapterName', ''),
                'is_tm2': entity.get('chapter') == '26',
                'who_api_version': 'v2',
                'source': 'WHO ICD-API',
                'last_synced': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ Failed to parse entity: {e}")
            return None