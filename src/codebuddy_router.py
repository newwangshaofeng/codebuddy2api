"""
CodeBuddy API Router - 兼容CodeBuddy官方API格式
"""
import json
import time
import uuid
import secrets
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .auth import authenticate
from .codebuddy_api_client import codebuddy_api_client
from .codebuddy_token_manager import codebuddy_token_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# --- CodeBuddy V1 API Models ---

class CodeBuddyMessage(BaseModel):
    role: str
    content: Any  # 可以是字符串或复杂对象


# --- API Endpoints ---

@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,  # 使用原始 Request 对象，绕过 Pydantic 验证
    x_conversation_id: Optional[str] = Header(None, alias="X-Conversation-ID"),
    x_conversation_request_id: Optional[str] = Header(None, alias="X-Conversation-Request-ID"),
    x_conversation_message_id: Optional[str] = Header(None, alias="X-Conversation-Message-ID"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    _token: str = Depends(authenticate)
):
    """
    CodeBuddy V1 聊天完成API - 完全透传模式
    """
    try:
        # 获取原始请求体
        try:
            request_body = await request.json()
        except Exception as e:
            logger.error(f"解析请求体失败: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON request body: {str(e)}")
        
        # 获取CodeBuddy凭证
        credential = codebuddy_token_manager.get_next_credential()
        if not credential:
            raise HTTPException(status_code=401, detail="没有可用的CodeBuddy凭证")
        
        bearer_token = credential.get('bearer_token')
        user_id = credential.get('user_id')
        
        if not bearer_token:
            raise HTTPException(status_code=401, detail="无效的CodeBuddy凭证")
        
        # 生成请求头
        headers = codebuddy_api_client.generate_codebuddy_headers(
            bearer_token=bearer_token,
            user_id=user_id,
            conversation_id=x_conversation_id,
            conversation_request_id=x_conversation_request_id,
            conversation_message_id=x_conversation_message_id,
            request_id=x_request_id
        )
        
        # 完全透传请求体，但需要处理一些 CodeBuddy 的特殊要求
        payload = request_body.copy()
        payload["stream"] = True  # CodeBuddy 只支持流式请求
        
        # 处理消息长度要求：CodeBuddy要求至少2条消息
        messages = payload.get("messages", [])
        if len(messages) == 1 and messages[0].get("role") == "user":
            # 添加系统消息
            system_msg = {
                "role": "system",
                "content": "You are a helpful assistant."
            }
            payload["messages"] = [system_msg] + messages
        
        # 应用关键词替换 - 防止CodeBuddy检测到竞争对手关键词
        def apply_keyword_replacement(text):
            if isinstance(text, str):
                text = text.replace("Claude Code", "CodeBuddy Code")
                text = text.replace("Anthropic's official CLI for Claude", "Tencent's official CLI for CodeBuddy")
                text = text.replace("Claude", "CodeBuddy")
                text = text.replace("Anthropic", "Tencent")
                text = text.replace("https://github.com/anthropics/claude-code/issues", "https://cnb.cool/codebuddy/codebuddy-code/-/issues")
                return text
            return text
        
        # 对所有消息应用关键词替换
        for msg in payload.get("messages", []):
            if msg.get("role") == "system" and isinstance(msg.get("content"), str):
                msg["content"] = apply_keyword_replacement(msg["content"])
            elif isinstance(msg.get("content"), str):
                msg["content"] = apply_keyword_replacement(msg["content"])
            elif isinstance(msg.get("content"), list):
                for item in msg["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        item["text"] = apply_keyword_replacement(item.get("text", ""))
        
        
        # 发送请求到CodeBuddy
        import httpx
        try:
            async with httpx.AsyncClient(verify=False, timeout=300) as client:  # 增加超时时间
                response = await client.post(
                    "https://www.codebuddy.ai/v2/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CodeBuddy API错误: {response.status_code} - {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"CodeBuddy API error: {error_text}"
                    )
        except httpx.TimeoutException:
            logger.error("CodeBuddy API 超时")
            raise HTTPException(status_code=504, detail="CodeBuddy API timeout")
        except httpx.NetworkError as e:
            logger.error(f"网络错误: {e}")
            raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"请求异常: {e}")
            raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
        
        # 检查客户端是否期望流式响应
        client_wants_stream = request_body.get("stream", False)
        
        if client_wants_stream:
            # 客户端要求流式，直接透传
            async def stream_response():
                try:
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk
                except Exception as e:
                    logger.error(f"流式响应错误: {e}")
                    error_chunk = f'data: {{"error": "Stream interrupted: {str(e)}"}}\n\n'
                    yield error_chunk.encode('utf-8')
            
            return StreamingResponse(
                stream_response(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*"
                }
            )
        else:
            # 客户端要求非流式，收集并合并所有流式响应块（真正透传）
            all_chunks = []
            
            # 收集所有流式响应块
            async for chunk in response.aiter_bytes():
                if chunk:
                    chunk_str = chunk.decode('utf-8')
                    for line in chunk_str.split('\n'):
                        if line.startswith('data: ') and not line.endswith('[DONE]'):
                            try:
                                data_str = line[6:]  # 移除 'data: ' 前缀
                                chunk_data = json.loads(data_str)
                                
                                # 收集所有有效的响应块
                                if "choices" in chunk_data:
                                    all_chunks.append(chunk_data)
                                    
                            except json.JSONDecodeError:
                                continue
            
            # 如果有响应块，合并为非流式格式
            if all_chunks:
                # 使用第一个块作为基础
                base_response = all_chunks[0].copy()
                base_response["object"] = "chat.completion"
                base_response["created"] = int(time.time())
                
                # 合并所有块的内容
                if "choices" in base_response and base_response["choices"]:
                    choice = base_response["choices"][0]
                    
                    # 如果第一个块就有完整的delta，直接转换
                    if "delta" in choice:
                        # 合并所有块的delta内容
                        merged_delta = choice["delta"].copy()
                        
                        
                        # 合并所有块的内容（包括第一个块）
                        merged_content = merged_delta.get("content", "") or ""
                        merged_tool_calls = {}  # 使用字典按index组织
                        
                        # 处理所有块（包括第一个）
                        for chunk in all_chunks:
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    merged_content += delta["content"]
                                if "tool_calls" in delta:
                                    # 合并工具调用参数
                                    for new_tool_call in delta["tool_calls"]:
                                        if new_tool_call.get("index") is not None:
                                            index = new_tool_call["index"]
                                            
                                            # 初始化工具调用槽位
                                            if index not in merged_tool_calls:
                                                merged_tool_calls[index] = {
                                                    "index": index,
                                                    "function": {"name": "", "arguments": ""}
                                                }
                                            
                                            # 合并工具调用信息
                                            if "function" in new_tool_call:
                                                # 合并参数字符串
                                                if "arguments" in new_tool_call["function"]:
                                                    merged_tool_calls[index]["function"]["arguments"] += new_tool_call["function"]["arguments"]
                                                
                                                # 设置工具名称（保留非空值）
                                                if "name" in new_tool_call["function"] and new_tool_call["function"]["name"]:
                                                    merged_tool_calls[index]["function"]["name"] = new_tool_call["function"]["name"]
                                            
                                            # 更新其他字段（id, type等）
                                            for key, value in new_tool_call.items():
                                                if key not in ["function", "index"]:
                                                    merged_tool_calls[index][key] = value
                        
                        # 转换为数组格式
                        merged_delta["content"] = merged_content
                        if merged_tool_calls:
                            merged_delta["tool_calls"] = list(merged_tool_calls.values())
                        
                        # 转换delta为message
                        choice["message"] = merged_delta
                        choice["message"]["role"] = choice["message"].get("role", "assistant")
                        choice["finish_reason"] = "stop"
                        if 'delta' in choice:
                            del choice["delta"]
                        
                
                return base_response
            else:
                # 如果没有收到有效响应，返回错误
                return {
                    "error": "No valid response received from CodeBuddy",
                    "details": "Stream ended without complete response"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CodeBuddy V1 API错误: {e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@router.get("/v1/models")
async def list_v1_models(_token: str = Depends(authenticate)):
    """获取CodeBuddy V1模型列表"""
    try:
        # 获取凭证
        credential = codebuddy_token_manager.get_next_credential()
        if not credential:
            raise HTTPException(status_code=401, detail="没有可用的CodeBuddy凭证")
        
        models = [
            "claude-4.0",
            "claude-3.7", 
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "o4-mini",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "auto-chat"
        ]
        
        return {
            "object": "list",
            "data": [{
                "id": model,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "codebuddy"
            } for model in models]
        }
        
    except Exception as e:
        logger.error(f"获取V1模型列表错误: {e}")
        raise HTTPException(status_code=500, detail="获取模型列表失败")

@router.get("/v1/credentials", summary="List all available credentials")
async def list_credentials(_token: str = Depends(authenticate)):
    """列出所有可用凭证的简略信息"""
    credentials = codebuddy_token_manager.get_all_credentials()
    safe_credentials = []
    for i, cred in enumerate(credentials):
        bearer_token = cred.get("bearer_token", "")
        safe_cred = {
            "index": i,
            "user_id": cred.get("user_id", "unknown"),
            "created_at": cred.get("created_at", 0),
            "has_token": bool(bearer_token),
            "token_preview": f"{bearer_token[:10]}...{bearer_token[-4:]}" if bearer_token and len(bearer_token) > 14 else "Invalid Token"
        }
        safe_credentials.append(safe_cred)
    
    return {"credentials": safe_credentials}


@router.post("/v1/credentials", summary="Add a new credential")
async def add_credential(
    request: Request,
    _token: str = Depends(authenticate)
):
    """添加一个新的认证凭证"""
    try:
        data = await request.json()
        bearer_token = data.get("bearer_token")
        user_id = data.get("user_id")
        filename = data.get("filename")

        if not bearer_token:
            raise HTTPException(status_code=422, detail="bearer_token is required")

        success = codebuddy_token_manager.add_credential(bearer_token, user_id, filename)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save credential file")
        
        return {"message": "Credential added successfully"}

    except Exception as e:
        logger.error(f"添加凭证失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))