"""
Unit tests for HFTextGenService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.hf_textgen_service import HFTextGenService, get_hf_textgen_service


class TestHFTextGenService:
    """Test suite for HFTextGenService."""
    
    def test_initialization_without_api_key(self):
        """Test that service raises error if no API key."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = ""
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            with pytest.raises(ValueError, match="API key required"):
                HFTextGenService()
    
    def test_initialization_with_api_key(self):
        """Test successful initialization with API key."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test_key"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            assert service.api_key == "hf_test_key"
            assert service.temperature == 0.2
            assert service.max_new_tokens == 400
    
    def test_set_temperature_valid(self):
        """Test updating temperature with valid value."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            service.set_temperature(0.7)
            
            assert service.temperature == 0.7
    
    def test_set_temperature_invalid(self):
        """Test that invalid temperature raises error."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            with pytest.raises(ValueError):
                service.set_temperature(1.5)  # > 1.0
            
            with pytest.raises(ValueError):
                service.set_temperature(-0.1)  # < 0.0
    
    def test_set_max_tokens_valid(self):
        """Test updating max tokens with valid value."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            service.set_max_tokens(600)
            
            assert service.max_new_tokens == 600
    
    def test_set_max_tokens_invalid(self):
        """Test that invalid max tokens raises error."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            with pytest.raises(ValueError):
                service.set_max_tokens(2000)  # > 1024
            
            with pytest.raises(ValueError):
                service.set_max_tokens(0)  # < 1
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful text generation."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            # Mock httpx response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"generated_text": "This is a test response"}
            ]
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await service.generate("Test prompt")
                
                assert result["generated_text"] == "This is a test response"
                assert result["model"] == "meta-llama/Llama-2-7b-chat-hf"
                assert "latency_ms" in result
                assert "output_tokens" in result
    
    @pytest.mark.asyncio
    async def test_generate_model_loading(self):
        """Test handling of model loading (503) response."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            # Mock 503 response
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.json.return_value = {"estimated_time": 20}
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                with pytest.raises(Exception, match="Model is loading"):
                    await service.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_invalid_api_key(self):
        """Test handling of invalid API key (401) response."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_invalid"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            # Mock 401 response
            mock_response = MagicMock()
            mock_response.status_code = 401
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                with pytest.raises(Exception, match="Invalid API key"):
                    await service.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_rate_limit(self):
        """Test handling of rate limit (429) response."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            # Mock 429 response
            mock_response = MagicMock()
            mock_response.status_code = 429
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                with pytest.raises(Exception, match="Rate limit exceeded"):
                    await service.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_timeout(self):
        """Test handling of request timeout."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=httpx.TimeoutException("Request timed out")
                )
                
                with pytest.raises(Exception, match="timed out"):
                    await service.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            # Mock httpx response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"generated_text": "Hello"}
            ]
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                result = await service.health_check()
                
                assert result["status"] == "ok"
                assert "latency_ms" in result
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            service = HFTextGenService()
            
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=Exception("API error")
                )
                
                result = await service.health_check()
                
                assert result["status"] == "error"
                assert "API error" in result["message"]
    
    def test_singleton_pattern(self):
        """Test that get_hf_textgen_service returns same instance."""
        with patch("app.services.hf_textgen_service.settings") as mock_settings:
            mock_settings.huggingface_api_key = "hf_test"
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.hf_generation_timeout = 30
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_max_output_tokens = 400
            
            # Reset singleton
            import app.services.hf_textgen_service
            app.services.hf_textgen_service._hf_service = None
            
            service1 = get_hf_textgen_service()
            service2 = get_hf_textgen_service()
            
            assert service1 is service2
