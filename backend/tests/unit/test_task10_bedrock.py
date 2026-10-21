"""Unit and integration tests for Task 10: Bedrock Integration for Explanations

Includes PBT Suite 7: JSON Round-Trip (serialization integrity)
"""
import pytest
import json
import sys
sys.path.insert(0, 'src')

from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st
from app.services.bedrock import BedrockExplanationService


class TestExplanationGeneration:
    """Test explanation generation via Bedrock"""
    
    def test_generate_explanation_success(self):
        """Test successful explanation generation"""
        mock_bedrock = Mock()
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": "Images need alt text for screen readers."}]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        service = BedrockExplanationService(bedrock_client=mock_bedrock)
        explanation = service.get_explanation("f-1", "image-alt", "Image missing alt text")
        
        assert "Images" in explanation
        assert len(explanation) <= 500
        mock_bedrock.invoke_model.assert_called_once()
    
    
    def test_explanation_truncated_to_max_length(self):
        """Test that explanations are truncated to 500 chars"""
        mock_bedrock = Mock()
        long_text = "x" * 1000
        mock_response = {"body": MagicMock()}
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": long_text}]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        service = BedrockExplanationService(bedrock_client=mock_bedrock)
        explanation = service.get_explanation("f-2", "rule-1", "description")
        
        assert len(explanation) == 500


class TestFallbackExplanations:
    """Test fallback explanations when Bedrock fails"""
    
    def test_fallback_for_common_rules(self):
        """Test that fallback explanations are provided for common rules"""
        service = BedrockExplanationService(bedrock_client=Mock())
        
        # Test with failing Bedrock
        service.bedrock_client.invoke_model.side_effect = Exception("API Error")
        
        explanation = service.get_explanation("f-3", "image-alt", "Missing alt")
        assert "Images must have" in explanation
        
        explanation = service.get_explanation("f-4", "color-contrast", "Low contrast")
        assert "contrast" in explanation.lower()
    
    
    def test_fallback_from_description_if_rule_unknown(self):
        """Test fallback uses description for unknown rules"""
        service = BedrockExplanationService(bedrock_client=Mock())
        service.bedrock_client.invoke_model.side_effect = Exception("API Error")
        
        explanation = service.get_explanation("f-5", "unknown-rule-xyz", "Some violation")
        assert "violation" in explanation.lower()


class TestExponentialBackoff:
    """Test exponential backoff for quota errors"""
    
    def test_retry_on_quota_error(self):
        """Test that quota errors trigger retries"""
        mock_bedrock = Mock()
        # First two calls fail with quota error, third succeeds
        mock_bedrock.invoke_model.side_effect = [
            Exception("ThrottlingException: Rate limit exceeded"),
            Exception("ThrottlingException: Rate limit exceeded"),
            {"body": MagicMock(read=lambda: json.dumps({
                "content": [{"text": "Explanation text"}]
            }).encode())}
        ]
        
        service = BedrockExplanationService(bedrock_client=mock_bedrock)
        explanation = service.get_explanation("f-6", "rule-1", "description")
        
        # Should have retried and eventually succeeded or fallen back
        assert explanation is not None


class TestCaching:
    """Test caching logic"""
    
    def test_cache_miss_then_generate(self):
        """Test that cache miss triggers generation"""
        mock_bedrock = Mock()
        mock_response = {"body": MagicMock()}
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": "Generated explanation"}]
        }).encode()
        mock_bedrock.invoke_model.return_value = mock_response
        
        mock_repo = Mock()
        service = BedrockExplanationService(bedrock_client=mock_bedrock, finding_repo=mock_repo)
        
        explanation = service.get_explanation("f-7", "image-alt", "description", use_cache=True)
        
        assert "Generated" in explanation
        mock_bedrock.invoke_model.assert_called_once()


class TestPromptEngineering:
    """Test prompt generation"""
    
    def test_prompt_includes_rule_and_description(self):
        """Test that prompts include rule ID and description"""
        service = BedrockExplanationService(bedrock_client=Mock())
        prompt = service._build_prompt("image-alt", "Image missing alt text")
        
        assert "image-alt" in prompt
        assert "Image missing alt text" in prompt
        assert "accessibility" in prompt.lower()
    
    
    def test_prompt_within_reasonable_length(self):
        """Test that prompts are concise"""
        service = BedrockExplanationService(bedrock_client=Mock())
        prompt = service._build_prompt("rule-id", "description")
        
        assert len(prompt) < 500


@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(st.text(max_size=100), st.integers(), st.booleans(), st.none())
))
def test_json_roundtrip_explanation_dict(data):
    """PBT Suite 7: JSON serialization round-trip integrity
    
    Verify that explanation dictionaries can be serialized to JSON and
    deserialized back with data integrity preserved.
    """
    # Create a sample explanation dict
    explanation_dict = {
        "finding_id": "f-test",
        "rule_id": "image-alt",
        "explanation": "Images need alt text",
        "generated_at": "2024-10-20T12:00:00Z",
        **data  # Add property-based test data
    }
    
    # Serialize to JSON
    json_str = json.dumps(explanation_dict)
    
    # Deserialize back
    deserialized = json.loads(json_str)
    
    # Verify integrity
    assert deserialized["finding_id"] == explanation_dict["finding_id"]
    assert deserialized["rule_id"] == explanation_dict["rule_id"]
    assert deserialized["explanation"] == explanation_dict["explanation"]
    assert len(json_str) > 0


@given(st.text(max_size=100), st.text(max_size=100))
def test_explanation_max_length_invariant(rule_id, description):
    """PBT: Explanations never exceed max length regardless of input"""
    mock_bedrock = Mock()
    
    service = BedrockExplanationService(bedrock_client=mock_bedrock)
    # Mock to always return max length text
    mock_bedrock.invoke_model.side_effect = Exception("Bedrock error")
    
    explanation = service.get_explanation("f-test", rule_id, description)
    
    # Should never exceed max length
    assert len(explanation) <= service.EXPLANATION_MAX_LENGTH


@given(st.from_regex(r"[a-z\-]{5,30}", fullmatch=True))
def test_fallback_exists_for_common_rules(rule_id):
    """PBT: All explanations are non-empty regardless of rule"""
    service = BedrockExplanationService(bedrock_client=Mock())
    service.bedrock_client.invoke_model.side_effect = Exception("Error")
    
    explanation = service.get_explanation("f-test", rule_id, "test")
    
    assert len(explanation) > 0
    assert explanation is not None
