"""
SQL Agent Web Application
=========================
FastAPI server for the SQL Agent chat interface.
Supports conversation history and memory.
"""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sql_agent import SQLAgent
from chat_store import ChatStore
from config import HOST, PORT, DATABASE_PATH

# ── Startup Checks ───────────────────────────────────────
if not os.path.exists(DATABASE_PATH):
    print("=" * 60)
    print("❌ LỖI: Không tìm thấy file database!")
    print(f"Đường dẫn mục tiêu: {DATABASE_PATH}")
    print("-" * 60)
    print("HƯỚNG DẪN XỬ LÝ:")
    print("1. Kiểm tra xem bạn đã có file 'my_data.db' chưa.")
    print("2. Nếu chưa, hãy chạy lệnh sau để import dữ liệu từ CSV:")
    print("   python csv_to_db.py")
    print("=" * 60)
    # Don't exit here to allow for troubleshooting, but the agent won't work

# Initialize FastAPI app
app = FastAPI(
    title="SQL Agent",
    description="Trợ lý SQL thông minh - Hỏi đáp dữ liệu bằng tiếng Việt",
    version="2.0.0"
)

# Initialize SQL Agent and Chat Store
agent = SQLAgent()
store = ChatStore()

# Setup templates
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)


# ── Request/Response Models ──────────────────────────────

class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


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


# ── Chat API ─────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a natural language question with conversation memory.
    If conversation_id is not provided, creates a new conversation.
    """
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
    return {"status": "ok", "message": "SQL Agent is running", "version": "2.0.0"}


# ── Run ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🤖 SQL Agent v2.0 - Chat History & Memory")
    print("=" * 50)
    print()
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print()
    print("📝 Tính năng mới:")
    print("   • Lưu lịch sử hội thoại")
    print("   • AI nhớ ngữ cảnh cuộc trò chuyện")
    print("   • Chuyển đổi giữa các cuộc hội thoại")
    print()
    
    uvicorn.run(app, host=HOST, port=PORT)
