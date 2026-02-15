"""
Sample data initialization script
Run this to populate the database with sample data for testing
"""

from models import Database


def initialize_sample_data():
    """Initialize the database with sample data"""
    
    print("Initializing sample data...")
    db = Database("working.db")
    
    try:
        # Add sample technicians
        print("Adding technicians...")
        tech_ids = []
        for name in ["John Smith", "Jane Doe", "Mike Johnson", "Sarah Williams"]:
            try:
                tech_ids.append(db.add_technician(name))
                print(f"  - Added {name}")
            except ValueError:
                print(f"  - {name} already exists")
        
        # Add sample locations
        print("\nAdding locations...")
        loc_ids = []
        locations = [
            ("Main Office", "123 Main St, City, State 12345"),
            ("Warehouse", "456 Industrial Ave, City, State 12345"),
            ("Remote Site A", "789 Country Road, Town, State 67890"),
            ("Remote Site B", "321 Highway 1, Village, State 11111")
        ]
        for name, address in locations:
            try:
                loc_ids.append(db.add_location(name, address))
                print(f"  - Added {name}")
            except ValueError:
                print(f"  - {name} already exists")
        
        # Add sample inventory items
        print("\nAdding inventory items...")
        items_data = [
            ("Security Camera", "HD 1080p IP Camera", 299.99, 50),
            ("Door Lock", "Electronic keypad lock", 149.99, 30),
            ("Motion Sensor", "PIR motion detector", 49.99, 100),
            ("Network Cable", "Cat6 Ethernet cable per foot", 0.99, 5000),
            ("Power Supply", "12V 2A power adapter", 24.99, 75),
            ("Junction Box", "Weatherproof junction box", 19.99, 60),
            ("Control Panel", "Security system main panel", 599.99, 15),
            ("Siren", "Outdoor alarm siren", 89.99, 40)
        ]
        
        for name, desc, price, stock in items_data:
            try:
                db.add_inventory_item(name, desc, price, stock)
                print(f"  - Added {name}")
            except Exception as e:
                print(f"  - Error adding {name}: {e}")
        
        # Add sample service orders
        print("\nAdding service orders...")
        techs = db.get_all_technicians()
        locs = db.get_all_locations()
        
        if techs and locs:
            service_orders = [
                ("12345-1", "123 Oak Street, Residential", techs[0][0], locs[0][0]),
                ("12345-2", "456 Elm Avenue, Commercial Building", techs[1][0], locs[1][0]),
                ("12345-3", "789 Pine Road, Industrial Complex", techs[0][0], locs[2][0])
            ]
            
            for service_num, address, tech_id, loc_id in service_orders:
                try:
                    db.add_service_order(service_num, address, tech_id, loc_id)
                    print(f"  - Added {service_num}")
                except ValueError:
                    print(f"  - {service_num} already exists")
        
        # Add sample transactions
        print("\nAdding sample transactions...")
        items = db.get_all_inventory_items()
        services = db.get_all_service_orders()
        
        if items and techs and locs and services:
            transactions = [
                (items[0]['item_id'], techs[0][0], locs[0][0], "Install", 2, items[0]['unit_price'], services[0][0]),
                (items[1]['item_id'], techs[0][0], locs[0][0], "Install", 3, items[1]['unit_price'], services[0][0]),
                (items[2]['item_id'], techs[1][0], locs[1][0], "Install", 5, items[2]['unit_price'], services[1][0]),
                (items[3]['item_id'], techs[1][0], locs[1][0], "Install", 150, items[3]['unit_price'], services[1][0]),
                (items[4]['item_id'], techs[0][0], locs[2][0], "Install", 4, items[4]['unit_price'], services[2][0]),
                (items[5]['item_id'], techs[0][0], locs[2][0], "Install", 2, items[5]['unit_price'], services[2][0])
            ]
            
            for item_id, tech_id, loc_id, action, qty, price, service_id in transactions:
                try:
                    db.add_transaction(item_id, tech_id, loc_id, action, qty, price, service_id)
                    print(f"  - Added transaction: {action} {qty} units")
                except Exception as e:
                    print(f"  - Error adding transaction: {e}")
        
        print("\n[OK] Sample data initialization complete!")
        print("\nYou can now:")
        print("1. Run the application: python main.py")
        print("2. Select Maintenance mode to view and edit data")
        print("3. Publish a snapshot to SharePoint")
        print("4. Test Office mode to view the snapshot")
        
    except Exception as e:
        print(f"\n[ERROR] Error during initialization: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_sample_data()
