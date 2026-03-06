"""
SQL Agent - Core Module
========================
Custom SQL agent using OpenAI GPT-4o directly with SQLite database.
No Vanna dependency required.
"""

import sqlite3
import json
import re
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, DATABASE_PATH
from train_schema import SCHEMA_PROMPT


class SQLAgent:
    """
    SQL Agent that:
    1. Takes natural language questions
    2. Generates SQL using OpenAI
    3. Executes SQL on SQLite
    4. Returns formatted Vietnamese response
    """
    
    def __init__(self):
        """Initialize the SQL Agent."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.db_path = DATABASE_PATH
        # Base prompt without date context
        self._base_prompt = SCHEMA_PROMPT
        
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
Dữ liệu trong database có từ 2025-08-01 đến 2025-12-16 (tháng 8 đến tháng 12 năm 2025).

**Format ngày trong database:** YYYY-MM-DD (VD: 2025-03-10 = ngày 10 tháng 3 năm 2025)

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

Yêu cầu:
1. Chỉ trả về JSON với format: {{"sql": "SELECT ...", "explanation": "Giải thích ngắn gọn"}}
2. SQL phải tương thích với SQLite
3. Giải thích bằng tiếng Việt
4. Nếu không thể tạo SQL, trả về: {{"sql": null, "explanation": "Lý do không thể tạo SQL"}}
5. Nếu người dùng đề cập "ở trên", "vừa rồi", "kết quả đó" → hãy sử dụng ngữ cảnh từ lịch sử hội thoại.

Chỉ trả về JSON, không có text khác."""

        # Build messages with history
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if history:
            for msg in history[-40:]:  # Last 20 pairs
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response - remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            return {
                "sql": None,
                "explanation": f"Lỗi parse JSON từ OpenAI: {str(e)}"
            }
        except Exception as e:
            return {
                "sql": None,
                "explanation": f"Lỗi gọi OpenAI: {str(e)}"
            }
    
    def generate_response(self, question: str, sql: str, sql_result: dict) -> str:
        """
        Generate a natural language response in Vietnamese.
        IMPORTANT: Only uses the SQL query and result from the CURRENT question,
        not from any previous conversation history.
        """
        if not sql_result["success"]:
            return f"❌ Lỗi khi chạy SQL: {sql_result['error']}"
        
        # Format data for the prompt
        data_preview = sql_result["data"][:20]  # Limit to 20 rows for prompt
        
        prompt = f"""Dựa vào kết quả truy vấn SQL VỪA CHẠY, hãy trả lời câu hỏi của người dùng bằng tiếng Việt.

⚠️ CHÚ Ý: Chỉ sử dụng kết quả SQL bên dưới đây (KHÔNG dùng kết quả SQL từ lịch sử hội thoại trước đó).

Câu hỏi hiện tại: {question}

SQL VỪA CHẠY (query mới nhất): {sql}

Kết quả MỚI NHẤT ({sql_result['row_count']} dòng):
Columns: {sql_result['columns']}
Data: {data_preview}

Yêu cầu:
1. Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu
2. Nếu có số liệu, format đẹp (ví dụ: 1,234,567)
3. Tóm tắt insights quan trọng nếu có
4. Không cần lặp lại SQL query"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý phân tích dữ liệu. Luôn trả lời bằng tiếng Việt. Chỉ phân tích kết quả SQL MỚI NHẤT được cung cấp."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"❌ Lỗi tạo câu trả lời: {str(e)}"
    
    def chat(self, question: str, history: list = None) -> dict:
        """
        Main chat method - handles the full flow.
        
        Args:
            question: The user's question
            history: Optional list of previous messages for conversation context
        
        Returns:
            dict with 'answer', 'sql', 'sql_explanation', 'data', 'error'
        """
        result = {
            "question": question,
            "sql": None,
            "sql_explanation": None,
            "data": None,
            "columns": None,
            "row_count": 0,
            "answer": None,
            "error": None
        }
        
        # Step 1: Generate SQL (with history for context understanding)
        sql_gen = self.generate_sql(question, history=history)
        result["sql"] = sql_gen.get("sql")
        result["sql_explanation"] = sql_gen.get("explanation")
        
        if not result["sql"]:
            result["answer"] = sql_gen.get("explanation", "Không thể tạo câu truy vấn SQL.")
            return result
        
        # Step 2: Execute SQL
        sql_result = self.execute_sql(result["sql"])
        result["data"] = sql_result["data"]
        result["columns"] = sql_result["columns"]
        result["row_count"] = sql_result["row_count"]
        
        if not sql_result["success"]:
            result["error"] = sql_result["error"]
            result["answer"] = f"❌ Lỗi SQL: {sql_result['error']}"
            return result
        
        # Step 3: Generate response (ONLY using current SQL result, not history)
        result["answer"] = self.generate_response(question, result["sql"], sql_result)
        
        return result


# Test the agent
if __name__ == "__main__":
    print("🤖 Testing SQL Agent...")
    print("=" * 50)
    
    agent = SQLAgent()
    
    # Test question
    test_question = "Có bao nhiêu sự kiện trong database?"
    print(f"❓ Question: {test_question}")
    print()
    
    response = agent.chat(test_question)
    
    print(f"🔍 SQL: {response['sql']}")
    print(f"📝 Explanation: {response['sql_explanation']}")
    print(f"📊 Row count: {response['row_count']}")
    print()
    print(f"💬 Answer:")
    print(response['answer'])
