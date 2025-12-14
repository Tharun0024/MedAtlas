"""
Directory Management Agent for MedAtlas.
Manages final provider profiles through auto-correction and data merging.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DirectoryManagementAgent:
    """Agent responsible for directory management and provider profile finalization."""
    
    def __init__(self):
        self.name = "DirectoryManagementAgent"
        self.high_confidence_threshold = 80
    
    def auto_correct_fields(self, provider: Dict[str, Any],
                           validated: Dict[str, Any],
                           enriched: Dict[str, Any],
                           confidence_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Auto-correct provider fields based on validation confidence.
        
        Strategy:
        - If a validated field has confidence > 80, replace the provider's original field.
        - If an enriched field exists and confidence isn't relevant, prefer enriched data 
          only if original is missing.
        - Only overwrite fields safely—never overwrite fields with low confidence.
        
        Args:
            provider: Original provider data from CSV
            validated: Validated data with field confidence scores
            enriched: Enriched data from web scraping/API calls
            confidence_scores: Dict of field -> confidence score (0-100)
            
        Returns:
            Provider dict with auto-corrected fields
        """
        corrected = provider.copy()
        
        # Define fields that can be auto-corrected
        correctable_fields = [
            'npi', 'phone', 'address_line1', 'address_line2', 'city', 'state', 'zip_code',
            'first_name', 'last_name', 'specialty', 'website', 'email', 'practice_name'
        ]
        
        for field in correctable_fields:
            field_confidence = confidence_scores.get(field, 0)
            
            # Safe auto-correction: only if confidence is high (>80)
            if field_confidence >= self.high_confidence_threshold:
                # Prefer validated data over enriched if both exist
                if validated.get(field) is not None and validated.get(field) != '':
                    corrected[field] = validated[field]
                    logger.debug(f"Auto-corrected {field} with validated data (confidence: {field_confidence})")
            
            # For enriched data: only use if original field is missing/empty
            elif enriched.get(field) is not None and enriched.get(field) != '':
                if corrected.get(field) is None or corrected.get(field) == '':
                    corrected[field] = enriched[field]
                    logger.debug(f"Filled missing {field} with enriched data")
        
        return corrected
    
    def merge_data(self, provider: Dict[str, Any],
                   validated: Dict[str, Any],
                   enriched: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge provider data with strict priority: validated > enriched > original.
        
        Creates a final_provider dict by merging all sources with the following priority:
        1. Validated data (most accurate, from validation agent)
        2. Enriched data (from web scraping/API calls)
        3. Original provider data (from CSV)
        
        Args:
            provider: Original provider data from CSV
            validated: Validated data from validation agent
            enriched: Enriched data from enrichment agent
            
        Returns:
            Final merged provider dict with all fields
        """
        # Start with original provider as base
        final_provider = provider.copy()
        
        # Define all possible fields to consider
        all_fields = set()
        all_fields.update(provider.keys())
        all_fields.update(validated.keys())
        all_fields.update(enriched.keys())
        
        # Apply merge priority: validated > enriched > original
        for field in all_fields:
            # Skip metadata/system fields
            if field in ['id', 'created_at', 'updated_at', 'confidence_scores', 
                        'npi_valid', 'phone_valid', 'validation_status']:
                continue
            
            # Try validated data first
            if field in validated and validated[field] is not None and validated[field] != '':
                final_provider[field] = validated[field]
            # Then enriched data if original is missing
            elif field in enriched and enriched[field] is not None and enriched[field] != '':
                if final_provider.get(field) is None or final_provider.get(field) == '':
                    final_provider[field] = enriched[field]
            # Original provider data is already in final_provider as base
        
        return final_provider
    
    def run(self, provider: Dict[str, Any],
            validated_result: Dict[str, Any],
            enriched_result: Dict[str, Any],
            qa_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full directory management workflow.
        
        Takes raw provider data and results from validation/enrichment/QA agents,
        applies auto-corrections, merges data, and returns final provider profile.
        
        Args:
            provider: Original provider data from CSV
            validated_result: Result from validation agent (may include confidence_scores)
            enriched_result: Result from enrichment agent
            qa_result: Result from QA agent (may include overall confidence)
            
        Returns:
            final_provider dict ready for database update, includes:
            - All merged fields (validated > enriched > original)
            - Metadata: confidence_score, risk_score, validation_status
            
        Raises:
            Gracefully handles missing fields and avoids crashes
        """
        try:
            # Extract confidence scores safely
            confidence_scores = validated_result.get('confidence_scores', {}) if validated_result else {}
            
            # Extract data dicts safely (handle None inputs)
            validated_data = validated_result if validated_result else {}
            enriched_data = enriched_result if enriched_result else {}
            qa_data = qa_result if qa_result else {}
            
            logger.info(f"DirectoryManagementAgent: Processing provider {provider.get('id', 'unknown')}")
            
            # Step 1: Auto-correct high-confidence fields
            corrected_provider = self.auto_correct_fields(
                provider,
                validated_data,
                enriched_data,
                confidence_scores
            )
            
            # Step 2: Merge all data with priority
            final_provider = self.merge_data(
                corrected_provider,
                validated_data,
                enriched_data
            )
            
            # Step 3: Add QA metadata
            final_provider['confidence_score'] = qa_data.get('confidence_score', 0)
            final_provider['risk_score'] = qa_data.get('risk_score', 0)
            final_provider['validation_status'] = qa_data.get('status', 'pending')
            # final_provider['discrepancy_count'] = qa_data.get('discrepancy_count', 0)
            # final_provider['last_updated'] = qa_data.get('timestamp', '')
            
            logger.info(f"DirectoryManagementAgent: Successfully finalized provider "
                       f"{provider.get('id', 'unknown')} with confidence "
                       f"{final_provider.get('confidence_score', 0)}")
            
            return final_provider
            
        except Exception as e:
            logger.error(f"DirectoryManagementAgent: Error processing provider {provider.get('id', 'unknown')}: {str(e)}")
            # Return original provider if processing fails
            return provider
