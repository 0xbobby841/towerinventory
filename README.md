# 🗼 Tower Inventory Management System

Modern desktop app for tracking inventory across tower sites, trucks, and other storage locations, and for recording what is installed or removed at specific service addresses/units.

Built with **Python 3**, **PySide6**, and **SQLite**.

---

## ✨ Features

- **Two Modes**
  - **Maintenance Mode** – full CRUD access:
    - Manage technicians, inventory, inventory locations, and service address/unit details.
    - Create transactions (Install / Remove / Repair).
    - Create service orders (optional).
    - Publish snapshots to SharePoint.
  - **Office Mode** – read‑only:
    - View inventory, transactions, and service orders from an `inventory_snapshot.db`.
    - Run summary reports and export to CSV.
    - Pull the latest snapshot from SharePoint.

- **Location Model**
  - **Inventory Locations** (`locations` table)
    - Where stock is stored (e.g., “Warehouse A”, “Truck #3”).
  - **Service Addresses/Units** (`location_details` table)
    - Where work is performed (e.g., `123 Main St`, `Unit 204`).
  - Each **transaction** now stores:
    - Inventory location (where items come from / go back to).
    - Service address + unit (where items are installed/removed).

- **Service Orders**
  - Service numbers are **optional** free‑text labels.
  - They can be reused and don’t have to exist beforehand.
  - When a matching service order exists, transactions link to the most recent one.

- **Validation Helpers**
  - Apartment/unit number validation (no spaces or slashes).
  - Service number format helper available but not enforced for existence.

- **Branding & UX**
  - Tower logo (`towerlogo.png`) used in the mode selector and both main windows.
  - Success and error sounds on key actions in Maintenance mode.
  - "Switch Mode" buttons allow jumping between Office and Maintenance without restarting.
  - Exit buttons in both modes show a confirmation dialog.

---

## 🛠️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/0xbobby841/towerinventory.git
cd towerinventory
```

2. **Create and activate a virtual environment** (recommended)

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

From the project root:

```bash
python main.py
```

You’ll see the **Mode Selection** dialog:

- Choose **Maintenance Mode** for full access.
- Choose **Office Mode** for read‑only / reporting.
- Configure your **SharePoint sync folder** once; it is stored locally in `sharepoint_config.txt` (ignored by Git).

### Databases

- `working.db`
  - Live writeable database used in **Maintenance Mode**.
- `inventory_snapshot.db`
  - Read‑only snapshot used in **Office Mode**.
  - Pulled from/pushed to your SharePoint folder via `SnapshotManager`.

Both `.db` files are in `.gitignore` so real data is never committed.

---

## 🧩 Key Data Model Highlights

- **Technicians**
  - `technicians(technician_id, name)`

- **Inventory Locations**
  - `locations(location_id, name, address, apartment_number)`

- **Service Address / Unit Details**
  - `location_details(detail_id, address, apartment_number)`

- **Inventory Items**
  - `inventory_items(item_id, name, description, unit_price, stock)`

- **Service Orders**
  - `service_orders(service_id, service_number, address, date_created, technician_id, location_id)`
  - `service_number` is nullable and non‑unique.

- **Transactions**
  - `transactions` includes:
    - Foreign keys to item, technician, inventory location, and optional service order.
    - `action_type` in `('Install', 'Remove', 'Repair')`.
    - `service_address` and `service_apartment` (copied from the chosen location detail at time of entry).

The schema is created automatically on startup; simple migrations (via `PRAGMA table_info` + `ALTER TABLE`) keep older databases compatible.

---

## 🧭 Usage Overview

### Maintenance Mode

- **Technicians tab** – add/remove technicians.
- **Inventory Items tab** – manage items, stock levels, and pricing.
- **Locations tab** – define inventory storage locations.
- **Location Details tab** – define service addresses/units.
- **New Transaction tab** – record installs/removals/repairs:
  - Pick technician, inventory location, service address/unit, and item.
  - Optional service number (free text).
  - Quantity automatically updates stock.
- **Service Orders tab** – create and review service orders.
- **View Transactions tab** – see all transactions with both inventory and service locations.

### Office Mode

- **Inventory tab** – view current snapshot of inventory.
- **Transactions tab** – filter and export transactions, including service locations.
- **Service Orders tab** – view and export service orders.
- **Summary Reports tab** – generate aggregate stats by action type, technician, and date range.
- **Reference Data tab** – read‑only view of technicians and locations.

---

## 🔐 Data & Git Safety

- `*.db`, `*.csv`, and local config files are excluded via `.gitignore`.
- Use **sample data** via `init_sample_data.py` for testing instead of production data.
- Never commit real addresses, units, or customer data to the repository.

---

## 🆘 Troubleshooting

- **PySide6 not installed**

```bash
python -m pip install PySide6
```

- **App can’t find `working.db`**
  - It will be created automatically if missing.
  - If migrating from an older system, copy your existing `working.db` into the project root.

- **Snapshot issues**
  - Check the SharePoint folder path in the mode selector.
  - Ensure you have read/write access.

If you run into specific tracebacks, open an issue in the GitHub repo with the error message and steps to reproduce.

---

**Tower Inventory Management System is ready for in‑house use with real tower sites, units, and technicians, while keeping your data and configuration out of Git.**
