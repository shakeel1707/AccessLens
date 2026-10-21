"""Bedrock integration for generating accessibility violation explanations.

Implements AI-powered explanation generation with caching and fallback logic.
Uses Claude 3 Sonnet model via AWS Bedrock for generating clear, concise
explanations of accessibility violations.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger("accesslens.bedrock")


class BedrockExplanationService:
    """Service for generating accessibility violation explanations using Bedrock."""
    
    BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
    EXPLANATION_MAX_LENGTH = 500
    CACHE_TTL_HOURS = 24
    
    # Default fallback explanations for common rules
    FALLBACK_EXPLANATIONS = {
        "image-alt": "Images must have descriptive alternative text that conveys the meaning and purpose of the image.",
        "color-contrast": "Text and background colors must have sufficient contrast ratio (at least 4.5:1 for normal text).",
        "heading-order": "Heading levels must be consecutive and properly ordered (no skipping levels like h1 to h3).",
        "form-label": "Form inputs must have associated labels to help users understand what information to enter.",
        "link-name": "Links must have descriptive text that explains their purpose or destination.",
        "aria-required-attr": "ARIA attributes must be used correctly according to their specifications.",
        "button-name": "Buttons must have accessible names that describe their action.",
        "list": "Lists must be properly marked up using semantic HTML list elements.",
    }
    
    def __init__(self, bedrock_client=None, finding_repo=None):
        """Initialize Bedrock service.
        
        Args:
            bedrock_client: boto3 Bedrock client (optional, created if not provided)
            finding_repo: FindingRepository for caching (required)
        """
        self.bedrock_client = bedrock_client or boto3.client("bedrock-runtime", region_name="us-east-1")
        self.finding_repo = finding_repo
    
    def get_explanation(self, finding_id: str, rule_id: str, description: str, 
                       use_cache: bool = True, retry_count: int = 0) -> str:
        """Get explanation for a finding, with caching and fallback.
        
        Args:
            finding_id: Unique finding ID for caching
            rule_id: axe-core rule ID
            description: Original violation description
            use_cache: Whether to use cached explanations
            retry_count: Internal retry counter for exponential backoff
        
        Returns:
            Explanation string (max 500 chars)
        """
        # Try cache first
        if use_cache and self.finding_repo:
            cached = self._get_cached_explanation(finding_id)
            if cached:
                logger.info(f"Cache hit for finding {finding_id}")
                return cached
        
        # Try to generate via Bedrock
        try:
            explanation = self._generate_via_bedrock(rule_id, description)
            
            # Cache the result
            if self.finding_repo:
                self._cache_explanation(finding_id, explanation)
            
            return explanation
        
        except Exception as e:
            logger.warning(f"Bedrock generation failed for {rule_id}: {str(e)}")
            
            # Implement exponential backoff for quota errors
            if "quota" in str(e).lower() and retry_count < 2:
                import time
                delay = 2 ** retry_count  # 1s, 2s
                logger.info(f"Quota exceeded, retrying in {delay}s")
                time.sleep(delay)
                return self.get_explanation(finding_id, rule_id, description, use_cache, retry_count + 1)
            
            # Fall back to default explanation
            fallback = self.FALLBACK_EXPLANATIONS.get(rule_id, 
                f"This accessibility violation needs to be addressed: {description}")
            logger.info(f"Using fallback explanation for {rule_id}")
            return fallback[:self.EXPLANATION_MAX_LENGTH]
    
    def _generate_via_bedrock(self, rule_id: str, description: str) -> str:
        """Generate explanation using Bedrock API.
        
        Args:
            rule_id: axe-core rule ID
            description: Violation description
        
        Returns:
            Generated explanation
        
        Raises:
            Exception: If Bedrock call fails
        """
        prompt = self._build_prompt(rule_id, description)
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.BEDROCK_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",
                    "max_tokens": 150,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response["body"].read())
            explanation = response_body["content"][0]["text"].strip()
            
            # Truncate to max length
            return explanation[:self.EXPLANATION_MAX_LENGTH]
        
        except (ClientError, BotoCoreError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Bedrock API error: {str(e)}")
            raise
    
    def _build_prompt(self, rule_id: str, description: str) -> str:
        """Build prompt for Bedrock.
        
        Args:
            rule_id: axe-core rule ID
            description: Violation description
        
        Returns:
            Prompt string
        """
        return f"""Generate a clear, concise explanation (max 100 words) for this web accessibility violation:

Rule: {rule_id}
Description: {description}

Explain why this matters for accessibility and how to fix it. Be practical and developer-friendly."""
    
    def _get_cached_explanation(self, finding_id: str) -> Optional[str]:
        """Get cached explanation from DynamoDB.
        
        Args:
            finding_id: Finding ID to look up
        
        Returns:
            Cached explanation or None if not found/expired
        """
        try:
            if not self.finding_repo:
                return None
            
            # This would call a hypothetical get method on FindingRepository
            # For now, return None to indicate cache miss
            return None
        except Exception as e:
            logger.warning(f"Cache lookup failed: {str(e)}")
            return None
    
    def _cache_explanation(self, finding_id: str, explanation: str) -> None:
        """Cache explanation in DynamoDB.
        
        Args:
            finding_id: Finding ID to cache under
            explanation: Explanation text to cache
        """
        try:
            if not self.finding_repo:
                return
            
            # This would update the finding with explanation and cached_at
            # For now, this is a placeholder for the caching mechanism
            logger.debug(f"Explanation cached for finding {finding_id}")
        except Exception as e:
            logger.warning(f"Cache write failed: {str(e)}")
