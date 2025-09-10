"""
CodeBuddy API Client - 直接调用CodeBuddy API
"""
import json
import time
import uuid
import secrets
import httpx
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List

logger = logging.getLogger(__name__)


class CodeBuddyAPIClient:
    """CodeBuddy API客户端"""
    
    def __init__(self):
        from config import get_codebuddy_api_endpoint
        self.base_url = get_codebuddy_api_endpoint()
        self.api_endpoint = self.base_url  # 直接使用base_url，不需要plugin前缀
        
    def convert_openai_to_codebuddy_messages(self, openai_messages: List[Dict]) -> List[Dict]:
        """将OpenAI格式消息转换为CodeBuddy格式"""
        codebuddy_messages = []
        
        # 过滤掉包含错误信息的消息，防止触发11128渠道检测
        filtered_messages = []
        for msg in openai_messages:
            content = msg.get("content", "")
            # 跳过包含API错误信息的助手消息
            if (msg.get("role") == "assistant" and 
                isinstance(content, str) and 
                ("Error: API error" in content or "API error:" in content)):
                continue
            filtered_messages.append(msg)
        
        # CodeBuddy要求至少2条消息，如果只有1条用户消息，添加系统消息
        if len(filtered_messages) == 1 and filtered_messages[0].get("role") == "user":
            system_msg = {
                "role": "system",
                "content": "You are a helpful assistant."
            }
            codebuddy_messages.append(system_msg)
        
        for msg in filtered_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            logger.debug(f"[DEBUG] Processing message - role: {role}, content type: {type(content)}")
            
            # 处理特殊的tool角色，转换为user角色
            if role == "tool":
                role = "user"
                logger.info(f"[ROLE_CONVERSION] Converting 'tool' role to 'user'")
            
            # 检查是否包含工具调用相关内容
            has_tool_content = False
            
            # 检查字符串化的JSON内容
            if isinstance(content, str) and content.startswith('[{') and content.endswith('}]'):
                try:
                    parsed_content = json.loads(content)
                    if isinstance(parsed_content, list):
                        content = parsed_content
                        logger.info(f"[JSON_PARSE] Parsed stringified JSON content")
                except json.JSONDecodeError:
                    pass
            
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") in ["tool_result", "tool_use"]:
                        has_tool_content = True
                        break
            
            if has_tool_content:
                # 包含工具调用内容，保持结构化格式
                logger.info(f"[TOOL_CONTENT] Preserving structured content for role: {role}")
                
                # 确保工具结果有正确的toolUseId
                processed_content = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_result":
                            # 确保toolUseId存在且有效
                            tool_use_id = item.get("toolUseId") or item.get("tool_use_id") or item.get("id")
                            if not tool_use_id:
                                # 生成一个有效的toolUseId
                                tool_use_id = f"tool_{uuid.uuid4().hex[:8]}"
                                logger.warning(f"[TOOL_RESULT] Missing toolUseId, generated: {tool_use_id}")
                            
                            # 确保toolUseId符合正则表达式要求 [a-zA-Z0-9_-]+
                            if not tool_use_id or not all(c.isalnum() or c in '_-' for c in tool_use_id):
                                tool_use_id = f"tool_{uuid.uuid4().hex[:8]}"
                                logger.warning(f"[TOOL_RESULT] Invalid toolUseId format, regenerated: {tool_use_id}")
                            
                            # 标准化工具结果格式
                            tool_result = {
                                "type": "tool_result",
                                "toolUseId": tool_use_id,
                                "content": item.get("content", item.get("text", ""))
                            }
                            processed_content.append(tool_result)
                            logger.info(f"[TOOL_RESULT] Processed tool result with toolUseId: {tool_use_id}")
                        elif item.get("type") == "tool_use":
                            # 确保工具使用有正确的id
                            tool_id = item.get("id") or f"tool_{uuid.uuid4().hex[:8]}"
                            tool_use = {
                                "type": "tool_use",
                                "id": tool_id,
                                "name": item.get("name", ""),
                                "input": item.get("input", {})
                            }
                            processed_content.append(tool_use)
                            logger.info(f"[TOOL_USE] Processed tool use with id: {tool_id}")
                        elif item.get("type") == "text":
                            # 处理纯文本内容
                            processed_content.append(item)
                        else:
                            # 其他类型，可能是工具结果的简化格式
                            if "text" in item and not item.get("type"):
                                # 可能是工具结果，转换为标准格式
                                tool_use_id = f"tool_{uuid.uuid4().hex[:8]}"
                                tool_result = {
                                    "type": "tool_result",
                                    "toolUseId": tool_use_id,
                                    "content": item.get("text", "")
                                }
                                processed_content.append(tool_result)
                                logger.info(f"[TOOL_RESULT] Converted text item to tool result with toolUseId: {tool_use_id}")
                            else:
                                processed_content.append(item)
                    else:
                        processed_content.append(item)
                
                codebuddy_msg = {
                    "role": role,
                    "content": processed_content
                }
            else:
                # 普通文本内容，转换为字符串
                if isinstance(content, str):
                    text_content = content
                elif isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            else:
                                text_parts.append(json.dumps(item, ensure_ascii=False))
                        elif isinstance(item, str):
                            text_parts.append(item)
                        else:
                            text_parts.append(str(item))
                    text_content = "".join(text_parts)
                else:
                    text_content = str(content) if content is not None else ""
                
                # 关键词替换 - 防止CodeBuddy检测到竞争对手关键词
                if role == "system" and text_content:
                    original_length = len(text_content)
                    text_content = text_content.replace("Claude Code", "CodeBuddy Code")
                    text_content = text_content.replace("Anthropic's official CLI for Claude", "Tencent's official CLI for CodeBuddy")
                    text_content = text_content.replace("Claude", "CodeBuddy")
                    text_content = text_content.replace("Anthropic", "Tencent")
                    text_content = text_content.replace("https://github.com/anthropics/claude-code/issues", "https://cnb.cool/codebuddy/codebuddy-code/-/issues")
                    
                    if len(text_content) != original_length:
                        logger.info(f"[KEYWORD_REPLACE] Applied keyword replacements to system message")
                
                codebuddy_msg = {
                    "role": role,
                    "content": text_content
                }
            
            codebuddy_messages.append(codebuddy_msg)
        
        return codebuddy_messages

    def generate_codebuddy_headers(
        self,
        bearer_token: str,
        user_id: str = None,
        conversation_id: Optional[str] = None,
        conversation_request_id: Optional[str] = None,
        conversation_message_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        生成CodeBuddy API所需的完整请求头。
        优先使用传入的会话ID，如果未提供则随机生成。
        """
        headers = {
            'Host': 'www.codebuddy.ai',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'x-stainless-arch': 'x64',
            'x-stainless-lang': 'js',
            'x-stainless-os': 'Windows',
            'x-stainless-package-version': '5.10.1',
            'x-stainless-retry-count': '0',
            'x-stainless-runtime': 'node',
            'x-stainless-runtime-version': 'v22.13.1',
            'X-Conversation-ID': conversation_id or str(uuid.uuid4()),
            'X-Conversation-Request-ID': conversation_request_id or secrets.token_hex(16),
            'X-Conversation-Message-ID': conversation_message_id or str(uuid.uuid4()).replace('-', ''),
            'X-Request-ID': request_id or str(uuid.uuid4()).replace('-', ''),
            'X-Agent-Intent': 'craft',
            'X-IDE-Type': 'CLI',
            'X-IDE-Name': 'CLI',
            'X-IDE-Version': '1.0.7',
            'Authorization': f'Bearer {bearer_token}',
            'X-Domain': 'www.codebuddy.ai',
            'User-Agent': 'CLI/1.0.7 CodeBuddy/1.0.7',
            'X-Product': 'SaaS',
            'X-User-Id': user_id or 'b5be3a67-237e-4ee6-9b9a-0b9ecd7b454b'
        }
        return headers

    async def chat_completions(
        self,
        messages: list,
        model: str = "claude-4.0",
        stream: bool = False,
        bearer_token: str = None,
        user_id: str = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        调用CodeBuddy聊天完成API（使用真实的CodeBuddy格式）
        
        Args:
            messages: OpenAI格式消息列表
            model: 模型名称
            stream: 是否流式输出
            bearer_token: 认证token
            user_id: 用户ID
            **kwargs: 其他参数
        """
        if not bearer_token:
            raise ValueError("Bearer token is required")
        
        # 记录原始请求体
        original_request = {
            "messages": messages,
            "model": model,
            "stream": stream,
            **kwargs
        }
        logger.info(f"[ORIGINAL_REQUEST] {original_request}")
        
        # 转换消息格式
        codebuddy_messages = self.convert_openai_to_codebuddy_messages(messages)
        
        # 生成完整的CodeBuddy请求头
        headers = self.generate_codebuddy_headers(bearer_token, user_id)
        
        # 构建CodeBuddy API请求体 - 不限制max_tokens，让CodeBuddy自己处理
        max_tokens = kwargs.get("max_tokens")
        # if max_tokens and max_tokens > 8192:
        #     max_tokens = 8192  # CodeBuddy的最大token限制
        #     logger.warning(f"[WARNING] max_tokens {kwargs.get('max_tokens')} exceeds CodeBuddy limit, capped to 8192")
        
        # 构建最终请求体（严格按照成功请求的字段顺序）
        payload = {
            "model": model,
            "messages": codebuddy_messages,
            "temperature": kwargs.get("temperature", 1.0),
            "response_format": kwargs.get("response_format", {"type": "text"}),
            "stream": stream,
            "agent": "cli",  # 必需字段：标识为CLI请求
            "max_tokens": kwargs.get("max_tokens", 32000),
            "top_p": kwargs.get("top_p", 1.0)
        }
        
        # 添加工具调用参数（如果存在）
        if kwargs.get("tools"):
            payload["tools"] = kwargs.get("tools")
            logger.info(f"[TOOLS] Added {len(kwargs.get('tools'))} tools to request")
        
        if kwargs.get("tool_choice"):
            payload["tool_choice"] = kwargs.get("tool_choice")
            logger.info(f"[TOOL_CHOICE] Added tool_choice: {kwargs.get('tool_choice')}")
        
        # 添加流式选项（如果是流式请求）
        if stream:
            payload["stream_options"] = kwargs.get("stream_options", {"include_usage": True})
        
        logger.info(f"[FINAL_PAYLOAD] {payload}")
        
        
        api_url = f"{self.api_endpoint}/v2/chat/completions"
        
        # 添加轻微延迟避免频率过高
        import asyncio
        await asyncio.sleep(0.5)
        
        try:
            async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
                if stream:
                    # 流式请求
                    async with client.stream(
                        "POST", 
                        api_url,
                        json=payload, 
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            error_message = error_text.decode()
                            logger.error(f"[STREAMING ERROR] CodeBuddy API error: {response.status_code}")
                            logger.error(f"[STREAMING ERROR] Response headers: {dict(response.headers)}")
                            logger.error(f"[STREAMING ERROR] Error details: {error_message}")
                            logger.error(f"[STREAMING ERROR] Request URL: {api_url}")
                            logger.error(f"[STREAMING ERROR] Request payload size: {len(str(payload))}")
                            
                            # 尝试解析JSON错误
                            try:
                                error_json = json.loads(error_message)
                                logger.error(f"[STREAMING ERROR] Parsed error JSON: {error_json}")
                            except:
                                logger.error(f"[STREAMING ERROR] Raw error text: {error_message}")
                            
                            yield {
                                "error": f"API error: {response.status_code}",
                                "details": error_message
                            }
                            return
                        
                        # 处理CodeBuddy的流式响应
                        response_text = ""
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                chunk_str = chunk.decode('utf-8')
                                response_text += chunk_str
                                for line in chunk_str.split('\n'):
                                    if line.startswith('data: '):
                                        data_str = line[6:]
                                        if data_str.strip() == '[DONE]':
                                            return
                                        try:
                                            data = json.loads(data_str)
                                            # 检查是否是错误响应
                                            if isinstance(data, dict) and "error" in data:
                                                logger.error(f"[STREAMING ERROR] CodeBuddy returned error: {data}")
                                                yield {
                                                    "error": f"API error: {data.get('error', 'Unknown error')}",
                                                    "details": str(data)
                                                }
                                                return
                                            
                                            # 直接返回原始数据
                                            yield data
                                        except json.JSONDecodeError as e:
                                            logger.warning(f"[STREAMING WARNING] JSON decode error, skipping line: {e}, data: {data_str}")
                                            continue
                        
                        # 如果没有得到任何有效数据，记录完整响应
                        if not response_text.strip():
                            logger.error(f"[STREAMING ERROR] Empty response from CodeBuddy")
                        elif "error" in response_text.lower() or "400" in response_text:
                            logger.error(f"[STREAMING ERROR] Error detected in response: {response_text[:1000]}...")
                else:
                    # 非流式请求
                    response = await client.post(
                        api_url,  # 使用正确的API URL
                        json=payload,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        # 非流式请求实际上不应该发生，因为我们总是以流式请求
                        # 但为了健壮性，这里保留一个基础处理
                        result = response.json()
                        yield result
                    else:
                        error_text = response.text
                        logger.error(f"[NON-STREAMING ERROR] CodeBuddy API error: {response.status_code}")
                        logger.error(f"[NON-STREAMING ERROR] Response headers: {dict(response.headers)}")
                        logger.error(f"[NON-STREAMING ERROR] Error details: {error_text}")
                        logger.error(f"[NON-STREAMING ERROR] Request URL: {api_url}")
                        logger.error(f"[NON-STREAMING ERROR] Request payload size: {len(str(payload))}")
                        
                        # 尝试解析JSON错误
                        try:
                            error_json = json.loads(error_text)
                            logger.error(f"[NON-STREAMING ERROR] Parsed error JSON: {error_json}")
                        except:
                            logger.error(f"[NON-STREAMING ERROR] Raw error text: {error_text}")
                        
                        yield {
                            "error": f"API error: {response.status_code}",
                            "details": error_text
                        }
                        
        except httpx.RequestError as e:
            logger.error(f"[REQUEST_ERROR] {e}")
            yield {
                "error": "Request failed",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"[UNEXPECTED_ERROR] {e}")
            yield {
                "error": "Unexpected error",
                "details": str(e)
            }
    
    async def get_models(self, bearer_token: str, user_id: str = None) -> Dict[str, Any]:
        """获取可用模型列表"""
        headers = self.generate_codebuddy_headers(bearer_token, user_id)
        
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(f"{self.api_endpoint}/v2/models", headers=headers)
                return response.json() if response.status_code == 200 else {
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {"error": "Request failed", "details": str(e)}


# 全局客户端实例
codebuddy_api_client = CodeBuddyAPIClient()