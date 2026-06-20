from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime
import json
import os
import uuid

app = Flask(__name__)
CORS(app)

# File paths for persistence (Vercel /tmp directory)
INVENTORY_FILE = '/tmp/inventory.json'
SALES_FILE = '/tmp/sales.json'
RESTOCKS_FILE = '/tmp/restocks.json'
TOKENS_FILE = '/tmp/tokens.json'

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'padmin123'

# Active tokens storage - loaded from disk
active_tokens = set()

# Initial inventory
initial_inventory = {"all seasons 250ml": {"stock": 4.0, "price": 450.0}}

def load_data():
    global inventory_data, sales_data, restocks_data, active_tokens

    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'r') as f:
            inventory_data = json.load(f)
    else:
        inventory_data = json.loads(json.dumps(initial_inventory))
        save_inventory()

    if os.path.exists(SALES_FILE):
        with open(SALES_FILE, 'r') as f:
            sales_data = json.load(f)
    else:
        sales_data = []

    if os.path.exists(RESTOCKS_FILE):
        with open(RESTOCKS_FILE, 'r') as f:
            restocks_data = json.load(f)
    else:
        restocks_data = []

    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as f:
            token_list = json.load(f)
            active_tokens = set(token_list)
    else:
        active_tokens = set()

def save_inventory():
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory_data, f)

def save_sales():
    with open(SALES_FILE, 'w') as f:
        json.dump(sales_data, f)

def save_restocks():
    with open(RESTOCKS_FILE, 'w') as f:
        json.dump(restocks_data, f)

def save_tokens():
    with open(TOKENS_FILE, 'w') as f:
        json.dump(list(active_tokens), f)

def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        if token not in active_tokens:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

load_data()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = str(uuid.uuid4())
        active_tokens.add(token)
        save_tokens()
        return jsonify({'success': True, 'token': token, 'message': 'Login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
        active_tokens.discard(token)
        save_tokens()
    return jsonify({'success': True})

@app.route('/api/check-auth')
def check_auth():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
        if token in active_tokens:
            return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})

@app.route('/api/products')
def get_products():
    products = []
    for name, data in inventory_data.items():
        products.append({'name': name, 'price': data['price'], 'stock': data['stock']})
    return jsonify(products)

@app.route('/api/inventory')
@token_required
def get_inventory():
    return jsonify(inventory_data)

@app.route('/api/sale', methods=['POST'])
@token_required
def record_sale():
    data = request.get_json()
    items = data.get('items', [])
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
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
            inventory_data[product]['stock'] -= qty
            sales_data.append({
                'date': date,
                'product': product,
                'quantity': qty,
                'unitPrice': item['price'],
                'total': item['price'] * qty,
                'type': 'Sale',
                'mpesa': mpesa,
                'cash': cash,
                'debt': debt
            })
        else:
            return jsonify({'error': f'Insufficient stock for {product}'}), 400

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
    if product in inventory_data:
        inventory_data[product]['stock'] += qty
        restocks_data.append({
            'date': date,
            'product': product,
            'quantity': qty,
            'unitPrice': inventory_data[product]['price'],
            'total': inventory_data[product]['price'] * qty,
            'type': 'Restock'
        })
        save_inventory()
        save_restocks()
        return jsonify({'success': True})
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/transactions')
@token_required
def get_transactions():
    all_transactions = sales_data + restocks_data
    return jsonify(sorted(all_transactions, key=lambda x: x['date'], reverse=True))

@app.route('/api/stats')
@token_required
def get_stats():
    today = datetime.now().strftime('%Y-%m-%d')
    today_sales = [s for s in sales_data if s['date'] == today]
    total_mpesa = sum(s.get('mpesa', 0) for s in sales_data)
    total_cash = sum(s.get('cash', 0) for s in sales_data)
    total_debt = sum(s.get('debt', 0) for s in sales_data)
    today_mpesa = sum(s.get('mpesa', 0) for s in today_sales)
    today_cash = sum(s.get('cash', 0) for s in today_sales)
    today_debt = sum(s.get('debt', 0) for s in today_sales)
    return jsonify({
        'totalSales': len(sales_data),
        'totalRevenue': sum(s['total'] for s in sales_data),
        'totalItems': sum(s['quantity'] for s in sales_data),
        'todaySales': sum(s['total'] for s in today_sales),
        'payments': {
            'totalMpesa': total_mpesa,
            'totalCash': total_cash,
            'totalDebt': total_debt,
            'todayMpesa': today_mpesa,
            'todayCash': today_cash,
            'todayDebt': today_debt
        }
    })

HTML_TEMPLATE = """
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
        .nav { display: flex; gap: 10px; }
        .nav button { background: #555; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; transition: background 0.3s; }
        .nav button:hover, .nav button.active { background: #667eea; }
        .content { padding: 20px; }
        .hidden { display: none !important; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; transition: background 0.3s; }
        button:hover { background: #5568d3; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #229954; }
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
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e0e0e0; border: none; cursor: pointer; border-radius: 5px; }
        .tab.active { background: #667eea; color: white; }
        .search-box { margin-bottom: 20px; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .product-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .product-card:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.1); transform: translateY(-2px); }
        .product-card.selected { border-color: #667eea; background: #f0f0ff; }
        .quantity-control { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
        .quantity-control button { width: 30px; height: 30px; padding: 0; border-radius: 50%; }
        .cart-summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 20px; }
        .total { font-size: 24px; font-weight: bold; color: #667eea; margin-top: 10px; }
        .payment-match { color: #27ae60; font-weight: bold; }
        .payment-mismatch { color: #e74c3c; font-weight: bold; }
        .out-of-stock { opacity: 0.5; pointer-events: none; }
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
                    <button onclick="showTab('transactions')" id="tab-transactions">Transactions</button>
                    <button onclick="showTab('stats')" id="tab-stats">Stats</button>
                    <button onclick="logout()" class="btn-danger">Logout</button>
                </div>
            </div>
            <div class="content">
                <div id="message" class="message"></div>
                <div id="posTab" class="tab-content">
                    <div class="search-box">
                        <input type="text" id="productSearch" placeholder="Search products..." onkeyup="filterProducts()">
                    </div>
                    <div class="product-grid" id="productGrid"></div>
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
                <div id="inventoryTab" class="tab-content hidden">
                    <h2>Inventory Management</h2>
                    <div style="margin: 20px 0;">
                        <h3>Restock Product</h3>
                        <select id="restockProduct"></select>
                        <input type="number" id="restockQty" placeholder="Quantity" min="1">
                        <button onclick="restock()">Restock</button>
                    </div>
                    <table id="inventoryTable">
                        <thead><tr><th>Product</th><th>Stock</th><th>Price (KES)</th><th>Status</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>
                <div id="transactionsTab" class="tab-content hidden">
                    <h2>Transaction History</h2>
                    <table id="transactionsTable">
                        <thead><tr><th>Date</th><th>Type</th><th>Product</th><th>Qty</th><th>Total (KES)</th><th>M-Pesa</th><th>Cash</th><th>Debt</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>
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
        if (authToken) { checkAuth(); }
        async function checkAuth() {
            try {
                const response = await fetch('/api/check-auth', { headers: { 'Authorization': 'Bearer ' + authToken } });
                const data = await response.json();
                if (data.authenticated) { showApp(); }
                else { localStorage.removeItem('pos_token'); authToken = null; showLogin(); }
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
        function logout() {
            fetch('/api/logout', { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken } });
            localStorage.removeItem('pos_token'); authToken = null; showLogin();
        }
        async function loadProducts() {
            try { const response = await fetch('/api/products'); products = await response.json(); renderProductGrid(); populateRestockSelect(); }
            catch (error) { console.error('Failed to load products'); }
        }
        async function loadInventory() {
            try { const response = await fetch('/api/inventory', { headers: { 'Authorization': 'Bearer ' + authToken } }); inventory = await response.json(); renderInventoryTable(); }
            catch (error) { console.error('Failed to load inventory'); }
        }
        function renderProductGrid() {
            const grid = document.getElementById('productGrid'); grid.innerHTML = '';
            products.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card' + (product.stock <= 0 ? ' out-of-stock' : '');
                card.innerHTML = `<h4>${product.name}</h4><p>KES ${product.price.toFixed(2)}</p><p class="${product.stock < 5 ? 'low-stock' : ''}">Stock: ${product.stock}</p><div class="quantity-control" onclick="event.stopPropagation()"><button onclick="updateCart('${product.name.replace(/'/g, "\'")}', -1)" ${product.stock <= 0 ? 'disabled' : ''}>-</button><span id="qty-${encodeURIComponent(product.name)}">0</span><button onclick="updateCart('${product.name.replace(/'/g, "\'")}', 1)" ${product.stock <= 0 ? 'disabled' : ''}>+</button></div>`;
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
            updateCartDisplay(); updatePaymentDisplay();
        }
        function updateCartDisplay() {
            const container = document.getElementById('cartItems'); container.innerHTML = ''; let total = 0;
            Object.entries(cart).forEach(([product, qty]) => {
                if (qty > 0) {
                    const productData = products.find(p => p.name === product);
                    const itemTotal = productData.price * qty; total += itemTotal;
                    const div = document.createElement('div'); div.className = 'cart-item';
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
            const items = Object.entries(cart).filter(([_, qty]) => qty > 0).map(([name, quantity]) => { const product = products.find(p => p.name === name); return { name, quantity, price: product.price }; });
            if (items.length === 0) { showMessage('message', 'Cart is empty!', 'error'); return; }
            const mpesa = parseFloat(document.getElementById('payMpesa').value) || 0;
            const cash = parseFloat(document.getElementById('payCash').value) || 0;
            const debt = parseFloat(document.getElementById('payDebt').value) || 0;
            const totalAmount = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            const totalPaid = mpesa + cash + debt;
            if (Math.abs(totalPaid - totalAmount) > 0.01) { showMessage('message', `Payment total (KES ${totalPaid.toFixed(2)}) does not match sale total (KES ${totalAmount.toFixed(2)})`, 'error'); return; }
            try {
                const response = await fetch('/api/sale', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken },
                    body: JSON.stringify({ items, payments: { mpesa, cash, debt } })
                });
                if (response.ok) {
                    showMessage('message', 'Sale completed successfully!', 'success');
                    cart = {};
                    document.getElementById('payMpesa').value = '';
                    document.getElementById('payCash').value = '';
                    document.getElementById('payDebt').value = '';
                    loadProducts(); loadInventory(); updatePaymentDisplay();
                } else { const data = await response.json(); showMessage('message', data.error || 'Sale failed', 'error'); }
            } catch (error) { showMessage('message', 'Sale failed: ' + error.message, 'error'); }
        }
        function renderInventoryTable() {
            const tbody = document.querySelector('#inventoryTable tbody'); tbody.innerHTML = '';
            Object.entries(inventory).forEach(([name, data]) => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${name}</td><td class="${data.stock < 5 ? 'low-stock' : ''}">${data.stock}</td><td>${data.price.toFixed(2)}</td><td>${data.stock < 5 ? 'Low Stock' : 'OK'}</td>`;
                tbody.appendChild(row);
            });
        }
        function populateRestockSelect() {
            const select = document.getElementById('restockProduct'); select.innerHTML = '';
            products.forEach(product => { const option = document.createElement('option'); option.value = product.name; option.textContent = product.name; select.appendChild(option); });
        }
        async function restock() {
            const product = document.getElementById('restockProduct').value;
            const quantity = parseInt(document.getElementById('restockQty').value);
            if (!quantity || quantity < 1) { showMessage('message', 'Invalid quantity', 'error'); return; }
            try {
                const response = await fetch('/api/restock', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + authToken }, body: JSON.stringify({ product, quantity }) });
                if (response.ok) { showMessage('message', 'Restocked successfully!', 'success'); document.getElementById('restockQty').value = ''; loadInventory(); loadProducts(); }
                else { const data = await response.json(); showMessage('message', data.error || 'Restock failed', 'error'); }
            } catch (error) { showMessage('message', 'Restock failed', 'error'); }
        }
        async function loadTransactions() {
            try {
                const response = await fetch('/api/transactions', { headers: { 'Authorization': 'Bearer ' + authToken } });
                const transactions = await response.json();
                const tbody = document.querySelector('#transactionsTable tbody'); tbody.innerHTML = '';
                transactions.forEach(t => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${t.date}</td><td>${t.type}</td><td>${t.product}</td><td>${t.quantity}</td><td>KES ${t.total.toFixed(2)}</td><td>${t.mpesa ? 'KES ' + t.mpesa.toFixed(2) : '-'}</td><td>${t.cash ? 'KES ' + t.cash.toFixed(2) : '-'}</td><td>${t.debt ? 'KES ' + t.debt.toFixed(2) : '-'}</td>`;
                    tbody.appendChild(row);
                });
            } catch (error) { console.error('Failed to load transactions'); }
        }
        async function loadStats() {
            try {
                const response = await fetch('/api/stats', { headers: { 'Authorization': 'Bearer ' + authToken } });
                const stats = await response.json();
                const grid = document.getElementById('statsGrid');
                const p = stats.payments || {};
                grid.innerHTML = `<div class="stat-card"><div>Total Sales</div><div class="stat-value">${stats.totalSales}</div></div><div class="stat-card"><div>Total Revenue</div><div class="stat-value">KES ${stats.totalRevenue.toFixed(2)}</div></div><div class="stat-card"><div>Items Sold</div><div class="stat-value">${stats.totalItems}</div></div><div class="stat-card"><div>Today's Sales</div><div class="stat-value">KES ${stats.todaySales.toFixed(2)}</div></div><div class="stat-card" style="background: linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%);"><div>Total M-Pesa</div><div class="stat-value">KES ${(p.totalMpesa || 0).toFixed(2)}</div></div><div class="stat-card" style="background: linear-gradient(135deg, #43a047 0%, #1b5e20 100%);"><div>Total Cash</div><div class="stat-value">KES ${(p.totalCash || 0).toFixed(2)}</div></div><div class="stat-card" style="background: linear-gradient(135deg, #e53935 0%, #b71c1c 100%);"><div>Total Debt</div><div class="stat-value">KES ${(p.totalDebt || 0).toFixed(2)}</div></div><div class="stat-card" style="background: linear-gradient(135deg, #fb8c00 0%, #e65100 100%);"><div>Today's M-Pesa</div><div class="stat-value">KES ${(p.todayMpesa || 0).toFixed(2)}</div></div><div class="stat-card" style="background: linear-gradient(135deg, #8e24aa 0%, #4a148c 100%);"><div>Today's Cash</div><div class="stat-value">KES ${(p.todayCash || 0).toFixed(2)}</div></div><div class="stat-card" style="background: linear-gradient(135deg, #f4511e 0%, #bf360c 100%);"><div>Today's Debt</div><div class="stat-value">KES ${(p.todayDebt || 0).toFixed(2)}</div></div>`;
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
            el.textContent = text; el.className = 'message ' + type; el.style.display = 'block';
            setTimeout(() => el.style.display = 'none', 3000);
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
