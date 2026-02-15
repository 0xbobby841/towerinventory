"""
Office Mode UI - Read-only access with filtering and reporting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QComboBox, QTableWidget,
                               QTableWidgetItem, QTabWidget, QMessageBox,
                               QGroupBox, QFormLayout, QHeaderView, QDateEdit,
                               QLineEdit, QApplication)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QIcon
from models import Database
from utils.snapshot_manager import SnapshotManager, ExportManager


class OfficeWindow(QMainWindow):
    """Main window for office mode with read-only access"""
    
    def __init__(self, sharepoint_path: str):
        super().__init__()
        self.snapshot_manager = SnapshotManager("inventory_snapshot.db", sharepoint_path)
        self.export_manager = ExportManager()
        
        # Try to pull snapshot first
        self.pull_snapshot_on_startup()
        
        # Connect to snapshot database
        self.db = Database("inventory_snapshot.db")
        
        self.init_ui()
        self.load_initial_data()
    
    def pull_snapshot_on_startup(self):
        """Attempt to pull the latest snapshot on startup"""
        success, message = self.snapshot_manager.pull_snapshot()
        # Don't show error if file doesn't exist yet
        if not success and "No snapshot found" not in message:
            QMessageBox.warning(
                None, "Snapshot Pull Failed",
                f"Could not pull snapshot from SharePoint:\n{message}\n\n"
                "You may be viewing outdated data."
            )
    
    def init_ui(self):
        """Initialize the main UI"""
        self.setWindowTitle("Tower Inventory - Office Mode (Read-Only)")
        self.setMinimumSize(1200, 800)
        
        # Set window icon
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "towerlogo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("Office Mode - Read Only")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Snapshot info
        info = self.snapshot_manager.get_snapshot_info()
        if info:
            info_label = QLabel(f"Snapshot: {info['modified']}")
            info_label.setStyleSheet("QLabel { color: gray; font-size: 10pt; }")
            header_layout.addWidget(info_label)
        
        main_layout.addLayout(header_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_inventory_tab(), "Inventory")
        self.tabs.addTab(self.create_transactions_tab(), "Transactions")
        self.tabs.addTab(self.create_service_orders_tab(), "Service Orders")
        self.tabs.addTab(self.create_summary_tab(), "Summary Reports")
        self.tabs.addTab(self.create_reference_tab(), "Reference Data")
        
        main_layout.addWidget(self.tabs)
        
        # Footer with controls
        footer_layout = QHBoxLayout()
        
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.confirm_exit)
        exit_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; }")
        footer_layout.addWidget(exit_btn)
        
        switch_btn = QPushButton("Switch Mode")
        switch_btn.clicked.connect(self.switch_mode)
        switch_btn.setStyleSheet("QPushButton { background-color: #ffc107; color: black; }")
        footer_layout.addWidget(switch_btn)
        
        footer_layout.addStretch()
        
        refresh_btn = QPushButton("Pull Latest Snapshot")
        refresh_btn.clicked.connect(self.pull_and_refresh)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        footer_layout.addWidget(refresh_btn)
        main_layout.addLayout(footer_layout)
    
    def create_inventory_tab(self):
        """Create the inventory view tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Search/filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        
        self.inv_search = QLineEdit()
        self.inv_search.setPlaceholderText("Search by item name...")
        self.inv_search.textChanged.connect(self.filter_inventory)
        filter_layout.addWidget(self.inv_search)
        
        export_inv_btn = QPushButton("Export to CSV")
        export_inv_btn.clicked.connect(self.export_inventory)
        filter_layout.addWidget(export_inv_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Description", "Unit Price", "Stock"]
        )
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.inventory_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_transactions_tab(self):
        """Create the transactions view tab with filtering"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QFormLayout()
        
        self.trans_tech_filter = QComboBox()
        self.trans_tech_filter.addItem("All Technicians", None)
        filter_layout.addRow("Technician:", self.trans_tech_filter)
        
        self.trans_loc_filter = QComboBox()
        self.trans_loc_filter.addItem("All Locations", None)
        filter_layout.addRow("Location:", self.trans_loc_filter)
        
        self.trans_action_filter = QComboBox()
        self.trans_action_filter.addItem("All Actions", None)
        self.trans_action_filter.addItems(["Install", "Remove", "Repair"])
        filter_layout.addRow("Action Type:", self.trans_action_filter)
        
        # Date filters
        date_layout = QHBoxLayout()
        self.trans_date_from = QDateEdit()
        self.trans_date_from.setCalendarPopup(True)
        self.trans_date_from.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.trans_date_from)
        
        self.trans_date_to = QDateEdit()
        self.trans_date_to.setCalendarPopup(True)
        self.trans_date_to.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.trans_date_to)
        date_layout.addStretch()
        
        filter_layout.addRow("Date Range:", date_layout)
        
        # Service number search
        self.trans_service_search = QLineEdit()
        self.trans_service_search.setPlaceholderText("Search by service number...")
        filter_layout.addRow("Service Number:", self.trans_service_search)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        apply_filter_btn = QPushButton("Apply Filters")
        apply_filter_btn.clicked.connect(self.filter_transactions)
        
        clear_filter_btn = QPushButton("Clear Filters")
        clear_filter_btn.clicked.connect(self.clear_transaction_filters)
        
        export_trans_btn = QPushButton("Export to CSV")
        export_trans_btn.clicked.connect(self.export_transactions)
        
        btn_layout.addWidget(apply_filter_btn)
        btn_layout.addWidget(clear_filter_btn)
        btn_layout.addWidget(export_trans_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(10)
        self.trans_table.setHorizontalHeaderLabels(
            ["ID", "Timestamp", "Action", "Quantity", "Price", 
             "Item", "Technician", "Service #", "Inventory Location", "Service Location"]
        )
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.trans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.trans_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.trans_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_service_orders_tab(self):
        """Create the service orders view tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.service_search = QLineEdit()
        self.service_search.setPlaceholderText("Search by service number or address...")
        self.service_search.textChanged.connect(self.filter_service_orders)
        search_layout.addWidget(self.service_search)
        
        export_service_btn = QPushButton("Export to CSV")
        export_service_btn.clicked.connect(self.export_service_orders)
        search_layout.addWidget(export_service_btn)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # Table
        self.service_table = QTableWidget()
        self.service_table.setColumnCount(6)
        self.service_table.setHorizontalHeaderLabels(
            ["ID", "Service Number", "Address", "Date Created", "Technician", "Location"]
        )
        self.service_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.service_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.service_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.service_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_summary_tab(self):
        """Create the summary reports tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_group = QGroupBox("Report Filters")
        filter_layout = QFormLayout()
        
        self.summary_tech_filter = QComboBox()
        self.summary_tech_filter.addItem("All Technicians", None)
        filter_layout.addRow("Technician:", self.summary_tech_filter)
        
        # Date range
        date_layout = QHBoxLayout()
        self.summary_date_from = QDateEdit()
        self.summary_date_from.setCalendarPopup(True)
        self.summary_date_from.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.summary_date_from)
        
        self.summary_date_to = QDateEdit()
        self.summary_date_to.setCalendarPopup(True)
        self.summary_date_to.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.summary_date_to)
        date_layout.addStretch()
        
        filter_layout.addRow("Date Range:", date_layout)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_summary)
        layout.addWidget(generate_btn)
        
        # Summary display
        self.summary_text = QLabel()
        self.summary_text.setWordWrap(True)
        self.summary_text.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 20px;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.summary_text)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_reference_tab(self):
        """Create reference data tab (technicians and locations)"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Sub-tabs for reference data
        ref_tabs = QTabWidget()
        
        # Technicians
        tech_widget = QWidget()
        tech_layout = QVBoxLayout()
        tech_table = QTableWidget()
        tech_table.setColumnCount(2)
        tech_table.setHorizontalHeaderLabels(["ID", "Name"])
        tech_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tech_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tech_layout.addWidget(tech_table)
        tech_widget.setLayout(tech_layout)
        self.ref_tech_table = tech_table
        
        # Locations
        loc_widget = QWidget()
        loc_layout = QVBoxLayout()
        loc_table = QTableWidget()
        loc_table.setColumnCount(3)
        loc_table.setHorizontalHeaderLabels(["ID", "Name", "Address"])
        loc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        loc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        loc_layout.addWidget(loc_table)
        loc_widget.setLayout(loc_layout)
        self.ref_loc_table = loc_table
        
        ref_tabs.addTab(tech_widget, "Technicians")
        ref_tabs.addTab(loc_widget, "Locations")
        
        layout.addWidget(ref_tabs)
        widget.setLayout(layout)
        return widget
    
    def load_initial_data(self):
        """Load all initial data"""
        self.load_inventory()
        self.load_transactions()
        self.load_service_orders()
        self.load_reference_data()
        self.populate_filter_combos()
    
    def load_inventory(self):
        """Load inventory items"""
        items = self.db.get_all_inventory_items()
        self.all_inventory = items  # Store for filtering
        self.display_inventory(items)
    
    def display_inventory(self, items):
        """Display inventory items in table"""
        self.inventory_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(item['item_id'])))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item['name']))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(item['description'] or ""))
            self.inventory_table.setItem(row, 3, QTableWidgetItem(f"${item['unit_price']:.2f}"))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(item['stock'])))
    
    def load_transactions(self):
        """Load all transactions"""
        transactions = self.db.get_all_transactions()
        self.all_transactions = transactions  # Store for filtering
        self.display_transactions(transactions)
    
    def display_transactions(self, transactions):
        """Display transactions in table"""
        self.trans_table.setRowCount(len(transactions))
        for row, trans in enumerate(transactions):
            self.trans_table.setItem(row, 0, QTableWidgetItem(str(trans['transaction_id'])))
            self.trans_table.setItem(row, 1, QTableWidgetItem(trans['timestamp']))
            self.trans_table.setItem(row, 2, QTableWidgetItem(trans['action_type']))
            self.trans_table.setItem(row, 3, QTableWidgetItem(str(trans['quantity'])))
            self.trans_table.setItem(row, 4, QTableWidgetItem(f"${trans['price']:.2f}"))
            self.trans_table.setItem(row, 5, QTableWidgetItem(trans['item_name']))
            self.trans_table.setItem(row, 6, QTableWidgetItem(trans['technician_name']))
            self.trans_table.setItem(row, 7, QTableWidgetItem(trans['service_number']))
            self.trans_table.setItem(row, 8, QTableWidgetItem(trans['location_name']))
            service_loc = trans['service_address']
            if trans['service_apartment']:
                service_loc = f"{service_loc} (Unit {trans['service_apartment']})" if service_loc else f"Unit {trans['service_apartment']}"
            self.trans_table.setItem(row, 9, QTableWidgetItem(service_loc))
    
    def load_service_orders(self):
        """Load service orders"""
        orders = self.db.get_all_service_orders()
        self.all_service_orders = orders  # Store for filtering
        self.display_service_orders(orders)
    
    def display_service_orders(self, orders):
        """Display service orders in table"""
        self.service_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.service_table.setItem(row, 0, QTableWidgetItem(str(order[0])))
            self.service_table.setItem(row, 1, QTableWidgetItem(order[1]))
            self.service_table.setItem(row, 2, QTableWidgetItem(order[2]))
            self.service_table.setItem(row, 3, QTableWidgetItem(order[3]))
            self.service_table.setItem(row, 4, QTableWidgetItem(order[4] or "N/A"))
            self.service_table.setItem(row, 5, QTableWidgetItem(order[5] or "N/A"))
    
    def load_reference_data(self):
        """Load reference data tables"""
        # Technicians
        techs = self.db.get_all_technicians()
        self.ref_tech_table.setRowCount(len(techs))
        for row, (tech_id, name) in enumerate(techs):
            self.ref_tech_table.setItem(row, 0, QTableWidgetItem(str(tech_id)))
            self.ref_tech_table.setItem(row, 1, QTableWidgetItem(name))
        
        # Locations
        locs = self.db.get_all_locations()
        self.ref_loc_table.setRowCount(len(locs))
        for row, (loc_id, name, address, apartment_number) in enumerate(locs):
            self.ref_loc_table.setItem(row, 0, QTableWidgetItem(str(loc_id)))
            self.ref_loc_table.setItem(row, 1, QTableWidgetItem(name))
            # Combine address and apartment number for display
            addr_display = address or ""
            if apartment_number:
                addr_display = f"{addr_display} (Unit {apartment_number})" if addr_display else f"Unit {apartment_number}"
            self.ref_loc_table.setItem(row, 2, QTableWidgetItem(addr_display))
    
    def populate_filter_combos(self):
        """Populate filter combo boxes"""
        # Technicians
        techs = self.db.get_all_technicians()
        for tech_id, name in techs:
            self.trans_tech_filter.addItem(name, tech_id)
            self.summary_tech_filter.addItem(name, tech_id)
        
        # Locations
        locs = self.db.get_all_locations()
        for loc_id, name, address, apartment_number in locs:
            self.trans_loc_filter.addItem(name, loc_id)
    
    def filter_inventory(self):
        """Filter inventory by search text"""
        search_text = self.inv_search.text().lower()
        
        if not search_text:
            self.display_inventory(self.all_inventory)
            return
        
        filtered = [
            item for item in self.all_inventory
            if search_text in item['name'].lower() or 
               search_text in (item['description'] or "").lower()
        ]
        self.display_inventory(filtered)
    
    def filter_transactions(self):
        """Apply filters to transactions"""
        filters = {}
        
        tech_id = self.trans_tech_filter.currentData()
        if tech_id:
            filters['technician_id'] = tech_id
        
        loc_id = self.trans_loc_filter.currentData()
        if loc_id:
            filters['location_id'] = loc_id
        
        action = self.trans_action_filter.currentData()
        if action:
            filters['action_type'] = action
        
        # Date filters
        date_from = self.trans_date_from.date().toString("yyyy-MM-dd")
        date_to = self.trans_date_to.date().toString("yyyy-MM-dd") + "T23:59:59"
        filters['date_from'] = date_from
        filters['date_to'] = date_to
        
        # Get filtered transactions
        transactions = self.db.get_all_transactions(filters)
        
        # Apply service number filter if specified
        service_search = self.trans_service_search.text().strip().lower()
        if service_search:
            transactions = [
                t for t in transactions 
                if service_search in t['service_number'].lower()
            ]
        
        self.display_transactions(transactions)
    
    def clear_transaction_filters(self):
        """Clear all transaction filters"""
        self.trans_tech_filter.setCurrentIndex(0)
        self.trans_loc_filter.setCurrentIndex(0)
        self.trans_action_filter.setCurrentIndex(0)
        self.trans_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.trans_date_to.setDate(QDate.currentDate())
        self.trans_service_search.clear()
        self.display_transactions(self.all_transactions)
    
    def filter_service_orders(self):
        """Filter service orders by search text"""
        search_text = self.service_search.text().lower()
        
        if not search_text:
            self.display_service_orders(self.all_service_orders)
            return
        
        filtered = [
            order for order in self.all_service_orders
            if search_text in order[1].lower() or  # service number
               search_text in order[2].lower()     # address
        ]
        self.display_service_orders(filtered)
    
    def generate_summary(self):
        """Generate summary report"""
        filters = {}
        
        tech_id = self.summary_tech_filter.currentData()
        if tech_id:
            filters['technician_id'] = tech_id
        
        date_from = self.summary_date_from.date().toString("yyyy-MM-dd")
        date_to = self.summary_date_to.date().toString("yyyy-MM-dd") + "T23:59:59"
        filters['date_from'] = date_from
        filters['date_to'] = date_to
        
        summary = self.db.get_transaction_summary(filters)
        
        # Build summary text
        text = "<h3>Transaction Summary Report</h3>"
        text += f"<p><b>Period:</b> {self.summary_date_from.date().toString('yyyy-MM-dd')} "
        text += f"to {self.summary_date_to.date().toString('yyyy-MM-dd')}</p>"
        
        if tech_id:
            tech_name = self.summary_tech_filter.currentText()
            text += f"<p><b>Technician:</b> {tech_name}</p>"
        else:
            text += "<p><b>Technician:</b> All</p>"
        
        text += "<hr>"
        
        total_transactions = sum(s['count'] for s in summary.values())
        total_value = sum(s['value'] for s in summary.values())
        
        text += f"<p><b>Total Transactions:</b> {total_transactions}</p>"
        text += f"<p><b>Total Value:</b> ${total_value:,.2f}</p>"
        
        text += "<h4>By Action Type:</h4>"
        text += "<table width='100%' style='border-collapse: collapse;'>"
        text += "<tr style='background-color: #e9ecef;'>"
        text += "<th style='padding: 8px; text-align: left;'>Action</th>"
        text += "<th style='padding: 8px; text-align: right;'>Count</th>"
        text += "<th style='padding: 8px; text-align: right;'>Quantity</th>"
        text += "<th style='padding: 8px; text-align: right;'>Value</th>"
        text += "</tr>"
        
        for action_type in ['Install', 'Remove', 'Repair']:
            s = summary[action_type]
            text += f"<tr style='border-bottom: 1px solid #dee2e6;'>"
            text += f"<td style='padding: 8px;'>{action_type}</td>"
            text += f"<td style='padding: 8px; text-align: right;'>{s['count']}</td>"
            text += f"<td style='padding: 8px; text-align: right;'>{s['quantity']}</td>"
            text += f"<td style='padding: 8px; text-align: right;'>${s['value']:,.2f}</td>"
            text += "</tr>"
        
        text += "</table>"
        
        self.summary_text.setText(text)
    
    def export_inventory(self):
        """Export inventory to CSV"""
        success, filepath = self.export_manager.export_inventory_to_csv(self.all_inventory)
        
        if success:
            QMessageBox.information(
                self, "Export Successful",
                f"Inventory exported to:\n{filepath}"
            )
        else:
            QMessageBox.critical(self, "Export Failed", filepath)
    
    def export_transactions(self):
        """Export transactions to CSV"""
        # Get currently displayed transactions
        transactions = []
        for row in range(self.trans_table.rowCount()):
            trans = {
                'transaction_id': self.trans_table.item(row, 0).text(),
                'timestamp': self.trans_table.item(row, 1).text(),
                'action_type': self.trans_table.item(row, 2).text(),
                'quantity': self.trans_table.item(row, 3).text(),
                'price': self.trans_table.item(row, 4).text().replace('$', ''),
                'item_name': self.trans_table.item(row, 5).text(),
                'technician_name': self.trans_table.item(row, 6).text(),
                'service_number': self.trans_table.item(row, 7).text(),
                'location_name': self.trans_table.item(row, 8).text()
            }
            transactions.append(trans)
        
        success, filepath = self.export_manager.export_transactions_to_csv(transactions)
        
        if success:
            QMessageBox.information(
                self, "Export Successful",
                f"Transactions exported to:\n{filepath}"
            )
        else:
            QMessageBox.critical(self, "Export Failed", filepath)
    
    def export_service_orders(self):
        """Export service orders to CSV"""
        # Get currently displayed orders
        orders = []
        for row in range(self.service_table.rowCount()):
            order = [
                self.service_table.item(row, 0).text(),
                self.service_table.item(row, 1).text(),
                self.service_table.item(row, 2).text(),
                self.service_table.item(row, 3).text(),
                self.service_table.item(row, 4).text(),
                self.service_table.item(row, 5).text()
            ]
            orders.append(order)
        
        success, filepath = self.export_manager.export_service_orders_to_csv(orders)
        
        if success:
            QMessageBox.information(
                self, "Export Successful",
                f"Service orders exported to:\n{filepath}"
            )
        else:
            QMessageBox.critical(self, "Export Failed", filepath)
    
    def pull_and_refresh(self):
        """Pull latest snapshot and refresh all data"""
        success, message = self.snapshot_manager.pull_snapshot()
        
        if success:
            # Reconnect to updated database
            self.db.close()
            self.db = Database("inventory_snapshot.db")
            
            # Reload all data
            self.load_initial_data()
            
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def confirm_exit(self):
        """Ask for confirmation before exiting the application"""
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit Tower Inventory?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Only close the database if it is still open
        try:
            self.db.close()
        except sqlite3.ProgrammingError:
            # Already closed; ignore
            pass
        event.accept()
    
    def switch_mode(self):
        """Switch to the other mode by closing with special exit code"""
        reply = QMessageBox.question(
            self, "Switch Mode",
            "This will close the current session and return to mode selection.\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Ensure database is closed before exiting to switch mode
            try:
                self.db.close()
            except sqlite3.ProgrammingError:
                pass
            QApplication.exit(1)  # Special exit code to indicate mode switch
