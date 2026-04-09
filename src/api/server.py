from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
import os
import json

from config.settings import settings
from src.brain.llm import QwenLLM, LLMResponse
from src.brain.waza_skills import WazaSkillsManager, WazaSkillRequest
from src.brain.memory import ConversationMemory
from src.tools.handlers import CodeExecutor, FileHandler, WebSearch
from src.api.auth import AuthManager

# Pydantic models
class QueryRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"

class SkillRequest(BaseModel):
    input: str
    context: Optional[Dict[str, Any]] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class CodeExecuteRequest(BaseModel):
    code: str
    language: str

class FileRequest(BaseModel):
    file_path: str
    content: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="Jarvis AI Assistant",
    description="Personal AI assistant with Waza Skills powered by Qwen LLM",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
llm: Optional[QwenLLM] = None
waza: Optional[WazaSkillsManager] = None
memory: Optional[ConversationMemory] = None
auth: Optional[AuthManager] = None
code_executor: Optional[CodeExecutor] = None
file_handler: Optional[FileHandler] = None
web_search: Optional[WebSearch] = None
active_websockets: Dict[str, WebSocket] = {}


@app.on_event("startup")
async def startup_event():
    global llm, waza, memory, auth, code_executor, file_handler, web_search
    
    # Initialize LLM
    api_type = settings.QWEN_API_TYPE
    llm = QwenLLM(
        api_type=api_type,
        api_key=settings.QWEN_API_KEY if api_type == "dashscope" else None,
        base_url=settings.QWEN_BASE_URL if api_type == "dashscope" else settings.OLLAMA_BASE_URL,
        model=settings.QWEN_MODEL if api_type == "dashscope" else settings.OLLAMA_MODEL,
        temperature=settings.TEMPERATURE,
        top_p=settings.TOP_P,
        max_tokens=settings.MAX_TOKENS,
    )
    
    # Initialize Waza Skills
    waza = WazaSkillsManager(llm)
    
    # Initialize Memory
    memory = ConversationMemory()
    await memory.initialize()
    
    # Initialize Auth
    auth = AuthManager()
    
    # Initialize Tools
    code_executor = CodeExecutor()
    file_handler = FileHandler()
    web_search = WebSearch()
    
    print(f"🤖 Jarvis Assistant initialized")
    print(f"📚 Model: {settings.QWEN_MODEL}")
    print(f"🛠️  Available skills: {', '.join(waza.get_available_skills())}")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "model": settings.QWEN_MODEL,
        "available_skills": waza.get_available_skills() if waza else [],
    }


@app.post("/query")
async def query(request: QueryRequest):
    if not llm:
        raise HTTPException(status_code=500, detail="LLM not initialized")
    
    try:
        response = await llm.query(request.message)
        
        # Save to memory
        if memory and request.user_id != "anonymous":
            await memory.save_conversation(
                conversation_id=str(uuid4()),
                user_id=request.user_id,
                user_message=request.message,
                assistant_message=response.content,
                tokens_input=response.tokens.input,
                tokens_output=response.tokens.output,
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/skill/{skill_name}")
async def use_skill(skill_name: str, request: SkillRequest):
    if not waza:
        raise HTTPException(status_code=500, detail="Waza skills not initialized")
    
    try:
        response = await waza.execute_skill(
            WazaSkillRequest(
                skill=skill_name,
                input=request.input,
                context=request.context,
            )
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/skills")
async def list_skills():
    if not waza:
        raise HTTPException(status_code=500, detail="Waza skills not initialized")
    
    skills = [
        {
            "name": s.name,
            "description": s.description,
            "enabled": s.enabled,
        }
        for s in waza.list_skills()
    ]
    return {"skills": skills}


@app.get("/skills/{skill_name}")
async def get_skill_info(skill_name: str):
    if not waza:
        raise HTTPException(status_code=500, detail="Waza skills not initialized")
    
    skill = waza.get_skill_info(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {
        "name": skill.name,
        "description": skill.description,
        "enabled": skill.enabled,
    }


# Authentication endpoints
@app.post("/auth/register")
async def register(user: UserCreate):
    if not auth:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    
    try:
        result = await auth.create_user(
            user_id=str(uuid4()),
            username=user.username,
            email=user.email,
            password=user.password,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
async def login(user: UserLogin):
    if not auth:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    
    result = await auth.authenticate_user(user.username, user.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return result


# Conversation history endpoints
@app.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 50, offset: int = 0):
    if not memory:
        raise HTTPException(status_code=500, detail="Memory not initialized")
    
    conversations = await memory.get_user_conversations(user_id, limit, offset)
    return {
        "conversations": [
            {
                "id": c.id,
                "user_message": c.user_message,
                "assistant_message": c.assistant_message,
                "skill_used": c.skill_used,
                "timestamp": c.timestamp.isoformat(),
                "tokens": {"input": c.tokens_input, "output": c.tokens_output},
            }
            for c in conversations
        ]
    }


@app.get("/history/{user_id}/stats")
async def get_history_stats(user_id: str):
    if not memory:
        raise HTTPException(status_code=500, detail="Memory not initialized")
    
    stats = await memory.get_conversation_stats(user_id)
    return stats


@app.post("/history/{user_id}/clear")
async def clear_history(user_id: str):
    if not memory:
        raise HTTPException(status_code=500, detail="Memory not initialized")
    
    count = await memory.clear_user_history(user_id)
    return {"message": f"Cleared {count} conversations", "count": count}


# Tool endpoints
@app.post("/tools/execute")
async def execute_code(request: CodeExecuteRequest):
    if not code_executor:
        raise HTTPException(status_code=500, detail="Code executor not initialized")
    
    result = await code_executor.execute(request.code, request.language)
    return {
        "success": result.success,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
    }


@app.get("/tools/file/read")
async def read_file(file_path: str):
    if not file_handler:
        raise HTTPException(status_code=500, detail="File handler not initialized")
    
    result = await file_handler.read_file(file_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.post("/tools/file/write")
async def write_file(request: FileRequest):
    if not file_handler:
        raise HTTPException(status_code=500, detail="File handler not initialized")
    
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    result = await file_handler.write_file(request.file_path, request.content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.get("/tools/search")
async def search_web(query: str, num_results: int = 5):
    if not web_search:
        raise HTTPException(status_code=500, detail="Web search not initialized")
    
    result = await web_search.search(query, num_results)
    return result


# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_websockets[user_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message = message_data.get("message", "")
                skill = message_data.get("skill")
                
                if skill and waza:
                    response = await waza.execute_skill(
                        WazaSkillRequest(skill=skill, input=message)
                    )
                elif llm:
                    response = await llm.query(message)
                else:
                    response = {"content": "Service not available"}
                
                await websocket.send_json({
                    "status": "success",
                    "content": response.content if hasattr(response, 'content') else response.get("content", ""),
                    "timestamp": datetime.now().isoformat(),
                })
            except json.JSONDecodeError:
                # Treat as plain text message
                if llm:
                    response = await llm.query(data)
                    await websocket.send_json({
                        "status": "success",
                        "content": response.content,
                        "timestamp": datetime.now().isoformat(),
                    })
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                })
    except WebSocketDisconnect:
        active_websockets.pop(user_id, None)
    except Exception as e:
        active_websockets.pop(user_id, None)


# Serve static files (web UI)
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def serve_ui():
    ui_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "static",
        "index.html",
    )
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    return HTMLResponse(
        content="<h1>Jarvis AI Assistant</h1><p>UI not found. Run with static files.</p>"
    )
