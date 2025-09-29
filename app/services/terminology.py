# app/services/terminology.py
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import os
from app.services.who_icd_api import WHOICDAPI
from app.data.csv_parser import CSVProcessor
from app.data.demo_data import generate_namaste_data, generate_icd11_tm2_data, generate_icd11_bio_data
from app.schemas import CodeSystemType, SearchResult, TranslateResponse, TerminologyVersion
from app.utils.phonetic import phonetic_similarity, find_phonetic_matches
from app.utils.similarity import semantic_similarity, extract_keywords
from app.utils.mapping import expand_synonyms, map_abbreviations
import rapidfuzz
from rapidfuzz import process, fuzz

from app.config import settings  

class TerminologyService:
    def __init__(self):
        self.versions = self._initialize_versions()
        self.namaste_data = generate_namaste_data()
        
        # Initialized WHO ICD-API service with proper error handling
        self.who_api = self._initialize_who_api()
        
        # Load or fetch ICD-11 data
        self.icd11_tm2_data = self._load_or_fetch_tm2_data()
        self.icd11_bio_data = self._load_or_fetch_biomedicine_data()
        
        self._add_version_metadata()
        self._rebuild_indexes()
    
    def _initialize_versions(self) -> List[TerminologyVersion]:
        """Initialize terminology versions"""
        return [
            TerminologyVersion(
                version="1.0.0",
                effective_date=datetime.now(),
                systems=["NAMASTE", "ICD11_TM2", "ICD11_BIO"],
                description="Initial version with demo data"
            )
        ]
    
    def _initialize_who_api(self) -> Optional[WHOICDAPI]:
        """Initialize WHO ICD-API service with proper error handling"""
        if not settings.who_api_configured:
            print("ℹ️ WHO ICD-API credentials not configured. Using demo data.")
            return None
        
        try:
            print("🔄 Initializing WHO ICD-API service...")
            who_api = WHOICDAPI()
            print("✅ WHO ICD-API service initialized successfully")
            return who_api
        except Exception as e:
            print(f"⚠️ WHO ICD-API initialization failed: {e}")
            print("ℹ️ Falling back to demo data")
            return None
    
    def _load_or_fetch_tm2_data(self) -> List[Dict[str, Any]]:
        """Load TM2 data from WHO API or use demo data"""
        if self.who_api:
            try:
                print("🔄 Fetching TM2 data from WHO ICD-API...")
                tm2_data = self.who_api.get_tm2_codes()
                
                if tm2_data:
                    print(f"✅ Fetched {len(tm2_data)} TM2 codes from WHO API")
                    return tm2_data
                else:
                    print("⚠️ No TM2 data received from WHO API, using demo data")
                    
            except Exception as e:
                print(f"⚠️ WHO API TM2 fetch failed: {e}")
        
        # Fallback to demo data
        from app.data.demo_data import generate_icd11_tm2_data
        print("ℹ️ Using demo TM2 data")
        return generate_icd11_tm2_data()

    def _load_or_fetch_biomedicine_data(self) -> List[Dict[str, Any]]:
        """Load biomedical data from WHO API or use demo data"""
        if self.who_api:
            try:
                print("🔄 Fetching biomedical data from WHO ICD-API...")
                bio_data = self.who_api.get_biomedicine_codes(limit=50)
                
                if bio_data:
                    print(f"✅ Fetched {len(bio_data)} biomedical codes from WHO API")
                    return bio_data
                else:
                    print("⚠️ No biomedical data received from WHO API, using demo data")
                    
            except Exception as e:
                print(f"⚠️ WHO API biomedical fetch failed: {e}")
        
        # Fallback to demo data
        from app.data.demo_data import generate_icd11_bio_data
        print("ℹ️ Using demo biomedical data")
        return generate_icd11_bio_data()
    
    def _parse_who_entity(self, entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse WHO API entity into our format"""
        try:
            return {
                "id": entity.get("@id", "").replace("http://id.who.int/icd/entity/", ""),
                "code": entity.get("code", ""),
                "display": entity.get("title", {}).get("@value", ""),
                "definition": entity.get("definition", {}).get("@value", ""),
                "chapter": entity.get("chapter", ""),
                "is_tm2": entity.get("chapter") == "26",
                "source": "WHO ICD-API",
                "last_synced": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ Failed to parse WHO entity: {e}")
            return None
    
    def _add_version_metadata(self):
        """Add version metadata to all terminology entries"""
        current_version = self.versions[0]
        
        for item in self.namaste_data:
            item.update({
                "version": current_version.version,
                "effective_date": current_version.effective_date.isoformat(),
                "last_updated": datetime.now().isoformat()
            })
        
        for item in self.icd11_tm2_data:
            item.update({
                "version": "2024-01",
                "effective_date": "2024-01-01",
                "who_api_version": "2.0.1",
                "last_updated": datetime.now().isoformat()
            })
        
        for item in self.icd11_bio_data:
            item.update({
                "version": "2024-01",
                "effective_date": "2024-01-01", 
                "who_api_version": "2.0.1",
                "last_updated": datetime.now().isoformat()
            })
    
    def _rebuild_indexes(self):
        """Rebuild all indexes after data updates"""
        self.namaste_by_code = {item["code"]: item for item in self.namaste_data}
        self.namaste_by_id = {item["id"]: item for item in self.namaste_data}
        self.tm2_by_code = {item["code"]: item for item in self.icd11_tm2_data}
        self.tm2_by_id = {item["id"]: item for item in self.icd11_tm2_data}
        self.bio_by_code = {item["code"]: item for item in self.icd11_bio_data}
        self.bio_by_id = {item["id"]: item for item in self.icd11_bio_data}
        self.search_index = self._create_search_index()
    
    def _create_search_index(self) -> List[Dict[str, Any]]:
        """Create a unified search index"""
        index = []
        
        # Add NAMASTE terms
        for item in self.namaste_data:
            index.append({
                "id": item["id"],
                "code": item["code"],
                "display": item["display"],
                "definition": item.get("definition", ""),
                "system": CodeSystemType.NAMASTE,
                "synonyms": item.get("synonyms", []),
                "dosha": item.get("dosha", ""),
                "category": item.get("system", ""),
                "mapped_tm2": item.get("icd11_tm2_code", ""),
                "mapped_bio": item.get("icd11_bio_code", ""),
                "search_text": f"{item['display']} {' '.join(item.get('synonyms', []))} {item.get('definition', '')} {item.get('dosha', '')} {item.get('system', '')}",
                "version": item.get("version", ""),
                "effective_date": item.get("effective_date", "")
            })
        
        # Add ICD-11 TM2 terms
        for item in self.icd11_tm2_data:
            index.append({
                "id": item["id"],
                "code": item["code"],
                "display": item["display"],
                "definition": item.get("definition", ""),
                "system": CodeSystemType.ICD11_TM2,
                "category": item.get("category", ""),
                "parent_code": item.get("parent_code", ""),
                "mapped_bio": item.get("icd11_bio_code", ""),
                "search_text": f"{item['display']} {item.get('definition', '')} {item.get('category', '')}",
                "version": item.get("version", ""),
                "effective_date": item.get("effective_date", "")
            })
        
        # Add ICD-11 Biomedical terms
        for item in self.icd11_bio_data:
            index.append({
                "id": item["id"],
                "code": item["code"],
                "display": item["display"],
                "definition": item.get("definition", ""),
                "system": CodeSystemType.ICD11_BIO,
                "category": item.get("category", ""),
                "search_text": f"{item['display']} {item.get('definition', '')} {item.get('category', '')}",
                "version": item.get("version", ""),
                "effective_date": item.get("effective_date", "")
            })
        
        return index
    
    def sync_with_who_api(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Sync with real WHO ICD-API"""
        try:
            if not self.who_api:
                return {
                    "status": "error",
                    "error": "WHO ICD-API not configured. Set WHO_ICD_CLIENT_ID and WHO_ICD_CLIENT_SECRET environment variables."
                }
            
            # Clear existing data to force refresh
            self.icd11_tm2_data = self._load_or_fetch_tm2_data()
            self.icd11_bio_data = self._load_or_fetch_biomedicine_data()
            
            # Create new version
            new_version = TerminologyVersion(
                version=f"1.0.{len(self.versions)}",
                effective_date=datetime.now(),
                systems=["ICD11_TM2", "ICD11_BIO"],
                description=f"WHO API Sync - {len(self.icd11_tm2_data)} TM2, {len(self.icd11_bio_data)} Bio codes"
            )
            self.versions.append(new_version)
            
            # Rebuild with new version
            self._add_version_metadata()
            self._rebuild_indexes()
            
            return {
                "status": "success",
                "tm2_count": len(self.icd11_tm2_data),
                "bio_count": len(self.icd11_bio_data),
                "new_version": new_version.version,
                "sync_date": datetime.now().isoformat(),
                "source": "WHO ICD-API"
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def search_who_api_direct(self, query: str, system: CodeSystemType) -> List[Dict[str, Any]]:
        """Search directly against WHO ICD-API (real-time)"""
        if not self.who_api:
            return []
        
        try:
            if system == CodeSystemType.ICD11_TM2:
                results = self.who_api.search_icd_entities(query, chapter='26')
            else:
                results = self.who_api.search_icd_entities(query)
            
            parsed_results = []
            for entity in results[:10]:
                parsed = self._parse_who_entity(entity)
                if parsed:
                    parsed_results.append(parsed)
            
            return parsed_results
        except Exception as e:
            print(f"WHO API search failed: {e}")
            return []
    
    def auto_map_namaste_to_icd(self, namaste_code: str, namaste_display: str) -> Dict[str, Any]:
        """Automatically map NAMASTE terms to ICD-11 using WHO API"""
        if not self.who_api:
            return {"status": "api_not_available"}
        
        try:
            # Search for similar terms in WHO API
            tm2_matches = self.search_who_api_direct(namaste_display, CodeSystemType.ICD11_TM2)
            bio_matches = self.search_who_api_direct(namaste_display, CodeSystemType.ICD11_BIO)
            
            # Calculate confidence based on match quality
            best_tm2_match = self._calculate_mapping_confidence(namaste_display, tm2_matches)
            best_bio_match = self._calculate_mapping_confidence(namaste_display, bio_matches)
            
            return {
                "status": "success",
                "namaste_code": namaste_code,
                "namaste_display": namaste_display,
                "suggested_tm2_mapping": best_tm2_match,
                "suggested_bio_mapping": best_bio_match,
                "all_matches": {
                    "tm2": tm2_matches[:3],
                    "biomedicine": bio_matches[:3]
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _calculate_mapping_confidence(self, namaste_term: str, icd_matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate confidence score for mapping matches"""
        if not icd_matches:
            return None
        
        best_match = icd_matches[0]
        display_score = fuzz.ratio(namaste_term.lower(), best_match['display'].lower()) / 100
        
        return {
            **best_match,
            "mapping_confidence": display_score,
            "match_type": "automatic" if display_score > 0.7 else "suggested"
        }
    
    def import_namaste_csv(self, csv_content: str) -> Dict[str, Any]:
        """Import NAMASTE data from CSV"""
        try:
            new_data = CSVProcessor.parse_namaste_csv(csv_content)
            
            # Create new version
            new_version = TerminologyVersion(
                version=f"1.0.{len(self.versions)}",
                effective_date=datetime.now(),
                systems=["NAMASTE"],
                description="Imported from CSV"
            )
            self.versions.append(new_version)
            
            # Update data with new version
            for item in new_data:
                item.update({
                    "version": new_version.version,
                    "effective_date": new_version.effective_date.isoformat(),
                    "last_updated": datetime.now().isoformat()
                })
            
            self.namaste_data.extend(new_data)
            self._rebuild_indexes()
            
            return {
                "status": "success",
                "imported_count": len(new_data),
                "new_version": new_version.version
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def search_terms(self, query: str, system: Optional[CodeSystemType] = None, 
                    patient_age: Optional[int] = None, patient_gender: Optional[str] = None,
                    existing_conditions: Optional[List[str]] = None, 
                    symptoms: Optional[List[str]] = None, limit: int = 10) -> List[SearchResult]:
        """Search for terms with advanced features"""
        # Preprocess query
        processed_query = map_abbreviations(query)
        expanded_queries = expand_synonyms(processed_query)
        
        results = []
        
        # Search across all expanded queries
        for search_query in expanded_queries:
            # First, try exact matches
            for item in self.search_index:
                if system and item["system"] != system:
                    continue
                
                # Check exact matches in display name and synonyms
                exact_match = (
                    search_query.lower() in item["display"].lower() or
                    any(search_query.lower() in syn.lower() for syn in item.get("synonyms", []))
                )
                
                if exact_match:
                    score = 1.0
                else:
                    # Calculate fuzzy match score
                    display_score = fuzz.partial_ratio(search_query, item["display"]) / 100
                    synonym_scores = [fuzz.partial_ratio(search_query, syn) / 100 for syn in item.get("synonyms", [])]
                    definition_score = fuzz.partial_ratio(search_query, item.get("definition", "")) / 100
                    
                    # Use the highest score
                    score = max(display_score, max(synonym_scores) if synonym_scores else 0, definition_score)
                
                # Apply context-based boosting
                score = self._apply_context_boosting(score, item, patient_age, patient_gender, 
                                                    existing_conditions, symptoms)
                
                if score > 0.3:  # Minimum threshold
                    # Get mapped codes
                    mapped_codes = {}
                    if item["system"] == CodeSystemType.NAMASTE:
                        if item.get("mapped_tm2"):
                            mapped_codes["icd11_tm2"] = item["mapped_tm2"]
                        if item.get("mapped_bio"):
                            mapped_codes["icd11_bio"] = item["mapped_bio"]
                    elif item["system"] == CodeSystemType.ICD11_TM2 and item.get("mapped_bio"):
                        mapped_codes["icd11_bio"] = item["mapped_bio"]
                    
                    results.append(SearchResult(
                        id=item["id"],
                        code=item["code"],
                        display=item["display"],
                        definition=item.get("definition"),
                        system=item["system"],
                        score=score,
                        mapping_confidence=0.9 if mapped_codes else None,
                        mapped_codes=mapped_codes or None,
                        version=item.get("version"),
                        effective_date=item.get("effective_date")
                    ))
        
        # Deduplicate and sort by score
        seen = set()
        unique_results = []
        for result in results:
            if result.id not in seen:
                seen.add(result.id)
                unique_results.append(result)
        
        # Sort by score descending
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        return unique_results[:limit]
    
    def _is_complication_of(self, item: Dict[str, Any], existing_conditions: List[str]) -> bool:
        """Check if this item represents a complication of existing conditions"""
        item_text = item.get("search_text", "").lower()
        
        complication_keywords = [
            "complication", "secondary", "due to", "caused by", 
            "associated with", "related to", "result of"
        ]
        
        for condition in existing_conditions:
            condition_lower = condition.lower()
            
            # Check if this item mentions both the condition and complication terms
            if (condition_lower in item_text and
                any(keyword in item_text for keyword in complication_keywords)):
                return True
        
        return False
    
    def _apply_context_boosting(self, score: float, item: Dict[str, Any], 
                               patient_age: Optional[int], patient_gender: Optional[str],
                               existing_conditions: Optional[List[str]], 
                               symptoms: Optional[List[str]]) -> float:
        """Apply context-based boosting to search score with stronger weights"""
        boosted_score = score
        
        # Stronger age-based boosting (2-3x instead of 1.2x)
        if patient_age:
            # Pediatric conditions
            if patient_age < 18 and any(term in item.get("search_text", "").lower() 
                                      for term in ["pediatric", "child", "infant", "juvenile"]):
                boosted_score *= 2.5
            
            # Geriatric conditions
            elif patient_age > 65 and any(term in item.get("search_text", "").lower() 
                                        for term in ["geriatric", "elderly", "senior", "age-related"]):
                boosted_score *= 2.5
        
        # Stronger gender-based boosting
        if patient_gender:
            gender_lower = patient_gender.lower()
            gender_terms = []
            
            if gender_lower == "female":
                gender_terms = ["female", "woman", "women", "gynec", "obstet", "menstrual", "pregnancy"]
            elif gender_lower == "male":
                gender_terms = ["male", "man", "men", "andro", "prostate", "testicular"]
            
            if any(term in item.get("search_text", "").lower() for term in gender_terms):
                boosted_score *= 2.5
        
        # Enhanced existing conditions boosting with complication detection
        if existing_conditions:
            for condition in existing_conditions:
                condition_lower = condition.lower()
                
                # Strong boost for direct matches
                if condition_lower in item.get("search_text", "").lower():
                    boosted_score *= 3.0
                
                # Even stronger boost for complications
                elif self._is_complication_of(item, [condition]):
                    boosted_score *= 4.0  # Very strong boost for complications
                    
                # Moderate boost for related terms
                elif any(term in item.get("search_text", "").lower() 
                        for term in self._get_related_terms(condition_lower)):
                    boosted_score *= 2.5
        
        # Stronger symptoms boosting
        if symptoms:
            for symptom in symptoms:
                symptom_lower = symptom.lower()
                if symptom_lower in item.get("search_text", "").lower():
                    boosted_score *= 2.0
                    break
        
        return min(boosted_score, 1.0)  # Cap at 1.0

    def _get_related_terms(self, condition: str) -> List[str]:
        """Get related terms for conditions to improve context matching"""
        related_terms_map = {
            "diabetes": ["diabetic", "madumeha", "sugar", "glucose", "hyperglycem", "insulin"],
            "hypertension": ["hypertensive", "high blood pressure", "htn", "bp"],
            "fever": ["jwara", "pyrexia", "temperature", "febrile"],
            "arthritis": ["joint", "amavata", "rheumat", "arthralgia"],
            "asthma": ["shwasa", "breathing", "wheez", "bronch"],
            "tb": ["tuberculosis", "rajayakshma", "kshaya", "mycobacter"],
            "anemia": ["pandu", "hemoglobin", "iron", "hemat"],
        }
        
        for key, terms in related_terms_map.items():
            if key in condition:
                return terms
        
        return []
    
    def translate_code(self, code: str, source_system: CodeSystemType, 
                      target_system: CodeSystemType) -> Optional[TranslateResponse]:
        """Translate a code from one system to another"""
        source_item = None
        
        # Find source item
        if source_system == CodeSystemType.NAMASTE:
            source_item = self.namaste_by_code.get(code) or self.namaste_by_id.get(code)
        elif source_system == CodeSystemType.ICD11_TM2:
            source_item = self.tm2_by_code.get(code) or self.tm2_by_id.get(code)
        elif source_system == CodeSystemType.ICD11_BIO:
            source_item = self.bio_by_code.get(code) or self.bio_by_id.get(code)
        
        if not source_item:
            return None
        
        target_code = None
        target_display = None
        confidence = 0.0
        
        # Handle different translation paths
        if source_system == CodeSystemType.NAMASTE and target_system == CodeSystemType.ICD11_TM2:
            target_code = source_item.get("icd11_tm2_code")
            if target_code:
                target_item = self.tm2_by_code.get(target_code)
                target_display = target_item.get("display") if target_item else None
                confidence = source_item.get("mapping_confidence", 0.8)
        
        elif source_system == CodeSystemType.NAMASTE and target_system == CodeSystemType.ICD11_BIO:
            target_code = source_item.get("icd11_bio_code")
            if target_code:
                target_item = self.bio_by_code.get(target_code)
                target_display = target_item.get("display") if target_item else None
                confidence = source_item.get("mapping_confidence", 0.8) * 0.9  # Slightly lower confidence for bio mapping
        
        elif source_system == CodeSystemType.ICD11_TM2 and target_system == CodeSystemType.ICD11_BIO:
            target_code = source_item.get("icd11_bio_code")
            if target_code:
                target_item = self.bio_by_code.get(target_code)
                target_display = target_item.get("display") if target_item else None
                confidence = 0.85
        
        elif source_system == CodeSystemType.ICD11_TM2 and target_system == CodeSystemType.NAMASTE:
            # Reverse mapping - find NAMASTE items that map to this TM2 code
            for namaste_item in self.namaste_data:
                if namaste_item.get("icd11_tm2_code") == code:
                    target_code = namaste_item["code"]
                    target_display = namaste_item["display"]
                    confidence = namaste_item.get("mapping_confidence", 0.8) * 0.9  # Lower confidence for reverse mapping
                    break
        
        if not target_code:
            return None
        
        return TranslateResponse(
            source_code=code,
            source_display=source_item.get("display", ""),
            target_code=target_code,
            target_display=target_display or "",
            confidence=confidence,
            source_version=source_item.get("version"),
            target_version=self._get_target_version(target_system)
        )
    
    def _get_target_version(self, system: CodeSystemType) -> str:
        """Get the current version for a target system"""
        if system == CodeSystemType.NAMASTE:
            return self.versions[-1].version if self.versions else "1.0.0"
        else:
            return "2024-01"  
    
    def get_code_details(self, code: str, system: CodeSystemType) -> Optional[Dict[str, Any]]:
        """Get detailed information about a code"""
        if system == CodeSystemType.NAMASTE:
            return self.namaste_by_code.get(code) or self.namaste_by_id.get(code)
        elif system == CodeSystemType.ICD11_TM2:
            return self.tm2_by_code.get(code) or self.tm2_by_id.get(code)
        elif system == CodeSystemType.ICD11_BIO:
            return self.bio_by_code.get(code) or self.bio_by_id.get(code)
        return None
    
    def get_fhir_codesystem(self, system: CodeSystemType, version: Optional[str] = None) -> Dict[str, Any]:
        """Generate FHIR CodeSystem resource"""
        if system == CodeSystemType.NAMASTE:
            data = self.namaste_data
            system_name = "NAMASTE"
            system_url = "http://namaste-ayush.gov.in/codesystem"
        elif system == CodeSystemType.ICD11_TM2:
            data = self.icd11_tm2_data
            system_name = "ICD-11 TM2"
            system_url = "http://who.int/icd/tm2"
        else:
            data = self.icd11_bio_data
            system_name = "ICD-11"
            system_url = "http://who.int/icd"
        
        
        if version:
            data = [item for item in data if item.get('version') == version]
        
        concepts = []
        for item in data:
            concept = {
                "code": item["code"],
                "display": item["display"],
                "definition": item.get("definition", "")
            }
            if item.get("synonyms"):
                concept["designation"] = [
                    {"value": synonym, "use": {"code": "synonym"}} 
                    for synonym in item["synonyms"]
                ]
            concepts.append(concept)
        
        return {
            "resourceType": "CodeSystem",
            "id": f"codesystem-{system.value}",
            "url": f"{system_url}/{version}" if version else system_url,
            "version": version or "current",
            "name": system_name,
            "status": "active",
            "content": "complete",
            "concept": concepts,
            "meta": {
                "lastUpdated": datetime.now().isoformat(),
                "versionId": str(len(self.versions))
            }
        }
    
    def get_fhir_conceptmap(self, source: CodeSystemType, target: CodeSystemType) -> Dict[str, Any]:
        """Generate FHIR ConceptMap resource"""
        concept_map = {
            "resourceType": "ConceptMap",
            "id": f"conceptmap-{source.value}-to-{target.value}",
            "url": f"http://namaste-icd11-service/conceptmap/{source.value}-to-{target.value}",
            "version": "1.0.0",
            "name": f"Map from {source.value} to {target.value}",
            "status": "active",
            "sourceUri": f"http://namaste-ayush.gov.in/codesystem/{source.value}",
            "targetUri": f"http://who.int/icd/{target.value}",
            "group": [{
                "source": source.value,
                "target": target.value,
                "element": []
            }],
            "meta": {
                "lastUpdated": datetime.now().isoformat()
            }
        }
        
        
        if source == CodeSystemType.NAMASTE:
            for item in self.namaste_data:
                target_code = None
                if target == CodeSystemType.ICD11_TM2:
                    target_code = item.get("icd11_tm2_code")
                elif target == CodeSystemType.ICD11_BIO:
                    target_code = item.get("icd11_bio_code")
                
                if target_code:
                    concept_map["group"][0]["element"].append({
                        "code": item["code"],
                        "target": [{
                            "code": target_code,
                            "equivalence": "equivalent",
                            "comment": f"Mapping confidence: {item.get('mapping_confidence', 0.8)}"
                        }]
                    })
        
        return concept_map
    
    def get_terminology_versions(self) -> List[TerminologyVersion]:
        """Get list of all terminology versions"""
        return self.versions
    
    def export_data(self, system: CodeSystemType, format: str = "json") -> Dict[str, Any]:
        """Export terminology data in specified format"""
        if system == CodeSystemType.NAMASTE:
            data = self.namaste_data
        elif system == CodeSystemType.ICD11_TM2:
            data = self.icd11_tm2_data
        else:
            data = self.icd11_bio_data
        
        if format.lower() == "csv":
            
            if data:
                headers = data[0].keys()
                csv_content = ",".join(headers) + "\n"
                for item in data:
                    row = [str(item.get(header, "")) for header in headers]
                    csv_content += ",".join(row) + "\n"
                
                return {
                    "format": "csv",
                    "content": csv_content,
                    "system": system.value,
                    "export_date": datetime.now().isoformat(),
                    "record_count": len(data)
                }
        
        
        return {
            "format": "json",
            "content": data,
            "system": system.value,
            "export_date": datetime.now().isoformat(),
            "record_count": len(data)
        }