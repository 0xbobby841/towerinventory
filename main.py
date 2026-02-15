"""
Main entry point for Inventory Management System
Provides mode selection: Maintenance (full access) or Office (read-only)
"""

import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QRadioButton, QButtonGroup,
                               QMessageBox, QFileDialog, QLineEdit, QFormLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
import os


class ModeSelector(QDialog):
    """Initial dialog to select application mode"""
    
    def __init__(self):
        super().__init__()
        self.selected_mode = None
        self.sharepoint_path = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the mode selection UI"""
        self.setWindowTitle("Tower Inventory - Mode Selection")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        
        # Set window icon
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "towerlogo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Tower: Inventory Management System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Select Application Mode")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Radio buttons for mode selection
        self.mode_group = QButtonGroup()
        
        self.maintenance_radio = QRadioButton("Maintenance Mode")
        self.maintenance_radio.setStyleSheet("QRadioButton { font-size: 12pt; }")
        maintenance_desc = QLabel("Full access: Create, edit, and manage all data\n"
                                 "Create transactions and publish snapshots")
        maintenance_desc.setStyleSheet("QLabel { color: gray; margin-left: 25px; }")
        
        self.office_radio = QRadioButton("Office Mode")
        self.office_radio.setStyleSheet("QRadioButton { font-size: 12pt; }")
        office_desc = QLabel("Read-only access: View data and generate reports\n"
                           "Pull snapshots from SharePoint")
        office_desc.setStyleSheet("QLabel { color: gray; margin-left: 25px; }")
        
        self.mode_group.addButton(self.maintenance_radio, 1)
        self.mode_group.addButton(self.office_radio, 2)
        
        layout.addWidget(self.maintenance_radio)
        layout.addWidget(maintenance_desc)
        layout.addSpacing(10)
        layout.addWidget(self.office_radio)
        layout.addWidget(office_desc)
        
        layout.addSpacing(20)
        
        # SharePoint path configuration
        sharepoint_group = QFormLayout()
        self.sharepoint_input = QLineEdit()
        self.sharepoint_input.setPlaceholderText("e.g., C:/Users/YourName/SharePoint/Inventory")
        
        # Try to load saved path
        default_path = self.load_saved_sharepoint_path()
        if default_path:
            self.sharepoint_input.setText(default_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_sharepoint_path)
        
        sp_layout = QHBoxLayout()
        sp_layout.addWidget(self.sharepoint_input)
        sp_layout.addWidget(browse_btn)
        
        sharepoint_group.addRow("SharePoint Sync Folder:", sp_layout)
        layout.addLayout(sharepoint_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        start_btn = QPushButton("Start Application")
        start_btn.clicked.connect(self.start_application)
        start_btn.setDefault(True)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                padding: 8px 20px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(start_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_sharepoint_path(self):
        """Open file dialog to select SharePoint folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select SharePoint Sync Folder",
            os.path.expanduser("~")
        )
        if folder:
            self.sharepoint_input.setText(folder)
    
    def load_saved_sharepoint_path(self):
        """Load previously saved SharePoint path"""
        config_file = "sharepoint_config.txt"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return None
    
    def save_sharepoint_path(self, path):
        """Save SharePoint path for future use"""
        try:
            with open("sharepoint_config.txt", 'w') as f:
                f.write(path)
        except:
            pass
    
    def start_application(self):
        """Validate selection and start the application"""
        # Check if mode is selected
        if not self.mode_group.checkedButton():
            QMessageBox.warning(
                self,
                "No Mode Selected",
                "Please select either Maintenance or Office mode."
            )
            return
        
        # Get SharePoint path
        sp_path = self.sharepoint_input.text().strip()
        if not sp_path:
            reply = QMessageBox.question(
                self,
                "No SharePoint Path",
                "No SharePoint sync folder specified. Continue with default location?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            sp_path = os.path.join(os.path.expanduser("~"), "sharepoint_sync")
            if not os.path.exists(sp_path):
                os.makedirs(sp_path)
        elif not os.path.exists(sp_path):
            QMessageBox.warning(
                self,
                "Invalid Path",
                f"The specified SharePoint path does not exist:\n{sp_path}"
            )
            return
        
        # Save the path for next time
        self.save_sharepoint_path(sp_path)
        
        # Set selected values
        self.selected_mode = "maintenance" if self.mode_group.checkedId() == 1 else "office"
        self.sharepoint_path = sp_path
        
        self.accept()


def run_application(mode, sharepoint_path):
    """Run the application in the specified mode"""
    # Import appropriate UI based on mode
    if mode == "maintenance":
        from ui.maintenance_ui import MaintenanceWindow
        window = MaintenanceWindow(sharepoint_path)
    else:
        from ui.office_ui import OfficeWindow
        window = OfficeWindow(sharepoint_path)
    
    window.show()
    return app.exec()


def main():
    """Main application entry point"""
    global app
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    while True:
        # Show mode selector
        selector = ModeSelector()
        
        if selector.exec() == QDialog.Accepted:
            mode = selector.selected_mode
            sharepoint_path = selector.sharepoint_path
            
            # Run application in selected mode
            result = run_application(mode, sharepoint_path)
            
            # If result is 0 (normal exit), break the loop
            # If result is something else (like mode switch), continue
            if result == 0:
                break
        else:
            break
    
    sys.exit(0)


if __name__ == "__main__":
    main()
