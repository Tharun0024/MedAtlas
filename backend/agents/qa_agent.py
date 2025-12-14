"""
QA Agent for MedAtlas.
Compares data sources and detects inconsistencies.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.database import insert_discrepancy, log_event
from backend.database import update_provider_after_validation


logger = logging.getLogger(__name__)


class QAAgent:
    """Agent responsible for quality assurance and discrepancy detection."""
    
    def __init__(self):
        self.name = "QAAgent"
    
    async def run(self, original: Dict[str, Any], 
                  validated_data: Dict[str, Any],
                  enriched_data: Dict[str, Any],
                  confidence_scores: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Main QA analysis method.
        
        Args:
            original: Original CSV data
            validated_data: Validated data from validation agent
            enriched_data: Enriched data from enrichment agent
            confidence_scores: Dictionary of confidence scores by field
            
        Returns:
            Dictionary with confidence score, status, and discrepancies
        """
        log_event("qa_start", 
                 f"Starting QA analysis for provider {original.get('npi')}", 
                 self.name, original.get('id'))
        
        # Generate discrepancies by comparing sources
        discrepancies = await self.compare_sources(original, validated_data, enriched_data)
        
        # Calculate final confidence from confidence scores
        if confidence_scores is None:
            confidence_scores = {}

        
        final_confidence = await self.calculate_confidence(confidence_scores)
        
        # Determine status based on confidence
        status = await self.determine_status(final_confidence)

        update_provider_after_validation(original.get("id"),
    {
        "validation_status": status,
        "confidence_score": final_confidence,
        "validated_data": validated_data,
        "enriched_data": enriched_data
    }
)
        
        # Insert discrepancies into database
        discrepancy_ids = []
        for disc in discrepancies:
            try:
                disc_id = insert_discrepancy({
                    "provider_id": original.get('id'),
                    "field_name": disc.get("field"),
                    "csv_value": str(disc.get("original", "")),
                    "api_value": str(disc.get("updated", "")),
                    "scraped_value": None,
                    "final_value": str(disc.get("updated", "")),
                    "confidence": 80,
                    "risk_level": "high" if disc.get("field") in ['npi', 'license_number'] else "medium",
                    "status": "open",
                    "notes": f"Value mismatch: {disc.get('original')} → {disc.get('updated')}"
                })
                discrepancy_ids.append(disc_id)
            except Exception as e:
                logger.error(f"Error inserting discrepancy: {e}")
        
        result = {
            "confidence_score": final_confidence,
            "status": status,
            "discrepancies": discrepancies,
            "discrepancy_count": len(discrepancies)
        }
        
        log_event("qa_complete", 
                 f"QA analysis complete. Confidence: {final_confidence}, Status: {status}, Discrepancies: {len(discrepancies)}", 
                 self.name, original.get('id'))
        
        return result
    
    async def compare_sources(self, original: Dict[str, Any], 
                             validated: Dict[str, Any],
                             enriched: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compare field-by-field across original, validated, and enriched data.
        Generate discrepancy entries for mismatches.
        
        Args:
            original: Original CSV data
            validated: Validated data from API
            enriched: Enriched data from scraping/OCR
            
        Returns:
            List of discrepancy dictionaries
        """
        discrepancies = []
        
        # Fields to compare
        comparison_fields = [
            'npi', 'first_name', 'last_name', 'phone', 'address_line1',
            'city', 'state', 'zip_code', 'specialty', 'license_number',
            'email', 'practice_name', 'organization_name'
        ]
        
        for field in comparison_fields:
            try:
                original_value = original.get(field)
                validated_value = validated.get(field)
                enriched_value = enriched.get(field)
                
                # Skip if all values are None or empty
                if not original_value and not validated_value and not enriched_value:
                    continue
                
                # Determine the "updated" value (prefer validated > enriched > original)
                updated_value = validated_value or enriched_value or original_value
                
                # Compare original vs updated
                if original_value and updated_value:
                    # Normalize for comparison (strip, lower case)
                    orig_normalized = str(original_value).strip().lower()
                    updated_normalized = str(updated_value).strip().lower()
                    
                    # If values differ, create discrepancy
                    if orig_normalized != updated_normalized:
                        discrepancy = {
                            "field": field,
                            "original": str(original_value),
                            "updated": str(updated_value),
                            "source": "api" if validated_value else "scraped" if enriched_value else "original"
                        }
                        discrepancies.append(discrepancy)
            except Exception as e:
                logger.error(f"Error comparing field {field}: {e}")
                continue
        
        return discrepancies
    
    async def calculate_confidence(self, conf_scores: Dict[str, int]) -> int:
     
        if not conf_scores:
            return 0
        
        # Filter out None/zero scores and calculate average
        valid_scores = [score for score in conf_scores.values() if score is not None and score > 0]
        
        if not valid_scores:
            return 0
        
        # Calculate average
        average = sum(valid_scores) / len(valid_scores)
        
        # Round to integer
        return int(round(average))
    
    async def determine_status(self, confidence: int) -> str:

        if confidence < 50:
            return "needs_review"
        elif confidence < 80:
            return "review_recommended"
        else:
            return "validated"
    
    async def analyze_provider(self, csv_data: Dict[str, Any], 
                              validated_data: Dict[str, Any],
                              enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        Calls run() with appropriate parameters.
        
        Args:
            csv_data: Original CSV data
            validated_data: Validated data from validation agent
            enriched_data: Enriched data from enrichment agent
            
        Returns:
            Dictionary with analysis results
        """
        confidence_scores = validated_data.get("confidence_scores", {})
        
        return await self.run(
            original=csv_data,
            validated_data=validated_data,
            enriched_data=enriched_data,
            confidence_scores=confidence_scores
        )

