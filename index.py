from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)
CORS(app)

GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycby2bGY0Z-dbAd6acP1kslfMjznNgYwMv3Kydka9lm9_e2HvNjJj108tBaOR8WuEaVGR9w/exec'

# File paths for local persistence (fallback only)
INVENTORY_FILE = '/tmp/inventory.json'
SALES_FILE = '/tmp/sales.json'
RESTOCKS_FILE = '/tmp/restocks.json'

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'padmin123'

# Global data stores
inventory_data = {}
sales_data = []
restocks_data = []


def safe_float(value, default=0):
    """Safely convert a value to float, handling empty strings and None"""
    if value is None or value == "" or value == " ":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert a value to int, handling empty strings and None"""
    if value is None or value == "" or value == " ":
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def read_sheet(sheet_name):
    """Read data from a Google Sheet via Apps Script"""
    try:
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json={"action": "read", "sheet": sheet_name},
            timeout=30
        )
        print(f"Reading sheet '{sheet_name}' - Status: {response.status_code}")

        data = response.json()

        # Handle case where Apps Script returns a JSON string of a 2D array
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, list):
            print(f"Unexpected data type from sheet '{sheet_name}': {type(data)}")
            return []

        print(f"Sheet '{sheet_name}' returned {len(data)} rows")
        return data

    except Exception as e:
        print(f"READ ERROR for sheet '{sheet_name}':", str(e))
        return []


def append_to_sheet(sheet_name, row):
    """Append a single row to a Google Sheet"""
    try:
        payload = {
            "sheet": sheet_name,
            "row": row
        }

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )

        print("========== GOOGLE SHEETS WRITE ==========")
        print("Sheet:", sheet_name)
        print("Row:", row)
        print("Status:", response.status_code)
        print("Response:", response.text)
        print("=========================================")

        return response.status_code == 200

    except Exception as e:
        print("Google Sheets Write Error:", str(e))
        return False


def sync_inventory_to_sheet():
    """Push current inventory to Google Sheet (batch update)"""
    try:
        rows = [["Product", "OpeningStock", "UnitPrice", "StockDate"]]
        today = datetime.now().strftime('%Y-%m-%d')
        for name, data in inventory_data.items():
            # Pad with empty strings to match the 10-column structure
            rows.append([name, data["stock"], data["price"], today, "", "", "", "", "", ""])

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json={
                "action": "batchUpdate",
                "sheet": "Inventory",
                "rows": rows
            },
            timeout=30
        )

        print("========== INVENTORY SYNC ==========")
        print("Status:", response.status_code)
        print("Response:", response.text)
        print("====================================")

        return response.status_code == 200
    except Exception as e:
        print("Inventory sync error:", e)
        return False


def load_inventory_from_sheet():
    """Load inventory from Google Sheet 'Inventory' tab"""
    global inventory_data

    data = read_sheet("Inventory")
    if not data or len(data) < 2:  # Need at least header + 1 data row
        print("No inventory data found in sheet or sheet is empty")
        return False

    inventory_data = {}

    # Skip header row (row 0)
    for row in data[1:]:
        if len(row) >= 3 and row[0]:
            product_name = str(row[0]).strip()
            stock = safe_float(row[1])
            price = safe_float(row[2])

            inventory_data[product_name] = {
                "stock": stock,
                "price": price
            }

    print(f"Loaded {len(inventory_data)} products from Google Sheet 'Inventory'")

    # Save to local file as backup
    save_inventory()
    return True


def load_sales_from_sheet():
    """Load sales history from Google Sheet 'Sales' tab"""
    global sales_data

    data = read_sheet("Sales")
    if not data or len(data) < 2:
        sales_data = []
        return

    sales_data = []
    for row in data[1:]:
        if len(row) >= 8:
            try:
                sales_data.append({
                    'date': str(row[0]) if row[0] else "",
                    'product': str(row[1]) if row[1] else "",
                    'quantity': safe_float(row[2]),
                    'unitPrice': safe_float(row[3]),
                    'total': safe_float(row[4]),
                    'mpesa': safe_float(row[5]),
                    'cash': safe_float(row[6]),
                    'debt': safe_float(row[7]),
                    'type': 'Sale'
                })
            except Exception as e:
                print(f"Error parsing sales row: {row}, error: {e}")
                continue

    print(f"Loaded {len(sales_data)} sales records from Google Sheet")
    save_sales()


def load_restocks_from_sheet():
    """Load restock history from Google Sheet 'Restocks' tab"""
    global restocks_data

    data = read_sheet("Restocks")
    if not data or len(data) < 2:
        restocks_data = []
        return

    restocks_data = []
    for row in data[1:]:
        if len(row) >= 5:
            try:
                # Your sheet: Date, Product, Qty, UnitPrice, [empty], TotalCost
                # So total is at index 5, not index 4
                total_idx = 5 if len(row) > 5 and row[5] not in [None, ""] else 4
                restocks_data.append({
                    'date': str(row[0]) if row[0] else "",
                    'product': str(row[1]) if row[1] else "",
                    'quantity': safe_float(row[2]),
                    'unitPrice': safe_float(row[3]),
                    'total': safe_float(row[total_idx]),
                    'type': 'Restock'
                })
            except Exception as e:
                print(f"Error parsing restock row: {row}, error: {e}")
                continue

    print(f"Loaded {len(restocks_data)} restock records from Google Sheet")
    save_restocks()


def load_data():
    """Load ALL data from Google Sheets (source of truth)"""
    # Try to load from Google Sheets first
    sheet_loaded = load_inventory_from_sheet()

    if not sheet_loaded:
        # Fallback to local file if sheet fails
        if os.path.exists(INVENTORY_FILE):
            with open(INVENTORY_FILE, 'r') as f:
                global inventory_data
                inventory_data = json.load(f)
            print("Loaded inventory from local fallback file")
        else:
            print("WARNING: No inventory data available!")
            inventory_data = {}

    # Load sales and restocks from sheets too
    load_sales_from_sheet()
    load_restocks_from_sheet()


def save_inventory():
    """Save inventory to /tmp (local backup only)"""
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory_data, f)


def save_sales():
    """Save sales to /tmp (local backup only)"""
    with open(SALES_FILE, 'w') as f:
        json.dump(sales_data, f)


def save_restocks():
    """Save restocks to /tmp (local backup only)"""
    with open(RESTOCKS_FILE, 'w') as f:
        json.dump(restocks_data, f)


def token_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated


# Load data on startup
load_data()


@app.route('/test-sheet')
def test_sheet():
    try:
        payload = {
            "sheet": "Sales",
            "row": [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "TEST",
                1,
                100,
                100,
                100,
                0,
                0
            ]
        }

        response = requests.post(
            GOOGLE_SCRIPT_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )

        return jsonify({
            "status_code": response.status_code,
            "response": response.text
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/debug-sheet')
def debug_sheet():
    sales = read_sheet("Sales")
    inventory = read_sheet("Inventory")
    restocks = read_sheet("Restocks")

    return jsonify({
        "inventory_rows": len(inventory),
        "inventory_sample": inventory[:3] if inventory else [],
        "sales_rows": len(sales),
        "sales_sample": sales[:3] if sales else [],
        "restocks_rows": len(restocks),
        "restocks_sample": restocks[:3] if restocks else [],
    })


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if (
        data.get('username') == ADMIN_USERNAME and
        data.get('password') == ADMIN_PASSWORD
    ):
        return jsonify({
            'success': True,
            'token': 'gerrit-admin',
            'message': 'Login successful'
        })

    return jsonify({
        'success': False,
        'message': 'Invalid credentials'
    }), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})


@app.route('/api/check-auth')
def check_auth():
    return jsonify({'authenticated': True})


@app.route('/api/products')
def get_products():
    """Public endpoint to get products (no auth required)"""
    products = []
    for name, data in inventory_data.items():
        products.append({
            'name': name,
            'price': data['price'],
            'stock': data['stock']
        })
    return jsonify(products)


@app.route('/api/inventory')
@token_required
def get_inventory():
    # Reload from sheet to get latest data
    load_inventory_from_sheet()
    return jsonify(inventory_data)


@app.route('/api/sale', methods=['POST'])
@token_required
def record_sale():
    data = request.get_json()
    items = data.get('items', [])
    sale_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    payments = data.get('payments', {})

    # Payment validation
    mpesa = float(payments.get('mpesa', 0) or 0)
    cash = float(payments.get('cash', 0) or 0)
    debt = float(payments.get('debt', 0) or 0)

    # Calculate total sale amount
    total_amount = sum(item['price'] * item['quantity'] for item in items)
    total_paid = mpesa + cash + debt

    # Allow small floating point tolerance
    if abs(total_paid - total_amount) > 0.01:
        return jsonify({'error': f'Payment total (KES {total_paid:.2f}) does not match sale total (KES {total_amount:.2f})'}), 400

    # Process each item
    for item in items:
        product = item['name']
        qty = item['quantity']

        if product in inventory_data and inventory_data[product]['stock'] >= qty:
            inventory_data[product]['stock'] -= qty

            # Add to local sales log
            sales_data.append({
                'date': sale_date,
                'product': product,
                'quantity': qty,
                'unitPrice': item['price'],
                'total': item['price'] * qty,
                'type': 'Sale',
                'mpesa': mpesa,
                'cash': cash,
                'debt': debt
            })

            # Write to Google Sheet - match your column structure
            append_to_sheet(
                "Sales",
                [
                    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),  # ISO format like your existing data
                    item['name'],
                    item['quantity'],
                    item['price'],
                    item['price'] * item['quantity'],
                    mpesa if mpesa > 0 else "",  # Empty string if 0 to match your sheet
                    cash if cash > 0 else "",
                    debt if debt > 0 else ""
                ]
            )
        else:
            return jsonify({'error': f'Insufficient stock for {product}'}), 400

    # Sync updated inventory back to Google Sheet
    sync_inventory_to_sheet()
    save_inventory()
    save_sales()

    return jsonify({'success': True})


@app.route('/api/restock', methods=['POST'])
@token_required
def record_restock():
    data = request.get_json()
    product = data.get('product')
    qty = data.get('quantity')
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

    if not product:
        return jsonify({'error': 'Product name is required'}), 400

    if not qty or qty < 1:
        return jsonify({'error': 'Invalid quantity'}), 400

    if product in inventory_data:
        inventory_data[product]['stock'] += qty

        # Add to local restocks log
        restocks_data.append({
            'date': date,
            'product': product,
            'quantity': qty,
            'unitPrice': inventory_data[product]['price'],
            'total': inventory_data[product]['price'] * qty,
            'type': 'Restock'
        })

        # Write to Google Sheet - match your column structure: Date, Product, Qty, UnitPrice, [empty], TotalCost
        append_to_sheet(
            "Restocks",
            [
                date,
                product,
                qty,
                inventory_data[product]['price'],
                "",  # Empty column 5
                inventory_data[product]['price'] * qty  # TotalCost at column 6
            ]
        )

        # Sync updated inventory back to Google Sheet
        sync_inventory_to_sheet()
        save_inventory()
        save_restocks()

        return jsonify({'success': True})

    return jsonify({'error': 'Product not found'}), 404


@app.route('/api/transactions')
@token_required
def get_transactions():
    # Reload from sheets to get latest data
    load_sales_from_sheet()
    load_restocks_from_sheet()

    transactions = []

    # Add sales
    for sale in sales_data:
        transactions.append({
            "date": sale['date'],
            "product": sale['product'],
            "quantity": sale['quantity'],
            "unitPrice": sale['unitPrice'],
            "total": sale['total'],
            "mpesa": sale['mpesa'],
            "cash": sale['cash'],
            "debt": sale['debt'],
            "type": "Sale"
        })

    # Add restocks
    for restock in restocks_data:
        transactions.append({
            "date": restock['date'],
            "product": restock['product'],
            "quantity": restock['quantity'],
            "unitPrice": restock['unitPrice'],
            "total": restock['total'],
            "type": "Restock",
            "mpesa": 0,
            "cash": 0,
            "debt": 0
        })

    transactions.sort(key=lambda x: x["date"], reverse=True)

    return jsonify(transactions)


@app.route('/api/stats')
@token_required
def get_stats():
    # Reload from sheet to get latest data
    load_sales_from_sheet()

    total_sales = len(sales_data)
    total_revenue = sum(s['total'] for s in sales_data)
    total_items = sum(s['quantity'] for s in sales_data)

    total_mpesa = sum(s['mpesa'] for s in sales_data)
    total_cash = sum(s['cash'] for s in sales_data)
    total_debt = sum(s['debt'] for s in sales_data)

    # Calculate today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    today_sales_data = [s for s in sales_data if today in str(s['date'])]

    today_revenue = sum(s['total'] for s in today_sales_data)
    today_mpesa = sum(s['mpesa'] for s in today_sales_data)
    today_cash = sum(s['cash'] for s in today_sales_data)
    today_debt = sum(s['debt'] for s in today_sales_data)

    return jsonify({
        "totalSales": total_sales,
        "totalRevenue": total_revenue,
        "totalItems": total_items,
        "todaySales": today_revenue,
        "payments": {
            "totalMpesa": total_mpesa,
            "totalCash": total_cash,
            "totalDebt": total_debt,
            "todayMpesa": today_mpesa,
            "todayCash": today_cash,
            "todayDebt": today_debt
        }
    })


# HTML Template with updated JavaScript for token auth
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerrit POS System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            max-width: 400px;
            margin: 100px auto;
        }
        .main-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: #333;
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav {
            display: flex;
            gap: 10px;
        }
        .nav button {
            background: #555;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .nav button:hover, .nav button.active {
            background: #667eea;
        }
        .content { padding: 20px; }
        .hidden { display: none !important; }
        input, select {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        button:hover { background: #5568d3; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #229954; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }
        .cart-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            margin: 5px 0;
            border-radius: 5px;
        }
        .low-stock { color: #e74c3c; font-weight: bold; }
        .message {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            display: none;
        }
        .message.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px;
            background: #e0e0e0;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        .tab.active { background: #667eea; color: white; }
        .search-box { margin-bottom: 20px; }
        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .product-card {
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .product-card:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .product-card.selected {
            border-color: #667eea;
            background: #f0f0ff;
        }
        .quantity-control {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }
        .quantity-control button {
            width: 30px;
            height: 30px;
            padding: 0;
            border-radius: 50%;
        }
        .cart-summary {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .total {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-top: 10px;
        }
        .payment-match { color: #27ae60; font-weight: bold; }
        .payment-mismatch { color: #e74c3c; font-weight: bold; }
        .out-of-stock { opacity: 0.5; pointer-events: none; }
    .pos-layout{
    display:grid;
    grid-template-columns: 2fr 380px;
    gap:20px;
    align-items:start;
}

.products-panel{
    width:100%;
}

.cart-panel{
    width:380px;
}

@media(max-width:900px){
    .pos-layout{
        grid-template-columns:1fr;
    }

    .cart-panel{
        width:100%;
    }
}
    </style>
</head>
<body>
    <div class="container">
        <!-- Login Section -->
        <div id="loginSection" class="login-container">
            <h2 style="text-align: center; margin-bottom: 30px; color: #333;">Gerrit POS Login</h2>
            <div id="loginMessage" class="message"></div>
            <input type="text" id="username" placeholder="Username" value="admin">
            <input type="password" id="password" placeholder="Password">
            <button onclick="login()" style="width: 100%; margin-top: 10px;">Login</button>
        </div>

        <!-- Main App Section -->
        <div id="appSection" class="main-container hidden">
            <div class="header">
                <h1>Gerrit POS System</h1>
                <div class="nav">
                    <button onclick="showTab('pos')" class="active" id="tab-pos">POS</button>
                    <button onclick="showTab('inventory')" id="tab-inventory">Inventory</button>
                    <button onclick="showTab('restock')" id="tab-restock">Restock</button>
                    <button onclick="showTab('transactions')" id="tab-transactions">Transactions</button>
                    <button onclick="showTab('stats')" id="tab-stats">Stats</button>
                    <button onclick="logout()" class="btn-danger">Logout</button>
                </div>
            </div>

            <div class="content">
                <div id="message" class="message"></div>

                <!-- POS Tab -->
                <div id="posTab" class="tab-content">
                    <div class="pos-layout">
                        <div class="products-panel">
                            <div class="search-box">
                        <input type="text" id="productSearch" placeholder="Search products..." onkeyup="filterProducts()">
                    </div>
                    <div class="product-grid" id="productGrid"></div>

                    </div>
                        <div class="cart-panel">
                        <div class="cart-summary">
                        <h3>Cart</h3>
                        <div id="cartItems"></div>
                        <div class="total">Total: KES <span id="cartTotal">0.00</span></div>
                        <div style="margin-top: 20px; border-top: 2px solid #ddd; padding-top: 15px;">
                            <h4>Payment Method</h4>
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px;">
                                <div>
                                    <label style="font-size: 12px; color: #666;">M-Pesa (KES)</label>
                                    <input type="number" id="payMpesa" placeholder="0" min="0" step="0.01" style="margin-top: 4px;" oninput="updatePaymentDisplay()">
                                </div>
                                <div>
                                    <label style="font-size: 12px; color: #666;">Cash (KES)</label>
                                    <input type="number" id="payCash" placeholder="0" min="0" step="0.01" style="margin-top: 4px;" oninput="updatePaymentDisplay()">
                                </div>
                                <div>
                                    <label style="font-size: 12px; color: #666;">Debt (KES)</label>
                                    <input type="number" id="payDebt" placeholder="0" min="0" step="0.01" style="margin-top: 4px;" oninput="updatePaymentDisplay()">
                                </div>
                            </div>
                            <div style="margin-top: 10px; font-size: 14px; color: #666;">
                                Payment Total: KES <span id="paymentTotal">0.00</span>
                                <span id="paymentMatch" style="margin-left: 10px;"></span>
                            </div>
                        </div>
                        <button onclick="checkout()" class="btn-success" style="width: 100%; margin-top: 15px;">Complete Sale</button>
                    </div>
                </div>
                </div>

                <!-- Inventory Tab -->
                <div id="inventoryTab" class="tab-content hidden">
                    <h2>Inventory Management</h2>
                    <table id="inventoryTable">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Stock</th>
                                <th>Price (KES)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>

               <!-- Restock Tab -->
                <div id="restockTab" class="tab-content hidden">

            <h2>Restock Inventory</h2>

            <div style="margin-bottom:15px;">
                <label>Date</label>
                <input type="date" id="restockDate">
            </div>

            <div style="margin-bottom:15px;">
                <label>Product</label>
                <select id="restockProduct"></select>
            </div>

            <div style="margin-bottom:15px;">
                <label>Quantity</label>
                <input
                    type="number"
                    id="restockQty"
                    min="1"
                    placeholder="Quantity">
            </div>

            <button onclick="restock()" class="btn-success">
                Add Stock
            </button>

        </div>

        </div>

                <!-- Transactions Tab -->
                <div id="transactionsTab" class="tab-content hidden">
                    <h2>Transaction History</h2>
                    <table id="transactionsTable">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Product</th>
                                <th>Qty</th>
                                <th>Total (KES)</th>
                                <th>M-Pesa</th>
                                <th>Cash</th>
                                <th>Debt</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>

                <!-- Stats Tab -->
                <div id="statsTab" class="tab-content hidden">
                    <h2>Sales Statistics</h2>
                    <div class="stats-grid" id="statsGrid"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let authToken = localStorage.getItem('pos_token');
        let inventory = {};
        let cart = {};
        let products = [];

        // Check auth on load
        if (authToken) {
            checkAuth();
        }

        async function checkAuth() {
            try {
                const response = await fetch('/api/check-auth', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await response.json();
                if (data.authenticated) {
                    showApp();
                } else {
                    localStorage.removeItem('pos_token');
                    authToken = null;
                    showLogin();
                }
            } catch (error) {
                showLogin();
            }
        }

        function showLogin() {
            document.getElementById('loginSection').classList.remove('hidden');
            document.getElementById('appSection').classList.add('hidden');
        }

        function showApp() {
            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('appSection').classList.remove('hidden');
            loadProducts();
            loadInventory();
        }

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();
                if (data.success) {
                    authToken = data.token;
                    localStorage.setItem('pos_token', authToken);
                    showMessage('loginMessage', 'Login successful!', 'success');
                    showApp();
                } else {
                    showMessage('loginMessage', data.message, 'error');
                }
            } catch (error) {
                showMessage('loginMessage', 'Login failed', 'error');
            }
        }

        function logout() {
            fetch('/api/logout', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + authToken }
            });
            localStorage.removeItem('pos_token');
            authToken = null;
            showLogin();
        }

        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                products = await response.json();
                renderProductGrid();
                populateRestockSelect();
            } catch (error) {
                console.error('Failed to load products');
            }
        }

        async function loadInventory() {
            try {
                const response = await fetch('/api/inventory', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                inventory = await response.json();
                renderInventoryTable();
            } catch (error) {
                console.error('Failed to load inventory');
            }
        }

        function renderProductGrid() {
            const grid = document.getElementById('productGrid');
            grid.innerHTML = '';

            products.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card' + (product.stock <= 0 ? ' out-of-stock' : '');
                card.innerHTML = `
                    <h4>${product.name}</h4>
                    <p>KES ${product.price.toFixed(2)}</p>
                    <p class="${product.stock < 5 ? 'low-stock' : ''}">Stock: ${product.stock}</p>
                    <div class="quantity-control" onclick="event.stopPropagation()">
                        <button onclick="updateCart('${product.name.replace(/'/g, "\\'")}', -1)" ${product.stock <= 0 ? 'disabled' : ''}>-</button>
                        <span id="qty-${encodeURIComponent(product.name)}">0</span>
                        <button onclick="updateCart('${product.name.replace(/'/g, "\\'")}', 1)" ${product.stock <= 0 ? 'disabled' : ''}>+</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function filterProducts() {
            const search = document.getElementById('productSearch').value.toLowerCase();
            const cards = document.querySelectorAll('.product-card');
            cards.forEach(card => {
                const name = card.querySelector('h4').textContent.toLowerCase();
                card.style.display = name.includes(search) ? 'block' : 'none';
            });
        }

        function getQtyElementId(productName) {
            return 'qty-' + encodeURIComponent(productName);
        }

        function updateCart(product, change) {
            if (!cart[product]) cart[product] = 0;
            cart[product] += change;
            if (cart[product] < 0) cart[product] = 0;

            const productData = products.find(p => p.name === product);
            if (cart[product] > productData.stock) {
                cart[product] = productData.stock;
                showMessage('message', 'Not enough stock!', 'error');
            }

            const qtyEl = document.getElementById(getQtyElementId(product));
            if (qtyEl) qtyEl.textContent = cart[product];
            updateCartDisplay();
            updatePaymentDisplay();
        }


        function updateCartDisplay() {
            const container = document.getElementById('cartItems');
            container.innerHTML = '';
            if (Object.keys(cart).length === 0) {
            document.getElementById('cartTotal').textContent = '0.00';
            return;
        }

        let total = 0;

            Object.entries(cart).forEach(([product, qty]) => {
                if (qty > 0) {
                    const productData = products.find(p => p.name === product);
                    const itemTotal = productData.price * qty;
                    total += itemTotal;

                    const div = document.createElement('div');
                    div.className = 'cart-item';
                    div.innerHTML = `
                        <span>${product} x ${qty} @ KES ${productData.price.toFixed(2)}</span>
                        <span>KES ${itemTotal.toFixed(2)}</span>
                    `;
                    container.appendChild(div);
                }
            });

            document.getElementById('cartTotal').textContent = total.toFixed(2);
        }

        function updatePaymentDisplay() {
            const mpesa = parseFloat(document.getElementById('payMpesa').value) || 0;
            const cash = parseFloat(document.getElementById('payCash').value) || 0;
            const debt = parseFloat(document.getElementById('payDebt').value) || 0;

            const paymentTotal = mpesa + cash + debt;
            const cartTotal = parseFloat(document.getElementById('cartTotal').textContent) || 0;

            document.getElementById('paymentTotal').textContent = paymentTotal.toFixed(2);

            const matchEl = document.getElementById('paymentMatch');
            if (Math.abs(paymentTotal - cartTotal) < 0.01 && cartTotal > 0) {
                matchEl.textContent = '✓ Balanced';
                matchEl.className = 'payment-match';
            } else if (cartTotal > 0) {
                matchEl.textContent = '✗ Mismatch';
                matchEl.className = 'payment-mismatch';
            } else {
                matchEl.textContent = '';
            }
        }

        async function checkout() {
            const items = Object.entries(cart)
                .filter(([_, qty]) => qty > 0)
                .map(([name, quantity]) => {
                    const product = products.find(p => p.name === name);
                    return { name, quantity, price: product.price };
                });

            if (items.length === 0) {
                showMessage('message', 'Cart is empty!', 'error');
                return;
            }

            const mpesa = parseFloat(document.getElementById('payMpesa').value) || 0;
            const cash = parseFloat(document.getElementById('payCash').value) || 0;
            const debt = parseFloat(document.getElementById('payDebt').value) || 0;

            const totalAmount = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            const totalPaid = mpesa + cash + debt;

            if (Math.abs(totalPaid - totalAmount) > 0.01) {
                showMessage('message', `Payment total (KES ${totalPaid.toFixed(2)}) does not match sale total (KES ${totalAmount.toFixed(2)})`, 'error');
                return;
            }

            try {
                const response = await fetch('/api/sale', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ 
                        items,
                        payments: { mpesa, cash, debt }
                    })
                });

            if (response.ok) {
    showMessage('message', 'Sale completed successfully!', 'success');

    // Clear cart object
    cart = {};

    // Force cart redraw
    updateCartDisplay();

    // Reset all visible quantity counters
    document.querySelectorAll('[id^="qty-"]').forEach(el => {
        el.textContent = '0';
    });

    // Clear payment fields
    document.getElementById('payMpesa').value = '';
    document.getElementById('payCash').value = '';
    document.getElementById('payDebt').value = '';

    updatePaymentDisplay();

    // Reload inventory/products
    await loadProducts();
    await loadInventory();

    console.log("Cart cleared");
                } else {
                    const data = await response.json();
                    showMessage('message', data.error || 'Sale failed', 'error');
                }
            } catch (error) {
                showMessage('message', 'Sale failed: ' + error.message, 'error');
            }
        }

        function renderInventoryTable() {
            const tbody = document.querySelector('#inventoryTable tbody');
            tbody.innerHTML = '';

            Object.entries(inventory).forEach(([name, data]) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${name}</td>
                    <td class="${data.stock < 5 ? 'low-stock' : ''}">${data.stock}</td>
                    <td>${data.price.toFixed(2)}</td>
                    <td>${data.stock < 5 ? 'Low Stock' : 'OK'}</td>
                `;
                tbody.appendChild(row);
            });
        }

        function populateRestockSelect() {
            const select = document.getElementById('restockProduct');
            select.innerHTML = '';
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.name;
                option.textContent = product.name;
                select.appendChild(option);
            });
        }

        async function restock() {

    const product =
        document.getElementById('restockProduct').value;

    const quantity =
        parseInt(document.getElementById('restockQty').value);

    const date =
        document.getElementById('restockDate').value;

    if (!quantity || quantity < 1) {

        showMessage(
            'message',
            'Invalid quantity',
            'error'
        );

        return;
    }

    try {

        const response = await fetch('/api/restock', {

            method: 'POST',

            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },

            body: JSON.stringify({
                product,
                quantity,
                date
            })
        });

        if (response.ok) {

            showMessage(
                'message',
                'Restocked successfully!',
                'success'
            );

            document.getElementById('restockQty').value = '';

            await loadInventory();
            await loadProducts();

        } else {

            const data = await response.json();

            showMessage(
                'message',
                data.error || 'Restock failed',
                'error'
            );
        }

    } catch (error) {

        showMessage(
            'message',
            'Restock failed: ' + error.message,
            'error'
        );
    }
}

       async function loadTransactions() {
                        const response = await fetch('/api/transactions', {
                            headers: { 'Authorization': 'Bearer ' + authToken }
                        });

                        const transactions = await response.json();

                        const tbody = document.querySelector('#transactionsTable tbody');

                        tbody.innerHTML = '';

                        transactions.forEach(t => {
                            const row = document.createElement('tr');

                            row.innerHTML = `
                                <td>${t.date}</td>
                                <td>${t.type}</td>
                                <td>${t.product}</td>
                                <td>${t.quantity}</td>
                                <td>${t.total}</td>
                                <td>${t.mpesa}</td>
                                <td>${t.cash}</td>
                                <td>${t.debt}</td>
                            `;

                            tbody.appendChild(row);
                        });
                    }
        async function loadStats() {
            try {
                const response = await fetch('/api/stats', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const stats = await response.json();

                const grid = document.getElementById('statsGrid');
                const p = stats.payments || {};
                grid.innerHTML = `
                    <div class="stat-card">
                        <div>Total Sales</div>
                        <div class="stat-value">${stats.totalSales}</div>
                    </div>
                    <div class="stat-card">
                        <div>Total Revenue</div>
                        <div class="stat-value">KES ${stats.totalRevenue.toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div>Items Sold</div>
                        <div class="stat-value">${stats.totalItems}</div>
                    </div>
                    <div class="stat-card">
                        <div>Today's Sales</div>
                        <div class="stat-value">KES ${stats.todaySales.toFixed(2)}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%);">
                        <div>Total M-Pesa</div>
                        <div class="stat-value">KES ${(p.totalMpesa || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #43a047 0%, #1b5e20 100%);">
                        <div>Total Cash</div>
                        <div class="stat-value">KES ${(p.totalCash || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #e53935 0%, #b71c1c 100%);">
                        <div>Total Debt</div>
                        <div class="stat-value">KES ${(p.totalDebt || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #fb8c00 0%, #e65100 100%);">
                        <div>Today's M-Pesa</div>
                        <div class="stat-value">KES ${(p.todayMpesa || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #8e24aa 0%, #4a148c 100%);">
                        <div>Today's Cash</div>
                        <div class="stat-value">KES ${(p.todayCash || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #f4511e 0%, #bf360c 100%);">
                        <div>Today's Debt</div>
                        <div class="stat-value">KES ${(p.todayDebt || 0).toFixed(2)}</div>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to load stats');
            }
        }

        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.nav button').forEach(el => el.classList.remove('active'));

            document.getElementById(tab + 'Tab').classList.remove('hidden');
            document.getElementById('tab-' + tab).classList.add('active');

            if (tab === 'inventory') loadInventory();
            if (tab === 'transactions') loadTransactions();
            if (tab === 'stats') loadStats();
        }

        function showMessage(elementId, text, type) {
            const el = document.getElementById(elementId);
            el.textContent = text;
            el.className = 'message ' + type;
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 3000);
        }

        document.addEventListener('DOMContentLoaded', () => {

    const today =
        new Date().toISOString().split('T')[0];

    const restockDate =
        document.getElementById('restockDate');

    if (restockDate) {
        restockDate.value = today;
    }
});
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    app.run(debug=True)
