import sqlite3
from datetime import datetime
from contextlib import contextmanager


class Database:
    def __init__(self, db_name='crm_database.db'):
        self.db_name = db_name
        self.init_database()
    
    @contextmanager # - это чтобы не надо было вручную закрывать файл
    def get_connection(self):
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = sqlite3.Row  
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                company TEXT,
                phone TEXT,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deals_count INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT CHECK(status IN ('в работе', 'завершена', 'отменена')) DEFAULT 'в работе',
                amount REAL NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_date TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_id ON deals (client_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deal_status ON deals (status)')
    
    # ===== МЕТОДЫ ДЛЯ КЛИЕНТОВ =====
    
    def add_client(self, full_name, company='',phone='', notes=''):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO clients (full_name, company,  phone, notes)
            VALUES (?, ?, ?, ?)
            ''', (full_name, company, phone,notes))
            return cursor.lastrowid
    
    def get_all_clients(self, sort_by='id'):
        """Получение всех клиентов"""
        valid_sorts = ['id', 'full_name', 'deals_count', 'total_profit', 'created_date']
        sort_by = sort_by if sort_by in valid_sorts else 'id'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM clients ORDER BY {sort_by} DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_client_by_id(self, client_id):
        """Получение клиента по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_client(self, client_id, **kwargs):
        """Обновление данных клиента"""
        if not kwargs:
            return False
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(client_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
            UPDATE clients 
            SET {set_clause}
            WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_client(self, client_id):
        """Удаление клиента (каскадно удалит его сделки)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
            return cursor.rowcount > 0
    
    def search_clients(self, search_text):
        """Поиск клиентов по имени, компании или email"""
        search_pattern = f'%{search_text}%'
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM clients 
            WHERE full_name LIKE ? 
               OR company LIKE ? 
               OR email LIKE ?
               OR phone LIKE ?
               OR notes LIKE ?
            ORDER BY full_name
            ''', (search_pattern, search_pattern, search_pattern, search_pattern))
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== МЕТОДЫ ДЛЯ СДЕЛОК =====
    
    def add_deal(self, client_id, title, amount, description='', status='в работе'):
        """Добавление новой сделки"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO deals (client_id, title, description, status, amount)
            VALUES (?, ?, ?, ?, ?)
            ''', (client_id, title, description, status, amount))
            
            if status == 'завершена':
                cursor.execute('''
                UPDATE clients 
                SET deals_count = deals_count + 1,
                    total_profit = total_profit + ?
                WHERE id = ?
                ''', (amount, client_id))
            else:
                cursor.execute('''
                UPDATE clients 
                SET deals_count = deals_count + 1
                WHERE id = ?
                ''', (client_id,))
            
            return cursor.lastrowid
    
    def get_all_deals(self, status_filter='все', sort_by='created_date'):
        """Получение всех сделок с фильтрацией"""
        valid_sorts = ['id', 'title', 'amount', 'created_date', 'status']
        sort_by = sort_by if sort_by in valid_sorts else 'created_date'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status_filter == 'все':
                cursor.execute(f'''
                SELECT deals.*, clients.full_name as client_name 
                FROM deals 
                LEFT JOIN clients ON deals.client_id = clients.id
                ORDER BY {sort_by} DESC
                ''')
            else:
                cursor.execute(f'''
                SELECT deals.*, clients.full_name as client_name 
                FROM deals 
                LEFT JOIN clients ON deals.client_id = clients.id
                WHERE deals.status = ?
                ORDER BY {sort_by} DESC
                ''', (status_filter,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_deal_status(self, deal_id, new_status):
        """Обновление статуса сделки"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT client_id, amount, status FROM deals WHERE id = ?', (deal_id,))
            deal = cursor.fetchone()
            
            if not deal:
                return False
            
            client_id = deal['client_id']
            amount = deal['amount']
            old_status = deal['status']
            
            cursor.execute('''
            UPDATE deals 
            SET status = ?, 
                closed_date = CASE WHEN ? = 'завершена' THEN CURRENT_TIMESTAMP ELSE NULL END
            WHERE id = ?
            ''', (new_status, new_status, deal_id))
            
            if old_status != 'завершена' and new_status == 'завершена':
                cursor.execute('''
                UPDATE clients 
                SET total_profit = total_profit + ?
                WHERE id = ?
                ''', (amount, client_id))
            elif old_status == 'завершена' and new_status != 'завершена':
                cursor.execute('''
                UPDATE clients 
                SET total_profit = total_profit - ?
                WHERE id = ?
                ''', (amount, client_id))
            
            return cursor.rowcount > 0
    
    def delete_deal(self, deal_id):
        """Удаление сделки"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT client_id, amount, status FROM deals WHERE id = ?', (deal_id,))
            deal = cursor.fetchone()
            
            if deal and deal['status'] == 'завершена':
                cursor.execute('''
                UPDATE clients 
                SET deals_count = deals_count - 1,
                    total_profit = total_profit - ?
                WHERE id = ?
                ''', (deal['amount'], deal['client_id']))
            elif deal:
                cursor.execute('''
                UPDATE clients 
                SET deals_count = deals_count - 1
                WHERE id = ?
                ''', (deal['client_id'],))
            
            # Удаляем сделку
            cursor.execute('DELETE FROM deals WHERE id = ?', (deal_id,))
            return cursor.rowcount > 0
    
    def search_deals(self, search_text):
        search_pattern = f'%{search_text}%'
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT deals.*, clients.full_name as client_name 
            FROM deals 
            LEFT JOIN clients ON deals.client_id = clients.id
            WHERE deals.title LIKE ? 
               OR deals.description LIKE ?
               OR clients.full_name LIKE ?
            ORDER BY deals.created_date DESC
            ''', (search_pattern, search_pattern, search_pattern))
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== СТАТИСТИКА =====
    
    def get_statistics(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total_clients FROM clients')
            total_clients = cursor.fetchone()['total_clients']
            
            cursor.execute("SELECT COUNT(*) as active_deals FROM deals WHERE status = 'в работе'")
            active_deals = cursor.fetchone()['active_deals']
            
            cursor.execute("SELECT SUM(amount) as total_amount FROM deals WHERE status = 'завершена'")
            total_amount = cursor.fetchone()['total_amount'] or 0
            
            cursor.execute("SELECT COUNT(*) as total_deals FROM deals WHERE status = 'завершена'")
            closed_deals = cursor.fetchone()['total_deals'] or 0

            cursor.execute("SELECT COUNT(*) as all_deals FROM deals")
            count_deals = cursor.fetchone()['all_deals'] or 0
            
            conversion = 0
            if total_clients > 0:
                conversion = round((closed_deals / count_deals) * 100, 1)
            
            return {
                'total_clients': total_clients,
                'active_deals': active_deals,
                'total_amount': total_amount,
                'conversion': conversion
            }
    
    def get_top_clients_by_profit(self, limit=5):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT id, full_name, total_profit, deals_count
            FROM clients 
            WHERE total_profit > 0
            ORDER BY total_profit DESC 
            LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_deal_status_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM deals 
            GROUP BY status
            """)
            return {row['status']: row['count'] for row in cursor.fetchall()}

    def get_monthly_profit(self, months=6):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
            SELECT strftime('%Y-%m', created_date) as month, 
                SUM(amount) as total 
            FROM deals 
            WHERE status = 'завершена' 
            AND created_date >= date('now', '-{months} months')
            GROUP BY month 
            ORDER BY month
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_top_clients_chart(self, limit=5):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
            SELECT full_name, total_profit
            FROM clients 
            WHERE total_profit > 0
            ORDER BY total_profit DESC 
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
            
            
            
            