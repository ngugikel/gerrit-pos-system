from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import requests

app = Flask(__name__)
CORS(app)

GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycby2bGY0Z-dbAd6acP1kslfMjznNgYwMv3Kydka9lm9_e2HvNjJj108tBaOR8WuEaVGR9w/exec'

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'padmin123'

# Global data stores
inventory_data = {}      # Current calculated stock
opening_stock = {}       # Original stock from Inventory sheet
sales_data = []
restocks_data = []


def safe_float(value, default=0):
    if value is None or value == "" or value == " ":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def read_sheet(sheet_name):
    try:
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json={"action": "read", "sheet": sheet_name},
            timeout=30
        )
        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, list):
            return []
        return data
    except Exception as e:
        print(f"READ ERROR for sheet '{sheet_name}':", str(e))
        return []


def append_to_sheet(sheet_name, row):
    try:
        payload = {"sheet": sheet_name, "row": row}
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print("Google Sheets Write Error:", str(e))
        return False


def load_opening_stock_from_sheet():
    """Load opening stock from Inventory sheet (read-only reference)"""
    global opening_stock
    data = read_sheet("Inventory")
    if not data or len(data) < 2:
        return False
    opening_stock = {}
    for row in data[1:]:
        if len(row) >= 3 and row[0]:
            opening_stock[str(row[0]).strip()] = {
                "stock": safe_float(row[1]),
                "price": safe_float(row[2])
            }
    print(f"Loaded {len(opening_stock)} products opening stock")
    return True


def load_sales_from_sheet():
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
            except:
                continue
    print(f"Loaded {len(sales_data)} sales records")


def load_restocks_from_sheet():
    global restocks_data
    data = read_sheet("Restocks")
    if not data or len(data) < 2:
        restocks_data = []
        return
    restocks_data = []
    for row in data[1:]:
        if len(row) >= 5:
            try:
                total_idx = 5 if len(row) > 5 and row[5] not in [None, ""] else 4
                restocks_data.append({
                    'date': str(row[0]) if row[0] else "",
                    'product': str(row[1]) if row[1] else "",
                    'quantity': safe_float(row[2]),
                    'unitPrice': safe_float(row[3]),
                    'total': safe_float(row[total_idx]),
                    'type': 'Restock'
                })
            except:
                continue
    print(f"Loaded {len(restocks_data)} restock records")


def calculate_current_stock():
    """Calculate current stock: OpeningStock - TotalSales + TotalRestocks"""
    global inventory_data
    inventory_data = {}

    for product, data in opening_stock.items():
        inventory_data[product] = {
            "stock": data["stock"],
            "price": data["price"]
        }

    # Subtract all sales
    for sale in sales_data:
        product = sale['product']
        if product in inventory_data:
            inventory_data[product]['stock'] -= sale['quantity']

    # Add all restocks
    for restock in restocks_data:
        product = restock['product']
        if product in inventory_data:
            inventory_data[product]['stock'] += restock['quantity']
        else:
            # Product exists in restocks but not in opening stock
            inventory_data[product] = {
                "stock": restock['quantity'],
                "price": restock['unitPrice']
            }

    print(f"Calculated current stock for {len(inventory_data)} products")


def load_data():
    load_opening_stock_from_sheet()
    load_sales_from_sheet()
    load_restocks_from_sheet()
    calculate_current_stock()


def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


load_data()


@app.route('/test-sheet')
def test_sheet():
    try:
        payload = {"sheet": "Sales", "row": [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "TEST", 1, 100, 100, 100, 0, 0]}
        response = requests.post(GOOGLE_SCRIPT_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=30)
        return jsonify({"status_code": response.status_code, "response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/debug-sheet')
def debug_sheet():
    sales = read_sheet("Sales")
    inventory = read_sheet("Inventory")
    restocks = read_sheet("Restocks")
    return jsonify({
        "inventory_rows": len(inventory),
        "opening_stock_count": len(opening_stock),
        "sales_rows": len(sales),
        "sales_in_memory": len(sales_data),
        "restocks_rows": len(restocks),
        "restocks_in_memory": len(restocks_data),
        "calculated_inventory": len(inventory_data),
        "sample_stock": {k: v['stock'] for k, v in list(inventory_data.items())[:3]},
    })


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
        return jsonify({'success': True, 'token': 'gerrit-admin', 'message': 'Login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})


@app.route('/api/check-auth')
def check_auth():
    return jsonify({'authenticated': True})


@app.route('/api/products')
def get_products():
    products = []
    for name, data in inventory_data.items():
        products.append({'name': name, 'price': data['price'], 'stock': data['stock']})
    return jsonify(products)


@app.route('/api/inventory')
@token_required
def get_inventory():
    # Recalculate from sheets to get latest
    load_data()
    return jsonify(inventory_data)


@app.route('/api/sale', methods=['POST'])
@token_required
def record_sale():
    data = request.get_json()
    items = data.get('items', [])
    sale_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    payments = data.get('payments', {})

    mpesa = float(payments.get('mpesa', 0) or 0)
    cash = float(payments.get('cash', 0) or 0)
    debt = float(payments.get('debt', 0) or 0)

    total_amount = sum(item['price'] * item['quantity'] for item in items)
    total_paid = mpesa + cash + debt

    if abs(total_paid - total_amount) > 0.01:
        return jsonify({'error': f'Payment total (KES {total_paid:.2f}) does not match sale total (KES {total_amount:.2f})'}), 400

    for item in items:
        product = item['name']
        qty = item['quantity']

        if product in inventory_data and inventory_data[product]['stock'] >= qty:
            # Update memory
            inventory_data[product]['stock'] -= qty

            # Add to sales log
            sales_data.append({
                'date': sale_date, 'product': product, 'quantity': qty,
                'unitPrice': item['price'], 'total': item['price'] * qty,
                'type': 'Sale', 'mpesa': mpesa, 'cash': cash, 'debt': debt
            })

            # Write to Sales sheet
            append_to_sheet("Sales", [
                sale_date, item['name'], item['quantity'], item['price'],
                item['price'] * item['quantity'],
                mpesa if mpesa > 0 else "",
                cash if cash > 0 else "",
                debt if debt > 0 else ""
            ])
        else:
            return jsonify({'error': f'Insufficient stock for {product}'}), 400

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

    # Update memory
    if product in inventory_data:
        inventory_data[product]['stock'] += qty
    else:
        # New product not in opening stock
        inventory_data[product] = {"stock": qty, "price": 0}

    # Add to restocks log
    restocks_data.append({
        'date': date, 'product': product, 'quantity': qty,
        'unitPrice': inventory_data[product]['price'],
        'total': inventory_data[product]['price'] * qty,
        'type': 'Restock'
    })

    # Write to Restocks sheet
    append_to_sheet("Restocks", [
        date, product, qty, inventory_data[product]['price'],
        "", inventory_data[product]['price'] * qty
    ])

    return jsonify({'success': True})


@app.route('/api/transactions')
@token_required
def get_transactions():
    load_sales_from_sheet()
    load_restocks_from_sheet()

    transactions = []
    for sale in sales_data:
        transactions.append({
            "date": sale['date'], "product": sale['product'], "quantity": sale['quantity'],
            "unitPrice": sale['unitPrice'], "total": sale['total'],
            "mpesa": sale['mpesa'], "cash": sale['cash'], "debt": sale['debt'], "type": "Sale"
        })
    for restock in restocks_data:
        transactions.append({
            "date": restock['date'], "product": restock['product'], "quantity": restock['quantity'],
            "unitPrice": restock['unitPrice'], "total": restock['total'],
            "type": "Restock", "mpesa": 0, "cash": 0, "debt": 0
        })
    transactions.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(transactions)


@app.route('/api/stats')
@token_required
def get_stats():
    load_sales_from_sheet()

    start_date = request.args.get('startDate', '')
    end_date = request.args.get('endDate', '')

    filtered_sales = sales_data
    if start_date or end_date:
        def parse_date_str(d):
            try:
                return d.split('T')[0] if 'T' in d else d
            except:
                return str(d)
        if start_date:
            filtered_sales = [s for s in filtered_sales if start_date <= parse_date_str(s['date'])]
        if end_date:
            filtered_sales = [s for s in filtered_sales if parse_date_str(s['date']) <= end_date]

    total_sales = len(filtered_sales)
    total_revenue = sum(s['total'] for s in filtered_sales)
    total_items = sum(s['quantity'] for s in filtered_sales)
    total_mpesa = sum(s['mpesa'] for s in filtered_sales)
    total_cash = sum(s['cash'] for s in filtered_sales)
    total_debt = sum(s['debt'] for s in filtered_sales)

    today = datetime.now().strftime('%Y-%m-%d')
    today_sales_data = [s for s in sales_data if today in str(s['date'])]
    today_revenue = sum(s['total'] for s in today_sales_data)
    today_mpesa = sum(s['mpesa'] for s in today_sales_data)
    today_cash = sum(s['cash'] for s in today_sales_data)
    today_debt = sum(s['debt'] for s in today_sales_data)

    return jsonify({
        "totalSales": total_sales, "totalRevenue": total_revenue,
        "totalItems": total_items, "todaySales": today_revenue,
        "payments": {
            "totalMpesa": total_mpesa, "totalCash": total_cash, "totalDebt": total_debt,
            "todayMpesa": today_mpesa, "todayCash": today_cash, "todayDebt": today_debt
        },
        "filterApplied": bool(start_date or end_date),
        "startDate": start_date, "endDate": end_date
    })


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerrit POS System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .login-container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); max-width: 400px; margin: 100px auto; }
        .main-container { background: white; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); overflow: hidden; }
        .header { background: #333; color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
        .nav { display: flex; gap: 10px; flex-wrap: wrap; }
        .nav button { background: #555; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; transition: background 0.3s; }
        .nav button:hover, .nav button.active { background: #667eea; }
        .content { padding: 20px; }
        .hidden { display: none !important; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; transition: background 0.3s; }
        button:hover { background: #5568d3; }
        .btn-danger { background: #e74c3c; } .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; } .btn-success:hover { background: #229954; }
        .btn-secondary { background: #6c757d; } .btn-secondary:hover { background: #545b62; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; text-align: center; }
        .stat-value { font-size: 36px; font-weight: bold; margin: 10px 0; }
        .cart-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #f8f9fa; margin: 5px 0; border-radius: 5px; }
        .low-stock { color: #e74c3c; font-weight: bold; }
        .message { padding: 15px; margin: 10px 0; border-radius: 5px; display: none; }
        .message.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .search-box { margin-bottom: 20px; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .product-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .product-card:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.1); transform: translateY(-2px); }
        .quantity-control { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
        .quantity-control button { width: 30px; height: 30px; padding: 0; border-radius: 50%; }
        .cart-summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px; }
        .total { font-size: 24px; font-weight: bold; color: #667eea; margin-top: 10px; }
        .payment-match { color: #27ae60; font-weight: bold; }
        .payment-mismatch { color: #e74c3c; font-weight: bold; }
        .out-of-stock { opacity: 0.5; pointer-events: none; }
        .pos-layout { display: grid; grid-template-columns: 2fr 380px; gap: 20px; align-items: start; }
        .products-panel { width: 100%; }
        .cart-panel { width: 380px; }
        .sale-date-section { background: #fff3e0; border: 1px solid #ffe0b2; border-radius: 8px; padding: 12px 15px; margin-bottom: 15px; }
        .sale-date-section label { font-size: 13px; color: #e65100; font-weight: 600; display: block; margin-bottom: 6px; }
        .sale-date-section input { margin: 0; border-color: #ffcc80; }
        .sale-date-section small { color: #f57c00; font-size: 12px; display: block; margin-top: 4px; }
        .stats-filter-section { background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 10px; padding: 20px; margin-bottom: 25px; }
        .stats-filter-section h3 { color: #1565c0; margin-bottom: 15px; font-size: 18px; }
        .filter-row { display: grid; grid-template-columns: 1fr 1fr auto auto; gap: 15px; align-items: end; }
        .filter-group { display: flex; flex-direction: column; }
        .filter-group label { font-size: 13px; color: #555; font-weight: 600; margin-bottom: 5px; }
        .filter-group input { margin: 0; }
        .filter-btn { padding: 12px 20px; height: fit-content; }
        .quick-filters { display: flex; gap: 8px; margin-bottom: 15px; flex-wrap: wrap; }
        .quick-filters button { padding: 8px 16px; font-size: 14px; }
        .quick-filters button.active { background: #1565c0; }
        .restock-form { max-width: 500px; background: #f8f9fa; padding: 30px; border-radius: 10px; }
        .restock-form label { display: block; margin-bottom: 5px; font-weight: 600; color: #333; }
        .restock-form .form-group { margin-bottom: 20px; }
        .restock-form select, .restock-form input { margin: 0; }
        .restock-info { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196f3; }
        .restock-info h4 { margin-bottom: 8px; color: #1565c0; }
        .restock-info p { color: #555; font-size: 14px; line-height: 1.5; }
        @media(max-width:900px) {
            .pos-layout { grid-template-columns: 1fr; }
            .cart-panel { width: 100%; }
            .nav { justify-content: center; }
            .filter-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="loginSection" class="login-container">
            <h2 style="text-align: center; margin-bottom: 30px; color: #333;">Gerrit POS Login</h2>
            <div id="loginMessage" class="message"></div>
            <input type="text" id="username" placeholder="Username" value="admin">
            <input type="password" id="password" placeholder="Password">
            <button onclick="login()" style="width: 100%; margin-top: 10px;">Login</button>
        </div>

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

                <!-- POS TAB -->
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
                                <div class="sale-date-section">
                                    <label for="saleDate">📅 Sale Date</label>
                                    <input type="date" id="saleDate">
                                    <small>Leave as today, or select a past date to backdate this sale</small>
                                </div>
                                <div style="border-top: 2px solid #ddd; padding-top: 15px;">
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
                </div>

                <!-- INVENTORY TAB -->
                <div id="inventoryTab" class="tab-content hidden">
                    <h2>Inventory Management</h2>
                    <table id="inventoryTable">
                        <thead><tr><th>Product</th><th>Stock</th><th>Price (KES)</th><th>Status</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>

                <!-- RESTOCK TAB -->
                <div id="restockTab" class="tab-content hidden">
                    <h2>Restock Inventory</h2>
                    <div class="restock-info">
                        <h4>ℹ️ How Restocking Works</h4>
                        <p>Select a product, enter the quantity received, and choose the date. The stock will be added to your current inventory and recorded in the Restocks log.</p>
                    </div>
                    <div class="restock-form">
                        <div class="form-group">
                            <label for="restockDate">Restock Date</label>
                            <input type="date" id="restockDate">
                            <small style="color: #666; display: block; margin-top: 4px;">You can backdate restocks by selecting a past date</small>
                        </div>
                        <div class="form-group">
                            <label for="restockProduct">Product</label>
                            <select id="restockProduct"></select>
                        </div>
                        <div class="form-group">
                            <label for="restockQty">Quantity to Add</label>
                            <input type="number" id="restockQty" min="1" placeholder="Enter quantity received">
                        </div>
                        <div class="form-group">
                            <label>Current Stock</label>
                            <div id="currentStockDisplay" style="padding: 12px; background: white; border-radius: 5px; border: 1px solid #ddd; color: #667eea; font-weight: bold;">Select a product to see current stock</div>
                        </div>
                        <button onclick="restock()" class="btn-success" style="width: 100%;">➕ Add Stock</button>
                    </div>
                </div>

                <!-- TRANSACTIONS TAB -->
                <div id="transactionsTab" class="tab-content hidden">
                    <h2>Transaction History</h2>
                    <table id="transactionsTable">
                        <thead><tr><th>Date</th><th>Type</th><th>Product</th><th>Qty</th><th>Total (KES)</th><th>M-Pesa</th><th>Cash</th><th>Debt</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>

                <!-- STATS TAB -->
                <div id="statsTab" class="tab-content hidden">
                    <h2>Sales Statistics</h2>
                    <div class="stats-filter-section">
                        <h3>📊 Filter by Date Range</h3>
                        <div class="quick-filters">
                            <button onclick="setQuickFilter('today')" id="qf-today">Today</button>
                            <button onclick="setQuickFilter('yesterday')" id="qf-yesterday">Yesterday</button>
                            <button onclick="setQuickFilter('thisWeek')" id="qf-thisWeek">This Week</button>
                            <button onclick="setQuickFilter('thisMonth')" id="qf-thisMonth">This Month</button>
                            <button onclick="setQuickFilter('all')" id="qf-all" class="active">All Time</button>
                        </div>
                        <div class="filter-row">
                            <div class="filter-group">
                                <label for="statsStartDate">From Date</label>
                                <input type="date" id="statsStartDate">
                            </div>
                            <div class="filter-group">
                                <label for="statsEndDate">To Date</label>
                                <input type="date" id="statsEndDate">
                            </div>
                            <button onclick="applyStatsFilter()" class="btn-success filter-btn">Apply Filter</button>
                            <button onclick="clearStatsFilter()" class="btn-secondary filter-btn">Clear</button>
                        </div>
                        <div id="filterStatus" style="margin-top: 10px; font-size: 14px; color: #1565c0;"></div>
                    </div>
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
        let currentStatsFilter = { startDate: '', endDate: '' };

        if (authToken) { checkAuth(); }

        async function checkAuth() {
            try {
                const response = await fetch('/api/check-auth', { headers: { 'Authorization': 'Bearer ' + authToken } });
                const data = await response.json();
                if (data.authenticated) { showApp(); } else { localStorage.removeItem('pos_token'); authToken = null; showLogin(); }
            } catch (error) { showLogin(); }
        }

        function showLogin() { document.getElementById('loginSection').classList.remove('hidden'); document.getElementById('appSection').classList.add('hidden'); }
        function showApp() { document.getElementById('loginSection').classList.add('hidden'); document.getElementById('appSection').classList.remove('hidden'); loadProducts(); loadInventory(); }

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            try {
                const response = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
                const data = await response.json();
                if (data.success) { authToken = data.token; localStorage.setItem('pos_token', authToken); showMessage('loginMessage', 'Login successful!', 'success'); showApp(); }
                else { showMessage('loginMessage', data.message, 'error'); }
            } catch (error) { showMessage('loginMessage', 'Login failed', 'error'); }
        }

        function logout() { fetch('/api/logout', { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken } }); localStorage.removeItem('pos_token'); authToken = null; showLogin(); }

        async function loadProducts() {
            try { const response = await fetch('/api/products'); products = await response.json(); renderProductGrid(); populateRestockSelect(); }
            catch (error) { console.error('Failed to load products'); }
        }

        async function loadInventory() {
            try { const response = await fetch('/api/inventory', { headers: { 'Authorization': 'Bearer ' + authToken } }); inventory = await response.json(); renderInventoryTable(); }
            catch (error) { console.error('Failed to load inventory'); }
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
                    </div>`;
                grid.appendChild(card);
            });
        }

        function filterProducts() {
            const search = document.getElementById('productSearch').value.toLowerCase();
            document.querySelectorAll('.product-card').forEach(card => { card.style.display = card.querySelector('h4').textContent.toLowerCase().includes(search) ? 'block' : 'none'; });
        }

        function getQtyElementId(productName) { return 'qty-' + encodeURIComponent(productName); }

        function updateCart(product, change) {
            if (!cart[product]) cart[product] = 0;
            cart[product] += change;
            if (cart[product] < 0) cart[product] = 0;
            const productData = products.find(p => p.name === product);
            if (cart[product] > productData.stock) { cart[product] = productData.stock; showMessage('message', 'Not enough stock!', 'error'); }
            const qtyEl = document.getElementById(getQtyElementId(product));
            if (qtyEl) qtyEl.textContent = cart[product];
            updateCartDisplay();
            updatePaymentDisplay();
        }

        function updateCartDisplay() {
            const container = document.getElementById('cartItems');
            container.innerHTML = '';
            if (Object.keys(cart).length === 0) { document.getElementById('cartTotal').textContent = '0.00'; return; }
            let total = 0;
            Object.entries(cart).forEach(([product, qty]) => {
                if (qty > 0) {
                    const productData = products.find(p => p.name === product);
                    const itemTotal = productData.price * qty;
                    total += itemTotal;
                    const div = document.createElement('div');
                    div.className = 'cart-item';
                    div.innerHTML = `<span>${product} x ${qty} @ KES ${productData.price.toFixed(2)}</span><span>KES ${itemTotal.toFixed(2)}</span>`;
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
            if (Math.abs(paymentTotal - cartTotal) < 0.01 && cartTotal > 0) { matchEl.textContent = '✓ Balanced'; matchEl.className = 'payment-match'; }
            else if (cartTotal > 0) { matchEl.textContent = '✗ Mismatch'; matchEl.className = 'payment-mismatch'; }
            else { matchEl.textContent = ''; }
        }

        async function checkout() {
            const items = Object.entries(cart).filter(([_, qty]) => qty > 0).map(([name, quantity]) => {
                const product = products.find(p => p.name === name);
                return { name, quantity, price: product.price };
            });
            if (items.length === 0) { showMessage('message', 'Cart is empty!', 'error'); return; }
            const mpesa = parseFloat(document.getElementById('payMpesa').value) || 0;
            const cash = parseFloat(document.getElementById('payCash').value) || 0;
            const debt = parseFloat(document.getElementById('payDebt').value) || 0;
            const saleDate = document.getElementById('saleDate').value || new Date().toISOString().split('T')[0];
            const totalAmount = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            const totalPaid = mpesa + cash + debt;
            if (Math.abs(totalPaid - totalAmount) > 0.01) { showMessage('message', `Payment total (KES ${totalPaid.toFixed(2)}) does not match sale total (KES ${totalAmount.toFixed(2)})`, 'error'); return; }
            try {
                const response = await fetch('/api/sale', {
                    method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                    body: JSON.stringify({ items, payments: { mpesa, cash, debt }, date: saleDate })
                });
                if (response.ok) {
                    showMessage('message', 'Sale completed successfully!', 'success');
                    cart = {}; updateCartDisplay();
                    document.querySelectorAll('[id^="qty-"]').forEach(el => { el.textContent = '0'; });
                    document.getElementById('payMpesa').value = '';
                    document.getElementById('payCash').value = '';
                    document.getElementById('payDebt').value = '';
                    updatePaymentDisplay();
                    await loadProducts(); await loadInventory();
                } else { const data = await response.json(); showMessage('message', data.error || 'Sale failed', 'error'); }
            } catch (error) { showMessage('message', 'Sale failed: ' + error.message, 'error'); }
        }

        function renderInventoryTable() {
            const tbody = document.querySelector('#inventoryTable tbody');
            tbody.innerHTML = '';
            Object.entries(inventory).forEach(([name, data]) => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${name}</td><td class="${data.stock < 5 ? 'low-stock' : ''}">${data.stock}</td><td>${data.price.toFixed(2)}</td><td>${data.stock < 5 ? 'Low Stock' : 'OK'}</td>`;
                tbody.appendChild(row);
            });
        }

        function populateRestockSelect() {
            const select = document.getElementById('restockProduct');
            select.innerHTML = '';
            const defaultOption = document.createElement('option');
            defaultOption.value = ''; defaultOption.textContent = '-- Select a product --';
            select.appendChild(defaultOption);
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.name;
                option.textContent = `${product.name} (Current: ${product.stock})`;
                select.appendChild(option);
            });
            select.addEventListener('change', updateRestockStockDisplay);
        }

        function updateRestockStockDisplay() {
            const select = document.getElementById('restockProduct');
            const display = document.getElementById('currentStockDisplay');
            const selectedProduct = select.value;
            if (!selectedProduct) { display.textContent = 'Select a product to see current stock'; display.style.color = '#667eea'; return; }
            const product = products.find(p => p.name === selectedProduct);
            if (product) {
                display.innerHTML = `<span style="font-size: 24px;">${product.stock}</span> units in stock<br><small>Unit Price: KES ${product.price.toFixed(2)}</small>`;
                display.style.color = product.stock < 5 ? '#e74c3c' : '#27ae60';
            }
        }

        async function restock() {
            const product = document.getElementById('restockProduct').value;
            const quantity = parseInt(document.getElementById('restockQty').value);
            const date = document.getElementById('restockDate').value;
            if (!product) { showMessage('message', 'Please select a product', 'error'); return; }
            if (!quantity || quantity < 1) { showMessage('message', 'Please enter a valid quantity (minimum 1)', 'error'); return; }
            try {
                const response = await fetch('/api/restock', {
                    method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                    body: JSON.stringify({ product, quantity, date })
                });
                if (response.ok) {
                    showMessage('message', `Successfully added ${quantity} units to ${product}!`, 'success');
                    document.getElementById('restockQty').value = '';
                    document.getElementById('restockProduct').value = '';
                    await loadProducts(); await loadInventory();
                    updateRestockStockDisplay();
                } else { const data = await response.json(); showMessage('message', data.error || 'Restock failed', 'error'); }
            } catch (error) { showMessage('message', 'Restock failed: ' + error.message, 'error'); }
        }

        async function loadTransactions() {
            const response = await fetch('/api/transactions', { headers: { 'Authorization': 'Bearer ' + authToken } });
            const transactions = await response.json();
            const tbody = document.querySelector('#transactionsTable tbody');
            tbody.innerHTML = '';
            transactions.forEach(t => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${t.date}</td><td>${t.type}</td><td>${t.product}</td><td>${t.quantity}</td><td>${t.total}</td><td>${t.mpesa}</td><td>${t.cash}</td><td>${t.debt}</td>`;
                tbody.appendChild(row);
            });
        }

        function getTodayStr() { return new Date().toISOString().split('T')[0]; }
        function getYesterdayStr() { const d = new Date(); d.setDate(d.getDate() - 1); return d.toISOString().split('T')[0]; }
        function getWeekStartStr() { const d = new Date(); d.setDate(d.getDate() - d.getDay()); return d.toISOString().split('T')[0]; }
        function getMonthStartStr() { const d = new Date(); d.setDate(1); return d.toISOString().split('T')[0]; }

        function setQuickFilter(period) {
            document.querySelectorAll('.quick-filters button').forEach(btn => btn.classList.remove('active'));
            document.getElementById('qf-' + period).classList.add('active');
            const today = getTodayStr();
            let start = '', end = today;
            switch(period) {
                case 'today': start = today; end = today; break;
                case 'yesterday': start = getYesterdayStr(); end = getYesterdayStr(); break;
                case 'thisWeek': start = getWeekStartStr(); end = today; break;
                case 'thisMonth': start = getMonthStartStr(); end = today; break;
                case 'all': start = ''; end = ''; break;
            }
            document.getElementById('statsStartDate').value = start;
            document.getElementById('statsEndDate').value = end;
            currentStatsFilter = { startDate: start, endDate: end };
            loadStats();
        }

        function applyStatsFilter() {
            const start = document.getElementById('statsStartDate').value;
            const end = document.getElementById('statsEndDate').value;
            currentStatsFilter = { startDate: start, endDate: end };
            document.querySelectorAll('.quick-filters button').forEach(btn => btn.classList.remove('active'));
            loadStats();
        }

        function clearStatsFilter() {
            document.getElementById('statsStartDate').value = '';
            document.getElementById('statsEndDate').value = '';
            currentStatsFilter = { startDate: '', endDate: '' };
            document.querySelectorAll('.quick-filters button').forEach(btn => btn.classList.remove('active'));
            document.getElementById('qf-all').classList.add('active');
            loadStats();
        }

        async function loadStats() {
            try {
                let url = '/api/stats';
                if (currentStatsFilter.startDate || currentStatsFilter.endDate) {
                    const params = new URLSearchParams();
                    if (currentStatsFilter.startDate) params.append('startDate', currentStatsFilter.startDate);
                    if (currentStatsFilter.endDate) params.append('endDate', currentStatsFilter.endDate);
                    url += '?' + params.toString();
                }
                const response = await fetch(url, { headers: { 'Authorization': 'Bearer ' + authToken } });
                const stats = await response.json();
                const statusEl = document.getElementById('filterStatus');
                if (stats.filterApplied) { statusEl.innerHTML = `Showing data from <strong>${stats.startDate || 'beginning'}</strong> to <strong>${stats.endDate || 'today'}</strong>`; }
                else { statusEl.textContent = 'Showing all-time data'; }
                const grid = document.getElementById('statsGrid');
                const p = stats.payments || {};
                grid.innerHTML = `
                    <div class="stat-card"><div>Total Sales</div><div class="stat-value">${stats.totalSales}</div></div>
                    <div class="stat-card"><div>Total Revenue</div><div class="stat-value">KES ${stats.totalRevenue.toFixed(2)}</div></div>
                    <div class="stat-card"><div>Items Sold</div><div class="stat-value">${stats.totalItems}</div></div>
                    <div class="stat-card"><div>Today's Sales</div><div class="stat-value">KES ${stats.todaySales.toFixed(2)}</div></div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%);"><div>Total M-Pesa</div><div class="stat-value">KES ${(p.totalMpesa || 0).toFixed(2)}</div></div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #43a047 0%, #1b5e20 100%);"><div>Total Cash</div><div class="stat-value">KES ${(p.totalCash || 0).toFixed(2)}</div></div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #e53935 0%, #b71c1c 100%);"><div>Total Debt</div><div class="stat-value">KES ${(p.totalDebt || 0).toFixed(2)}</div></div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #fb8c00 0%, #e65100 100%);"><div>Today's M-Pesa</div><div class="stat-value">KES ${(p.todayMpesa || 0).toFixed(2)}</div></div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #8e24aa 0%, #4a148c 100%);"><div>Today's Cash</div><div class="stat-value">KES ${(p.todayCash || 0).toFixed(2)}</div></div>
                    <div class="stat-card" style="background: linear-gradient(135deg, #f4511e 0%, #bf360c 100%);"><div>Today's Debt</div><div class="stat-value">KES ${(p.todayDebt || 0).toFixed(2)}</div></div>
                `;
            } catch (error) { console.error('Failed to load stats'); }
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
            el.textContent = text; el.className = 'message ' + type;
            el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 3000);
        }

        document.addEventListener('DOMContentLoaded', () => {
            const today = new Date().toISOString().split('T')[0];
            const saleDate = document.getElementById('saleDate');
            const restockDate = document.getElementById('restockDate');
            if (saleDate) saleDate.value = today;
            if (restockDate) restockDate.value = today;
        });
    </script>
</body>
</html>
'''


if __name__ == '__main__':
    app.run(debug=True)
