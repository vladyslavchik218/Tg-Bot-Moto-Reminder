import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "motorcycle_diary.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                current_mileage INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Maintenance records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                maintenance_type TEXT NOT NULL,
                mileage INTEGER NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Knowledge base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                keywords TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reminder_type TEXT NOT NULL,
                last_check_mileage INTEGER,
                last_check_date TIMESTAMP,
                next_remind_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Maintenance intervals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_intervals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                maintenance_type TEXT NOT NULL,
                interval_km INTEGER NOT NULL,
                interval_days INTEGER,
                last_mileage INTEGER,
                last_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()
    
    def update_mileage(self, user_id: int, mileage: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET current_mileage = ? WHERE user_id = ?', (mileage, user_id))
        conn.commit()
        conn.close()
    
    def get_current_mileage(self, user_id: int) -> Optional[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_mileage FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def add_maintenance_record(self, user_id: int, maintenance_type: str, mileage: int, notes: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance_records (user_id, maintenance_type, mileage, notes)
            VALUES (?, ?, ?, ?)
        ''', (user_id, maintenance_type, mileage, notes))
        conn.commit()
        conn.close()
    
    def get_maintenance_records(self, user_id: int, maintenance_type: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if maintenance_type:
            cursor.execute('''
                SELECT id, maintenance_type, mileage, date, notes 
                FROM maintenance_records 
                WHERE user_id = ? AND maintenance_type = ?
                ORDER BY date DESC
            ''', (user_id, maintenance_type))
        else:
            cursor.execute('''
                SELECT id, maintenance_type, mileage, date, notes 
                FROM maintenance_records 
                WHERE user_id = ?
                ORDER BY date DESC
            ''', (user_id,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'type': row[1],
                'mileage': row[2],
                'date': row[3],
                'notes': row[4]
            })
        
        conn.close()
        return records
    
    def get_last_maintenance(self, user_id: int, maintenance_type: str) -> Optional[Dict]:
        records = self.get_maintenance_records(user_id, maintenance_type)
        return records[0] if records else None
    
    def add_knowledge_item(self, user_id: int, title: str, url: str, description: str = None, 
                          keywords: str = None, category: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge_base (user_id, title, url, description, keywords, category)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, url, description, keywords, category))
        conn.commit()
        conn.close()
    
    def search_knowledge_base(self, user_id: int, query: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, url, description, keywords, category 
            FROM knowledge_base 
            WHERE user_id = ? AND (
                title LIKE ? OR 
                description LIKE ? OR 
                keywords LIKE ? OR
                category LIKE ?
            )
            ORDER BY created_at DESC
        ''', (user_id, f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0],
                'title': row[1],
                'url': row[2],
                'description': row[3],
                'keywords': row[4],
                'category': row[5]
            })
        
        conn.close()
        return items
    
    def get_all_knowledge_items(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, url, description, keywords, category 
            FROM knowledge_base 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0],
                'title': row[1],
                'url': row[2],
                'description': row[3],
                'keywords': row[4],
                'category': row[5]
            })
        
        conn.close()
        return items
    
    def update_reminder(self, user_id: int, reminder_type: str, last_check_mileage: int = None, 
                      last_check_date: str = None, next_remind_date: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO reminders 
            (user_id, reminder_type, last_check_mileage, last_check_date, next_remind_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, reminder_type, last_check_mileage, last_check_date, next_remind_date))
        conn.commit()
        conn.close()
    
    def get_reminder(self, user_id: int, reminder_type: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT last_check_mileage, last_check_date, next_remind_date 
            FROM reminders 
            WHERE user_id = ? AND reminder_type = ?
        ''', (user_id, reminder_type))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'last_check_mileage': result[0],
                'last_check_date': result[1],
                'next_remind_date': result[2]
            }
        return None
    
    def get_all_users(self) -> List[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
    
    # Maintenance intervals methods
    def set_maintenance_interval(self, user_id: int, maintenance_type: str, interval_km: int, 
                                interval_days: int = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO maintenance_intervals 
            (user_id, maintenance_type, interval_km, interval_days)
            VALUES (?, ?, ?, ?)
        ''', (user_id, maintenance_type, interval_km, interval_days))
        conn.commit()
        conn.close()
    
    def get_maintenance_interval(self, user_id: int, maintenance_type: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT interval_km, interval_days, last_mileage, last_date 
            FROM maintenance_intervals 
            WHERE user_id = ? AND maintenance_type = ?
        ''', (user_id, maintenance_type))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'interval_km': result[0],
                'interval_days': result[1],
                'last_mileage': result[2],
                'last_date': result[3]
            }
        return None
    
    def update_maintenance_interval_last(self, user_id: int, maintenance_type: str, 
                                        last_mileage: int, last_date: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE maintenance_intervals 
            SET last_mileage = ?, last_date = ?
            WHERE user_id = ? AND maintenance_type = ?
        ''', (last_mileage, last_date, user_id, maintenance_type))
        conn.commit()
        conn.close()
    
    def get_all_intervals(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT maintenance_type, interval_km, interval_days, last_mileage, last_date 
            FROM maintenance_intervals 
            WHERE user_id = ?
        ''', (user_id,))
        
        intervals = []
        for row in cursor.fetchall():
            intervals.append({
                'maintenance_type': row[0],
                'interval_km': row[1],
                'interval_days': row[2],
                'last_mileage': row[3],
                'last_date': row[4]
            })
        
        conn.close()
        return intervals
    
    # Statistics methods
    def get_statistics(self, user_id: int) -> Dict:
        records = self.get_maintenance_records(user_id)
        current_mileage = self.get_current_mileage(user_id)
        
        # Count by type
        type_counts = {}
        for record in records:
            type_counts[record['type']] = type_counts.get(record['type'], 0) + 1
        
        return {
            'total_records': len(records),
            'type_counts': type_counts,
            'current_mileage': current_mileage
        }
