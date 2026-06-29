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
                current_motorcycle_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Motorcycles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS motorcycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                model TEXT,
                year INTEGER,
                current_mileage INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Maintenance records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                motorcycle_id INTEGER DEFAULT 1,
                maintenance_type TEXT NOT NULL,
                mileage INTEGER NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                price REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (motorcycle_id) REFERENCES motorcycles(id)
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

        # Seasonal reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasonal_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                reminder_type TEXT NOT NULL,
                reminder_date TEXT,
                enabled INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # MOT/Technical inspection table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mot_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                motorcycle_id INTEGER DEFAULT 1,
                inspection_date TEXT NOT NULL,
                next_inspection_date TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (motorcycle_id) REFERENCES motorcycles(id)
            )
        ''')

        # Parts/Inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                motorcycle_id INTEGER DEFAULT 1,
                name TEXT NOT NULL,
                part_number TEXT,
                quantity INTEGER DEFAULT 1,
                purchase_date TEXT,
                expiry_date TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (motorcycle_id) REFERENCES motorcycles(id)
            )
        ''')

        # Trips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                motorcycle_id INTEGER DEFAULT 1,
                start_location TEXT,
                end_location TEXT,
                distance_km REAL NOT NULL,
                date TEXT NOT NULL,
                duration_minutes INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (motorcycle_id) REFERENCES motorcycles(id)
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

        # Create default motorcycle if user doesn't have any
        motorcycles = self.get_motorcycles(user_id)
        if not motorcycles:
            self.add_motorcycle(user_id, "Мій мотоцикл")

    def add_motorcycle(self, user_id: int, name: str, model: str = None, year: int = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO motorcycles (user_id, name, model, year)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, model, year))
        conn.commit()
        conn.close()

    def get_motorcycles(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, model, year, current_mileage
            FROM motorcycles
            WHERE user_id = ?
            ORDER BY created_at
        ''', (user_id,))

        motorcycles = []
        for row in cursor.fetchall():
            motorcycles.append({
                'id': row[0],
                'name': row[1],
                'model': row[2],
                'year': row[3],
                'current_mileage': row[4]
            })

        conn.close()
        return motorcycles

    def get_current_motorcycle(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT current_motorcycle_id FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            motorcycle_id = result[0]
            motorcycles = self.get_motorcycles(user_id)
            for moto in motorcycles:
                if moto['id'] == motorcycle_id:
                    return moto
        return None

    def set_current_motorcycle(self, user_id: int, motorcycle_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET current_motorcycle_id = ? WHERE user_id = ?
        ''', (motorcycle_id, user_id))
        conn.commit()
        conn.close()

    def update_motorcycle_mileage(self, motorcycle_id: int, mileage: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE motorcycles SET current_mileage = ? WHERE id = ?
        ''', (mileage, motorcycle_id))
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
    
    def add_maintenance_record(self, user_id: int, maintenance_type: str, mileage: int, notes: str = None, price: float = 0, motorcycle_id: int = None):
        if motorcycle_id is None:
            current_moto = self.get_current_motorcycle(user_id)
            motorcycle_id = current_moto['id'] if current_moto else 1

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance_records (user_id, motorcycle_id, maintenance_type, mileage, notes, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, motorcycle_id, maintenance_type, mileage, notes, price))
        conn.commit()
        conn.close()
    
    def get_maintenance_records(self, user_id: int, maintenance_type: str = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if maintenance_type:
            cursor.execute('''
                SELECT id, motorcycle_id, maintenance_type, mileage, date, notes, price
                FROM maintenance_records
                WHERE user_id = ? AND maintenance_type = ?
                ORDER BY date DESC
            ''', (user_id, maintenance_type))
        else:
            cursor.execute('''
                SELECT id, motorcycle_id, maintenance_type, mileage, date, notes, price
                FROM maintenance_records
                WHERE user_id = ?
                ORDER BY date DESC
            ''', (user_id,))

        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'motorcycle_id': row[1],
                'type': row[2],
                'mileage': row[3],
                'date': row[4],
                'notes': row[5],
                'price': row[6]
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
        type_costs = {}
        total_cost = 0

        for record in records:
            type_counts[record['type']] = type_counts.get(record['type'], 0) + 1
            cost = record.get('price', 0) or 0
            type_costs[record['type']] = type_costs.get(record['type'], 0) + cost
            total_cost += cost

        return {
            'total_records': len(records),
            'type_counts': type_counts,
            'current_mileage': current_mileage,
            'total_cost': total_cost,
            'type_costs': type_costs
        }

    # Seasonal reminders methods
    def set_seasonal_reminder(self, user_id: int, reminder_type: str, reminder_date: str = None, enabled: bool = True):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO seasonal_reminders (user_id, reminder_type, reminder_date, enabled)
            VALUES (?, ?, ?, ?)
        ''', (user_id, reminder_type, reminder_date, 1 if enabled else 0))
        conn.commit()
        conn.close()

    def get_seasonal_reminder(self, user_id: int, reminder_type: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT reminder_date, enabled
            FROM seasonal_reminders
            WHERE user_id = ? AND reminder_type = ?
        ''', (user_id, reminder_type))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'reminder_date': result[0],
                'enabled': bool(result[1])
            }
        return None

    def get_all_seasonal_reminders(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT reminder_type, reminder_date, enabled
            FROM seasonal_reminders
            WHERE user_id = ?
        ''', (user_id,))

        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                'reminder_type': row[0],
                'reminder_date': row[1],
                'enabled': bool(row[2])
            })

        conn.close()
        return reminders

    # MOT/Technical inspection methods
    def add_mot_record(self, user_id: int, inspection_date: str, next_inspection_date: str, notes: str = None, motorcycle_id: int = None):
        if motorcycle_id is None:
            current_moto = self.get_current_motorcycle(user_id)
            motorcycle_id = current_moto['id'] if current_moto else 1

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO mot_records (user_id, motorcycle_id, inspection_date, next_inspection_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, motorcycle_id, inspection_date, next_inspection_date, notes))
        conn.commit()
        conn.close()

    def get_mot_records(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, motorcycle_id, inspection_date, next_inspection_date, notes, created_at
            FROM mot_records
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'motorcycle_id': row[1],
                'inspection_date': row[2],
                'next_inspection_date': row[3],
                'notes': row[4],
                'created_at': row[5]
            })

        conn.close()
        return records

    def get_next_mot_reminder(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT next_inspection_date, motorcycle_id
            FROM mot_records
            WHERE user_id = ?
            ORDER BY next_inspection_date DESC
            LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'next_inspection_date': result[0],
                'motorcycle_id': result[1]
            }
        return None

    # Parts/Inventory methods
    def add_part(self, user_id: int, name: str, part_number: str = None, quantity: int = 1,
                 purchase_date: str = None, expiry_date: str = None, notes: str = None, motorcycle_id: int = None):
        if motorcycle_id is None:
            current_moto = self.get_current_motorcycle(user_id)
            motorcycle_id = current_moto['id'] if current_moto else 1

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO parts_inventory (user_id, motorcycle_id, name, part_number, quantity, purchase_date, expiry_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, motorcycle_id, name, part_number, quantity, purchase_date, expiry_date, notes))
        conn.commit()
        conn.close()

    def get_parts(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, motorcycle_id, name, part_number, quantity, purchase_date, expiry_date, notes
            FROM parts_inventory
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        parts = []
        for row in cursor.fetchall():
            parts.append({
                'id': row[0],
                'motorcycle_id': row[1],
                'name': row[2],
                'part_number': row[3],
                'quantity': row[4],
                'purchase_date': row[5],
                'expiry_date': row[6],
                'notes': row[7]
            })

        conn.close()
        return parts

    def update_part_quantity(self, part_id: int, quantity: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE parts_inventory SET quantity = ? WHERE id = ?
        ''', (quantity, part_id))
        conn.commit()
        conn.close()

    def delete_part(self, part_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM parts_inventory WHERE id = ?', (part_id,))
        conn.commit()
        conn.close()

    def get_expiring_parts(self, user_id: int, days: int = 30) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, expiry_date, quantity
            FROM parts_inventory
            WHERE user_id = ? AND expiry_date IS NOT NULL
        ''', (user_id,))

        parts = []
        from datetime import datetime, timedelta
        today = datetime.now()
        threshold = today + timedelta(days=days)

        for row in cursor.fetchall():
            try:
                expiry_date = datetime.strptime(row[2], '%d.%m.%Y')
                if expiry_date <= threshold:
                    parts.append({
                        'id': row[0],
                        'name': row[1],
                        'expiry_date': row[2],
                        'quantity': row[3]
                    })
            except ValueError:
                continue

        conn.close()
        return parts

    # Trips methods
    def add_trip(self, user_id: int, start_location: str, end_location: str, distance_km: float,
                 date: str, duration_minutes: int = None, notes: str = None, motorcycle_id: int = None):
        if motorcycle_id is None:
            current_moto = self.get_current_motorcycle(user_id)
            motorcycle_id = current_moto['id'] if current_moto else 1

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trips (user_id, motorcycle_id, start_location, end_location, distance_km, date, duration_minutes, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, motorcycle_id, start_location, end_location, distance_km, date, duration_minutes, notes))
        conn.commit()
        conn.close()

    def get_trips(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, motorcycle_id, start_location, end_location, distance_km, date, duration_minutes, notes
            FROM trips
            WHERE user_id = ?
            ORDER BY date DESC
        ''', (user_id,))

        trips = []
        for row in cursor.fetchall():
            trips.append({
                'id': row[0],
                'motorcycle_id': row[1],
                'start_location': row[2],
                'end_location': row[3],
                'distance_km': row[4],
                'date': row[5],
                'duration_minutes': row[6],
                'notes': row[7]
            })

        conn.close()
        return trips

    def get_trip_statistics(self, user_id: int) -> Dict:
        trips = self.get_trips(user_id)

        total_distance = 0
        total_duration = 0
        total_trips = len(trips)

        for trip in trips:
            total_distance += trip['distance_km']
            if trip['duration_minutes']:
                total_duration += trip['duration_minutes']

        return {
            'total_trips': total_trips,
            'total_distance': total_distance,
            'total_duration': total_duration
        }

    # Backup/Export methods
    def export_to_json(self, user_id: int) -> str:
        import json
        from datetime import datetime

        data = {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'motorcycles': self.get_motorcycles(user_id),
            'maintenance_records': self.get_maintenance_records(user_id),
            'knowledge_base': self.get_all_knowledge_items(user_id),
            'seasonal_reminders': self.get_all_seasonal_reminders(user_id),
            'mot_records': self.get_mot_records(user_id),
            'parts_inventory': self.get_parts(user_id),
            'trips': self.get_trips(user_id)
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def import_from_json(self, user_id: int, json_data: str):
        import json

        data = json.loads(json_data)

        # Import motorcycles
        for moto in data.get('motorcycles', []):
            self.add_motorcycle(user_id, moto['name'], moto.get('model'), moto.get('year'))

        # Import maintenance records
        for record in data.get('maintenance_records', []):
            self.add_maintenance_record(
                user_id,
                record['type'],
                record['mileage'],
                record.get('notes'),
                record.get('price', 0),
                record.get('motorcycle_id')
            )

        # Import knowledge base
        for item in data.get('knowledge_base', []):
            self.add_knowledge_item(
                user_id,
                item['title'],
                item['url'],
                item.get('description'),
                None,
                item.get('category')
            )

        # Import seasonal reminders
        for reminder in data.get('seasonal_reminders', []):
            self.set_seasonal_reminder(
                user_id,
                reminder['reminder_type'],
                reminder.get('reminder_date'),
                reminder['enabled']
            )

        # Import MOT records
        for mot in data.get('mot_records', []):
            self.add_mot_record(
                user_id,
                mot['inspection_date'],
                mot['next_inspection_date'],
                mot.get('notes'),
                mot.get('motorcycle_id')
            )

        # Import parts
        for part in data.get('parts_inventory', []):
            self.add_part(
                user_id,
                part['name'],
                part.get('part_number'),
                part.get('quantity', 1),
                part.get('purchase_date'),
                part.get('expiry_date'),
                part.get('notes'),
                part.get('motorcycle_id')
            )

        # Import trips
        for trip in data.get('trips', []):
            self.add_trip(
                user_id,
                trip.get('start_location'),
                trip.get('end_location'),
                trip['distance_km'],
                trip['date'],
                trip.get('duration_minutes'),
                trip.get('notes'),
                trip.get('motorcycle_id')
            )
