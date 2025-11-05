"""
Optional LLM integration for name validation and enhancement.

This module provides optional features using language models:
- Validate cultural authenticity of name combinations
- Generate middle names
- Provide cultural context about names
"""

import os
from typing import Dict, Optional

from anthropic import Anthropic


class LLMValidator:
    """Validates and enhances names using language models."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM validator.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)

    def is_available(self) -> bool:
        """Check if LLM validation is available."""
        return self.client is not None

    def validate_name_combination(
        self, first_name: str, last_name: str, ethnicity: str
    ) -> Dict[str, any]:
        """
        Validate if a first name + last name combination is culturally appropriate.

        Args:
            first_name: The first name
            last_name: The surname
            ethnicity: Target ethnicity

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "confidence": float,
                "explanation": str
            }
        """
        if not self.is_available():
            return {
                "is_valid": True,
                "confidence": 0.5,
                "explanation": "LLM validation not available (no API key)",
            }

        prompt = f"""Analyze whether the name combination "{first_name} {last_name}" is culturally plausible for someone of {ethnicity} ethnicity.

Consider:
1. Are both names commonly associated with this ethnicity?
2. Is this combination realistic (not mixing incompatible cultural origins)?
3. Does this name exist in real populations?

Respond in JSON format:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "explanation": "brief explanation"
}}"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",  # Use cheapest model
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = message.content[0].text
            # Simple JSON extraction (you may want to use json.loads for production)
            if "true" in response_text.lower():
                is_valid = True
            else:
                is_valid = False

            return {
                "is_valid": is_valid,
                "confidence": 0.8,  # Default confidence
                "explanation": response_text,
            }

        except Exception as e:
            return {
                "is_valid": True,
                "confidence": 0.5,
                "explanation": f"Validation error: {str(e)}",
            }

    def generate_middle_name(
        self,
        first_name: str,
        last_name: str,
        ethnicity: str,
        gender: Optional[str] = None,
    ) -> str:
        """
        Generate a culturally appropriate middle name.

        Args:
            first_name: The first name
            last_name: The surname
            ethnicity: Target ethnicity
            gender: Optional gender (M/F)

        Returns:
            Generated middle name
        """
        if not self.is_available():
            return ""

        gender_text = f" for a {gender.lower()} person" if gender else ""

        prompt = f"""Generate a single culturally appropriate middle name to go with the name "{first_name} {last_name}" for someone of {ethnicity} ethnicity{gender_text}.

Requirements:
- The middle name should be authentic and commonly used
- It should fit naturally with the first and last name
- Respond with ONLY the middle name, no explanation

Middle name:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )

            middle_name = message.content[0].text.strip()
            # Remove any quotes or extra punctuation
            middle_name = middle_name.strip("\"'.,")

            return middle_name

        except Exception as e:
            print(f"Warning: Could not generate middle name: {e}")
            return ""

    def get_name_context(self, name: str, name_type: str = "first") -> Dict[str, str]:
        """
        Get cultural context and information about a name.

        Args:
            name: The name to analyze
            name_type: "first" or "last"

        Returns:
            Dictionary with context information:
            {
                "origin": str,
                "meaning": str,
                "cultural_notes": str
            }
        """
        if not self.is_available():
            return {
                "origin": "Unknown",
                "meaning": "Unknown",
                "cultural_notes": "LLM context not available",
            }

        prompt = f"""Provide brief cultural context for the {name_type} name "{name}".

Include:
1. Cultural/ethnic origin
2. Meaning (if known)
3. Any notable cultural context

Keep response concise (2-3 sentences max).

Response:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )

            context = message.content[0].text.strip()

            return {
                "origin": "See cultural_notes",
                "meaning": "See cultural_notes",
                "cultural_notes": context,
            }

        except Exception as e:
            return {
                "origin": "Unknown",
                "meaning": "Unknown",
                "cultural_notes": f"Error fetching context: {e}",
            }


# Singleton instance for easy access
_validator_instance: Optional[LLMValidator] = None


def get_validator(api_key: Optional[str] = None) -> LLMValidator:
    """Get or create LLM validator instance."""
    global _validator_instance

    if _validator_instance is None:
        _validator_instance = LLMValidator(api_key)

    return _validator_instance
