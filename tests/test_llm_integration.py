import os
import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.utils import utils

# Load environment variables
load_dotenv()

class TestOpenAIIntegration:
    """Test OpenAI model integration and vision capabilities"""

    def setup_method(self):
        """Setup test environment"""
        # Ensure required environment variables are set
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
        if not self.api_key:
            pytest.skip("OPENAI_API_KEY not set")

    def test_gpt4_turbo_initialization(self):
        """Test GPT-4 Turbo model initialization"""
        llm = utils.get_llm_model(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.8,
            base_url=self.base_url,
            api_key=self.api_key
        )
        assert llm is not None

    def test_gpt4_vision_initialization(self):
        """Test GPT-4 Vision model initialization"""
        llm = utils.get_llm_model(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.8,
            base_url=self.base_url,
            api_key=self.api_key,
            vision=True
        )
        assert llm is not None

    @pytest.mark.asyncio
    async def test_vision_capability(self):
        """Test vision capability with an example image"""
        llm = utils.get_llm_model(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.8,
            base_url=self.base_url,
            api_key=self.api_key,
            vision=True
        )
        
        # Use a test image
        image_path = "assets/examples/test.png"
        if not os.path.exists(image_path):
            pytest.skip(f"Test image not found at {image_path}")
        
        image_data = utils.encode_image(image_path)
        message = HumanMessage(
            content=[
                {"type": "text", "text": "describe this image"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ]
        )
        response = await llm.ainvoke([message])
        assert response is not None
        assert isinstance(response.content, str)
        assert len(response.content) > 0

class TestAzureOpenAIIntegration:
    """Test Azure OpenAI integration"""

    def setup_method(self):
        """Setup test environment"""
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not self.api_key or not self.endpoint:
            pytest.skip("Azure OpenAI credentials not set")

    def test_azure_model_initialization(self):
        """Test Azure OpenAI model initialization"""
        llm = utils.get_llm_model(
            provider="azure_openai",
            model_name="gpt-4",
            temperature=0.8,
            base_url=self.endpoint,
            api_key=self.api_key
        )
        assert llm is not None

    @pytest.mark.asyncio
    async def test_azure_basic_completion(self):
        """Test basic completion with Azure OpenAI"""
        llm = utils.get_llm_model(
            provider="azure_openai",
            model_name="gpt-4",
            temperature=0.8,
            base_url=self.endpoint,
            api_key=self.api_key
        )
        
        message = HumanMessage(content="Say hello!")
        response = await llm.ainvoke([message])
        assert response is not None
        assert isinstance(response.content, str)
        assert len(response.content) > 0

class TestAnthropicIntegration:
    """Test Anthropic model integration"""

    def setup_method(self):
        """Setup test environment"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

    def test_claude_initialization(self):
        """Test Claude model initialization"""
        llm = utils.get_llm_model(
            provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            temperature=0.8,
            api_key=self.api_key
        )
        assert llm is not None

    @pytest.mark.asyncio
    async def test_basic_completion(self):
        """Test basic completion with Claude"""
        llm = utils.get_llm_model(
            provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            temperature=0.8,
            api_key=self.api_key
        )
        
        message = HumanMessage(content="Say hello!")
        response = await llm.ainvoke([message])
        assert response is not None
        assert isinstance(response.content, str)
        assert len(response.content) > 0

def test_model_names_consistency():
    """Test that model names are consistent between toolchain and utils"""
    # Test OpenAI models
    openai_models = utils.model_names["openai"]
    expected_openai = ["gpt-4o"]
    assert all(model in openai_models for model in expected_openai), "Missing expected OpenAI models"

    # Test Gemini models
    gemini_models = utils.model_names["gemini"]
    expected_gemini = ["gemini-1.5-pro", "gemini-2.0-flash"]
    assert all(model in gemini_models for model in expected_gemini), "Missing expected Gemini models"

    # Test Anthropic models
    anthropic_models = utils.model_names["anthropic"]
    expected_anthropic = ["claude-3-5-sonnet-latest", "claude-3-5-sonnet-20241022"]
    assert all(model in anthropic_models for model in expected_anthropic), "Missing expected Anthropic models"

    # Test DeepSeek models
    deepseek_models = utils.model_names["deepseek"]
    expected_deepseek = ["deepseek-chat"]
    assert all(model in deepseek_models for model in expected_deepseek), "Missing expected DeepSeek models"

    # Test Azure OpenAI models
    azure_models = utils.model_names["azure_openai"]
    expected_azure = ["gpt-4", "gpt-3.5-turbo"]
    assert all(model in azure_models for model in expected_azure), "Missing expected Azure OpenAI models"

    # Test Ollama models
    ollama_models = utils.model_names["ollama"]
    expected_ollama = ["qwen2.5:7b", "llama2:7b"]
    assert all(model in ollama_models for model in expected_ollama), "Missing expected Ollama models"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 