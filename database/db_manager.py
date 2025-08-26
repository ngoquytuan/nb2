import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    # Dán đoạn code này vào file database/db_manager.py, thay thế cho hàm init_database() cũ

    def init_database(self):
        """Khởi tạo database và các bảng"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Tạo bảng system_settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                data_type TEXT DEFAULT 'string',
                description TEXT,
                category TEXT DEFAULT 'general',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Tạo bảng messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                sender TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                classification TEXT,
                naive_bayes_score REAL,
                llm_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        ''')

        # 3. Tạo bảng logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filter_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                step TEXT,
                result TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        ''')
        
        # 4. Insert default settings
        default_settings = [
            ('llm_provider', 'openai', 'string', 'LLM Provider (openai/groq/openrouter)', 'llm'),
            ('openai_api_key', '', 'password', 'OpenAI API Key', 'llm'),
            ('groq_api_key', '', 'password', 'Groq API Key', 'llm'), 
            ('openrouter_api_key', '', 'password', 'OpenRouter API Key', 'llm'),
            ('naive_bayes_threshold', '0.7', 'float', 'Ngưỡng confidence cho Naive Bayes', 'filter'),
            ('suspicious_threshold', '0.5', 'float', 'Ngưỡng đánh dấu suspicious', 'filter'),
            ('enable_mock_fallback', 'true', 'boolean', 'Bật mock analysis khi LLM lỗi', 'system'),
            ('max_processing_time', '30', 'int', 'Timeout tối đa (giây)', 'system'),
            ('enable_health_check', 'true', 'boolean', 'Bật kiểm tra health LLM', 'system')
        ]
        
        for key, value, data_type, desc, category in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO system_settings 
                (key, value, data_type, description, category) 
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, data_type, desc, category))
        
        # FIX: Chỉ commit và close kết nối một lần duy nhất ở cuối hàm
        conn.commit()
        conn.close()
    
    # Thêm methods cho settings
    def get_setting(self, key: str, default=None):
        """Lấy giá trị setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value, data_type FROM system_settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return default
            
        value, data_type = result
        
        # Convert theo data type
        if data_type == 'int':
            return int(value)
        elif data_type == 'float':
            return float(value)
        elif data_type == 'boolean':
            return value.lower() in ('true', '1', 'yes')
        else:
            return value

    def update_setting(self, key: str, value: any):
        """Cập nhật setting một cách an toàn"""
        try:
            # 'with' sẽ tự động quản lý việc commit hoặc rollback
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE system_settings 
                    SET value = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE key = ?
                ''', (str(value), key))
            # Khi khối 'with' kết thúc mà không có lỗi, conn.commit() được tự động gọi
        except sqlite3.Error as e:
            # In ra lỗi nếu có vấn đề khi ghi vào database
            print(f"Database error while updating setting '{key}': {e}")

    def get_all_settings(self) -> Dict:
        """Lấy tất cả settings theo category"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM system_settings ORDER BY category, key")
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for row in rows:
            category = row['category']
            if category not in settings:
                settings[category] = []
                
            settings[category].append({
                'key': row['key'],
                'value': row['value'],
                'data_type': row['data_type'],
                'description': row['description'],
                'updated_at': row['updated_at']
            })
        
        return settings
        
    def add_message(self, content: str, sender: str) -> int:
        """Thêm message vào queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO messages (content, sender) VALUES (?, ?)",
            (content, sender)
        )
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_pending_messages(self) -> List[Dict]:
        """Lấy các message chưa xử lý"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM messages WHERE status = 'pending' ORDER BY created_at"
        )
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return messages
    
    def update_message_status(self, message_id: int, status: str, 
                            classification: str = None, 
                            naive_bayes_score: float = None,
                            llm_score: float = None):
        """Cập nhật trạng thái message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = ["status = ?", "processed_at = CURRENT_TIMESTAMP"]
        values = [status]
        
        if classification:
            update_fields.append("classification = ?")
            values.append(classification)
        
        if naive_bayes_score is not None:
            update_fields.append("naive_bayes_score = ?")
            values.append(naive_bayes_score)
            
        if llm_score is not None:
            update_fields.append("llm_score = ?")
            values.append(llm_score)
        
        values.append(message_id)
        
        query = f"UPDATE messages SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def log_filter_step(self, message_id: int, step: str, result: str, details: str = None):
        """Ghi log các bước filter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO filter_logs (message_id, step, result, details) VALUES (?, ?, ?, ?)",
            (message_id, step, result, details or "")
        )
        
        conn.commit()
        conn.close()
    
    def get_inbox_messages(self, status: str = 'approved') -> List[Dict]:
        """Lấy messages trong inbox"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM messages WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return messages
    
    def get_all_messages_with_logs(self) -> List[Dict]:
        """Lấy tất cả messages kèm logs để debug"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT m.*, 
                   GROUP_CONCAT(
                       fl.step || ': ' || fl.result || 
                       CASE WHEN fl.details != '' THEN ' (' || fl.details || ')' ELSE '' END
                       , ' | '
                   ) as filter_history
            FROM messages m
            LEFT JOIN filter_logs fl ON m.id = fl.message_id
            GROUP BY m.id
            ORDER BY m.created_at DESC
        '''
        
        cursor.execute(query)
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return messages