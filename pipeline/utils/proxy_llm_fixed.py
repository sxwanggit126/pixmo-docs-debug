"""
Fixed Proxy LLM support for DataDreamer compatibility
"""

import os
import json
from datadreamer.llms import OpenAI
from datadreamer.llms.openai import _is_chat_model
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyLLM(OpenAI):
    """
    Fixed proxy LLM class that handles both chat and completion endpoints.
    """

    def __init__(self, model_name, system_prompt=None, **kwargs):
        """Initialize the proxy LLM."""
        api_key = os.getenv("PROXY_API_KEY")
        base_url = os.getenv("PROXY_BASE_URL")

        if not api_key:
            raise ValueError("PROXY_API_KEY not found in environment variables")
        if not base_url:
            raise ValueError("PROXY_BASE_URL not found in environment variables")

        # Store original model name
        self._proxy_model_name = model_name
        self._system_prompt = system_prompt

        # Force chat model detection for Claude
        if "claude" in model_name.lower():
            # Override the _is_chat_model function to return True for Claude
            import datadreamer.llms.openai
            original_is_chat_model = datadreamer.llms.openai._is_chat_model

            def patched_is_chat_model(model_name):
                if "claude" in model_name.lower():
                    return True
                return original_is_chat_model(model_name)

            datadreamer.llms.openai._is_chat_model = patched_is_chat_model
            # Clear the lru_cache if it exists
            if hasattr(original_is_chat_model, 'cache_clear'):
                original_is_chat_model.cache_clear()

        # Initialize parent class
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            system_prompt=system_prompt,
            **kwargs
        )

        print(f"Initialized ProxyLLM with model: {model_name} via {base_url}")

    @property
    def model_name(self):
        """Return the actual model name for API calls."""
        return self._proxy_model_name

    @model_name.setter
    def model_name(self, value):
        """Allow parent class to set model_name during init."""
        # Parent class tries to set this, but we use our own storage
        pass

    def run(self, prompts, **kwargs):
        """Override run method to ensure proper request formatting."""
        # Patch the chat.completions.create to use correct model name and filter params
        if hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
            original_create = self.client.chat.completions.create

            def patched_create(**create_kwargs):
                # Ensure model name is correct
                create_kwargs['model'] = self._proxy_model_name

                # Filter parameters for Claude
                if "claude" in self._proxy_model_name.lower():
                    # Log the request for debugging
                    logger.info(f"=== Claude Chat Request ===")
                    logger.info(f"Model: {create_kwargs.get('model')}")
                    logger.info(f"Parameters: {list(create_kwargs.keys())}")

                    # Only keep essential parameters
                    filtered = {
                        'model': create_kwargs['model'],
                        'messages': create_kwargs.get('messages', []),
                        'temperature': create_kwargs.get('temperature', 1.0),
                        'max_tokens': create_kwargs.get('max_tokens', 100)
                    }
                    create_kwargs = filtered

                # Fix messages format if needed
                if 'messages' in create_kwargs and isinstance(create_kwargs['messages'], list):
                    fixed_messages = []
                    for msg in create_kwargs['messages']:
                        fixed_msg = {'role': str(msg.get('role', 'user'))}
                        content = msg.get('content', '')
                        if isinstance(content, list):
                            # Convert array to string
                            text_parts = []
                            for part in content:
                                if isinstance(part, dict) and 'text' in part:
                                    text_parts.append(part['text'])
                                else:
                                    text_parts.append(str(part))
                            fixed_msg['content'] = ' '.join(text_parts)
                        else:
                            fixed_msg['content'] = str(content)
                        fixed_messages.append(fixed_msg)
                    create_kwargs['messages'] = fixed_messages

                return original_create(**create_kwargs)

            # Temporarily replace the method
            self.client.chat.completions.create = patched_create

            try:
                # Call parent run method
                result = super().run(prompts, **kwargs)
                return result
            finally:
                # Restore original method
                self.client.chat.completions.create = original_create
        else:
            # Fallback to parent implementation
            return super().run(prompts, **kwargs)