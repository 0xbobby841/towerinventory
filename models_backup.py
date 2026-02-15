"""
Database models and CRUD operations for Inventory Management System
Uses SQLite with full relational integrity
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class Database:
    """Main database handler for the inventory system"""
    
    def __init__(self, db_path: str = "working.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection with foreign key support"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def create_tables(self):
        """Create all required tables with proper relationships"""
        
        # Technicians table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                technician_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Locations table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT
            )
        """)
        
        # Location Details table (for addresses)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS location_details (
                detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                apartment_number TEXT
            )
        """)
        
        # Inventory Items table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                unit_price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """)
        
        # Service Orders table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_orders (
                service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_number TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                date_created TEXT NOT NULL,
                technician_id INTEGER,
                location_id INTEGER,
                FOREIGN KEY (technician_id) REFERENCES technicians(technician_id),
                FOREIGN KEY (location_id) REFERENCES locations(location_id)
            )
        """)
        
        # Transactions table (append-only)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                technician_id INTEGER NOT NULL,
                service_id INTEGER,
                location_id INTEGER NOT NULL,
                action_type TEXT NOT NULL CHECK(action_type IN ('Install', 'Remove', 'Repair')),
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
                FOREIGN KEY (technician_id) REFERENCES technicians(technician_id),
                FOREIGN KEY (service_id) REFERENCES service_orders(service_id),
                FOREIGN KEY (location_id) REFERENCES locations(location_id)
            )
        """)
        
        self.conn.commit()
    
    # ==================== TECHNICIANS ====================
    
    def add_technician(self, name: str) -> int:
        """Add a new technician"""
        try:
            self.cursor.execute("INSERT INTO technicians (name) VALUES (?)", (name,))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Technician '{name}' already exists")
    
    def get_all_technicians(self) -> List[Tuple]:
        """Get all technicians"""
        self.cursor.execute("SELECT technician_id, name FROM technicians ORDER BY name")
        return self.cursor.fetchall()
    
    def update_technician(self, technician_id: int, name: str):
        """Update technician name"""
        self.cursor.execute("UPDATE technicians SET name = ? WHERE technician_id = ?", 
                          (name, technician_id))
        self.conn.commit()
    
    def delete_technician(self, technician_id: int):
        """Delete a technician"""
        self.cursor.execute("DELETE FROM technicians WHERE technician_id = ?", (technician_id,))
        self.conn.commit()
    
    # ==================== LOCATIONS ====================
    
    def add_location(self, name: str, address: str = "") -> int:
        """Add a new location"""
        try:
            self.cursor.execute("INSERT INTO locations (name, address) VALUES (?, ?)", 
                              (name, address))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Location '{name}' already exists")
    
    def get_all_locations(self) -> List[Tuple]:
        """Get all locations"""
        self.cursor.execute("SELECT location_id, name, address FROM locations ORDER BY name")
        return self.cursor.fetchall()
    
    def update_location(self, location_id: int, name: str, address: str = ""):
        """Update location details"""
        self.cursor.execute("UPDATE locations SET name = ?, address = ? WHERE location_id = ?",
                          (name, address, location_id))
        self.conn.commit()
    
    def delete_location(self, location_id: int):
        """Delete a location"""
        self.cursor.execute("DELETE FROM locations WHERE location_id = ?", (location_id,))
        self.conn.commit()
    
    # ==================== LOCATION DETAILS ====================
    
    def add_location_detail(self, address: str, apartment_number: str = "") -> int:
        """Add a new location detail"""
        self.cursor.execute("INSERT INTO location_details (address, apartment_number) VALUES (?, ?)", 
                          (address, apartment_number))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_location_details(self) -> List[Tuple]:
        """Get all location details"""
        self.cursor.execute("SELECT detail_id, address, apartment_number FROM location_details ORDER BY address")
        return self.cursor.fetchall()
    
    def update_location_detail(self, detail_id: int, address: str, apartment_number: str = ""):
        """Update location detail"""
        self.cursor.execute("UPDATE location_details SET address = ?, apartment_number = ? WHERE detail_id = ?",
                          (address, apartment_number, detail_id))
        self.conn.commit()
    
    def delete_location_detail(self, detail_id: int):
        """Delete a location detail"""
        self.cursor.execute("DELETE FROM location_details WHERE detail_id = ?", (detail_id,))
        self.conn.commit()
    
    # ==================== INVENTORY ITEMS ====================
    
    def add_inventory_item(self, name: str, description: str, unit_price: float, 
                          stock: int) -> int:
        """Add a new inventory item"""
        self.cursor.execute("""
            INSERT INTO inventory_items (name, description, unit_price, stock) 
            VALUES (?, ?, ?, ?)
        """, (name, description, unit_price, stock))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_inventory_items(self) -> List[Dict]:
        """Get all inventory items"""
        self.cursor.execute("""
            SELECT item_id, name, description, unit_price, stock 
            FROM inventory_items 
            ORDER BY name
        """)
        items = []
        for row in self.cursor.fetchall():
            item = {
                'item_id': row[0],
                'name': row[1],
                'description': row[2],
                'unit_price': row[3],
                'stock': row[4]
            }
            items.append(item)
        return items
    
    def update_inventory_item(self, item_id: int, name: str, description: str, 
                             unit_price: float, stock: int):
        """Update inventory item"""
        self.cursor.execute("""
            UPDATE inventory_items 
            SET name = ?, description = ?, unit_price = ?, stock = ? 
            WHERE item_id = ?
        """, (name, description, unit_price, stock, item_id))
        
        self.conn.commit()
    
    def delete_inventory_item(self, item_id: int):
        """Delete an inventory item"""
        self.cursor.execute("DELETE FROM inventory_items WHERE item_id = ?", (item_id,))
        self.conn.commit()
    
    def update_stock(self, item_id: int, quantity_change: int):
        """Update stock quantity (positive to add, negative to remove)"""
        self.cursor.execute("""
            UPDATE inventory_items 
            SET stock = stock + ? 
            WHERE item_id = ?
        """, (quantity_change, item_id))
        self.conn.commit()
    
    # ==================== SERVICE ORDERS ====================
    
    def add_service_order(self, service_number: str, address: str, 
                         technician_id: int = None, location_id: int = None) -> int:
        """Add a new service order"""
        date_created = datetime.now().isoformat()
        try:
            self.cursor.execute("""
                INSERT INTO service_orders (service_number, address, date_created, 
                                          technician_id, location_id)
                VALUES (?, ?, ?, ?, ?)
            """, (service_number, address, date_created, technician_id, location_id))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Service number '{service_number}' already exists")
    
    def get_service_order_by_number(self, service_number: str) -> Optional[Tuple]:
        """Get service order by service number"""
        self.cursor.execute("""
            SELECT service_id, service_number, address, date_created, 
                   technician_id, location_id
            FROM service_orders 
            WHERE service_number = ?
        """, (service_number,))
        return self.cursor.fetchone()
    
    def get_all_service_orders(self) -> List[Tuple]:
        """Get all service orders"""
        self.cursor.execute("""
            SELECT so.service_id, so.service_number, so.address, so.date_created,
                   t.name as technician_name, l.name as location_name
            FROM service_orders so
            LEFT JOIN technicians t ON so.technician_id = t.technician_id
            LEFT JOIN locations l ON so.location_id = l.location_id
            ORDER BY so.date_created DESC
        """)
        return self.cursor.fetchall()
    
    # ==================== TRANSACTIONS ====================
    
    def add_transaction(self, item_id: int, technician_id: int, location_id: int,
                       action_type: str, quantity: int, price: float, 
                       service_id: int = None) -> int:
        """
        Add a new transaction (append-only)
        Updates inventory stock automatically based on action type
        """
        if action_type not in ['Install', 'Remove', 'Repair']:
            raise ValueError("action_type must be 'Install', 'Remove', or 'Repair'")
        
        timestamp = datetime.now().isoformat()
        
        self.cursor.execute("""
            INSERT INTO transactions 
            (item_id, technician_id, service_id, location_id, action_type, 
             quantity, price, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, technician_id, service_id, location_id, action_type, 
              quantity, price, timestamp))
        
        # Update stock based on action type
        if action_type == 'Install':
            self.update_stock(item_id, -quantity)  # Decrease stock
        elif action_type == 'Remove':
            self.update_stock(item_id, quantity)   # Increase stock
        # Repair doesn't affect stock
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_transactions(self, filters: Dict = None) -> List[Dict]:
        """
        Get all transactions with optional filters
        
        Args:
            filters: Dict with optional keys: technician_id, service_id, location_id,
                    date_from, date_to, action_type
        """
        query = """
            SELECT t.transaction_id, t.timestamp, t.action_type, t.quantity, t.price,
                   i.name as item_name, tech.name as technician_name,
                   so.service_number, l.name as location_name
            FROM transactions t
            JOIN inventory_items i ON t.item_id = i.item_id
            JOIN technicians tech ON t.technician_id = tech.technician_id
            LEFT JOIN service_orders so ON t.service_id = so.service_id
            JOIN locations l ON t.location_id = l.location_id
        """
        
        conditions = []
        params = []
        
        if filters:
            if filters.get('technician_id'):
                conditions.append("t.technician_id = ?")
                params.append(filters['technician_id'])
            
            if filters.get('service_id'):
                conditions.append("t.service_id = ?")
                params.append(filters['service_id'])
            
            if filters.get('location_id'):
                conditions.append("t.location_id = ?")
                params.append(filters['location_id'])
            
            if filters.get('action_type'):
                conditions.append("t.action_type = ?")
                params.append(filters['action_type'])
            
            if filters.get('date_from'):
                conditions.append("t.timestamp >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append("t.timestamp <= ?")
                params.append(filters['date_to'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY t.timestamp DESC"
        
        self.cursor.execute(query, params)
        
        transactions = []
        for row in self.cursor.fetchall():
            transactions.append({
                'transaction_id': row[0],
                'timestamp': row[1],
                'action_type': row[2],
                'quantity': row[3],
                'price': row[4],
                'item_name': row[5],
                'technician_name': row[6],
                'service_number': row[7] or 'N/A',
                'location_name': row[8]
            })
        
        return transactions
    
    def get_transaction_summary(self, filters: Dict = None) -> Dict:
        """Get summary statistics for transactions"""
        query = """
            SELECT 
                COUNT(*) as total_transactions,
                SUM(quantity) as total_quantity,
                SUM(price * quantity) as total_value,
                action_type
            FROM transactions t
        """
        
        conditions = []
        params = []
        
        if filters:
            if filters.get('technician_id'):
                conditions.append("t.technician_id = ?")
                params.append(filters['technician_id'])
            
            if filters.get('date_from'):
                conditions.append("t.timestamp >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append("t.timestamp <= ?")
                params.append(filters['date_to'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " GROUP BY action_type"
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        summary = {
            'Install': {'count': 0, 'quantity': 0, 'value': 0},
            'Remove': {'count': 0, 'quantity': 0, 'value': 0},
            'Repair': {'count': 0, 'quantity': 0, 'value': 0}
        }
        
        for row in results:
            action_type = row[3]
            summary[action_type] = {
                'count': row[0],
                'quantity': row[1] or 0,
                'value': row[2] or 0
            }
        
        return summary
