"""
Maintenance Mode UI - Full access with CRUD operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox,
                               QDoubleSpinBox, QTextEdit, QTableWidget, QTableWidgetItem,
                               QTabWidget, QMessageBox, QCheckBox, QGroupBox,
                               QFormLayout, QHeaderView, QDialog, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from models import Database
from utils.snapshot_manager import SnapshotManager, ExportManager, ValidationHelper, SoundManager


class MaintenanceWindow(QMainWindow):
    """Main window for maintenance mode with full access"""
    
    def __init__(self, sharepoint_path: str):
        super().__init__()
        self.db = Database("working.db")
        self.snapshot_manager = SnapshotManager("working.db", sharepoint_path)
        self.export_manager = ExportManager()
        self.validator = ValidationHelper()
        self.sound_manager = SoundManager()
        self.init_ui()
        self.load_initial_data()
    
    def init_ui(self):
        """Initialize the main UI"""
        self.setWindowTitle("Tower Inventory - Maintenance Mode")
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
        header = QLabel("Maintenance Mode - Full Access")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_transaction_tab(), "New Transaction")
        self.tabs.addTab(self.create_inventory_tab(), "Inventory Items")
        self.tabs.addTab(self.create_technicians_tab(), "Technicians")
        self.tabs.addTab(self.create_locations_tab(), "Locations")
        self.tabs.addTab(self.create_location_details_tab(), "Location Details")
        self.tabs.addTab(self.create_service_orders_tab(), "Service Orders")
        self.tabs.addTab(self.create_view_transactions_tab(), "View Transactions")
        
        main_layout.addWidget(self.tabs)
        
        # Footer with snapshot controls
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
        
        snapshot_info_btn = QPushButton("Snapshot Info")
        snapshot_info_btn.clicked.connect(self.show_snapshot_info)
        
        publish_btn = QPushButton("Publish Snapshot to SharePoint")
        publish_btn.clicked.connect(self.publish_snapshot)
        publish_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        footer_layout.addWidget(snapshot_info_btn)
        footer_layout.addWidget(publish_btn)
        main_layout.addLayout(footer_layout)
    
    def create_transaction_tab(self):
        """Create the transaction entry tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form for transaction entry
        form = QGroupBox("Create New Transaction")
        form_layout = QFormLayout()
        
        # Technician selection
        self.tech_combo = QComboBox()
        form_layout.addRow("Technician:", self.tech_combo)
        
        # Inventory location selection (where inventory is stored)
        self.location_combo = QComboBox()
        form_layout.addRow("Inventory Location:", self.location_combo)

        # Service address/unit selection (where work is performed)
        self.service_loc_detail_combo = QComboBox()
        form_layout.addRow("Service Address/Unit:", self.service_loc_detail_combo)
        
        # Inventory item selection
        self.item_combo = QComboBox()
        self.item_combo.currentIndexChanged.connect(self.update_item_price)
        form_layout.addRow("Inventory Item:", self.item_combo)
        
        # Action type
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Install", "Remove", "Repair"])
        form_layout.addRow("Action Type:", self.action_combo)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.update_total_price)
        form_layout.addRow("Quantity:", self.quantity_spin)
        
        # Unit Price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMinimum(0.01)
        self.price_spin.setMaximum(999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("$ ")
        self.price_spin.valueChanged.connect(self.update_total_price)
        form_layout.addRow("Unit Price:", self.price_spin)
        
        # Total price display
        self.total_price_label = QLabel("$0.00")
        self.total_price_label.setStyleSheet("QLabel { font-size: 14pt; font-weight: bold; }")
        form_layout.addRow("Total Price:", self.total_price_label)
        
        # Service order section
        service_layout = QHBoxLayout()
        self.service_number_input = QLineEdit()
        self.service_number_input.setPlaceholderText("Enter service number (optional)")
        service_layout.addWidget(self.service_number_input)
        
        new_service_btn = QPushButton("New Service Order")
        new_service_btn.clicked.connect(self.create_new_service_order)
        service_layout.addWidget(new_service_btn)
        
        form_layout.addRow("Service Number:", service_layout)
        
        form.setLayout(form_layout)
        layout.addWidget(form)
        
        # Submit button
        submit_layout = QHBoxLayout()
        submit_layout.addStretch()
        
        submit_btn = QPushButton("Submit Transaction")
        submit_btn.clicked.connect(self.submit_transaction)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 30px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        submit_layout.addWidget(submit_btn)
        layout.addLayout(submit_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_inventory_tab(self):
        """Create the inventory management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form for adding/editing items
        form = QGroupBox("Add/Edit Inventory Item")
        form_layout = QFormLayout()
        
        self.inv_name_input = QLineEdit()
        form_layout.addRow("Item Name:", self.inv_name_input)
        
        self.inv_desc_input = QTextEdit()
        self.inv_desc_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.inv_desc_input)
        
        self.inv_price_spin = QDoubleSpinBox()
        self.inv_price_spin.setMinimum(0.01)
        self.inv_price_spin.setMaximum(999999.99)
        self.inv_price_spin.setDecimals(2)
        self.inv_price_spin.setPrefix("$ ")
        form_layout.addRow("Unit Price:", self.inv_price_spin)
        
        self.inv_stock_spin = QSpinBox()
        self.inv_stock_spin.setMinimum(0)
        self.inv_stock_spin.setMaximum(999999)
        form_layout.addRow("Stock Quantity:", self.inv_stock_spin)
        
        form.setLayout(form_layout)
        layout.addWidget(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_inventory_item)
        
        update_btn = QPushButton("Update Selected")
        update_btn.clicked.connect(self.update_inventory_item)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_inventory_item)
        delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        
        clear_btn = QPushButton("Clear Form")
        clear_btn.clicked.connect(self.clear_inventory_form)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(update_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Description", "Unit Price", "Stock"]
        )
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inventory_table.itemSelectionChanged.connect(self.inventory_selection_changed)
        layout.addWidget(self.inventory_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_technicians_tab(self):
        """Create the technicians management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Technician Name:"))
        self.tech_name_input = QLineEdit()
        form_layout.addWidget(self.tech_name_input)
        
        add_tech_btn = QPushButton("Add Technician")
        add_tech_btn.clicked.connect(self.add_technician)
        form_layout.addWidget(add_tech_btn)
        
        delete_tech_btn = QPushButton("Delete Selected")
        delete_tech_btn.clicked.connect(self.delete_technician)
        delete_tech_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        form_layout.addWidget(delete_tech_btn)
        
        form_layout.addStretch()
        layout.addLayout(form_layout)
        
        # Table
        self.tech_table = QTableWidget()
        self.tech_table.setColumnCount(2)
        self.tech_table.setHorizontalHeaderLabels(["ID", "Name"])
        self.tech_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tech_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tech_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_locations_tab(self):
        """Create the locations management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form = QGroupBox("Add/Edit Location")
        form_layout = QFormLayout()
        
        self.loc_name_input = QLineEdit()
        form_layout.addRow("Location Name:", self.loc_name_input)
        
        self.loc_address_input = QTextEdit()
        self.loc_address_input.setMaximumHeight(60)
        form_layout.addRow("Address:", self.loc_address_input)
        
        self.loc_apartment_input = QLineEdit()
        form_layout.addRow("Apartment Number:", self.loc_apartment_input)
        
        form.setLayout(form_layout)
        layout.addWidget(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_loc_btn = QPushButton("Add Location")
        add_loc_btn.clicked.connect(self.add_location)
        
        delete_loc_btn = QPushButton("Delete Selected")
        delete_loc_btn.clicked.connect(self.delete_location)
        delete_loc_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        
        btn_layout.addWidget(add_loc_btn)
        btn_layout.addWidget(delete_loc_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.location_table = QTableWidget()
        self.location_table.setColumnCount(4)
        self.location_table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Apartment Number"])
        self.location_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.location_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.location_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_location_details_tab(self):
        """Create the location details management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Form
        form = QGroupBox("Add Location Detail")
        form_layout = QFormLayout()
        
        self.loc_detail_address_input = QTextEdit()
        self.loc_detail_address_input.setMaximumHeight(60)
        form_layout.addRow("Address:", self.loc_detail_address_input)
        
        self.loc_detail_apartment_input = QLineEdit()
        form_layout.addRow("Apartment Number:", self.loc_detail_apartment_input)
        
        form.setLayout(form_layout)
        layout.addWidget(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_detail_btn = QPushButton("Add Location Detail")
        add_detail_btn.clicked.connect(self.add_location_detail)
        
        delete_detail_btn = QPushButton("Delete Selected")
        delete_detail_btn.clicked.connect(self.delete_location_detail)
        delete_detail_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        
        btn_layout.addWidget(add_detail_btn)
        btn_layout.addWidget(delete_detail_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Table
        self.location_detail_table = QTableWidget()
        self.location_detail_table.setColumnCount(3)
        self.location_detail_table.setHorizontalHeaderLabels(["ID", "Address", "Apartment Number"])
        self.location_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.location_detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.location_detail_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_service_orders_tab(self):
        """Create the service orders view tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Table
        self.service_table = QTableWidget()
        self.service_table.setColumnCount(6)
        self.service_table.setHorizontalHeaderLabels(
            ["ID", "Service Number", "Address", "Date Created", "Technician", "Location"]
        )
        self.service_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.service_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_view_transactions_tab(self):
        """Create the transactions view tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_transactions)
        layout.addWidget(refresh_btn)
        
        # Table
        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(10)
        self.trans_table.setHorizontalHeaderLabels(
            ["ID", "Timestamp", "Action", "Quantity", "Price", 
             "Item", "Technician", "Service #", "Inventory Location", "Service Location"]
        )
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.trans_table)
        
        widget.setLayout(layout)
        return widget
    
    # Data loading methods
    def load_initial_data(self):
        """Load all initial data"""
        self.load_technicians()
        self.load_locations()
        self.load_location_details()
        self.load_inventory()
        self.load_service_orders()
        self.load_transactions()
    
    def load_technicians(self):
        """Load technicians into combo and table"""
        techs = self.db.get_all_technicians()
        
        # Update combo
        self.tech_combo.clear()
        for tech_id, name in techs:
            self.tech_combo.addItem(name, tech_id)
        
        # Update table
        self.tech_table.setRowCount(len(techs))
        for row, (tech_id, name) in enumerate(techs):
            self.tech_table.setItem(row, 0, QTableWidgetItem(str(tech_id)))
            self.tech_table.setItem(row, 1, QTableWidgetItem(name))
    
    def load_locations(self):
        """Load locations into combo and table"""
        locs = self.db.get_all_locations()
        
        # Update combo
        self.location_combo.clear()
        for loc_id, name, address, apartment_number in locs:
            self.location_combo.addItem(name, loc_id)
        
        # Update table
        self.location_table.setRowCount(len(locs))
        for row, (loc_id, name, address, apartment_number) in enumerate(locs):
            self.location_table.setItem(row, 0, QTableWidgetItem(str(loc_id)))
            self.location_table.setItem(row, 1, QTableWidgetItem(name))
            self.location_table.setItem(row, 2, QTableWidgetItem(address or ""))
            self.location_table.setItem(row, 3, QTableWidgetItem(apartment_number or ""))
    
    def load_inventory(self):
        """Load inventory items"""
        items = self.db.get_all_inventory_items()
        
        # Update combo
        self.item_combo.clear()
        for item in items:
            self.item_combo.addItem(item['name'], item['item_id'])
        
        # Update table
        self.inventory_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(item['item_id'])))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item['name']))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(item['description'] or ""))
            self.inventory_table.setItem(row, 3, QTableWidgetItem(f"${item['unit_price']:.2f}"))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(item['stock'])))
    
    def load_location_details(self):
        """Load location details into table"""
        details = self.db.get_all_location_details()
        
        self.location_detail_table.setRowCount(len(details))
        for row, (detail_id, address, apartment_number) in enumerate(details):
            self.location_detail_table.setItem(row, 0, QTableWidgetItem(str(detail_id)))
            self.location_detail_table.setItem(row, 1, QTableWidgetItem(address))
            self.location_detail_table.setItem(row, 2, QTableWidgetItem(apartment_number or ""))
        
        # Also populate the service address/unit combo for transactions
        if hasattr(self, "service_loc_detail_combo"):
            self.service_loc_detail_combo.clear()
            for detail_id, address, apartment_number in details:
                label = address
                if apartment_number:
                    label = f"{address} - Unit {apartment_number}"
                self.service_loc_detail_combo.addItem(label, detail_id)
    
    def load_service_orders(self):
        """Load service orders"""
        orders = self.db.get_all_service_orders()
        
        self.service_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.service_table.setItem(row, 0, QTableWidgetItem(str(order[0])))
            self.service_table.setItem(row, 1, QTableWidgetItem(order[1]))
            self.service_table.setItem(row, 2, QTableWidgetItem(order[2]))
            self.service_table.setItem(row, 3, QTableWidgetItem(order[3]))
            self.service_table.setItem(row, 4, QTableWidgetItem(order[4] or "N/A"))
            self.service_table.setItem(row, 5, QTableWidgetItem(order[5] or "N/A"))
    
    def load_transactions(self):
        """Load all transactions"""
        transactions = self.db.get_all_transactions()
        
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
    
    # Event handlers
    def update_item_price(self):
        """Update price when item is selected"""
        item_id = self.item_combo.currentData()
        if item_id:
            items = self.db.get_all_inventory_items()
            for item in items:
                if item['item_id'] == item_id:
                    self.price_spin.setValue(item['unit_price'])
                    break
        self.update_total_price()
    
    def update_total_price(self):
        """Calculate and display total price"""
        quantity = self.quantity_spin.value()
        unit_price = self.price_spin.value()
        total = quantity * unit_price
        self.total_price_label.setText(f"${total:.2f}")
    
    def submit_transaction(self):
        """Submit a new transaction"""
        try:
            # Validate selections
            if self.tech_combo.currentIndex() < 0:
                raise ValueError("Please select a technician")
            if self.location_combo.currentIndex() < 0:
                raise ValueError("Please select a location")
            if self.item_combo.currentIndex() < 0:
                raise ValueError("Please select an inventory item")
            if self.service_loc_detail_combo.currentIndex() < 0:
                raise ValueError("Please select a service address/unit")
            
            tech_id = self.tech_combo.currentData()
            loc_id = self.location_combo.currentData()
            item_id = self.item_combo.currentData()
            service_detail_id = self.service_loc_detail_combo.currentData()
            action = self.action_combo.currentText()
            quantity = self.quantity_spin.value()
            price = self.price_spin.value()
            
            # Handle service order (optional, free-text label)
            service_id = None
            service_number = self.service_number_input.text().strip()
            if service_number:
                # Try to link to the most recent matching service order, but do NOT require it
                service = self.db.get_service_order_by_number(service_number)
                if service:
                    service_id = service[0]

            # Resolve service address/unit from selected location detail
            service_address = ""
            service_apartment = ""
            details = self.db.get_all_location_details()
            for detail_id, address, apartment_number in details:
                if detail_id == service_detail_id:
                    service_address = address
                    service_apartment = apartment_number or ""
                    break
            
            # Add transaction
            self.db.add_transaction(
                item_id, tech_id, loc_id, action, quantity, price,
                service_id, service_address, service_apartment
            )
            
            QMessageBox.information(self, "Success", "Transaction added successfully!")
            self.sound_manager.play_success()
            
            # Refresh data
            self.load_inventory()
            self.load_transactions()
            
            # Clear service number
            self.service_number_input.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add transaction:\n{str(e)}")
            self.sound_manager.play_error()
    
    def create_new_service_order(self):
        """Open dialog to create a new service order"""
        dialog = ServiceOrderDialog(self.db, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_service_orders()
            self.service_number_input.setText(dialog.service_number)

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
    
    def add_technician(self):
        """Add a new technician"""
        try:
            name = self.validator.validate_not_empty(
                self.tech_name_input.text(), "Technician name"
            )
            self.db.add_technician(name)
            self.tech_name_input.clear()
            self.load_technicians()
            QMessageBox.information(self, "Success", "Technician added successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def delete_technician(self):
        """Delete selected technician"""
        selected = self.tech_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a technician to delete")
            return
        
        tech_id = int(self.tech_table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this technician?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_technician(tech_id)
                self.load_technicians()
                QMessageBox.information(self, "Success", "Technician deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")
    
    def add_location(self):
        """Add a new location"""
        try:
            name = self.validator.validate_not_empty(
                self.loc_name_input.text(), "Location name"
            )
            address = self.validator.validate_not_empty(
                self.loc_address_input.toPlainText(), "Address"
            )
            apartment_number = self.validator.validate_apartment_number(
                self.loc_apartment_input.text().strip()
            )
            
            self.db.add_location(name, address, apartment_number)
            self.loc_name_input.clear()
            self.loc_address_input.clear()
            self.loc_apartment_input.clear()
            self.load_locations()
            QMessageBox.information(self, "Success", "Location added successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def delete_location(self):
        """Delete selected location"""
        selected = self.location_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a location to delete")
            return
        
        loc_id = int(self.location_table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this location?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_location(loc_id)
                self.load_locations()
                QMessageBox.information(self, "Success", "Location deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")
    
    def add_location_detail(self):
        """Add a new location detail"""
        try:
            address = self.validator.validate_not_empty(
                self.loc_detail_address_input.toPlainText(), "Address"
            )
            apartment_number = self.validator.validate_apartment_number(
                self.loc_detail_apartment_input.text().strip()
            )
            
            self.db.add_location_detail(address, apartment_number)
            self.loc_detail_address_input.clear()
            self.loc_detail_apartment_input.clear()
            self.load_location_details()
            QMessageBox.information(self, "Success", "Location detail added successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def delete_location_detail(self):
        """Delete selected location detail"""
        selected = self.location_detail_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a location detail to delete")
            return
        
        detail_id = int(self.location_detail_table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this location detail?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_location_detail(detail_id)
                self.load_location_details()
                QMessageBox.information(self, "Success", "Location detail deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")
    
    def add_inventory_item(self):
        """Add a new inventory item"""
        try:
            name = self.validator.validate_not_empty(
                self.inv_name_input.text(), "Item name"
            )
            description = self.inv_desc_input.toPlainText().strip()
            price = self.inv_price_spin.value()
            stock = self.inv_stock_spin.value()
            
            self.db.add_inventory_item(name, description, price, stock)
            self.clear_inventory_form()
            self.load_inventory()
            QMessageBox.information(self, "Success", "Inventory item added successfully!")
            self.sound_manager.play_success()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.sound_manager.play_error()
    
    def update_inventory_item(self):
        """Update selected inventory item"""
        selected = self.inventory_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an item to update")
            return
        
        try:
            item_id = int(self.inventory_table.item(selected[0].row(), 0).text())
            name = self.validator.validate_not_empty(
                self.inv_name_input.text(), "Item name"
            )
            description = self.inv_desc_input.toPlainText().strip()
            price = self.inv_price_spin.value()
            stock = self.inv_stock_spin.value()
            
            self.db.update_inventory_item(item_id, name, description, price, stock)
            self.clear_inventory_form()
            self.load_inventory()
            QMessageBox.information(self, "Success", "Inventory item updated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def delete_inventory_item(self):
        """Delete selected inventory item"""
        selected = self.inventory_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete")
            return
        
        item_id = int(self.inventory_table.item(selected[0].row(), 0).text())
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_inventory_item(item_id)
                self.load_inventory()
                QMessageBox.information(self, "Success", "Item deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{str(e)}")
    
    def clear_inventory_form(self):
        """Clear the inventory form"""
        self.inv_name_input.clear()
        self.inv_desc_input.clear()
        self.inv_price_spin.setValue(0.01)
        self.inv_stock_spin.setValue(0)
    
    def inventory_selection_changed(self):
        """Handle inventory table selection change"""
        selected = self.inventory_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        item_id = int(self.inventory_table.item(row, 0).text())
        
        # Find item in data
        items = self.db.get_all_inventory_items()
        for item in items:
            if item['item_id'] == item_id:
                self.inv_name_input.setText(item['name'])
                self.inv_desc_input.setPlainText(item['description'] or "")
                self.inv_price_spin.setValue(item['unit_price'])
                self.inv_stock_spin.setValue(item['stock'])
                break
    
    def publish_snapshot(self):
        """Publish database snapshot to SharePoint"""
        reply = QMessageBox.question(
            self, "Confirm Publish",
            "This will create a snapshot of the current database and copy it to SharePoint.\n"
            "Office users will see this version. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Close and reopen database to ensure all changes are committed
            self.db.close()
            self.db.connect()
            
            success, message = self.snapshot_manager.publish_snapshot()
            
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)
    
    def show_snapshot_info(self):
        """Show information about the current snapshot"""
        info = self.snapshot_manager.get_snapshot_info()
        
        if info:
            message = f"Current Snapshot Information:\n\n"
            message += f"Location: {info['path']}\n"
            message += f"Size: {info['size']:,} bytes\n"
            message += f"Last Modified: {info['modified']}"
        else:
            message = "No snapshot found in SharePoint folder."
        
        QMessageBox.information(self, "Snapshot Info", message)
    
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
            "Any unsaved changes will be lost. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Ensure database is closed before exiting to switch mode
            try:
                self.db.close()
            except sqlite3.ProgrammingError:
                pass
            QApplication.exit(1)  # Special exit code to indicate mode switch


class ServiceOrderDialog(QDialog):
    """Dialog for creating a new service order"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.service_number = None
        self.sound_manager = SoundManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Create New Service Order")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.service_num_input = QLineEdit()
        form.addRow("Service Number:", self.service_num_input)
        
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        form.addRow("Address:", self.address_input)
        
        self.tech_combo = QComboBox()
        techs = self.db.get_all_technicians()
        self.tech_combo.addItem("(None)", None)
        for tech_id, name in techs:
            self.tech_combo.addItem(name, tech_id)
        form.addRow("Technician (optional):", self.tech_combo)
        
        self.loc_combo = QComboBox()
        locs = self.db.get_all_locations()
        self.loc_combo.addItem("(None)", None)
        for loc_id, name, address, apartment_number in locs:
            display_text = name
            if apartment_number:
                display_text += f" ({apartment_number})"
            self.loc_combo.addItem(display_text, loc_id)
        form.addRow("Location (optional):", self.loc_combo)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_service_order)
        create_btn.setDefault(True)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_service_order(self):
        """Create the service order"""
        try:
            service_number = self.service_num_input.text().strip()
            if service_number:  # Only validate if not empty
                service_number = self.validator.validate_service_number(service_number)
            
            address = self.address_input.toPlainText().strip()
            if not address:
                raise ValueError("Address is required")
            
            tech_id = self.tech_combo.currentData()
            loc_id = self.loc_combo.currentData()
            
            self.db.add_service_order(service_number, address, tech_id, loc_id)
            self.service_number = service_number
            self.service_num_input.clear()
            self.address_input.clear()
            
            QMessageBox.information(self, "Success", "Service order created successfully!")
            self.sound_manager.play_success()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.sound_manager.play_error()
