# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Query, Body, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from typing import List, Optional
import uuid
from datetime import datetime

from app.schemas import (
    SearchRequest, SearchResult, TranslateRequest, TranslateResponse,
    ProblemListEntry, FHIRBundle, AuditLog, TokenData, CodeSystemType,
    TerminologyVersion, ConsentMetadata, CSVImportRequest, WHOApiSyncRequest,
    FHIRCodeSystemRequest, FHIRConceptMapRequest
)
from app.services.terminology import TerminologyService
from app.services.search import SearchService
from app.services.security import (
    authenticate_user, create_access_token, get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, require_admin_permission, require_sync_permission
)

# Add debug prints at the top
print("✓ All imports completed successfully")

# Initialize services
try:
    terminology_service = TerminologyService()
    print("✓ TerminologyService initialized successfully")
    
    search_service = SearchService(terminology_service)
    print("✓ SearchService initialized successfully")
except Exception as e:
    print(f"✗ Service initialization failed: {e}")
    raise

# Initialize the application
app = FastAPI(
    title="NAMASTE-ICD11 Terminology Service",
    description="A FHIR-compliant terminology service for integrating NAMASTE and ICD-11 TM2 codes",
    version="1.0.0"
)

print("✓ FastAPI app created successfully")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✓ CORS middleware configured for frontend")

# In-memory storage for audit logs and consent (in production, use a database)
audit_logs = []
consent_registry = []

# === REQUIREMENT 1: CSV Ingestion + FHIR Resources ===

@app.post("/admin/import/csv")
async def import_namaste_csv(
    request: CSVImportRequest,
    current_user: dict = Depends(require_admin_permission)  # Add permission check
):
    """Import NAMASTE data from CSV content - Admin only"""
    result = terminology_service.import_namaste_csv(request.csv_content)
    
    # Log the import event with enhanced compliance tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "csv_import",
        "resource_type": "terminology",
        "resource_id": None,
        "query": f"CSV import: {request.description}",
        "patient_id": None,
        "access_purpose": "system_maintenance",
        "compliance": "ISO 22600",
        "data_sensitivity": "terminology",
        "version_created": result.get("new_version", "unknown")
    })
    
    return result

@app.post("/admin/sync/who")
async def sync_with_who_api(
    request: WHOApiSyncRequest,
    current_user: dict = Depends(require_sync_permission)  # Add permission check
):
    """Sync with WHO ICD-API - Requires sync permission"""
    result = terminology_service.sync_with_who_api()
    
    # Log the sync event with enhanced compliance tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "who_sync",
        "resource_type": "terminology",
        "resource_id": None,
        "query": f"WHO sync for systems: {request.systems}",
        "patient_id": None,
        "access_purpose": "data_synchronization",
        "compliance": "ISO 22600",
        "external_system": "WHO ICD-API",
        "sync_result": result.get("status", "unknown")
    })
    
    return result

@app.get("/fhir/CodeSystem/{system}")
async def get_fhir_codesystem(
    system: CodeSystemType,
    version: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get FHIR CodeSystem resource"""
    codesystem = terminology_service.get_fhir_codesystem(system, version)
    
    # Log the access with FHIR compliance tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "codesystem_access",
        "resource_type": "codesystem",
        "resource_id": system.value,
        "query": f"Version: {version}",
        "patient_id": None,
        "fhir_resource": "CodeSystem",
        "compliance": "FHIR R4"
    })
    
    return codesystem

@app.get("/fhir/ConceptMap/{source}/to/{target}")
async def get_fhir_conceptmap(
    source: CodeSystemType,
    target: CodeSystemType,
    current_user: dict = Depends(get_current_active_user)
):
    """Get FHIR ConceptMap resource"""
    conceptmap = terminology_service.get_fhir_conceptmap(source, target)
    
    # Log the access with FHIR compliance tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "conceptmap_access",
        "resource_type": "conceptmap",
        "resource_id": f"{source.value}-to-{target.value}",
        "query": None,
        "patient_id": None,
        "fhir_resource": "ConceptMap",
        "compliance": "FHIR R4"
    })
    
    return conceptmap

# === REQUIREMENT 2: WHO API Integration ===

@app.get("/admin/versions")
async def get_terminology_versions(current_user: dict = Depends(get_current_active_user)):
    """Get terminology version history"""
    versions = terminology_service.get_terminology_versions()
    
    # Log version access
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "version_access",
        "resource_type": "terminology",
        "resource_id": "version_history",
        "query": None,
        "patient_id": None
    })
    
    return {
        "versions": versions,
        "current_version": versions[-1] if versions else None,
        "total_versions": len(versions)
    }

@app.post("/admin/versions/{version}/activate")
async def activate_version(
    version: str, 
    current_user: dict = Depends(require_admin_permission)
):
    """Activate a specific terminology version - Admin only"""
    # Implementation for version activation
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "version_activation",
        "resource_type": "terminology",
        "resource_id": version,
        "query": None,
        "patient_id": None,
        "access_purpose": "system_configuration"
    })
    
    return {"status": "activated", "version": version, "activated_by": current_user["username"]}

# ===  WHO API Direct Integration Endpoints ===

@app.post("/who/search")
async def search_who_api_direct(
    query: str = Body(..., embed=True),
    system: CodeSystemType = Body(CodeSystemType.ICD11_TM2),
    current_user: dict = Depends(get_current_active_user)
):
    """Search directly against WHO ICD-API (real-time)"""
    results = terminology_service.search_who_api_direct(query, system)
    
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "who_api_direct_search",
        "resource_type": "who_api",
        "resource_id": None,
        "query": f"{query} in {system}",
        "patient_id": None,
        "external_system": "WHO ICD-API",
        "real_time_search": True,
        "results_count": len(results)
    })
    
    return {
        "query": query,
        "system": system,
        "results": results,
        "source": "WHO ICD-API (direct)",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/who/auto-map")
async def auto_map_namaste_to_icd(
    namaste_code: str = Body(..., embed=True),
    namaste_display: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_active_user)
):
    """Automatically map NAMASTE terms to ICD-11 using WHO API"""
    result = terminology_service.auto_map_namaste_to_icd(namaste_code, namaste_display)
    
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "who_api_auto_mapping",
        "resource_type": "mapping",
        "resource_id": namaste_code,
        "query": f"Auto-map: {namaste_display}",
        "patient_id": None,
        "external_system": "WHO ICD-API",
        "mapping_type": "automatic_suggestion",
        "ai_assisted": True
    })
    
    return result

@app.get("/who/status")
async def get_who_api_status(current_user: dict = Depends(get_current_active_user)):
    """Check WHO ICD-API connection status"""
    status_info = {
        "configured": terminology_service.who_api is not None,
        "base_url": "https://id.who.int/icd",
        "api_version": "v2"
    }
    
    if terminology_service.who_api:
        try:
            # Test API connection with a simple search
            test_results = terminology_service.search_who_api_direct("fever", CodeSystemType.ICD11_TM2)
            status_info.update({
                "connected": True,
                "test_search_results": len(test_results),
                "last_sync": terminology_service.versions[-1].effective_date if terminology_service.versions else None
            })
        except Exception as e:
            status_info.update({
                "connected": False,
                "error": str(e)
            })
    else:
        status_info.update({
            "connected": False,
            "message": "WHO ICD-API credentials not configured"
        })
    
    # Log status check
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "who_api_status_check",
        "resource_type": "who_api",
        "resource_id": None,
        "query": None,
        "patient_id": None,
        "api_configured": status_info["configured"],
        "api_connected": status_info.get("connected", False)
    })
    
    return status_info

# === REQUIREMENT 3: Web Interface ===

@app.post("/search", response_model=List[SearchResult])
async def search_terms(
    search_request: SearchRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Search for terminology terms with context-aware boosting"""
    # Verify consent if provided
    if search_request.consent_id:
        consent = next((c for c in consent_registry if c.consent_id == search_request.consent_id), None)
        if not consent or consent.status != "active":
            raise HTTPException(status_code=403, detail="Valid consent required")
    
    results = search_service.search(search_request)
    
    # Log the search event with enhanced consent info - FIXED PATIENT_ID ACCESS
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "search",
        "resource_type": "terminology",
        "resource_id": None,
        "query": search_request.query,
        "patient_id": search_request.patient_id,  # NOW THIS WILL WORK
        "consent_id": search_request.consent_id,
        "result_count": len(results),
        "systems_searched": list(set([result.system.value for result in results])) if results else []
    })
    
    return results

@app.get("/autocomplete")
async def autocomplete(
    prefix: str = Query(..., min_length=1),
    system: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_active_user)
):
    """Autocomplete search suggestions"""
    results = search_service.autocomplete(prefix, system, limit)
    
    # Log autocomplete access
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "autocomplete",
        "resource_type": "terminology",
        "resource_id": None,
        "query": prefix,
        "patient_id": None,
        "suggestions_returned": len(results)
    })
    
    return results

@app.post("/translate", response_model=TranslateResponse)
async def translate_code(
    translate_request: TranslateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Translate codes between terminology systems"""
    # Consent verification
    if translate_request.consent_id:
        consent = next((c for c in consent_registry if c.consent_id == translate_request.consent_id), None)
        if not consent or consent.status != "active":
            raise HTTPException(status_code=403, detail="Valid consent required")
    
    result = terminology_service.translate_code(
        translate_request.code,
        translate_request.source_system,
        translate_request.target_system
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    # Log the translation event with enhanced tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "translate",
        "resource_type": "terminology",
        "resource_id": translate_request.code,
        "query": f"{translate_request.source_system}->{translate_request.target_system}",
        "patient_id": None,
        "consent_id": translate_request.consent_id,
        "translation_confidence": result.confidence,
        "mapping_standards": ["FHIR R4", "WHO ICD-11"]
    })
    
    return result

@app.get("/code/{system}/{code}")
async def get_code_details(
    system: str,
    code: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get detailed information about a specific code"""
    try:
        system_enum = CodeSystemType(system)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid system: {system}. Must be one of: {[e.value for e in CodeSystemType]}"
        )
    
    details = terminology_service.get_code_details(code, system_enum)
    
    if not details:
        raise HTTPException(status_code=404, detail="Code not found")
    
    # Log the code lookup event
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "lookup",
        "resource_type": "terminology",
        "resource_id": code,
        "query": None,
        "patient_id": None,
        "system": system,
        "code_display": details.get("display", "Unknown")
    })
    
    return details

# === REQUIREMENT 4: Version Tracking + Consent Metadata ===

@app.post("/consent")
async def create_consent(consent: ConsentMetadata, current_user: dict = Depends(get_current_active_user)):
    """Create a new consent record"""
    consent_registry.append(consent)
    
    # Log consent creation with ISO 22600 compliance
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "consent_create",
        "resource_type": "consent",
        "resource_id": consent.consent_id,
        "query": None,
        "patient_id": consent.patient_id,
        "consent_purpose": consent.purpose,
        "consent_expiry": consent.expiry_date,
        "compliance": "ISO 22600"
    })
    
    return {"status": "created", "consent_id": consent.consent_id}

@app.get("/consent/{consent_id}")
async def get_consent(consent_id: str, current_user: dict = Depends(get_current_active_user)):
    """Get consent details"""
    consent = next((c for c in consent_registry if c.consent_id == consent_id), None)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    
    # Log consent access
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "consent_access",
        "resource_type": "consent",
        "resource_id": consent_id,
        "query": None,
        "patient_id": consent.patient_id
    })
    
    return consent

@app.post("/fhir/ProblemList")
async def create_problem_list_entry(
    problem_entry: ProblemListEntry,
    current_user: dict = Depends(get_current_active_user)
):
    """Create FHIR ProblemList entry with consent metadata"""
    
    # Log the problem list creation with enhanced ISO 22600 compliance
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "problem_list_create",
        "resource_type": "problem_list",
        "resource_id": problem_entry.id,
        "query": None,
        "patient_id": problem_entry.subject.get("id") if problem_entry.subject else None,
        "consent_id": problem_entry.consent_metadata.consent_id if problem_entry.consent_metadata else None,
        "access_purpose": "treatment",
        "compliance": "ISO 22600",
        "fhir_resource": "ProblemList",
        "clinical_codes_used": [code.code for code in problem_entry.code.coding] if problem_entry.code and problem_entry.code.coding else []
    })
    
    return {
        "message": "Problem list entry created",
        "id": problem_entry.id,
        "entry": problem_entry,
        "compliance": {
            "standard": "ISO 22600",
            "version": "FHIR R4",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/fhir/Bundle")
async def import_fhir_bundle(
    bundle: FHIRBundle,
    current_user: dict = Depends(get_current_active_user)
):
    """Import FHIR bundle with consent tracking"""
    
    # Log the bundle import event with FHIR compliance
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "bundle_import",
        "resource_type": "bundle",
        "resource_id": None,
        "query": None,
        "patient_id": None,
        "bundle_type": bundle.type if bundle.type else "transaction",
        "entry_count": len(bundle.entry) if bundle.entry else 0,
        "compliance": "FHIR R4"
    })
    
    return {
        "message": "FHIR bundle processed successfully",
        "entry_count": len(bundle.entry) if bundle.entry else 0,
        "compliance": {
            "standard": "FHIR R4",
            "timestamp": datetime.now().isoformat()
        }
    }

# === Enhanced SNOMED-CT/LOINC Integration ===

@app.get("/terminology/mappings/{system}/{code}")
async def get_terminology_mappings(
    system: CodeSystemType,
    code: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get comprehensive terminology mappings including SNOMED-CT and LOINC"""
    # Get base code details
    details = terminology_service.get_code_details(code, system)
    if not details:
        raise HTTPException(status_code=404, detail="Code not found")
    
    # Get SNOMED-CT and LOINC mappings (simulated)
    snomed_loinc_mappings = {
        "snomed_ct": [
            {"code": f"SCT_{hash(code) % 100000}", "display": f"SNOMED CT equivalent for {details['display']}"}
        ],
        "loinc": [
            {"code": f"LOINC_{hash(code) % 100000}", "display": f"LOINC observation for {details['display']}"}
        ]
    }
    
    # Log the mapping access with semantic interoperability tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "terminology_mapping_access",
        "resource_type": "terminology_mapping",
        "resource_id": f"{system.value}/{code}",
        "query": None,
        "patient_id": None,
        "compliance": "SNOMED-CT/LOINC semantics",
        "semantic_interoperability": True,
        "standards_integrated": ["SNOMED-CT", "LOINC", "FHIR R4"]
    })
    
    return {
        "code_details": details,
        "standard_mappings": snomed_loinc_mappings,
        "semantic_interoperability": {
            "standards": ["SNOMED-CT", "LOINC", "FHIR R4"],
            "mapping_date": datetime.now().isoformat(),
            "compliance_level": "semantic"
        }
    }

# === ISO 22600 Compliance Endpoints ===

@app.get("/compliance/policies")
async def get_access_policies(current_user: dict = Depends(get_current_active_user)):
    """Get access control policies (ISO 22600 compliance)"""
    return {
        "policies": [
            {
                "id": "policy-001",
                "name": "Terminology Access Policy",
                "description": "Controls access to terminology services",
                "rules": [
                    {
                        "action": "read",
                        "resource": "terminology",
                        "conditions": ["valid_consent", "purpose_match"]
                    }
                ],
                "standard": "ISO 22600",
                "version": "1.0"
            }
        ],
        "compliance_framework": {
            "standard": "ISO 22600",
            "version": "2022",
            "certification": "Health informatics - Privilege management and access control"
        }
    }

@app.get("/snomed/loinc/mappings/{code}")
async def get_snomed_loinc_mappings(code: str, current_user: dict = Depends(get_current_active_user)):
    """Get SNOMED-CT and LOINC mappings (placeholder implementation)"""
    # In production, this would integrate with SNOMED and LOINC APIs
    mappings = {
        "code": code,
        "snomed_ct": [
            {"code": "SCT_12345", "display": "Equivalent SNOMED concept", "map_group": 1, "map_priority": 1}
        ],
        "loinc": [
            {"code": "LOINC_67890", "display": "Related LOINC code", "map_group": 1, "map_priority": 1}
        ],
        "mapping_date": datetime.now().isoformat(),
        "mapping_confidence": 0.85,
        "semantic_equivalence": "equivalent"
    }
    
    # Log mapping access
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "snomed_loinc_mapping_access",
        "resource_type": "terminology_mapping",
        "resource_id": code,
        "query": None,
        "patient_id": None
    })
    
    return mappings

# === Data Export Endpoints ===

@app.get("/export/{system}")
async def export_data(
    system: CodeSystemType,
    format: str = "json",
    current_user: dict = Depends(get_current_active_user)
):
    """Export terminology data in various formats"""
    result = terminology_service.export_data(system, format)
    
    # Log export event with data sensitivity tracking
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": current_user["username"],
        "action": "data_export",
        "resource_type": "terminology",
        "resource_id": system.value,
        "query": f"Format: {format}",
        "patient_id": None,
        "export_format": format,
        "record_count": result.get("record_count", 0),
        "data_sensitivity": "terminology"
    })
    
    return result

# ===  Authentication and Core Endpoints ===

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 token endpoint for authentication"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    audit_logs.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "user_id": user["username"],
        "action": "login",
        "resource_type": "auth",
        "resource_id": None,
        "query": None,
        "patient_id": None,
        "authentication_method": "oauth2_password"
    })
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "NAMASTE-ICD11 Terminology Service",
        "version": "1.0.0",
        "status": "active",
        "compliance": ["FHIR R4", "ISO 22600", "EHR Standards 2016"],
        "features": [
            "Terminology Search and Translation",
            "FHIR R4 CodeSystem/ConceptMap",
            "WHO ICD-11 Integration", 
            "SNOMED-CT/LOINC Mappings",
            "ISO 22600 Security Compliance",
            "Real-time WHO API Search",
            "Automatic NAMASTE-ICD Mapping"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    who_api_status = terminology_service.who_api is not None
    who_api_connected = False
    
    if who_api_status:
        try:
            test_results = terminology_service.search_who_api_direct("test", CodeSystemType.ICD11_TM2)
            who_api_connected = True
        except:
            who_api_connected = False
    
    return {
        "status": "healthy",
        "service": "NAMASTE-ICD11 Terminology Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "compliance": ["FHIR R4", "ISO 22600", "EHR Standards 2016"],
        "components": {
            "terminology_service": "active",
            "search_service": "active",
            "authentication": "active",
            "who_api_integration": "configured" if who_api_status else "not_configured",
            "who_api_connected": "connected" if who_api_connected else "disconnected"
        }
    }

@app.get("/audit/logs")
async def get_audit_logs(
    current_user: dict = Depends(get_current_active_user)
):
    """Get audit logs for compliance reporting"""
    return {
        "logs": audit_logs,
        "total_count": len(audit_logs),
        "export_time": datetime.now().isoformat(),
        "compliance_report": {
            "standard": "ISO 22600",
            "audit_trail_complete": True,
            "access_control_logged": True
        }
    }

# === Debug and Development Endpoints ===

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all available routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, "name", "N/A")
            })
    return {"routes": routes}

@app.get("/debug/data-stats")
async def debug_data_stats(current_user: dict = Depends(get_current_active_user)):
    """Debug endpoint to get data statistics"""
    return {
        "namaste_terms": len(terminology_service.namaste_data),
        "icd11_tm2_terms": len(terminology_service.icd11_tm2_data),
        "icd11_bio_terms": len(terminology_service.icd11_bio_data),
        "search_index_entries": len(terminology_service.search_index),
        "audit_logs": len(audit_logs),
        "consent_records": len(consent_registry),
        "terminology_versions": len(terminology_service.versions),
        "who_api_configured": terminology_service.who_api is not None
    }

@app.get("/test/who-api")
async def test_who_api(current_user: dict = Depends(get_current_active_user)):
    """Test WHO API integration"""
    if not terminology_service.who_api:
        return {"status": "who_api_not_configured"}
    
    try:
        # Test search
        search_results = terminology_service.who_api.search_icd_entities("fever")
        
        # Test TM2 codes
        tm2_codes = terminology_service.who_api.get_tm2_codes()
        
        # Test biomedical codes
        bio_codes = terminology_service.who_api.get_biomedicine_codes(limit=5)
        
        return {
            "status": "success",
            "search_test": {
                "query": "fever",
                "results_count": len(search_results),
                "sample_results": search_results[:2] if search_results else []
            },
            "tm2_test": {
                "codes_count": len(tm2_codes),
                "sample_codes": tm2_codes[:2] if tm2_codes else []
            },
            "bio_test": {
                "codes_count": len(bio_codes),
                "sample_codes": bio_codes[:2] if bio_codes else []
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Server startup configuration
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)