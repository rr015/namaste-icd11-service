# app/services/search.py
from typing import List, Dict, Optional
import redis
import json
from app.schemas import SearchRequest, SearchResult
from app.services.terminology import TerminologyService
import logging

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, terminology_service: TerminologyService):
        self.terminology_service = terminology_service
        # Initialize Redis client for caching with error handling
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()  # Test connection
            logger.info("Redis connected successfully")
        except redis.ConnectionError:
            logger.warning("Redis not available, running without cache")
            self.redis_client = None
    
    def search(self, search_request: SearchRequest) -> List[SearchResult]:
        # Create cache key
        cache_key = f"search:{search_request.query}:{search_request.system}:{search_request.patient_age}:{search_request.patient_gender}:{search_request.limit}"
        
        # Check cache first if Redis is available
        if self.redis_client:
            try:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return [SearchResult(**item) for item in json.loads(cached_result)]
            except redis.RedisError:
                logger.warning("Redis error, continuing without cache")
        
        # Perform search
        results = self.terminology_service.search_terms(
            query=search_request.query,
            system=search_request.system,
            patient_age=search_request.patient_age,
            patient_gender=search_request.patient_gender,
            existing_conditions=search_request.existing_conditions,
            symptoms=search_request.symptoms,
            limit=search_request.limit
        )
        
        # Cache the results for 1 hour if Redis is available
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, 3600, json.dumps([result.dict() for result in results]))
            except redis.RedisError:
                logger.warning("Redis error, could not cache results")
        
        return results
    
    def autocomplete(self, prefix: str, system: Optional[str] = None, limit: int = 5) -> List[str]:
        # Create cache key
        cache_key = f"autocomplete:{prefix}:{system}:{limit}"
        
        # Check cache first if Redis is available
        if self.redis_client:
            try:
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
            except redis.RedisError:
                logger.warning("Redis error, continuing without cache")
        
        # Get suggestions
        suggestions = []
        for item in self.terminology_service.search_index:
            if system and item["system"].value != system:
                continue
            
            if item["display"].lower().startswith(prefix.lower()):
                suggestions.append(item["display"])
            
            for synonym in item.get("synonyms", []):
                if synonym.lower().startswith(prefix.lower()):
                    suggestions.append(synonym)
            
            if len(suggestions) >= limit * 2:  # Get more than needed to filter
                break
        
        # Deduplicate and limit
        unique_suggestions = list(set(suggestions))[:limit]
        
        # Cache the results for 1 hour if Redis is available
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, 3600, json.dumps(unique_suggestions))
            except redis.RedisError:
                logger.warning("Redis error, could not cache results")
        
        return unique_suggestions