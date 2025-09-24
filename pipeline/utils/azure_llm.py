"""
Azure OpenAI LLM support for DataDreamer with Azure AD authentication
支持 GPT-4.1 等新模型
"""

import os
import time
import threading
from datetime import datetime, timedelta
from datadreamer.llms import OpenAI
from dotenv import load_dotenv
import logging
import requests
import openai

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AzureTokenManager:
    """管理 Azure AD 访问令牌的自动刷新"""

    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires_at = None
        self.lock = threading.Lock()

        # 获取初始令牌
        self._refresh_token()

    def _refresh_token(self):
        """从 Azure AD 获取新的访问令牌"""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://cognitiveservices.azure.com/.default",
            "grant_type": "client_credentials"
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # 默认1小时

            # 提前5分钟刷新令牌
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info(f"Azure AD token refreshed, expires at: {self.token_expires_at}")

        except Exception as e:
            logger.error(f"Failed to refresh Azure AD token: {e}")
            raise

    def get_token(self):
        """获取有效的访问令牌，如果需要则自动刷新"""
        with self.lock:
            if self.token is None or datetime.now() >= self.token_expires_at:
                self._refresh_token()
            return self.token


class AzureLLM(OpenAI):
    """
    Azure OpenAI LLM 类，支持 Azure AD 认证和模型部署映射
    完全支持 GPT-4.1 等新模型
    """

    def __init__(self, model_name, system_prompt=None, **kwargs):
        """初始化 Azure OpenAI LLM"""

        # 获取 Azure 配置
        self.tenant_id = os.getenv("AZURE_OPENAI_TENANT_ID")
        self.client_id = os.getenv("AZURE_OPENAI_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_OPENAI_CLIENT_SECRET")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        # 检查必需的配置
        required_configs = [self.tenant_id, self.client_id, self.client_secret, self.endpoint]
        if not all(required_configs):
            raise ValueError("Missing required Azure OpenAI configuration. Check your environment variables.")

        # 初始化令牌管理器
        self.token_manager = AzureTokenManager(self.tenant_id, self.client_id, self.client_secret)

        # 模型名称到部署名称的映射
        self.deployment_mapping = self._get_deployment_mapping()

        # 获取实际的部署名称
        self.deployment_name = self._get_deployment_name(model_name)
        self._original_model_name = model_name  # 存储原始模型名称

        # 构建 Azure OpenAI 端点 URL
        base_url = f"{self.endpoint.rstrip('/')}/openai/deployments/{self.deployment_name}"

        # GPT-4.1 需要更新的 API 版本
        if "gpt-4.1" in model_name.lower():
            self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
            logger.info(f"Using updated API version for GPT-4.1: {self.api_version}")

        # 修复 DataDreamer 的模型名称识别问题
        # DataDreamer 无法识别 gpt-4.1 为 chat 模型，所以我们传递一个它能识别的名称
        datadreamer_model_name = self._get_datadreamer_compatible_name(model_name)

        logger.info(f"Model mapping: {model_name} -> deployment: {self.deployment_name}, datadreamer: {datadreamer_model_name}")

        # 初始化父类，使用 DataDreamer 兼容的模型名称
        super().__init__(
            model_name=datadreamer_model_name,  # 使用 DataDreamer 兼容名称
            api_key=self.token_manager.get_token(),  # 使用 Azure AD token
            base_url=base_url,
            system_prompt=system_prompt,
            api_version=self.api_version,
            **kwargs
        )

        logger.info(f"Initialized AzureLLM: {model_name} -> {self.deployment_name}")
        logger.info(f"Azure endpoint: {base_url}")

    def _get_datadreamer_compatible_name(self, model_name):
        """
        将模型名称转换为 DataDreamer 能识别的名称
        统一使用 gpt-4-preview，因为我们不会使用 GPT-3 系列模型
        """
        # 统一返回 gpt-4-preview，DataDreamer 会将其识别为 chat 模型
        return "gpt-4-preview"

    def _get_deployment_mapping(self):
        """获取模型名称到 Azure 部署名称的映射"""
        return {
            # 常用模型的显式映射（如果部署名称与模型名称不同）
            "gpt-4o": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            "gpt-4o-mini": os.getenv("AZURE_OPENAI_MINI_DEPLOYMENT", "gpt-4o-mini"),
            "claude-sonnet": os.getenv("AZURE_ANTHROPIC_DEPLOYMENT", "gpt-4o"),
            "claude-3-sonnet": os.getenv("AZURE_ANTHROPIC_DEPLOYMENT", "gpt-4o"),
            "claude-3-7-sonnet-20250219": os.getenv("AZURE_ANTHROPIC_DEPLOYMENT", "gpt-4o"),
        }

    def _get_deployment_name(self, model_name):
        """根据模型名称获取对应的 Azure 部署名称"""
        # 先检查映射表
        deployment_name = self.deployment_mapping.get(model_name)

        # 如果映射表中没有，直接使用模型名称作为部署名称（假设部署名称 = 模型名称）
        if deployment_name is None:
            deployment_name = model_name
            logger.info(f"No explicit mapping for '{model_name}', using model name as deployment name")

        # 如果是 Claude 模型但没有对应的 Azure 部署，记录警告
        if "claude" in model_name.lower() and deployment_name.startswith("gpt"):
            logger.warning(f"Claude model '{model_name}' mapped to GPT deployment '{deployment_name}' "
                          "as Claude is not available on Azure OpenAI")

        # 检查 GPT-4.1 映射
        if "gpt-4.1" in model_name.lower():
            logger.info(f"GPT-4.1 model '{model_name}' mapped to deployment '{deployment_name}'")

        return deployment_name

    def _refresh_client_token(self):
        """刷新客户端的访问令牌"""
        new_token = self.token_manager.get_token()

        # 更新 OpenAI 客户端的 API key
        if hasattr(self.client, 'api_key'):
            self.client.api_key = new_token

        # 如果客户端有默认 headers，也更新它们
        if hasattr(self.client, 'default_headers'):
            self.client.default_headers["Authorization"] = f"Bearer {new_token}"

    def run(self, prompts, **kwargs):
        """重写 run 方法以处理 Azure 特定的逻辑和 GPT-4.1 支持"""

        # 确保令牌是最新的
        self._refresh_client_token()

        # 获取原始的 create 方法
        if hasattr(self.client.chat.completions, 'create'):
            original_create = self.client.chat.completions.create

            def azure_create(**create_kwargs):
                # 确保使用正确的 Azure 部署名称，而不是 DataDreamer 兼容名称
                create_kwargs['model'] = self.deployment_name

                # 添加 Azure 特定的参数
                if 'extra_headers' not in create_kwargs:
                    create_kwargs['extra_headers'] = {}

                create_kwargs['extra_headers']['api-version'] = self.api_version

                # GPT-4.1 特殊处理
                if "gpt-4.1" in self._original_model_name:
                    # GPT-4.1 支持更大的上下文窗口和特殊参数
                    if 'max_tokens' not in create_kwargs:
                        # GPT-4.1 默认可以使用更多 tokens
                        create_kwargs['max_tokens'] = min(8192, kwargs.get("max_tokens", 4096))

                    # 可能的 GPT-4.1 特定参数
                    if 'reasoning_effort' in kwargs:
                        create_kwargs['reasoning_effort'] = kwargs['reasoning_effort']

                    logger.debug(f"GPT-4.1 request: deployment={self.deployment_name}, "
                               f"max_tokens={create_kwargs.get('max_tokens')}")

                logger.debug(f"Azure OpenAI request: deployment={self.deployment_name}, "
                           f"api-version={self.api_version}, original_model={self._original_model_name}")

                try:
                    return original_create(**create_kwargs)
                except Exception as e:
                    # 如果是认证错误，尝试刷新令牌
                    if "401" in str(e) or "Unauthorized" in str(e):
                        logger.warning("Authentication failed, refreshing token...")
                        self._refresh_client_token()
                        create_kwargs['extra_headers']['Authorization'] = f"Bearer {self.token_manager.get_token()}"
                        return original_create(**create_kwargs)
                    # 如果是模型不存在的错误，给出更有用的错误信息
                    elif "DeploymentNotFound" in str(e) or "NotFound" in str(e):
                        logger.error(f"Deployment '{self.deployment_name}' not found. "
                                   f"Please check your Azure OpenAI deployment configuration.")
                        raise ValueError(f"Azure deployment '{self.deployment_name}' for model "
                                       f"'{self._original_model_name}' not found. Please check your "
                                       f"deployment configuration in the Azure portal.")
                    else:
                        raise

            # 临时替换方法
            self.client.chat.completions.create = azure_create

            try:
                # 调用父类的 run 方法
                result = super().run(prompts, **kwargs)
                return result
            finally:
                # 恢复原始方法
                self.client.chat.completions.create = original_create
        else:
            # 备用方案
            return super().run(prompts, **kwargs)

    @property
    def original_model_name(self):
        """返回原始模型名称以便于日志记录"""
        return self._original_model_name

    def __repr__(self):
        return f"AzureLLM(model='{self._original_model_name}', deployment='{self.deployment_name}')"


def create_azure_llm(model_name, system_prompt=None, **kwargs):
    """便捷函数：创建 Azure LLM 实例"""
    try:
        return AzureLLM(model_name=model_name, system_prompt=system_prompt, **kwargs)
    except Exception as e:
        logger.error(f"Failed to create Azure LLM for model '{model_name}': {e}")
        raise