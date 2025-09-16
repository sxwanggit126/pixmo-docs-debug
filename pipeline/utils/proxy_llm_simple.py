"""
Simplified Proxy LLM support that avoids serialization issues.
"""

import os
import json
from datadreamer.llms import OpenAI
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ProxyLLM(OpenAI):
    """
    Simplified proxy LLM class that works around serialization issues.
    """

    def __init__(self, model_name, system_prompt=None, **kwargs):
        """Initialize the proxy LLM."""
        api_key = os.getenv("PROXY_API_KEY")
        base_url = os.getenv("PROXY_BASE_URL")

        if not api_key:
            raise ValueError("PROXY_API_KEY not found in environment variables")
        if not base_url:
            raise ValueError("PROXY_BASE_URL not found in environment variables")

        # Store model name for later use
        self._proxy_model_name = model_name

        # Initialize parent class
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            system_prompt=system_prompt,
            **kwargs
        )

        print(f"Initialized ProxyLLM with model: {model_name} via {base_url}")

    def run(self, prompts, **kwargs):
        """Override run method to filter parameters."""
        # Store original client methods
        if hasattr(self.client.chat.completions, 'create'):
            original_create = self.client.chat.completions.create

            def filtered_create(**create_kwargs):
                logger.info(f"=== ORIGINAL REQUEST ===")
                logger.info(f"Keys: {list(create_kwargs.keys())}")

                # Log each parameter to find the problematic one
                for key, value in create_kwargs.items():
                    value_type = type(value).__name__
                    if isinstance(value, list):
                        logger.info(f"  {key}: {value_type} with {len(value)} items")
                        if value and len(value) > 0:
                            logger.info(f"    First item type: {type(value[0])}")
                    elif isinstance(value, dict):
                        logger.info(f"  {key}: {value_type} with keys {list(value.keys())}")
                    else:
                        logger.info(f"  {key}: {value_type} = {value}")

                # Filter parameters strictly for Claude
                filtered_kwargs = {}

                # Only include absolutely essential parameters
                if "claude" in self._proxy_model_name.lower():
                    # Ultra-minimal for Claude
                    filtered_kwargs["model"] = self._proxy_model_name
                    filtered_kwargs["messages"] = create_kwargs.get("messages", [])
                    filtered_kwargs["temperature"] = create_kwargs.get("temperature", 1.0)
                    filtered_kwargs["max_tokens"] = create_kwargs.get("max_tokens", 100)
                else:
                    # More permissive for other models
                    essential = ["model", "messages", "temperature", "max_tokens", "n", "stream"]
                    for key in essential:
                        if key in create_kwargs:
                            filtered_kwargs[key] = create_kwargs[key]

                # Fix messages format
                if "messages" in filtered_kwargs and isinstance(filtered_kwargs["messages"], list):
                    fixed_messages = []
                    for msg in filtered_kwargs["messages"]:
                        fixed_msg = {"role": str(msg.get("role", "user"))}

                        content = msg.get("content", "")
                        if isinstance(content, list):
                            # This might be the issue - log it
                            logger.warning(f"Found list content in message: {content}")
                            # Convert array content to string
                            text_parts = []
                            for part in content:
                                if isinstance(part, dict):
                                    if "text" in part:
                                        text_parts.append(str(part["text"]))
                                    else:
                                        logger.warning(f"Unknown dict content: {part}")
                                else:
                                    text_parts.append(str(part))
                            fixed_msg["content"] = " ".join(text_parts)
                        else:
                            fixed_msg["content"] = str(content)

                        fixed_messages.append(fixed_msg)
                    filtered_kwargs["messages"] = fixed_messages

                logger.info(f"=== FILTERED REQUEST ===")
                logger.info(json.dumps(filtered_kwargs, indent=2, default=str))

                try:
                    return original_create(**filtered_kwargs)
                except Exception as e:
                    logger.error(f"API error: {e}")
                    logger.error(f"Failed with params: {list(filtered_kwargs.keys())}")
                    raise

            # Temporarily replace the method
            self.client.chat.completions.create = filtered_create

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