"""
Utilities for snapshot management and SharePoint synchronization
"""

import os
import shutil
from datetime import datetime
from typing import Optional
import csv


class SnapshotManager:
    """Handles database snapshot creation and synchronization"""
    
    def __init__(self, working_db: str = "working.db", 
                 sharepoint_path: str = None):
        """
        Initialize snapshot manager
        
        Args:
            working_db: Path to the working database
            sharepoint_path: Path to SharePoint sync folder
        """
        self.working_db = working_db
        self.snapshot_name = "inventory_snapshot.db"
        self.sharepoint_path = sharepoint_path or self._get_default_sharepoint_path()
    
    def _get_default_sharepoint_path(self) -> str:
        """Get default SharePoint path or create a local sync folder"""
        # Default to a 'sharepoint_sync' folder in the user's home directory
        default_path = os.path.join(os.path.expanduser("~"), "sharepoint_sync")
        if not os.path.exists(default_path):
            os.makedirs(default_path)
        return default_path
    
    def set_sharepoint_path(self, path: str):
        """Update the SharePoint sync folder path"""
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")
        self.sharepoint_path = path
    
    def publish_snapshot(self) -> tuple[bool, str]:
        """
        Create a snapshot of the working database and copy to SharePoint
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Ensure working database exists
            if not os.path.exists(self.working_db):
                return False, "Working database not found"
            
            # Create snapshot in local directory
            snapshot_path = self.snapshot_name
            shutil.copy2(self.working_db, snapshot_path)
            
            # Copy to SharePoint folder
            sharepoint_snapshot = os.path.join(self.sharepoint_path, self.snapshot_name)
            shutil.copy2(snapshot_path, sharepoint_snapshot)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True, f"Snapshot published successfully at {timestamp}"
            
        except Exception as e:
            return False, f"Error publishing snapshot: {str(e)}"
    
    def pull_snapshot(self, target_path: str = None) -> tuple[bool, str]:
        """
        Pull the latest snapshot from SharePoint to local directory
        
        Args:
            target_path: Where to save the pulled snapshot (defaults to current dir)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            sharepoint_snapshot = os.path.join(self.sharepoint_path, self.snapshot_name)
            
            # Check if snapshot exists in SharePoint
            if not os.path.exists(sharepoint_snapshot):
                return False, "No snapshot found in SharePoint folder"
            
            # Determine target path
            if target_path is None:
                target_path = self.snapshot_name
            
            # Copy from SharePoint to local
            shutil.copy2(sharepoint_snapshot, target_path)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True, f"Snapshot pulled successfully at {timestamp}"
            
        except Exception as e:
            return False, f"Error pulling snapshot: {str(e)}"
    
    def get_snapshot_info(self) -> Optional[dict]:
        """Get information about the current snapshot in SharePoint"""
        try:
            sharepoint_snapshot = os.path.join(self.sharepoint_path, self.snapshot_name)
            
            if not os.path.exists(sharepoint_snapshot):
                return None
            
            stat = os.stat(sharepoint_snapshot)
            return {
                'path': sharepoint_snapshot,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception:
            return None


class ExportManager:
    """Handles data export to CSV and Excel formats"""
    
    def __init__(self, export_dir: str = "exports"):
        """
        Initialize export manager
        
        Args:
            export_dir: Directory to save exported files
        """
        self.export_dir = export_dir
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
    
    def export_to_csv(self, data: list, headers: list, filename: str) -> tuple[bool, str]:
        """
        Export data to CSV file
        
        Args:
            data: List of dictionaries or tuples containing the data
            headers: List of column headers
            filename: Output filename (without extension)
        
        Returns:
            Tuple of (success: bool, filepath: str)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.export_dir, f"{filename}_{timestamp}.csv")
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for row in data:
                    if isinstance(row, dict):
                        writer.writerow([row.get(h, '') for h in headers])
                    else:
                        writer.writerow(row)
            
            return True, filepath
            
        except Exception as e:
            return False, f"Error exporting to CSV: {str(e)}"
    
    def export_transactions_to_csv(self, transactions: list) -> tuple[bool, str]:
        """Export transactions to CSV"""
        headers = ['Transaction ID', 'Timestamp', 'Action Type', 'Quantity', 
                  'Price', 'Item Name', 'Technician', 'Service Number', 'Location']
        
        data = []
        for t in transactions:
            data.append([
                t.get('transaction_id', ''),
                t.get('timestamp', ''),
                t.get('action_type', ''),
                t.get('quantity', ''),
                t.get('price', ''),
                t.get('item_name', ''),
                t.get('technician_name', ''),
                t.get('service_number', ''),
                t.get('location_name', '')
            ])
        
        return self.export_to_csv(data, headers, "transactions")
    
    def export_inventory_to_csv(self, items: list) -> tuple[bool, str]:
        """Export inventory items to CSV"""
        headers = ['Item ID', 'Name', 'Description', 'Unit Price', 'Stock', 'Properties']
        
        data = []
        for item in items:
            properties = ', '.join(item.get('properties', []))
            data.append([
                item.get('item_id', ''),
                item.get('name', ''),
                item.get('description', ''),
                item.get('unit_price', ''),
                item.get('stock', ''),
                properties
            ])
        
        return self.export_to_csv(data, headers, "inventory")
    
    def export_service_orders_to_csv(self, orders: list) -> tuple[bool, str]:
        """Export service orders to CSV"""
        headers = ['Service ID', 'Service Number', 'Address', 'Date Created', 
                  'Technician', 'Location']
        
        return self.export_to_csv(orders, headers, "service_orders")


class ValidationHelper:
    """Helper functions for data validation"""
    
    @staticmethod
    def validate_positive_number(value: str, field_name: str = "Value") -> float:
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if num < 0:
                raise ValueError(f"{field_name} must be positive")
            return num
        except ValueError:
            raise ValueError(f"{field_name} must be a valid number")
    
    @staticmethod
    def validate_positive_integer(value: str, field_name: str = "Value") -> int:
        """Validate that a value is a positive integer"""
        try:
            num = int(value)
            if num < 0:
                raise ValueError(f"{field_name} must be positive")
            return num
        except ValueError:
            raise ValueError(f"{field_name} must be a valid integer")
    
    @staticmethod
    def validate_not_empty(value: str, field_name: str = "Field") -> str:
        """Validate that a string is not empty"""
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty")
        return value.strip()
    
    @staticmethod
    def validate_action_type(value: str) -> str:
        """Validate action type"""
        valid_types = ['Install', 'Remove', 'Repair']
        if value not in valid_types:
            raise ValueError(f"Action type must be one of: {', '.join(valid_types)}")
        return value
