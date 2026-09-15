"""
Асинхронная база данных для Членометра
"""

import sqlite3
import asyncio
from datetime import datetime


class Database:
    def __init__(self, db_name='dickup.db'):
        self.db_name = db_name
        self.lock = asyncio.Lock()
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                dick_size REAL DEFAULT 0.0,
                wank_count INTEGER DEFAULT 0,
                last_wank TEXT,
                last_up TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_stats (
                server_id TEXT,
                user_id TEXT,
                dick_size REAL DEFAULT 0.0,
                wank_count INTEGER DEFAULT 0,
                PRIMARY KEY (server_id, user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def get_user(self, user_id, username=None):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row and username:
                cursor.execute('''
                    INSERT INTO users (user_id, username, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, username, datetime.now().isoformat()))
                conn.commit()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
            
            user = dict(row) if row else None
            conn.close()
            return user
    
    async def update_username(self, user_id, username):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET username = ? WHERE user_id = ?
            ''', (username, user_id))
            conn.commit()
            conn.close()
    
    async def add_wank(self, user_id, username=None):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO users (user_id, username, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, username, datetime.now().isoformat()))
            
            cursor.execute('''
                UPDATE users 
                SET wank_count = wank_count + 1, last_wank = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            cursor.execute('SELECT wank_count FROM users WHERE user_id = ?', (user_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
    
    async def add_size(self, user_id, amount, username=None):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO users (user_id, username, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, username, datetime.now().isoformat()))
            
            cursor.execute('''
                UPDATE users 
                SET dick_size = dick_size + ?, last_up = ?
                WHERE user_id = ?
            ''', (amount, datetime.now().isoformat(), user_id))
            
            conn.commit()
            cursor.execute('SELECT dick_size FROM users WHERE user_id = ?', (user_id,))
            size = cursor.fetchone()[0]
            conn.close()
            return size
    
    async def get_global_top(self, limit=10):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, dick_size, wank_count 
                FROM users 
                ORDER BY dick_size DESC 
                LIMIT ?
            ''', (limit,))
            top = cursor.fetchall()
            conn.close()
            return [dict(row) for row in top]
    
    async def get_global_top_by_wanks(self, limit=10):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, dick_size, wank_count 
                FROM users 
                ORDER BY wank_count DESC 
                LIMIT ?
            ''', (limit,))
            top = cursor.fetchall()
            conn.close()
            return [dict(row) for row in top]
    
    async def get_server_top(self, server_id, limit=10):
        """
        Получает топ пользователей сервера.
        Сначала проверяет server_stats, если пусто — берёт всех пользователей из users
        """
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Сначала пробуем получить из server_stats
            cursor.execute('''
                SELECT u.username, s.dick_size, s.wank_count
                FROM server_stats s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.server_id = ?
                ORDER BY s.dick_size DESC
                LIMIT ?
            ''', (server_id, limit))
            top = cursor.fetchall()
            
            # Если server_stats пустой для этого сервера, берём просто всех пользователей
            if not top:
                print(f" server_stats пуст для {server_id}, берём из users")
                cursor.execute('''
                    SELECT username, dick_size, wank_count
                    FROM users
                    WHERE wank_count > 0 OR dick_size > 0
                    ORDER BY dick_size DESC
                    LIMIT ?
                ''', (limit,))
                top = cursor.fetchall()
            
            conn.close()
            return [dict(row) for row in top]
    
    async def update_server_stats(self, server_id, user_id, dick_size, wank_count):
        """Обновляет или создаёт запись статистики для пользователя на сервере"""
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO server_stats (server_id, user_id, dick_size, wank_count)
                VALUES (?, ?, ?, ?)
            ''', (server_id, user_id, dick_size, wank_count))
            conn.commit()
            conn.close()
    
    async def get_user_server_stats(self, server_id, user_id):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dick_size, wank_count FROM server_stats
                WHERE server_id = ? AND user_id = ?
            ''', (server_id, user_id))
            stats = cursor.fetchone()
            conn.close()
            return dict(stats) if stats else None
    
    async def get_total_users(self):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            conn.close()
            return count
    
    async def get_total_wanks(self):
        async with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(wank_count) FROM users')
            total = cursor.fetchone()[0] or 0
            conn.close()
            return total