"""
CodeBuddy Router - 处理CodeBuddy API请求
"""
import json
import time
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import StreamingResponse

from .models import (
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    ChatCompletionChoice,
    ModelList, 
    Model,
    Message
)
from .auth import authenticate
from .codebuddy_api_client import codebuddy_api_client
from .codebuddy_token_manager import codebuddy_token_manager
from config import get_available_models

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/v1/models", response_model=ModelList)
async def list_models(_token: str = Depends(authenticate)):
    """返回可用的CodeBuddy模型列表"""
    # CodeBuddy没有公开的模型列表API，直接返回配置的默认模型列表
    models = get_available_models()
    return ModelList(data=[
        Model(id=model_id, created=int(time.time())) for model_id in models
    ])


@router.post("/v1/chat/completions")
async def chat_completions(
    http_request: Request,
    x_session_id: Optional[str] = Header(None),
    x_working_directory: Optional[str] = Header(None),
    _token: str = Depends(authenticate)
):
    """处理聊天完成请求"""
    
    # 先记录原始请求体
    try:
        body = await http_request.body()
        # 尝试不同的编码方式
        try:
            raw_data = body.decode('utf-8')
        except UnicodeDecodeError:
            try:
                raw_data = body.decode('gbk')
            except UnicodeDecodeError:
                raw_data = body.decode('utf-8', errors='replace')

        logger.debug(f"[RAW REQUEST] Received request body (length: {len(raw_data)})")
        logger.debug(f"[RAW REQUEST] Body preview: {raw_data[:500]}...")

        # 尝试解析JSON
        parsed_data = json.loads(raw_data)
        logger.debug(f"[PARSED] Model: {parsed_data.get('model')}, Stream: {parsed_data.get('stream')}")
        logger.debug(f"[PARSED] Messages count: {len(parsed_data.get('messages', []))}")

        # 现在尝试创建ChatCompletionRequest对象
        request = ChatCompletionRequest(**parsed_data)
        logger.debug(f"[SUCCESS] Successfully parsed ChatCompletionRequest")

    except Exception as e:
        logger.error(f"[ERROR] Failed to parse request: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid request format: {str(e)}")
    
    # 记录请求
    logger.info(f"Chat completion request: model={request.model}, stream={request.stream}")
    
    try:
        # 获取认证凭证
        credential = codebuddy_token_manager.get_next_credential()
        if not credential:
            raise HTTPException(
                status_code=401, 
                detail="No valid CodeBuddy credentials found. Please add credential files to .codebuddy_creds directory."
            )
        
        bearer_token = credential.get('bearer_token')
        user_id = credential.get('user_id')
        
        if not bearer_token:
            raise HTTPException(status_code=401, detail="Invalid credential: missing bearer_token")
        
        if request.stream:
            # 流式响应
            async def stream_generator():
                try:
                    response_id = f"chatcmpl-{uuid.uuid4().hex}"
                    async for chunk_data in codebuddy_api_client.chat_completions(
                        messages=[msg.dict() for msg in request.messages],
                        model=request.model,
                        stream=True,
                        bearer_token=bearer_token,
                        user_id=user_id,
                        **{k: v for k, v in {
                            'temperature': request.temperature,
                            'max_tokens': request.max_tokens,
                            'top_p': request.top_p,
                            'tools': request.tools,
                            'tool_choice': request.tool_choice
                        }.items() if v is not None}
                    ):
                        if "error" in chunk_data:
                            error_content = {"error": chunk_data.get("details", str(chunk_data))}
                            yield f"data: {json.dumps(error_content)}\n\n"
                            yield "data: [DONE]\n\n"
                            return
                        
                        # 直接转发CodeBuddy响应
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                
                except Exception as e:
                    logger.error(f"Stream error: {str(e)}")
                    error_content = {"error": f"An unexpected error occurred: {str(e)}"}
                    yield f"data: {json.dumps(error_content)}\n\n"
                    yield "data: [DONE]\n\n"
            
            # 添加会话ID到响应头
            response = StreamingResponse(
                stream_generator(), 
                media_type="text/event-stream",
                headers={"X-Session-ID": x_session_id or f"session-{uuid.uuid4().hex[:8]}"}
            )
            return response
        
        else:
            # 非流式响应
            collected_content = ""
            response_id = f"chatcmpl-{uuid.uuid4().hex}"
            final_usage = None
            
            async for chunk_data in codebuddy_api_client.chat_completions(
                messages=[msg.dict() for msg in request.messages],
                model=request.model,
                stream=True,  # 强制使用流式
                bearer_token=bearer_token,
                user_id=user_id,
                **{k: v for k, v in {
                    'temperature': request.temperature,
                    'max_tokens': request.max_tokens,
                    'top_p': request.top_p,
                    'tools': request.tools,
                    'tool_choice': request.tool_choice
                }.items() if v is not None}
            ):
                if "error" in chunk_data:
                    raise HTTPException(status_code=500, detail=chunk_data["error"])

                if "choices" in chunk_data and chunk_data["choices"]:
                    delta = chunk_data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        collected_content += content
                
                if "usage" in chunk_data:
                    final_usage = chunk_data["usage"]

            return {
                "id": response_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": collected_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": final_usage
            }
    
    except Exception as e:
        logger.error(f"Chat completion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/credentials")
async def list_credentials(_token: str = Depends(authenticate)):
    """列出所有可用凭证"""
    credentials = codebuddy_token_manager.get_all_credentials()
    safe_credentials = []
    for i, cred in enumerate(credentials):
        bearer_token = cred.get("bearer_token", "")
        safe_cred = {
            "index": i,
            "user_id": cred.get("user_id", "unknown"),
            "created_at": cred.get("created_at", 0),
            "has_token": bool(bearer_token),
            "token_preview": bearer_token[:20] + "..." if bearer_token else None
        }
        safe_credentials.append(safe_cred)
    
    return {"credentials": safe_credentials}


@router.post("/v1/credentials")
async def add_credential(
    bearer_token: str,
    user_id: Optional[str] = None,
    filename: Optional[str] = None,
    _token: str = Depends(authenticate)
):
    """添加新的认证凭证"""
    success = codebuddy_token_manager.add_credential(bearer_token, user_id, filename)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add credential")
    return {"message": "Credential added successfully"}