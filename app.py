"""
SQL Agent Web Application (Multi-Dataset)
==========================================
FastAPI server for the SQL Agent chat interface.
Supports multiple datasets (Vaccine + Long Châu Pharmacy).
"""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sql_agent import SQLAgent
from chat_store import ChatStore
from config import HOST, PORT, DATASETS

# ── Startup Checks ───────────────────────────────────────
for key, cfg in DATASETS.items():
    if not os.path.exists(cfg["db_path"]):
        print(f"⚠️ Database cho [{key}] chưa tồn tại: {cfg['db_path']}")
        print(f"   Chạy: python csv_to_db.py")

# Initialize FastAPI app
app = FastAPI(
    title="SQL Agent - Multi-Dataset",
    description="Trợ lý SQL thông minh - Hỏi đáp dữ liệu bằng tiếng Việt",
    version="3.0.0"
)

# Initialize SQL Agents for each dataset
agents = {}
for key in DATASETS:
    try:
        agents[key] = SQLAgent(dataset=key)
    except Exception as e:
        print(f"⚠️ Không thể khởi tạo agent [{key}]: {e}")

store = ChatStore()

# Setup templates and static files
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ── Request/Response Models ──────────────────────────────

class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    dataset: str = "vaccine"  # "vaccine" or "longchau"


class ChatResponse(BaseModel):
    question: str
    sql: str | None
    sql_explanation: str | None
    answer: str
    data: list | None
    columns: list | None
    row_count: int
    error: str | None
    conversation_id: str


class ConversationRename(BaseModel):
    title: str


# ── Page Routes ──────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})


# ── Dataset API ──────────────────────────────────────────

@app.get("/datasets")
async def list_datasets():
    """List available datasets with metadata."""
    return {
        key: {
            "name": cfg["name"],
            "short_name": cfg["short_name"],
            "icon": cfg["icon"],
            "description": cfg["description"],
            "color": cfg["color"],
            "available": key in agents,
        }
        for key, cfg in DATASETS.items()
    }


# ── Chat API ─────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a natural language question with conversation memory.
    Supports dataset selection per request.
    """
    dataset = request.dataset
    if dataset not in agents:
        raise HTTPException(status_code=400, detail=f"Dataset '{dataset}' không khả dụng.")
    
    agent = agents[dataset]
    conv_id = request.conversation_id

    # Create new conversation if needed
    if not conv_id:
        conv = store.create_conversation()
        conv_id = conv["id"]

    # Get conversation history for context
    history = store.get_history_for_llm(conv_id, max_pairs=20)

    # Save user message
    store.add_message(conv_id, "user", request.question)

    # Process with agent (passing history for context)
    result = agent.chat(request.question, history=history)

    # Save assistant message (with SQL metadata)
    store.add_message(
        conv_id, "assistant", result["answer"],
        sql_query=result.get("sql"),
        sql_data=result.get("data"),
        sql_columns=result.get("columns"),
        row_count=result.get("row_count", 0)
    )

    # Auto-title on first message
    msgs = store.get_messages(conv_id)
    if len(msgs) <= 2:  # First Q&A pair
        store.auto_title(conv_id, request.question)

    return ChatResponse(
        conversation_id=conv_id,
        **result
    )


# ── Conversation API ─────────────────────────────────────

@app.get("/conversations")
async def list_conversations():
    """List all conversations for sidebar."""
    return store.list_conversations()


@app.post("/conversations")
async def create_conversation():
    """Create a new empty conversation."""
    return store.create_conversation()


@app.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str):
    """Get all messages for a conversation."""
    conv = store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "conversation": conv,
        "messages": store.get_messages(conv_id)
    }


@app.put("/conversations/{conv_id}")
async def rename_conversation(conv_id: str, body: ConversationRename):
    """Rename a conversation."""
    conv = store.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    store.rename_conversation(conv_id, body.title)
    return {"status": "ok"}


@app.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation and all its messages."""
    store.delete_conversation(conv_id)
    return {"status": "ok"}


# ── Health ───────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "SQL Agent is running",
        "version": "3.0.0",
        "datasets": list(agents.keys())
    }


# ── Run ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🤖 SQL Agent v3.0 - Multi-Dataset")
    print("=" * 50)
    print()
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print()
    print("📊 Datasets:")
    for key, cfg in DATASETS.items():
        status = "✅" if key in agents else "❌"
        print(f"   {status} {cfg['icon']} {cfg['name']}")
    print()
    
    uvicorn.run(app, host=HOST, port=PORT)
