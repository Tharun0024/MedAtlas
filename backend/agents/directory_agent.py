"""
Directory Management Agent for MedAtlas.
Manages final provider profiles through auto-correction and data merging.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from backend.database import get_all_providers, get_discrepancies, DB_PATH  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


class DirectoryManagementAgent:
    """Agent responsible for directory management and provider profile finalization."""
    
    def __init__(self):
        self.name = "DirectoryManagementAgent"
        self.high_confidence_threshold = 80
    
    def auto_correct_fields(
        self,
        provider: Dict[str, Any],
        validated: Dict[str, Any],
        enriched: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Auto-correct provider fields based on validation confidence.
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
                    logger.debug(
                        f"Auto-corrected {field} with validated data "
                        f"(confidence: {field_confidence})"
                    )
            
            # For enriched data: only use if original field is missing/empty
            elif enriched.get(field) is not None and enriched.get(field) != '':
                if corrected.get(field) is None or corrected.get(field) == '':
                    corrected[field] = enriched[field]
                    logger.debug(f"Filled missing {field} with enriched data")
        
        return corrected
    
    def merge_data(
        self,
        provider: Dict[str, Any],
        validated: Dict[str, Any],
        enriched: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge provider data with strict priority: validated > enriched > original.
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
            if field in [
                'id',
                'created_at',
                'updated_at',
                'confidence_scores',
                'npi_valid',
                'phone_valid',
                'validation_status',
            ]:
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
    
    def run(
        self,
        provider: Dict[str, Any],
        validated_result: Dict[str, Any],
        enriched_result: Dict[str, Any],
        qa_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute full directory management workflow.
        """
        try:
            # Extract confidence scores safely
            confidence_scores = (
                validated_result.get('confidence_scores', {}) if validated_result else {}
            )
            
            # Extract data dicts safely (handle None inputs)
            validated_data = validated_result if validated_result else {}
            enriched_data = enriched_result if enriched_result else {}
            qa_data = qa_result if qa_result else {}
            
            logger.info(
                "DirectoryManagementAgent: Processing provider %s",
                provider.get('id', 'unknown'),
            )
            
            # Step 1: Auto-correct high-confidence fields
            corrected_provider = self.auto_correct_fields(
                provider,
                validated_data,
                enriched_data,
                confidence_scores,
            )
            
            # Step 2: Merge all data with priority
            final_provider = self.merge_data(
                corrected_provider,
                validated_data,
                enriched_data,
            )
            
            # Step 3: Add QA metadata
            final_provider['confidence_score'] = qa_data.get('confidence_score', 0)
            final_provider['risk_score'] = qa_data.get('risk_score', 0)
            final_provider['validation_status'] = qa_data.get('status', 'pending')
            
            logger.info(
                "DirectoryManagementAgent: Successfully finalized provider %s with confidence %s",
                provider.get('id', 'unknown'),
                final_provider.get('confidence_score', 0),
            )
            
            return final_provider
        
        except Exception as e:
            logger.error(
                "DirectoryManagementAgent: Error processing provider %s: %s",
                provider.get('id', 'unknown'),
                str(e),
            )
            # Return original provider if processing fails
            return provider

    async def finalize_provider(
        self,
        provider_id: int,
        validated_data: Dict[str, Any],
        enriched_data: Dict[str, Any],
        qa_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Async wrapper used by PipelineOrchestrator.

        It adapts orchestrator inputs to this agent's existing `run` method and
        returns the final provider record.
        """
        # Build base provider dict; ensure id is present for logs
        provider: Dict[str, Any] = {"id": provider_id, **validated_data}

        final_provider = self.run(
            provider=provider,
            validated_result=validated_data,
            enriched_result=enriched_data,
            qa_result=qa_results,
        )

        return final_provider

    async def export_directory(
        self,
        format: str = "csv",
        provider_ids: Optional[List[int]] = None,
        include_discrepancies: bool = True,
    ) -> Dict[str, Any]:
        """
        Export the current provider directory to disk.
        """
        try:
            # Determine exports directory relative to the project root (same as export endpoint)
            project_root = os.path.dirname(DB_PATH)
            exports_dir = os.path.join(project_root, "exports")
            os.makedirs(exports_dir, exist_ok=True)

            # Load providers from DB (directory view source of truth)
            providers = get_all_providers(limit=100000, offset=0)

            if provider_ids:
                id_set = set(provider_ids)
                providers = [p for p in providers if p.get("id") in id_set]

            final_directory: List[Dict[str, Any]] = []

            for p in providers:
                # Safely extract nested data, treating None as empty dicts
                validated_data = p.get("validated_data") or {}
                enriched_data = p.get("enriched_data") or {}

                # Build a minimal QA-like payload from stored provider fields
                qa_result: Dict[str, Any] = {
                    "confidence_score": p.get("confidence_score", 0),
                    "risk_score": p.get("risk_score", 0),
                    "status": p.get("validation_status", "pending"),
                }

                # Base provider (exclude JSON blobs we expand separately)
                base_provider = p.copy()
                base_provider.pop("validated_data", None)
                base_provider.pop("enriched_data", None)

                final_provider = self.run(
                    provider=base_provider,
                    validated_result=validated_data,
                    enriched_result=enriched_data,
                    qa_result=qa_result,
                )

                # Optionally include discrepancy count for transparency
                if include_discrepancies:
                    try:
                        disc = get_discrepancies(provider_id=p.get("id"))
                        final_provider["discrepancy_count"] = len(disc)
                    except Exception:
                        # Never fail export because of discrepancy lookup issues
                        final_provider["discrepancy_count"] = 0

                final_directory.append(final_provider)

            # Generate filename
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            fmt = (format or "csv").lower()
            if fmt not in {"csv", "json"}:
                fmt = "csv"
            filename = f"medatlas_directory_{ts}.{fmt}"
            filepath = os.path.join(exports_dir, filename)

            # Serialize to disk
            if fmt == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(final_directory, f, ensure_ascii=False, default=str, indent=2)
            else:
                # CSV export
                import csv

                # Determine CSV header from union of keys to be robust to partial data
                header_fields = set()
                for row in final_directory:
                    header_fields.update(row.keys())
                fieldnames = sorted(header_fields)

                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in final_directory:
                        writer.writerow(row)

            logger.info(
                "DirectoryManagementAgent: Exported %s providers to %s",
                len(final_directory),
                filepath,
            )

            return {
                "filename": filename,
                "provider_count": len(final_directory),
                "format": fmt,
            }

        except Exception as e:
            logger.error(
                "DirectoryManagementAgent: export_directory failed: %s",
                str(e),
            )
            # Let the API layer turn this into an HTTP 500; keep contract simple
            raise
