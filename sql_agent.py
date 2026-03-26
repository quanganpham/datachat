"""
SQL Agent - Core Module (Multi-Dataset)
========================================
Custom SQL agent using OpenAI GPT-4o directly with SQLite database.
Supports multiple datasets (Vaccine, Long Châu Pharmacy).
"""

import sqlite3
import json
import re
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, DATASETS
from train_schema import VACCINE_SCHEMA_PROMPT
from train_schema_lc import LONGCHAU_SCHEMA_PROMPT

# Map dataset keys to their schema prompts
SCHEMA_PROMPTS = {
    "vaccine": VACCINE_SCHEMA_PROMPT,
    "longchau": LONGCHAU_SCHEMA_PROMPT,
}


class SQLAgent:
    """
    SQL Agent that:
    1. Takes natural language questions
    2. Generates SQL using OpenAI
    3. Executes SQL on SQLite
    4. Returns formatted Vietnamese response
    
    Supports multiple datasets via dataset parameter.
    """
    
    def __init__(self, dataset="vaccine"):
        """Initialize the SQL Agent for a specific dataset."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.dataset = dataset
        self.db_path = DATASETS[dataset]["db_path"]
        self._base_prompt = SCHEMA_PROMPTS[dataset]
        
        # Dangerous SQL commands to block
        self.blocked_keywords = [
            'DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'TRUNCATE',
            'CREATE', 'REPLACE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
    
    @property
    def system_prompt(self):
        """Generate system prompt with current date context."""
        today = datetime.now()
        date_context = f"""
═══════════════════════════════════════════════════════════════
## 0. NGÀY HIỆN TẠI (QUAN TRỌNG!)
═══════════════════════════════════════════════════════════════

**Hôm nay là:** {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %d %B %Y')})
**Năm hiện tại:** {today.year}

Khi user hỏi về "hôm nay", "tuần này", "tháng này" → sử dụng năm {today.year}.

"""
        return date_context + self._base_prompt
    
    def validate_sql(self, sql: str) -> tuple[bool, str]:
        """
        Validate SQL to block dangerous commands.
        
        Returns:
            tuple(is_safe, error_message)
        """
        if not sql:
            return False, "SQL query is empty"
        
        sql_upper = sql.upper().strip()
        
        # Check for blocked keywords at the start of the query
        for keyword in self.blocked_keywords:
            if sql_upper.startswith(keyword):
                return False, f"❌ Lệnh {keyword} bị chặn. Chỉ cho phép SELECT query."
        
        # Additional check: must start with SELECT or WITH (for CTEs)
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return False, "❌ Chỉ cho phép SELECT query. Các lệnh khác bị chặn."
        
        # Check for dangerous keywords anywhere in the query (sub-query injection)
        for keyword in ['DELETE ', 'DROP ', 'INSERT ', 'UPDATE ', 'ALTER ', 'TRUNCATE ']:
            if keyword in sql_upper:
                return False, f"❌ Phát hiện lệnh nguy hiểm ({keyword.strip()}) trong query. Bị chặn."
        
        return True, ""
    
    def execute_sql(self, sql: str) -> dict:
        """
        Execute SQL query on SQLite database.
        
        Returns:
            dict with 'success', 'data', 'columns', 'error' keys
        """
        # Validate SQL first
        is_safe, error_msg = self.validate_sql(sql)
        if not is_safe:
            return {
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": error_msg
            }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Fetch all results
            rows = cursor.fetchall()
            conn.close()
            
            return {
                "success": True,
                "data": rows,
                "columns": columns,
                "row_count": len(rows),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": str(e)
            }
    
    def generate_sql(self, question: str, history: list = None) -> dict:
        """
        Generate SQL query from natural language question.
        Accepts optional history for conversation context.
        
        Returns:
            dict with 'sql', 'explanation' keys
        """
        prompt = f"""Dựa vào câu hỏi của người dùng, hãy tạo câu truy vấn SQL phù hợp.

Câu hỏi: {question}

HƯỚNG DẪN QUAN TRỌNG:
1. Nếu câu hỏi yêu cầu truy vấn dữ liệu → tạo SQL query và giải thích.
2. Nếu câu hỏi là follow-up/tiếp nối (ví dụ: "giải thích cách làm", "tại sao lại ra kết quả này", "chi tiết hơn") → Hãy xem lại lịch sử hội thoại (conversation history) ở trên và trả lời dựa trên ngữ cảnh trước đó. Giải thích CHI TIẾT từng bước.
3. Nếu câu hỏi hoàn toàn không liên quan đến dữ liệu (chào hỏi, hỏi thời tiết...) → trả lời trực tiếp.

Trả lời CHÍNH XÁC dạng JSON:
{{
  "sql": "SELECT ...",
  "explanation": "Giải thích ngắn gọn bằng tiếng Việt"
}}

Nếu KHÔNG cần SQL (follow-up hoặc câu hỏi chung), trả về:
{{
  "sql": null,
  "explanation": "Câu trả lời chi tiết, đầy đủ bằng tiếng Việt. Dùng markdown: **bold**, bullet list, số thứ tự khi liệt kê."
}}"""

        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history if available
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "sql": result.get("sql"),
                "explanation": result.get("explanation", "")
            }
        except Exception as e:
            return {
                "sql": None,
                "explanation": f"❌ Lỗi khi tạo SQL: {str(e)}"
            }
    
    def generate_answer(self, question: str, sql: str, data: list, columns: list, 
                        row_count: int, error: str = None, history: list = None) -> str:
        """
        Generate a natural language answer from SQL results.
        Uses conversation history for context-aware responses.
        """
        if error:
            context = f"""Câu hỏi: {question}
SQL đã thử: {sql}
Lỗi: {error}

Hãy giải thích lỗi và gợi ý cách hỏi lại bằng tiếng Việt."""
        else:
            # Format data for LLM
            data_preview = data[:20] if data else []
            data_str = ""
            if columns and data_preview:
                data_str = f"Cột: {columns}\nDữ liệu ({row_count} dòng):\n"
                for row in data_preview:
                    data_str += str(row) + "\n"
            
            context = f"""Câu hỏi: {question}
SQL: {sql}
{data_str}

Hãy trả lời câu hỏi dựa trên kết quả trên bằng tiếng Việt, rõ ràng và có cấu trúc.
Dùng markdown formatting: **bold** cho điểm quan trọng, bullet list khi liệt kê, format số với dấu phẩy ngăn cách hàng nghìn.
Không cần lặp lại SQL query."""

        messages = [{"role": "system", "content": self.system_prompt}]
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": context})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Lỗi khi tạo câu trả lời: {str(e)}"
    
    def chat(self, question: str, history: list = None) -> dict:
        """
        Full chat pipeline: Question → SQL → Execute → Answer.
        
        Returns:
            dict with 'question', 'sql', 'sql_explanation', 'answer', 
                  'data', 'columns', 'row_count', 'error'
        """
        # Step 1: Generate SQL
        sql_result = self.generate_sql(question, history=history)
        sql = sql_result["sql"]
        sql_explanation = sql_result["explanation"]
        
        # If no SQL needed (general chat)
        if not sql:
            return {
                "question": question,
                "sql": None,
                "sql_explanation": sql_explanation,
                "answer": sql_explanation,
                "data": None,
                "columns": None,
                "row_count": 0,
                "error": None
            }
        
        # Step 2: Execute SQL
        exec_result = self.execute_sql(sql)
        
        # Step 3: Generate answer
        answer = self.generate_answer(
            question, sql,
            exec_result["data"],
            exec_result["columns"],
            exec_result["row_count"],
            exec_result["error"],
            history=history
        )
        
        return {
            "question": question,
            "sql": sql,
            "sql_explanation": sql_explanation,
            "answer": answer,
            "data": exec_result["data"] if exec_result["success"] else None,
            "columns": exec_result["columns"] if exec_result["success"] else None,
            "row_count": exec_result["row_count"],
            "error": exec_result["error"]
        }
