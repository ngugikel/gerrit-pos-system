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

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'padmin123'

# Active tokens storage (in-memory for serverless)
active_tokens = set()

# Initial inventory
initial_inventory = {"all seasons 250ml": {"stock": 4.0, "price": 450.0}, "all seasons 375ml": {"stock": 0.0, "price": 650.0}, "all seasons 750ml": {"stock": 2.0, "price": 1300.0}, "Alter Wine": {"stock": 1.0, "price": 1400.0}, "Asconi": {"stock": 1.0, "price": 1950.0}, "Best Gin  250ml": {"stock": 0.0, "price": 320.0}, "Best Gin  750ml": {"stock": 0.0, "price": 900.0}, "Best vodka 250ml": {"stock": 0.0, "price": 300.0}, "Best vodka 750ml": {"stock": 3.0, "price": 850.0}, "Best whisky 750ml": {"stock": 0.0, "price": 1150.0}, "Best whisky 250ml": {"stock": 0.0, "price": 300.0}, "Blue ice": {"stock": 4.0, "price": 180.0}, "Bacardi": {"stock": 1.0, "price": 2700.0}, "balozi": {"stock": 6.0, "price": 240.0}, "Bombay Saphire": {"stock": 1.0, "price": 3450.0}, "Beefeater London 750ml": {"stock": 1.0, "price": 2350.0}, "beefeater pink 750ml": {"stock": 3.0, "price": 3150.0}, "beefeater pink 1litre": {"stock": 1.0, "price": 3150.0}, "beefeater london gin 1000ml": {"stock": 1.0, "price": 2850.0}, "black $ white 1000ml": {"stock": 0.0, "price": 1850.0}, "black $ white 750ml": {"stock": 0.0, "price": 1400.0}, "black $ white 350ml": {"stock": 1.0, "price": 730.0}, "bond 7 750ml": {"stock": 2.0, "price": 1600.0}, "bond 7 250ml": {"stock": 3.0, "price": 500.0}, "Black Label 1000ml": {"stock": 0.0, "price": 4500.0}, "Black Label 750ml": {"stock": 1.0, "price": 3700.0}, "black label 350ml": {"stock": 2.0, "price": 2100.0}, "Back label 250ml": {"stock": 2.0, "price": 0.0}, "black $ white 250ml": {"stock": 0.0, "price": 500.0}, "black bird": {"stock": 1.0, "price": 1100.0}, "captain morgan 1 litre (spiced)": {"stock": 1.0, "price": 2800.0}, "captain morgan 750ml": {"stock": 4.0, "price": 1150.0}, "captain morgan 250ml": {"stock": 4.0, "price": 400.0}, "chrome gin 750ml": {"stock": 3.0, "price": 700.0}, "chrome gin 250ml": {"stock": 6.0, "price": 250.0}, "chrome vodka 750ml": {"stock": 3.0, "price": 700.0}, "chrome vodka 250ml": {"stock": 7.0, "price": 250.0}, "circo": {"stock": 1.0, "price": 4500.0}, "chivas regal": {"stock": 1.0, "price": 4400.0}, "caprice sweet red": {"stock": 0.0, "price": 950.0}, "caprice white": {"stock": 1.0, "price": 950.0}, "crazy cock 750ml": {"stock": 0.0, "price": 1150.0}, "crazy cock 350ml": {"stock": 0.0, "price": 650.0}, "crazy cock 250ml": {"stock": 1.0, "price": 450.0}, "caribia gin 750ml": {"stock": 2.0, "price": 870.0}, "caribia gin 350ml": {"stock": 0.0, "price": 0.0}, "caribia gin 250ml": {"stock": 4.0, "price": 300.0}, "county 750ml": {"stock": 1.0, "price": 800.0}, "county 250ml": {"stock": 4.0, "price": 300.0}, "Camino tequlla ": {"stock": 0.0, "price": 2600.0}, "clubman 750ml ": {"stock": 1.0, "price": 900.0}, "cellar cask 5litre": {"stock": 1.0, "price": 4500.0}, "cellar cask Red 750ml": {"stock": 1.0, "price": 1050.0}, "chamdor Red": {"stock": 1.0, "price": 900.0}, "desperado": {"stock": 2.0, "price": 350.0}, "drostdy sweet red": {"stock": 4.0, "price": 1150.0}, "drostdy Sweet white": {"stock": 1.0, "price": 1150.0}, "delush Red": {"stock": 1.0, "price": 1000.0}, "eristoff": {"stock": 1.0, "price": 1400.0}, "first choice 750ml": {"stock": 3.0, "price": 800.0}, "famous grouse 1litre": {"stock": 1.0, "price": 2800.0}, "famous grouse 750ml": {"stock": 1.0, "price": 2150.0}, "faxe": {"stock": 5.0, "price": 340.0}, "gordons pink 1litre": {"stock": 2.0, "price": 2800.0}, "gordons pink 750ml": {"stock": 1.0, "price": 2300.0}, "gordons original 1litre": {"stock": 0.0, "price": 2900.0}, "gordons original 750ml": {"stock": 0.0, "price": 2400.0}, "gordons lemon 750ml": {"stock": 1.0, "price": 2300.0}, "gordons orange": {"stock": 0.0, "price": 2300.0}, "glenfiddich": {"stock": 2.0, "price": 7400.0}, "gilbeys pink 750ml": {"stock": 1.0, "price": 1600.0}, "gilbeys pink 350ml": {"stock": 1.0, "price": 710.0}, "gilbeys pink 250ml": {"stock": 1.0, "price": 500.0}, "gilbeys original 750ml": {"stock": 1.0, "price": 1600.0}, "gilgeys original 350ml": {"stock": 1.0, "price": 710.0}, "gilbeys 250ml": {"stock": 2.0, "price": 500.0}, "gibsons 750ml": {"stock": 0.0, "price": 1600.0}, "gibsons 350ml": {"stock": 0.0, "price": 0.0}, "gibsons 250ml": {"stock": 0.0, "price": 0.0}, "glen silver": {"stock": 2.0, "price": 1700.0}, "guinness": {"stock": 6.0, "price": 270.0}, "general meakins": {"stock": 3.0, "price": 270.0}, "grande france White Semi- Sweet": {"stock": 1.0, "price": 1400.0}, "hunters choice 750ml": {"stock": 4.0, "price": 1100.0}, "hunters choice 350": {"stock": 5.0, "price": 550.0}, "hunters choice 250ml": {"stock": 6.0, "price": 450.0}, "hunters gold": {"stock": 2.0, "price": 250.0}, "heinekein": {"stock": 6.0, "price": 290.0}, "henessy SP 750ML": {"stock": 1.0, "price": 6000.0}, "hendricks 1litre": {"stock": 1.0, "price": 5000.0}, "hendricks 750ml": {"stock": 3.0, "price": 4000.0}, "imperial blue 750ml": {"stock": 3.0, "price": 1050.0}, "jack daniel original": {"stock": 0.0, "price": 0.0}, "jack daniel  750ml (honey)": {"stock": 1.0, "price": 4500.0}, "jagermeister 1lite ": {"stock": 1.5, "price": 3400.0}, "jagermeister 750ml": {"stock": 1.0, "price": 2800.0}, "jameson 1lite": {"stock": 0.0, "price": 3600.0}, "jameson 750ml": {"stock": 0.0, "price": 2950.0}, "jameson 350ml": {"stock": 2.0, "price": 1450.0}, "jameson 250ml": {"stock": 0.0, "price": 0.0}, "j $ b 750ml": {"stock": 1.0, "price": 1900.0}, "jose quavo 750ml": {"stock": 0.0, "price": 2900.0}, "kc smooth 750 ml": {"stock": 2.0, "price": 900.0}, "kc smooth 350ml": {"stock": 1.0, "price": 450.0}, "kc smooth 250ml": {"stock": 3.0, "price": 320.0}, "kc pineapple 750ml": {"stock": 3.0, "price": 900.0}, "kc pineapple 350ml": {"stock": 0.0, "price": 450.0}, "kc pineapple 250ml": {"stock": 5.0, "price": 320.0}, "kc ginger $ lemon 750ml": {"stock": 3.0, "price": 900.0}, "kc ginger $ lemon 350ml": {"stock": 0.0, "price": 450.0}, "kc ginnger $ lemon 250ml": {"stock": 6.0, "price": 320.0}, "kibao voka 750ml": {"stock": 2.0, "price": 780.0}, "kibao voka 350ml": {"stock": 0.0, "price": 450.0}, "kibao vodka 250ml": {"stock": 4.0, "price": 300.0}, "kibao gin 750ml": {"stock": 2.0, "price": 750.0}, "kibao gin 350ml": {"stock": 0.0, "price": 450.0}, "kibao  gin 250ml": {"stock": 4.0, "price": 260.0}, "konyagi 750ml": {"stock": 2.0, "price": 800.0}, "konyagi 500ml": {"stock": 0.0, "price": 550.0}, "konyagi 250ml": {"stock": 5.0, "price": 300.0}, "kane 750ml": {"stock": 4.0, "price": 750.0}, "kane 250ml": {"stock": 0.0, "price": 250.0}, "k.o tonic ": {"stock": 1.0, "price": 150.0}, "k.o  bottle": {"stock": 3.0, "price": 300.0}, "leadimg warigi 750ml": {"stock": 1.0, "price": 770.0}, "mara (wine) Red": {"stock": 1.0, "price": 1300.0}, "mikado(cherry)": {"stock": 1.0, "price": 1600.0}, "mikado (pineapple)": {"stock": 1.0, "price": 1600.0}, "malibu": {"stock": 1.0, "price": 2350.0}, "ministers reserve 750ml": {"stock": 1.0, "price": 1600.0}, "monkey shoulder": {"stock": 1.0, "price": 4500.0}, "martini": {"stock": 1.0, "price": 2700.0}, "monster": {"stock": 4.0, "price": 250.0}, "manyatta (can)": {"stock": 1.0, "price": 300.0}, "manyatta ( bottle)": {"stock": 3.0, "price": 300.0}, "namaqua sweet red (wine)": {"stock": 2.0, "price": 1000.0}, "o pm vodka 750ml": {"stock": 2.0, "price": 1250.0}, "o pm vodka 350ml": {"stock": 1.0, "price": 680.0}, "o pm vodka 250ml": {"stock": 2.0, "price": 450.0}, "old monk": {"stock": 1.0, "price": 1050.0}, "oj 16%": {"stock": 6.0, "price": 400.0}, "oj 12%": {"stock": 0.0, "price": 320.0}, "Old smuggler": {"stock": 1.0, "price": 1400.0}, "paddy irish": {"stock": 0.0, "price": 1500.0}, "passport scotch": {"stock": 1.0, "price": 1350.0}, "pervack 1litre": {"stock": 1.0, "price": 1500.0}, "pervack  750ml": {"stock": 0.0, "price": 1300.0}, "penasol white wine": {"stock": 2.0, "price": 950.0}, "penasol red wine": {"stock": 1.0, "price": 950.0}, "robertson 1.5litre": {"stock": 1.0, "price": 2100.0}, "robertson 750ml": {"stock": 1.0, "price": 1200.0}, "red label 1litre ": {"stock": 0.0, "price": 2700.0}, "red label 750ml": {"stock": 0.0, "price": 2300.0}, "red label 350ml": {"stock": 0.0, "price": 1050.0}, "red label 250ml": {"stock": 0.0, "price": 700.0}, "redbull": {"stock": 0.0, "price": 230.0}, "rosso nobile (wine)": {"stock": 2.0, "price": 1500.0}, "smirnoff vodka 1litre": {"stock": 1.0, "price": 2000.0}, "smirnoff vodka 750ml": {"stock": 1.0, "price": 1600.0}, "smirnoff vodka 350ml": {"stock": 0.0, "price": 750.0}, "smirnoff vodka 250ml": {"stock": 2.0, "price": 510.0}, "smirnoff pineapple punch ": {"stock": 5.0, "price": 220.0}, "smirnoff guaranna": {"stock": 5.0, "price": 220.0}, "smirnoff black ice": {"stock": 18.0, "price": 220.0}, "sweet berry ": {"stock": 2.0, "price": 150.0}, "strumbras": {"stock": 2.0, "price": 700.0}, "savanna": {"stock": 3.0, "price": 300.0}, "southern comfort 1litre": {"stock": 1.0, "price": 2700.0}, "southern comfort 750ml": {"stock": 3.0, "price": 2400.0}, "southern comfort 350ml": {"stock": 3.0, "price": 750.0}, "sky infusion ": {"stock": 2.0, "price": 1500.0}, "star walker ": {"stock": 1.0, "price": 1500.0}, "sun chaser(wine)": {"stock": 1.0, "price": 950.0}, "singleton ": {"stock": 1.0, "price": 5700.0}, "tanqueray  1litre ( no 10)": {"stock": 1.0, "price": 6050.0}, " tanqueray 750ml ( no 10)                 ": {"stock": 1.0, "price": 5050.0}, "tanqueray  gin 1litre": {"stock": 0.0, "price": 3750.0}, "tanqueray  gin 750ml": {"stock": 1.0, "price": 2850.0}, "top secret 750ml": {"stock": 0.0, "price": 870.0}, "top secret 250ml": {"stock": 3.0, "price": 310.0}, "three barrels 750ml": {"stock": 1.0, "price": 2850.0}, "tusker lager (can)": {"stock": 4.0, "price": 240.0}, "tusker cider (can)": {"stock": 10.0, "price": 280.0}, "tusker malt (green)": {"stock": 1.0, "price": 300.0}, "versus white (wine)": {"stock": 1.0, "price": 1200.0}, "VAT 69  1 LITRE": {"stock": 0.0, "price": 2200.0}, "VAT 69  750ML": {"stock": 0.0, "price": 900.0}, "VAT 69 350ML": {"stock": 0.0, "price": 950.0}, "VAT 69 250ML": {"stock": 1.0, "price": 650.0}, "Viceroy 750ml": {"stock": 2.0, "price": 1500.0}, "viceroy 350ml": {"stock": 2.0, "price": 760.0}, "viceroy 250ml": {"stock": 2.0, "price": 520.0}, "V$A imperial ": {"stock": 1.0, "price": 900.0}, "wild turkey (bourbon)": {"stock": 1.0, "price": 4200.0}, "white cap (can)": {"stock": 6.0, "price": 270.0}, "william lawsons 1litre": {"stock": 1.0, "price": 3000.0}, "william lawsons 750ml": {"stock": 0.0, "price": 2000.0}, "william lawsons 350ml": {"stock": 2.0, "price": 1050.0}, "william lawsons 250ml": {"stock": 0.0, "price": 0.0}, "zappa black": {"stock": 1.0, "price": 1750.0}, "zappa original": {"stock": 1.0, "price": 1750.0}, "zappa blue": {"stock": 1.0, "price": 1750.0}, "# 7": {"stock": 1.0, "price": 1200.0}, "58 gin": {"stock": 1.0, "price": 1450.0}, " miniute maid ": {"stock": 8.0, "price": 160.0}, "water 500ml ": {"stock": 12.0, "price": 30.0}, "water  dasani": {"stock": 5.0, "price": 70.0}, "soda 2litre": {"stock": 6.0, "price": 200.0}, "sodalitre 1litre": {"stock": 8.0, "price": 120.0}, "dunhill double switch": {"stock": 0.0, "price": 600.0}, "dunhill single switch": {"stock": 0.0, "price": 600.0}, "pall mall (king safari)": {"stock": 0.0, "price": 300.0}, "pall mall ( menthol)": {"stock": 0.0, "price": 300.0}, "oris milano": {"stock": 0.0, "price": 400.0}, "oris menthol": {"stock": 0.0, "price": 400.0}, "rothmans red ": {"stock": 0.0, "price": 500.0}, "rothmans blue": {"stock": 0.0, "price": 500.0}, "dunhill embassy": {"stock": 0.0, "price": 600.0}, "lemonade": {"stock": 3.0, "price": 50.0}, "predator": {"stock": 3.0, "price": 70.0}}

def load_data():
    """Load data from /tmp files or initialize"""
    global inventory_data, sales_data, restocks_data
    
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

def save_inventory():
    """Save inventory to /tmp"""
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory_data, f)

def save_sales():
    """Save sales to /tmp"""
    with open(SALES_FILE, 'w') as f:
        json.dump(sales_data, f)

def save_restocks():
    """Save restocks to /tmp"""
    with open(RESTOCKS_FILE, 'w') as f:
        json.dump(restocks_data, f)

def token_required(f):
    """Decorator to check for valid token"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        if token not in active_tokens:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

# Load data on startup
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
        return jsonify({'success': True, 'token': token, 'message': 'Login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
        active_tokens.discard(token)
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
    return jsonify(inventory_data)

@app.route('/api/sale', methods=['POST'])
@token_required
def record_sale():
    data = request.get_json()
    items = data.get('items', [])
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

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
                'type': 'Sale'
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
    today_sales = sum(s['total'] for s in sales_data if s['date'] == today)

    return jsonify({
        'totalSales': len(sales_data),
        'totalRevenue': sum(s['total'] for s in sales_data),
        'totalItems': sum(s['quantity'] for s in sales_data),
        'todaySales': today_sales
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
                    <button onclick="showTab('transactions')" id="tab-transactions">Transactions</button>
                    <button onclick="showTab('stats')" id="tab-stats">Stats</button>
                    <button onclick="logout()" class="btn-danger">Logout</button>
                </div>
            </div>

            <div class="content">
                <div id="message" class="message"></div>

                <!-- POS Tab -->
                <div id="posTab" class="tab-content">
                    <div class="search-box">
                        <input type="text" id="productSearch" placeholder="Search products..." onkeyup="filterProducts()">
                    </div>
                    <div class="product-grid" id="productGrid"></div>
                    
                    <div class="cart-summary">
                        <h3>Cart</h3>
                        <div id="cartItems"></div>
                        <div class="total">Total: KES <span id="cartTotal">0</span></div>
                        <button onclick="checkout()" class="btn-success" style="width: 100%; margin-top: 15px;">Complete Sale</button>
                    </div>
                </div>

                <!-- Inventory Tab -->
                <div id="inventoryTab" class="tab-content hidden">
                    <h2>Inventory Management</h2>
                    <div style="margin: 20px 0;">
                        <h3>Restock Product</h3>
                        <select id="restockProduct"></select>
                        <input type="number" id="restockQty" placeholder="Quantity" min="1">
                        <button onclick="restock()">Restock</button>
                    </div>
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
                card.className = 'product-card';
                card.innerHTML = `
                    <h4>${product.name}</h4>
                    <p>KES ${product.price}</p>
                    <p class="${product.stock < 5 ? 'low-stock' : ''}">Stock: ${product.stock}</p>
                    <div class="quantity-control" onclick="event.stopPropagation()">
                        <button onclick="updateCart('${product.name}', -1)">-</button>
                        <span id="qty-${product.name}">0</span>
                        <button onclick="updateCart('${product.name}', 1)">+</button>
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

        function updateCart(product, change) {
            if (!cart[product]) cart[product] = 0;
            cart[product] += change;
            if (cart[product] < 0) cart[product] = 0;
            
            const productData = products.find(p => p.name === product);
            if (cart[product] > productData.stock) {
                cart[product] = productData.stock;
                showMessage('message', 'Not enough stock!', 'error');
            }
            
            document.getElementById(`qty-${product}`).textContent = cart[product];
            updateCartDisplay();
        }

        function updateCartDisplay() {
            const container = document.getElementById('cartItems');
            container.innerHTML = '';
            let total = 0;
            
            Object.entries(cart).forEach(([product, qty]) => {
                if (qty > 0) {
                    const productData = products.find(p => p.name === product);
                    const itemTotal = productData.price * qty;
                    total += itemTotal;
                    
                    const div = document.createElement('div');
                    div.className = 'cart-item';
                    div.innerHTML = `
                        <span>${product} x ${qty}</span>
                        <span>KES ${itemTotal.toFixed(2)}</span>
                    `;
                    container.appendChild(div);
                }
            });
            
            document.getElementById('cartTotal').textContent = total.toFixed(2);
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
            
            try {
                const response = await fetch('/api/sale', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ items })
                });
                
                if (response.ok) {
                    showMessage('message', 'Sale completed!', 'success');
                    cart = {};
                    loadProducts();
                    loadInventory();
                    renderProductGrid();
                } else {
                    const data = await response.json();
                    showMessage('message', data.error || 'Sale failed', 'error');
                }
            } catch (error) {
                showMessage('message', 'Sale failed', 'error');
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
                    <td>${data.price}</td>
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
            const product = document.getElementById('restockProduct').value;
            const quantity = parseInt(document.getElementById('restockQty').value);
            
            if (!quantity || quantity < 1) {
                showMessage('message', 'Invalid quantity', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/restock', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ product, quantity })
                });
                
                if (response.ok) {
                    showMessage('message', 'Restocked successfully!', 'success');
                    document.getElementById('restockQty').value = '';
                    loadInventory();
                    loadProducts();
                } else {
                    const data = await response.json();
                    showMessage('message', data.error || 'Restock failed', 'error');
                }
            } catch (error) {
                showMessage('message', 'Restock failed', 'error');
            }
        }

        async function loadTransactions() {
            try {
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
                        <td>KES ${t.total.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Failed to load transactions');
            }
        }

        async function loadStats() {
            try {
                const response = await fetch('/api/stats', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const stats = await response.json();
                
                const grid = document.getElementById('statsGrid');
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
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
