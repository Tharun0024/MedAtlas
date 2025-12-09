"""
Pipeline Orchestrator for MedAtlas.
Runs the 4-agent AI pipeline for provider data validation and enrichment.
"""

import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from backend.agents import (
    DataValidationAgent,
    EnrichmentAgent,
    QAAgent,
    DirectoryManagementAgent
)
from backend.database import (
    get_all_providers,
    get_provider,
    insert_provider,
    log_event
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the 4-agent pipeline."""
    
    def __init__(self):
        self.validation_agent = DataValidationAgent()
        self.enrichment_agent = EnrichmentAgent()
        self.qa_agent = QAAgent()
        self.directory_agent = DirectoryManagementAgent()
    
    async def process_provider(self, provider_id: int, pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single provider through the pipeline.
        
        Args:
            provider_id: Provider ID
            pdf_path: Optional path to PDF file
            
        Returns:
            Final processing results
        """
        logger.info(f"Processing provider {provider_id}")
        
        # Get provider data
        provider = get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        
        # Step 1: Data Validation Agent
        logger.info(f"Step 1: Validating provider {provider_id}")
        validation_results = await self.validation_agent.validate_provider(provider)
        validated_data = validation_results.get("validated_data", provider.copy())
        
        # Step 2: Enrichment Agent
        logger.info(f"Step 2: Enriching provider {provider_id}")
        enriched_data = await self.enrichment_agent.enrich_provider(
            validated_data,
            pdf_path=pdf_path
        )
        
        # Step 3: QA Agent
        logger.info(f"Step 3: QA analysis for provider {provider_id}")
        qa_results = await self.qa_agent.analyze_provider(
            csv_data=provider,
            validated_data=validated_data,
            enriched_data=enriched_data
        )
        
        # Step 4: Directory Management Agent
        logger.info(f"Step 4: Finalizing provider {provider_id}")
        final_results = await self.directory_agent.finalize_provider(
            provider_id=provider_id,
            validated_data=validated_data,
            enriched_data=enriched_data,
            qa_results=qa_results
        )
        
        logger.info(f"Completed processing provider {provider_id}. "
                   f"Confidence: {final_results['confidence_score']}, "
                   f"Risk: {final_results['risk_score']}")
        
        return {
            "provider_id": provider_id,
            "validation_results": validation_results,
            "enriched_data": enriched_data,
            "qa_results": qa_results,
            "final_results": final_results
        }
    
    async def process_all_providers(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process all providers through the pipeline.
        
        Args:
            limit: Optional limit on number of providers to process
            
        Returns:
            List of processing results
        """
        providers = get_all_providers(limit=limit or 1000)
        results = []
        
        logger.info(f"Processing {len(providers)} providers")
        
        # Process providers sequentially (can be parallelized if needed)
        for provider in providers:
            try:
                result = await self.process_provider(provider["id"])
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing provider {provider['id']}: {e}")
                results.append({
                    "provider_id": provider["id"],
                    "error": str(e)
                })
        
        return results
    
    async def process_from_csv(self, csv_path: str, pdf_paths: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Process providers from a CSV file.
        
        Args:
            csv_path: Path to CSV file
            pdf_paths: Optional dictionary mapping NPI to PDF path
            
        Returns:
            List of processing results
        """
        # Load CSV
        df = pd.read_csv(csv_path)
        
        results = []
        
        for _, row in df.iterrows():
            # Create provider data
            provider_data = {
                "npi": str(row.get("NPI", "")).strip() if pd.notna(row.get("NPI")) else None,
                "first_name": str(row.get("First Name", "")).strip() if pd.notna(row.get("First Name")) else None,
                "last_name": str(row.get("Last Name", "")).strip() if pd.notna(row.get("Last Name")) else None,
                "organization_name": str(row.get("Organization Name", "")).strip() if pd.notna(row.get("Organization Name")) else None,
                "provider_type": str(row.get("Provider Type", "")).strip() if pd.notna(row.get("Provider Type")) else None,
                "specialty": str(row.get("Specialty", "")).strip() if pd.notna(row.get("Specialty")) else None,
                "address_line1": str(row.get("Address Line 1", "")).strip() if pd.notna(row.get("Address Line 1")) else None,
                "address_line2": str(row.get("Address Line 2", "")).strip() if pd.notna(row.get("Address Line 2")) else None,
                "city": str(row.get("City", "")).strip() if pd.notna(row.get("City")) else None,
                "state": str(row.get("State", "")).strip() if pd.notna(row.get("State")) else None,
                "zip_code": str(row.get("ZIP Code", "")).strip() if pd.notna(row.get("ZIP Code")) else None,
                "phone": str(row.get("Phone", "")).strip() if pd.notna(row.get("Phone")) else None,
                "email": str(row.get("Email", "")).strip() if pd.notna(row.get("Email")) else None,
                "website": str(row.get("Website", "")).strip() if pd.notna(row.get("Website")) else None,
                "license_number": str(row.get("License Number", "")).strip() if pd.notna(row.get("License Number")) else None,
                "license_state": str(row.get("License State", "")).strip() if pd.notna(row.get("License State")) else None,
                "practice_name": str(row.get("Practice Name", "")).strip() if pd.notna(row.get("Practice Name")) else None,
                "source_file": csv_path,
                "raw_data": row.to_dict()
            }
            
            # Insert provider
            provider_id = insert_provider(provider_data)
            
            # Get PDF path if available
            pdf_path = None
            if pdf_paths and provider_data["npi"]:
                pdf_path = pdf_paths.get(provider_data["npi"])
            
            # Process through pipeline
            try:
                result = await self.process_provider(provider_id, pdf_path=pdf_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing provider {provider_id}: {e}")
                results.append({
                    "provider_id": provider_id,
                    "error": str(e)
                })
        
        return results


async def main():
    """Main entry point for pipeline."""
    orchestrator = PipelineOrchestrator()
    
    # Example: Process all providers
    # results = await orchestrator.process_all_providers(limit=10)
    
    # Example: Process from CSV
    # results = await orchestrator.process_from_csv("data/providers.csv")
    
    logger.info("Pipeline orchestrator ready. Use orchestrator.process_provider() or process_all_providers()")


if __name__ == "__main__":
    asyncio.run(main())

