"""
Data Validation Agent for MedAtlas.

Responsible only for validating a single provider record.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DataValidationAgent:
    async def validate_provider(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a provider dict.

        Args:
            provider: Raw provider data from the database.

        Returns:
            {
                "validated_data": <possibly cleaned provider>,
                "issues": [<list of validation issue strings>]
            }
        """
        issues: List[str] = []
        validated = dict(provider)

        # Example simple checks (replace with your real logic):
        if not validated.get("npi"):
            issues.append("Missing NPI.")
        if not validated.get("first_name") and not validated.get("organization_name"):
            issues.append("Missing provider name.")

        # Add more field-level checks as needed...

        logger.info(f"Validated provider {validated.get('id')}: {len(issues)} issues")
        return {
            "validated_data": validated,
            "issues": issues,
        }
