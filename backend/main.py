"""
Pipeline Runner for MedAtlas.
Runs the 4-agent validation pipeline for providers.
"""

import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from typing import Dict, Any, List, Optional
from backend.database import (
    get_all_providers,
    update_provider_after_validation,
    insert_discrepancy,
    log_event
)
from backend.agents import (
    DataValidationAgent,
    EnrichmentAgent,
    QAAgent,
    DirectoryManagementAgent
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_validation_pipeline(limit: int = 10000, offset: int = 0) -> Dict[str, Any]:
    """
    Run full validation pipeline for all providers.
    
    Pipeline flow for each provider:
    1. DataValidationAgent.run(provider) → validated_result
    2. EnrichmentAgent.run(provider, validated_result) → enriched_result
    3. QAAgent.run(original=provider, validated=validated_result, enriched=enriched_result) → qa_result
    4. DirectoryManagementAgent.run(provider, validated_result, enriched_result, qa_result) → final_provider
    5. Save final_provider to database with update_provider_after_validation()
    6. Insert all discrepancies using insert_discrepancy()
    
    Returns:
        {
            "status": "success",
            "validated": count of validated providers,
            "needs_review": count of providers needing review,
            "total": total providers processed
        }
    
    Note:
    - Handles missing fields gracefully (no crashes)
    - One provider failing does NOT stop the pipeline
    - All exceptions are logged and tracked
    """
    logger.info("=" * 80)
    logger.info("STARTING VALIDATION PIPELINE")
    logger.info("=" * 80)
    
    # Initialize agents
    validation_agent = DataValidationAgent()
    enrichment_agent = EnrichmentAgent()
    qa_agent = QAAgent()
    directory_agent = DirectoryManagementAgent()
    
    # Fetch all providers from database
    try:
        providers = get_all_providers(limit=limit, offset=offset)
        logger.info(f"Fetched {len(providers)} providers to validate")
    except Exception as e:
        logger.error(f"Failed to fetch providers from database: {e}")
        return {
            "status": "error",
            "message": f"Failed to fetch providers: {str(e)}",
            "validated": 0,
            "needs_review": 0,
            "total": 0
        }
    
    # Initialize counters
    validated_count = 0
    needs_review_count = 0
    total_processed = 0
    
    # Process each provider through the pipeline
    for provider in providers:
        provider_id = provider.get("id", "unknown")
        total_processed += 1
        
        try:
            logger.info(f"[{total_processed}/{len(providers)}] Processing provider ID: {provider_id}")
            
            # ========== STEP 1: DATA VALIDATION AGENT ==========
            logger.debug(f"Provider {provider_id}: Running DataValidationAgent...")
            validated_result = await validation_agent.run(provider)
            
            # Extract confidence scores for later use
            confidence_scores = validated_result.get("confidence_scores", {})
            
            # ========== STEP 2: ENRICHMENT AGENT ==========
            logger.debug(f"Provider {provider_id}: Running EnrichmentAgent...")
            enriched_result = await enrichment_agent.run(provider, validated_result)
            
            # ========== STEP 3: QA AGENT ==========
            logger.debug(f"Provider {provider_id}: Running QAAgent...")
            qa_result = await qa_agent.run(
                original=provider,
                validated_data=validated_result,
                enriched_data=enriched_result,
                confidence_scores=confidence_scores
            )
            
            # ========== STEP 4: DIRECTORY MANAGEMENT AGENT ==========
            logger.debug(f"Provider {provider_id}: Running DirectoryManagementAgent...")
            final_provider = directory_agent.run(
                provider=provider,
                validated_result=validated_result,
                enriched_result=enriched_result,
                qa_result=qa_result
            )
            
            # ========== STEP 5: PREPARE FINAL RECORD FOR DATABASE ==========
            confidence_score = qa_result.get("confidence_score", 0)
            risk_score = qa_result.get("risk_score", 0)
            qa_status = qa_result.get("status", "pending")
            discrepancy_count = qa_result.get("discrepancy_count", 0)
            
            # Determine validation status based on confidence
            if confidence_score >= 80:
                validation_status = "validated"
                validated_count += 1
            elif confidence_score >= 50:
                validation_status = "needs_review"
                needs_review_count += 1
            else:
                validation_status = "review_recommended"
                needs_review_count += 1
            
            # Prepare update dict for database
            provider_update = {
                "validation_status": validation_status,
                "confidence_score": confidence_score,
                "risk_score": risk_score,
                "discrepancy_count": discrepancy_count,
                "qa_status": qa_status,
                # Include merged fields from final profile
                "phone": final_provider.get("phone"),
                "address_line1": final_provider.get("address_line1"),
                "address_line2": final_provider.get("address_line2"),
                "city": final_provider.get("city"),
                "state": final_provider.get("state"),
                "zip_code": final_provider.get("zip_code"),
                "specialty": final_provider.get("specialty"),
                "website": final_provider.get("website"),
                "email": final_provider.get("email"),
                "first_name": final_provider.get("first_name"),
                "last_name": final_provider.get("last_name"),
            }
            
            # ========== STEP 6: SAVE TO DATABASE ==========
            logger.debug(f"Provider {provider_id}: Updating database...")
            update_provider_after_validation(provider_id, provider_update)
            
            # ========== STEP 7: INSERT DISCREPANCIES ==========
            discrepancies = qa_result.get("discrepancies", [])
            if discrepancies:
                logger.debug(f"Provider {provider_id}: Inserting {len(discrepancies)} discrepancies...")
                for discrepancy in discrepancies:
                    try:
                        discrepancy["provider_id"] = provider_id
                        insert_discrepancy(discrepancy)
                    except Exception as disc_error:
                        logger.error(f"Provider {provider_id}: Failed to insert discrepancy: {disc_error}")
            
            # Log success
            log_message = (
                f"Provider {provider_id} completed: "
                f"status={validation_status}, "
                f"confidence={confidence_score}%, "
                f"risk={risk_score}, "
                f"discrepancies={discrepancy_count}"
            )
            logger.info(log_message)
            
        except Exception as e:
            # ========== ERROR HANDLING ==========
            # One provider failure should NOT stop the pipeline
            logger.error(f"Provider {provider_id}: PIPELINE ERROR - {str(e)}", exc_info=True)
            
            # Try to mark as needs_review and save error state
            try:
                update_provider_after_validation(provider_id, {
                    "validation_status": "needs_review",
                    "confidence_score": 0,
                    "risk_score": 100
                })
                needs_review_count += 1
            except Exception as update_error:
                logger.error(f"Provider {provider_id}: Failed to mark as needs_review: {update_error}")
                needs_review_count += 1
            
            # Log the event for audit trail
            try:
                log_event("validation_error",
                         f"Pipeline error for provider {provider_id}: {str(e)}",
                         "ValidationPipeline",
                         provider_id)
            except:
                pass
    
    # ========== FINAL SUMMARY ==========
    logger.info("=" * 80)
    logger.info("VALIDATION PIPELINE COMPLETE")
    logger.info(f"Total Processed: {total_processed}")
    logger.info(f"Validated: {validated_count}")
    logger.info(f"Needs Review: {needs_review_count}")
    logger.info("=" * 80)
    
    return {
        "status": "success",
        "validated": validated_count,
        "needs_review": needs_review_count,
        "total": total_processed
    }

