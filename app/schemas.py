
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CodeSystemType(str, Enum):
    NAMASTE = "namaste"
    ICD11_TM2 = "icd11_tm2"
    ICD11_BIO = "icd11_bio"

class TerminologyVersion(BaseModel):
    version: str
    effective_date: datetime
    systems: List[str]
    description: str

class ConsentMetadata(BaseModel):
    consent_id: str
    patient_id: str
    purpose: str
    scope: List[str]
    valid_from: datetime
    valid_to: datetime
    status: str = "active"

class AuditLog(BaseModel):
    id: str
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    query: Optional[str] = None
    patient_id: Optional[str] = None
    consent_id: Optional[str] = None
    access_purpose: str = "treatment"

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    system: Optional[CodeSystemType] = Field(None, description="Filter by terminology system")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    patient_age: Optional[int] = Field(None, ge=0, le=120, description="Patient age for context-aware search")
    patient_gender: Optional[str] = Field(None, description="Patient gender for context-aware search")
    existing_conditions: Optional[List[str]] = Field(None, description="Existing medical conditions for context")
    symptoms: Optional[List[str]] = Field(None, description="Current symptoms for context")
    consent_id: Optional[str] = Field(None, description="Consent identifier for audit logging")
    patient_id: Optional[str] = Field(None, description="Patient identifier for audit logging")
    offset: int = Field(0, ge=0, description="Pagination offset")  # Added offset field

    class Config:
        schema_extra = {
            "example": {
                "query": "fever",
                "system": "namaste",
                "limit": 10,
                "patient_age": 35,
                "patient_gender": "female",
                "existing_conditions": ["diabetes", "hypertension"],
                "symptoms": ["headache", "cough"],
                "consent_id": "consent-12345",
                "patient_id": "patient-67890",
                "offset": 0
            }
        }

class SearchResult(BaseModel):
    id: str
    code: str
    display: str
    definition: Optional[str] = None
    system: CodeSystemType
    score: float
    mapping_confidence: Optional[float] = None
    mapped_codes: Optional[Dict[str, str]] = None
    version: Optional[str] = None

class TranslateRequest(BaseModel):
    code: str
    source_system: CodeSystemType
    target_system: CodeSystemType
    consent_id: Optional[str] = None

class TranslateResponse(BaseModel):
    source_code: str
    source_display: str
    target_code: str
    target_display: str
    confidence: float
    source_version: Optional[str] = None  
    target_version: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "source_code": "AY001",
                "source_display": "Jwara (Fever)",
                "target_code": "TM2_KA50",
                "target_display": "Disorders of Jwara",
                "confidence": 0.95,
                "source_version": "1.0.0",
                "target_version": "2024-01"
            }
        }

class CSVImportRequest(BaseModel):
    csv_content: str
    description: str

class WHOApiSyncRequest(BaseModel):
    systems: List[CodeSystemType]
    force_refresh: bool = False

class FHIRCodeSystemRequest(BaseModel):
    system: CodeSystemType
    version: Optional[str] = None

class FHIRConceptMapRequest(BaseModel):
    source: CodeSystemType
    target: CodeSystemType

class ProblemListEntry(BaseModel):
    id: str
    clinical_status: str
    verification_status: str
    category: str
    code: Dict[str, str]
    subject: Dict[str, str]
    encounter: Dict[str, str]
    recorded_date: datetime
    evidence: Optional[List[Dict[str, Any]]] = None
    consent_metadata: Optional[ConsentMetadata] = None

class FHIRBundle(BaseModel):
    resourceType: str = "Bundle"
    type: str
    entry: List[Dict[str, Any]]
    meta: Optional[Dict[str, Any]] = None

class TokenData(BaseModel):
    sub: str
    name: str
    abha_number: Optional[str] = None
    scope: List[str] = []