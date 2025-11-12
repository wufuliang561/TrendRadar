# coding=utf-8
"""大模型调用服务

负责调用 OpenAI 兼容格式的大模型 API
"""

from typing import List, Dict, Any, Optional, Tuple, Iterator
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk
from openai import APIError, APITimeoutError, RateLimitError


class LLMService:
    """大模型服务类

    支持所有兼容 OpenAI API 格式的服务商:
    - OpenAI
    - Azure OpenAI
    - DeepSeek
    - Moonshot
    - 本地 Ollama
    等等
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        timeout: int = 60
    ):
        """初始化 LLM 服务

        Args:
            base_url: API 基础 URL
            api_key: API 密钥
            model: 模型名称
            max_tokens: 最大生成 Token 数
            temperature: 温度参数
            timeout: 超时时间（秒）
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Tuple[Optional[str], bool, Optional[str], Optional[Dict[str, int]]]:
        """调用聊天补全 API

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            max_tokens: 最大生成 Token 数（覆盖默认值）
            temperature: 温度参数（覆盖默认值）

        Returns:
            Tuple: (回复内容, 是否成功, 错误信息, Token 使用情况)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature
            )

            # 提取回复
            reply = response.choices[0].message.content

            # 提取 Token 使用情况
            token_usage = None
            if hasattr(response, 'usage') and response.usage:
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }

            return reply, True, None, token_usage

        except RateLimitError as e:
            error_msg = f"API 速率限制: {str(e)}"
            print(f"[LLMService] {error_msg}")
            return None, False, error_msg, None

        except APITimeoutError as e:
            error_msg = f"API 请求超时: {str(e)}"
            print(f"[LLMService] {error_msg}")
            return None, False, error_msg, None

        except APIError as e:
            error_msg = f"API 错误: {str(e)}"
            print(f"[LLMService] {error_msg}")
            return None, False, error_msg, None

        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            print(f"[LLMService] {error_msg}")
            return None, False, error_msg, None

    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Iterator[Dict[str, Any]]:
        """调用聊天补全 API（流式输出）

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            max_tokens: 最大生成 Token 数（覆盖默认值）
            temperature: 温度参数（覆盖默认值）

        Yields:
            Dict: 流式数据块
                - type: "content" | "error" | "done"
                - content: 文本内容（仅 type="content" 时）
                - error: 错误信息（仅 type="error" 时）
                - token_usage: Token 使用情况（仅 type="done" 时）
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                stream=True
            )

            full_content = ""

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta

                    if delta.content:
                        full_content += delta.content
                        yield {
                            "type": "content",
                            "content": delta.content
                        }

            # 流式结束，返回完成信号
            yield {
                "type": "done",
                "full_content": full_content,
                "token_usage": None  # OpenAI 流式 API 不返回 token usage
            }

        except RateLimitError as e:
            yield {
                "type": "error",
                "error": f"API 速率限制: {str(e)}"
            }

        except APITimeoutError as e:
            yield {
                "type": "error",
                "error": f"API 请求超时: {str(e)}"
            }

        except APIError as e:
            yield {
                "type": "error",
                "error": f"API 错误: {str(e)}"
            }

        except Exception as e:
            yield {
                "type": "error",
                "error": f"未知错误: {str(e)}"
            }

    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """测试 API 连接

        Returns:
            Tuple: (是否成功, 错误信息)
        """
        test_messages = [
            {"role": "user", "content": "Hello"}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=test_messages,
                max_tokens=10
            )

            if response.choices:
                return True, None
            else:
                return False, "API 返回结果为空"

        except Exception as e:
            return False, str(e)

    def format_messages(
        self,
        system_prompt: Optional[str] = None,
        user_message: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """格式化消息列表

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            history: 历史消息

        Returns:
            List[Dict]: 格式化的消息列表
        """
        messages = []

        # 添加系统提示词
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加历史消息
        if history:
            messages.extend(history)

        # 添加用户消息
        if user_message:
            messages.append({
                "role": "user",
                "content": user_message
            })

        return messages

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息

        Returns:
            Dict: 配置信息
        """
        return {
            "base_url": self.base_url,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "api_key_configured": bool(self.api_key and self.api_key != "")
        }


def create_llm_service_from_config(config: Dict[str, Any]) -> LLMService:
    """从配置创建 LLM 服务实例

    Args:
        config: 配置字典（包含 LLM_CONFIG）

    Returns:
        LLMService: LLM 服务实例

    Raises:
        ValueError: 配置不完整
    """
    llm_config = config.get("LLM_CONFIG", {})

    base_url = llm_config.get("BASE_URL")
    api_key = llm_config.get("API_KEY")
    model = llm_config.get("MODEL")
    print(llm_config)
    if not base_url or not model:
        raise ValueError("LLM 配置不完整: 缺少 base_url 或 model")

    if not api_key:
        print("警告: 未配置 API Key,请通过环境变量 LLM_API_KEY 设置")

    return LLMService(
        base_url=base_url,
        api_key=api_key or "",
        model=model,
        max_tokens=llm_config.get("MAX_TOKENS", 2000),
        temperature=llm_config.get("TEMPERATURE", 0.7),
        timeout=llm_config.get("TIMEOUT", 60)
    )
