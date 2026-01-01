"""
Unit tests for HFTextGenService

Tests cover:
- Singleton pattern
- Initialization (API mode)
- Generation logic
- Input validation
- Output validation
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ai.hf_textgen_service import (
    HFTextGenService,
    get_textgen_service,
    GenerationError,
    ModelLoadError
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before and after each test."""
    HFTextGenService._instance = None
    yield
    HFTextGenService._instance = None


class TestSingletonPattern:
    """Test that HFTextGenService follows singleton pattern."""
    
    def test_singleton_same_instance(self):
        """Verify that multiple calls return the same instance."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service1 = HFTextGenService()
                service2 = HFTextGenService()
                
                assert service1 is service2, "Should return same instance"
    
    def test_get_textgen_service_singleton(self):
        """Test factory function returns singleton."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service1 = get_textgen_service()
                service2 = get_textgen_service()
                
                assert service1 is service2


class TestInitialization:
    """Test service initialization in different modes."""
    
    def test_init_api_mode_success(self):
        """Test successful initialization in API mode."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.huggingface_api_key = "hf_test_key_123"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient') as mock_client:
                service = HFTextGenService()
                
                assert service._initialized is True
                assert service.use_api is True
                assert service.model_name == "meta-llama/Llama-2-7b-chat-hf"
                mock_client.assert_called_once()
    
    def test_init_api_mode_no_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = None  # No key
            
            with pytest.raises(ModelLoadError, match="Service initialization failed"):
                HFTextGenService()


class TestGeneration:
    """Test text generation functionality."""
    
    def test_generate_api_mode_success(self):
        """Test successful generation in API mode."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Faith is trust in God and His promises."
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                result = service.generate("What is faith?")
                
                assert result == "Faith is trust in God and His promises."
                mock_client.text_generation.assert_called_once()
    
    def test_generate_empty_prompt_raises_error(self):
        """Test that empty prompt raises GenerationError."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="Cannot generate from empty prompt"):
                    service.generate("")
    
    def test_generate_whitespace_only_prompt_raises_error(self):
        """Test that whitespace-only prompt raises GenerationError."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="Cannot generate from empty prompt"):
                    service.generate("   \n\t  ")
    
    def test_generate_uses_default_parameters(self):
        """Test that generation uses config defaults when params not specified."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Generated answer with sufficient length."
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                service.generate("What is grace?")
                
                # Verify defaults were used
                call_kwargs = mock_client.text_generation.call_args[1]
                assert call_kwargs['max_new_tokens'] == 400
                assert call_kwargs['temperature'] == 0.2
                assert call_kwargs['top_p'] == 0.9
                assert call_kwargs['repetition_penalty'] == 1.1
    
    def test_generate_respects_custom_parameters(self):
        """Test that custom parameters override defaults."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Custom generation response."
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                service.generate(
                    "Test prompt",
                    max_new_tokens=200,
                    temperature=0.5,
                    top_p=0.95,
                    repetition_penalty=1.2
                )
                
                # Verify custom params were used
                call_kwargs = mock_client.text_generation.call_args[1]
                assert call_kwargs['max_new_tokens'] == 200
                assert call_kwargs['temperature'] == 0.5
                assert call_kwargs['top_p'] == 0.95
                assert call_kwargs['repetition_penalty'] == 1.2


class TestOutputValidation:
    """Test output validation logic."""
    
    def test_validate_output_too_short_fails(self):
        """Test that very short output fails validation."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Too short"  # <20 chars
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="failed validation"):
                    service.generate("Test prompt")
    
    def test_validate_output_empty_fails(self):
        """Test that empty output fails validation."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = ""
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="failed validation"):
                    service.generate("Test prompt")
    
    def test_validate_output_repetitive_fails(self):
        """Test that highly repetitive output fails validation."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                # Very repetitive text
                mock_client.text_generation.return_value = "the same words " * 20
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="failed validation"):
                    service.generate("Test prompt")
    
    def test_validate_output_good_quality_passes(self):
        """Test that good quality output passes validation."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                good_response = (
                    "Faith is the confident trust in God and His promises, even when we cannot see "
                    "the outcome. The Bible describes it as 'the substance of things hoped for, "
                    "the evidence of things not seen' (Hebrews 11:1)."
                )
                mock_client.text_generation.return_value = good_response
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                result = service.generate("What is faith?")
                
                assert result == good_response


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_api_error_raises_generation_error(self):
        """Test that API errors are caught and wrapped in GenerationError."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.side_effect = Exception("API timeout")
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="Text generation failed"):
                    service.generate("Test prompt")


class TestModelInfo:
    """Test get_model_info method."""
    
    def test_get_model_info_api_mode(self):
        """Test model info in API mode."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            
            with patch('huggingface_hub.InferenceClient'):
                service = HFTextGenService()
                info = service.get_model_info()
                
                assert info['model_name'] == "meta-llama/Llama-2-7b-chat-hf"
                assert info['mode'] == "api"
                assert info['max_output_tokens'] == 400
                assert info['temperature'] == 0.2
                assert info['initialized'] is True


class TestRetryLogic:
    """Test retry mechanism with exponential backoff."""
    
    def test_retry_on_transient_failure(self):
        """Test that generation retries on transient failures."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                # Fail twice, then succeed
                mock_client.text_generation.side_effect = [
                    Exception("Temporary error"),
                    Exception("Temporary error"),
                    "Success after retry - this is a valid response with sufficient length."
                ]
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                result = service.generate("Test prompt")
                
                assert result == "Success after retry - this is a valid response with sufficient length."
                assert mock_client.text_generation.call_count == 3
    
    def test_retry_exhausted_raises_error(self):
        """Test that exhausted retries raise GenerationError."""
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                # Always fail
                mock_client.text_generation.side_effect = Exception("Persistent error")
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError):
                    service.generate("Test prompt")
                
                # Should have tried 3 times
                assert mock_client.text_generation.call_count == 3
    
    def test_get_textgen_service_singleton(self):
        """Test factory function returns singleton."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service1 = get_textgen_service()
                service2 = get_textgen_service()
                
                assert service1 is service2


class TestInitialization:
    """Test service initialization in different modes."""
    
    def test_init_api_mode_success(self):
        """Test successful initialization in API mode."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.huggingface_api_key = "hf_test_key_123"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient') as mock_client:
                service = HFTextGenService()
                
                assert service._initialized is True
                assert service.use_api is True
                assert service.model_name == "meta-llama/Llama-2-7b-chat-hf"
                mock_client.assert_called_once()
    
    def test_init_api_mode_no_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = None  # No key
            
            with pytest.raises(ModelLoadError, match="Service initialization failed"):
                HFTextGenService()
    
    def test_init_local_mode_success(self):
        """Test successful initialization in local mode."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = False
            mock_settings.hf_generation_model = "test-model"
            
            with patch('transformers.AutoModelForCausalLM') as mock_model:
                with patch('transformers.AutoTokenizer') as mock_tokenizer:
                    # Create mock model with parameters
                    mock_model_instance = MagicMock()
                    mock_param = MagicMock()
                    mock_param.device = "cpu"
                    # Make parameters() return an iterator, not a list
                    mock_model_instance.parameters.return_value = iter([mock_param])
                    mock_model.from_pretrained.return_value = mock_model_instance
                    
                    service = HFTextGenService()
                    
                    assert service._initialized is True
                    assert service.use_api is False
                    mock_model.from_pretrained.assert_called_once()
                    mock_tokenizer.from_pretrained.assert_called_once()


class TestGeneration:
    """Test text generation functionality."""
    
    def test_generate_api_mode_success(self):
        """Test successful generation in API mode."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Faith is trust in God and His promises."
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                result = service.generate("What is faith?")
                
                assert result == "Faith is trust in God and His promises."
                mock_client.text_generation.assert_called_once()
    
    def test_generate_empty_prompt_raises_error(self):
        """Test that empty prompt raises GenerationError."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="Cannot generate from empty prompt"):
                    service.generate("")
    
    def test_generate_whitespace_only_prompt_raises_error(self):
        """Test that whitespace-only prompt raises GenerationError."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            
            with patch('huggingface_hub.InferenceClient'):
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="Cannot generate from empty prompt"):
                    service.generate("   \n\t  ")
    
    def test_generate_uses_default_parameters(self):
        """Test that generation uses config defaults when params not specified."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Generated answer with sufficient length."
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                service.generate("What is grace?")
                
                # Verify defaults were used
                call_kwargs = mock_client.text_generation.call_args[1]
                assert call_kwargs['max_new_tokens'] == 400
                assert call_kwargs['temperature'] == 0.2
                assert call_kwargs['top_p'] == 0.9
                assert call_kwargs['repetition_penalty'] == 1.1
    
    def test_generate_respects_custom_parameters(self):
        """Test that custom parameters override defaults."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Custom generation response."
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                service.generate(
                    "Test prompt",
                    max_new_tokens=200,
                    temperature=0.5,
                    top_p=0.95,
                    repetition_penalty=1.2
                )
                
                # Verify custom params were used
                call_kwargs = mock_client.text_generation.call_args[1]
                assert call_kwargs['max_new_tokens'] == 200
                assert call_kwargs['temperature'] == 0.5
                assert call_kwargs['top_p'] == 0.95
                assert call_kwargs['repetition_penalty'] == 1.2


class TestOutputValidation:
    """Test output validation logic."""
    
    def test_validate_output_too_short_fails(self):
        """Test that very short output fails validation."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = "Too short"  # <20 chars
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="failed validation"):
                    service.generate("Test prompt")
    
    def test_validate_output_empty_fails(self):
        """Test that empty output fails validation."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.return_value = ""
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="failed validation"):
                    service.generate("Test prompt")
    
    def test_validate_output_repetitive_fails(self):
        """Test that highly repetitive output fails validation."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                # Very repetitive text
                mock_client.text_generation.return_value = "the same words " * 20
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="failed validation"):
                    service.generate("Test prompt")
    
    def test_validate_output_good_quality_passes(self):
        """Test that good quality output passes validation."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                good_response = (
                    "Faith is the confident trust in God and His promises, even when we cannot see "
                    "the outcome. The Bible describes it as 'the substance of things hoped for, "
                    "the evidence of things not seen' (Hebrews 11:1)."
                )
                mock_client.text_generation.return_value = good_response
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                result = service.generate("What is faith?")
                
                assert result == good_response


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_api_error_raises_generation_error(self):
        """Test that API errors are caught and wrapped in GenerationError."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                mock_client.text_generation.side_effect = Exception("API timeout")
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError, match="Text generation failed"):
                    service.generate("Test prompt")


class TestModelInfo:
    """Test get_model_info method."""
    
    def test_get_model_info_api_mode(self):
        """Test model info in API mode."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "meta-llama/Llama-2-7b-chat-hf"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            
            with patch('huggingface_hub.InferenceClient'):
                service = HFTextGenService()
                info = service.get_model_info()
                
                assert info['model_name'] == "meta-llama/Llama-2-7b-chat-hf"
                assert info['mode'] == "api"
                assert info['max_output_tokens'] == 400
                assert info['temperature'] == 0.2
                assert info['initialized'] is True
    
    def test_get_model_info_local_mode(self):
        """Test model info in local mode."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = False
            mock_settings.hf_generation_model = "test-model"
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            
            with patch('transformers.AutoModelForCausalLM') as mock_model:
                with patch('transformers.AutoTokenizer'):
                    mock_model_instance = MagicMock()
                    mock_param = MagicMock()
                    mock_param.device = "cpu"
                    # Make parameters() return an iterator, not a list
                    mock_model_instance.parameters.return_value = iter([mock_param])
                    mock_model.from_pretrained.return_value = mock_model_instance
                    
                    service = HFTextGenService()
                    info = service.get_model_info()
                    
                    assert info['mode'] == "local"
                    assert info['initialized'] is True


class TestRetryLogic:
    """Test retry mechanism with exponential backoff."""
    
    def test_retry_on_transient_failure(self):
        """Test that generation retries on transient failures."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                # Fail twice, then succeed
                mock_client.text_generation.side_effect = [
                    Exception("Temporary error"),
                    Exception("Temporary error"),
                    "Success after retry - this is a valid response with sufficient length."
                ]
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                result = service.generate("Test prompt")
                
                assert result == "Success after retry - this is a valid response with sufficient length."
                assert mock_client.text_generation.call_count == 3
    
    def test_retry_exhausted_raises_error(self):
        """Test that exhausted retries raise GenerationError."""
        # Reset singleton
        HFTextGenService._instance = None
        
        with patch('app.services.hf_textgen_service.settings') as mock_settings:
            mock_settings.hf_use_api = True
            mock_settings.hf_generation_model = "test-model"
            mock_settings.huggingface_api_key = "test-key"
            mock_settings.hf_generation_timeout = 60
            mock_settings.assistant_max_output_tokens = 400
            mock_settings.hf_generation_temperature = 0.2
            mock_settings.assistant_model_top_p = 0.9
            mock_settings.assistant_model_repition_penalty = 1.1
            
            with patch('huggingface_hub.InferenceClient') as mock_client_class:
                mock_client = Mock()
                # Always fail
                mock_client.text_generation.side_effect = Exception("Persistent error")
                mock_client_class.return_value = mock_client
                
                service = HFTextGenService()
                
                with pytest.raises(GenerationError):
                    service.generate("Test prompt")
                
                # Should have tried 3 times
                assert mock_client.text_generation.call_count == 3


# Fixtures for test cleanup
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test."""
    HFTextGenService._instance = None
    yield
    HFTextGenService._instance = None
