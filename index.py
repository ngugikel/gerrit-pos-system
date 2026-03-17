from flask import Flask, jsonify, request, session, render_template_string
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'gerrit-pos-secret-key-2024'
CORS(app)

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'padmin123'

# Initial inventory
initial_inventory = {"all seasons 250ml": {"stock": 4.0, "price": 450.0}, "all seasons 375ml": {"stock": 0.0, "price": 650.0}, "all seasons 750ml": {"stock": 2.0, "price": 1300.0}, "Alter Wine": {"stock": 1.0, "price": 1400.0}, "Asconi": {"stock": 1.0, "price": 1950.0}, "Best Gin  250ml": {"stock": 0.0, "price": 320.0}, "Best Gin  750ml": {"stock": 0.0, "price": 900.0}, "Best vodka 250ml": {"stock": 0.0, "price": 300.0}, "Best vodka 750ml": {"stock": 3.0, "price": 850.0}, "Best whisky 750ml": {"stock": 0.0, "price": 1150.0}, "Best whisky 250ml": {"stock": 0.0, "price": 300.0}, "Blue ice": {"stock": 4.0, "price": 180.0}, "Bacardi": {"stock": 1.0, "price": 2700.0}, "balozi": {"stock": 6.0, "price": 240.0}, "Bombay Saphire": {"stock": 1.0, "price": 3450.0}, "Beefeater London 750ml": {"stock": 1.0, "price": 2350.0}, "beefeater pink 750ml": {"stock": 3.0, "price": 3150.0}, "beefeater pink 1litre": {"stock": 1.0, "price": 3150.0}, "beefeater london gin 1000ml": {"stock": 1.0, "price": 2850.0}, "black $ white 1000ml": {"stock": 0.0, "price": 1850.0}, "black $ white 750ml": {"stock": 0.0, "price": 1400.0}, "black $ white 350ml": {"stock": 1.0, "price": 730.0}, "bond 7 750ml": {"stock": 2.0, "price": 1600.0}, "bond 7 250ml": {"stock": 3.0, "price": 500.0}, "Black Label 1000ml": {"stock": 0.0, "price": 4500.0}, "Black Label 750ml": {"stock": 1.0, "price": 3700.0}, "black label 350ml": {"stock": 2.0, "price": 2100.0}, "Back label 250ml": {"stock": 2.0, "price": 0.0}, "black $ white 250ml": {"stock": 0.0, "price": 500.0}, "black bird": {"stock": 1.0, "price": 1100.0}, "captain morgan 1 litre (spiced)": {"stock": 1.0, "price": 2800.0}, "captain morgan 750ml": {"stock": 4.0, "price": 1150.0}, "captain morgan 250ml": {"stock": 4.0, "price": 400.0}, "chrome gin 750ml": {"stock": 3.0, "price": 700.0}, "chrome gin 250ml": {"stock": 6.0, "price": 250.0}, "chrome vodka 750ml": {"stock": 3.0, "price": 700.0}, "chrome vodka 250ml": {"stock": 7.0, "price": 250.0}, "circo": {"stock": 1.0, "price": 4500.0}, "chivas regal": {"stock": 1.0, "price": 4400.0}, "caprice sweet red": {"stock": 0.0, "price": 950.0}, "caprice white": {"stock": 1.0, "price": 950.0}, "crazy cock 750ml": {"stock": 0.0, "price": 1150.0}, "crazy cock 350ml": {"stock": 0.0, "price": 650.0}, "crazy cock 250ml": {"stock": 1.0, "price": 450.0}, "caribia gin 750ml": {"stock": 2.0, "price": 870.0}, "caribia gin 350ml": {"stock": 0.0, "price": 0.0}, "caribia gin 250ml": {"stock": 4.0, "price": 300.0}, "county 750ml": {"stock": 1.0, "price": 800.0}, "county 250ml": {"stock": 4.0, "price": 300.0}, "Camino tequlla ": {"stock": 0.0, "price": 2600.0}, "clubman 750ml ": {"stock": 1.0, "price": 900.0}, "cellar cask 5litre": {"stock": 1.0, "price": 4500.0}, "cellar cask Red 750ml": {"stock": 1.0, "price": 1050.0}, "chamdor Red": {"stock": 1.0, "price": 900.0}, "desperado": {"stock": 2.0, "price": 350.0}, "drostdy sweet red": {"stock": 4.0, "price": 1150.0}, "drostdy Sweet white": {"stock": 1.0, "price": 1150.0}, "delush Red": {"stock": 1.0, "price": 1000.0}, "eristoff": {"stock": 1.0, "price": 1400.0}, "first choice 750ml": {"stock": 3.0, "price": 800.0}, "famous grouse 1litre": {"stock": 1.0, "price": 2800.0}, "famous grouse 750ml": {"stock": 1.0, "price": 2150.0}, "faxe": {"stock": 5.0, "price": 340.0}, "gordons pink 1litre": {"stock": 2.0, "price": 2800.0}, "gordons pink 750ml": {"stock": 1.0, "price": 2300.0}, "gordons original 1litre": {"stock": 0.0, "price": 2900.0}, "gordons original 750ml": {"stock": 0.0, "price": 2400.0}, "gordons lemon 750ml": {"stock": 1.0, "price": 2300.0}, "gordons orange": {"stock": 0.0, "price": 2300.0}, "glenfiddich": {"stock": 2.0, "price": 7400.0}, "gilbeys pink 750ml": {"stock": 1.0, "price": 1600.0}, "gilbeys pink 350ml": {"stock": 1.0, "price": 710.0}, "gilbeys pink 250ml": {"stock": 1.0, "price": 500.0}, "gilbeys original 750ml": {"stock": 1.0, "price": 1600.0}, "gilgeys original 350ml": {"stock": 1.0, "price": 710.0}, "gilbeys 250ml": {"stock": 2.0, "price": 500.0}, "gibsons 750ml": {"stock": 0.0, "price": 1600.0}, "gibsons 350ml": {"stock": 0.0, "price": 0.0}, "gibsons 250ml": {"stock": 0.0, "price": 0.0}, "glen silver": {"stock": 2.0, "price": 1700.0}, "guinness": {"stock": 6.0, "price": 270.0}, "general meakins": {"stock": 3.0, "price": 270.0}, "grande france White Semi- Sweet": {"stock": 1.0, "price": 1400.0}, "hunters choice 750ml": {"stock": 4.0, "price": 1100.0}, "hunters choice 350": {"stock": 5.0, "price": 550.0}, "hunters choice 250ml": {"stock": 6.0, "price": 450.0}, "hunters gold": {"stock": 2.0, "price": 250.0}, "heinekein": {"stock": 6.0, "price": 290.0}, "henessy SP 750ML": {"stock": 1.0, "price": 6000.0}, "hendricks 1litre": {"stock": 1.0, "price": 5000.0}, "hendricks 750ml": {"stock": 3.0, "price": 4000.0}, "imperial blue 750ml": {"stock": 3.0, "price": 1050.0}, "jack daniel original": {"stock": 0.0, "price": 0.0}, "jack daniel  750ml (honey)": {"stock": 1.0, "price": 4500.0}, "jagermeister 1lite ": {"stock": 1.5, "price": 3400.0}, "jagermeister 750ml": {"stock": 1.0, "price": 2800.0}, "jameson 1lite": {"stock": 0.0, "price": 3600.0}, "jameson 750ml": {"stock": 0.0, "price": 2950.0}, "jameson 350ml": {"stock": 2.0, "price": 1450.0}, "jameson 250ml": {"stock": 0.0, "price": 0.0}, "j $ b 750ml": {"stock": 1.0, "price": 1900.0}, "jose quavo 750ml": {"stock": 0.0, "price": 2900.0}, "kc smooth 750 ml": {"stock": 2.0, "price": 900.0}, "kc smooth 350ml": {"stock": 1.0, "price": 450.0}, "kc smooth 250ml": {"stock": 3.0, "price": 320.0}, "kc pineapple 750ml": {"stock": 3.0, "price": 900.0}, "kc pineapple 350ml": {"stock": 0.0, "price": 450.0}, "kc pineapple 250ml": {"stock": 5.0, "price": 320.0}, "kc ginger $ lemon 750ml": {"stock": 3.0, "price": 900.0}, "kc ginger $ lemon 350ml": {"stock": 0.0, "price": 450.0}, "kc ginnger $ lemon 250ml": {"stock": 6.0, "price": 320.0}, "kibao voka 750ml": {"stock": 2.0, "price": 780.0}, "kibao voka 350ml": {"stock": 0.0, "price": 450.0}, "kibao vodka 250ml": {"stock": 4.0, "price": 300.0}, "kibao gin 750ml": {"stock": 2.0, "price": 750.0}, "kibao gin 350ml": {"stock": 0.0, "price": 450.0}, "kibao  gin 250ml": {"stock": 4.0, "price": 260.0}, "konyagi 750ml": {"stock": 2.0, "price": 800.0}, "konyagi 500ml": {"stock": 0.0, "price": 550.0}, "konyagi 250ml": {"stock": 5.0, "price": 300.0}, "kane 750ml": {"stock": 4.0, "price": 750.0}, "kane 250ml": {"stock": 0.0, "price": 250.0}, "k.o tonic ": {"stock": 1.0, "price": 150.0}, "k.o  bottle": {"stock": 3.0, "price": 300.0}, "leadimg warigi 750ml": {"stock": 1.0, "price": 770.0}, "mara (wine) Red": {"stock": 1.0, "price": 1300.0}, "mikado(cherry)": {"stock": 1.0, "price": 1600.0}, "mikado (pineapple)": {"stock": 1.0, "price": 1600.0}, "malibu": {"stock": 1.0, "price": 2350.0}, "ministers reserve 750ml": {"stock": 1.0, "price": 1600.0}, "monkey shoulder": {"stock": 1.0, "price": 4500.0}, "martini": {"stock": 1.0, "price": 2700.0}, "monster": {"stock": 4.0, "price": 250.0}, "manyatta (can)": {"stock": 1.0, "price": 300.0}, "manyatta ( bottle)": {"stock": 3.0, "price": 300.0}, "namaqua sweet red (wine)": {"stock": 2.0, "price": 1000.0}, "o pm vodka 750ml": {"stock": 2.0, "price": 1250.0}, "o pm vodka 350ml": {"stock": 1.0, "price": 680.0}, "o pm vodka 250ml": {"stock": 2.0, "price": 450.0}, "old monk": {"stock": 1.0, "price": 1050.0}, "oj 16%": {"stock": 6.0, "price": 400.0}, "oj 12%": {"stock": 0.0, "price": 320.0}, "Old smuggler": {"stock": 1.0, "price": 1400.0}, "paddy irish": {"stock": 0.0, "price": 1500.0}, "passport scotch": {"stock": 1.0, "price": 1350.0}, "pervack 1litre": {"stock": 1.0, "price": 1500.0}, "pervack  750ml": {"stock": 0.0, "price": 1300.0}, "penasol white wine": {"stock": 2.0, "price": 950.0}, "penasol red wine": {"stock": 1.0, "price": 950.0}, "robertson 1.5litre": {"stock": 1.0, "price": 2100.0}, "robertson 750ml": {"stock": 1.0, "price": 1200.0}, "red label 1litre ": {"stock": 0.0, "price": 2700.0}, "red label 750ml": {"stock": 0.0, "price": 2300.0}, "red label 350ml": {"stock": 0.0, "price": 1050.0}, "red label 250ml": {"stock": 0.0, "price": 700.0}, "redbull": {"stock": 0.0, "price": 230.0}, "rosso nobile (wine)": {"stock": 2.0, "price": 1500.0}, "smirnoff vodka 1litre": {"stock": 1.0, "price": 2000.0}, "smirnoff vodka 750ml": {"stock": 1.0, "price": 1600.0}, "smirnoff vodka 350ml": {"stock": 0.0, "price": 750.0}, "smirnoff vodka 250ml": {"stock": 2.0, "price": 510.0}, "smirnoff pineapple punch ": {"stock": 5.0, "price": 220.0}, "smirnoff guaranna": {"stock": 5.0, "price": 220.0}, "smirnoff black ice": {"stock": 18.0, "price": 220.0}, "sweet berry ": {"stock": 2.0, "price": 150.0}, "strumbras": {"stock": 2.0, "price": 700.0}, "savanna": {"stock": 3.0, "price": 300.0}, "southern comfort 1litre": {"stock": 1.0, "price": 2700.0}, "southern comfort 750ml": {"stock": 3.0, "price": 2400.0}, "southern comfort 350ml": {"stock": 3.0, "price": 750.0}, "sky infusion ": {"stock": 2.0, "price": 1500.0}, "star walker ": {"stock": 1.0, "price": 1500.0}, "sun chaser(wine)": {"stock": 1.0, "price": 950.0}, "singleton ": {"stock": 1.0, "price": 5700.0}, "tanqueray  1litre ( no 10)": {"stock": 1.0, "price": 6050.0}, " tanqueray 750ml ( no 10)                 ": {"stock": 1.0, "price": 5050.0}, "tanqueray  gin 1litre": {"stock": 0.0, "price": 3750.0}, "tanqueray  gin 750ml": {"stock": 1.0, "price": 2850.0}, "top secret 750ml": {"stock": 0.0, "price": 870.0}, "top secret 250ml": {"stock": 3.0, "price": 310.0}, "three barrels 750ml": {"stock": 1.0, "price": 2850.0}, "tusker lager (can)": {"stock": 4.0, "price": 240.0}, "tusker cider (can)": {"stock": 10.0, "price": 280.0}, "tusker malt (green)": {"stock": 1.0, "price": 300.0}, "versus white (wine)": {"stock": 1.0, "price": 1200.0}, "VAT 69  1 LITRE": {"stock": 0.0, "price": 2200.0}, "VAT 69  750ML": {"stock": 0.0, "price": 900.0}, "VAT 69 350ML": {"stock": 0.0, "price": 950.0}, "VAT 69 250ML": {"stock": 1.0, "price": 650.0}, "Viceroy 750ml": {"stock": 2.0, "price": 1500.0}, "viceroy 350ml": {"stock": 2.0, "price": 760.0}, "viceroy 250ml": {"stock": 2.0, "price": 520.0}, "V$A imperial ": {"stock": 1.0, "price": 900.0}, "wild turkey (bourbon)": {"stock": 1.0, "price": 4200.0}, "white cap (can)": {"stock": 6.0, "price": 270.0}, "william lawsons 1litre": {"stock": 1.0, "price": 3000.0}, "william lawsons 750ml": {"stock": 0.0, "price": 2000.0}, "william lawsons 350ml": {"stock": 2.0, "price": 1050.0}, "william lawsons 250ml": {"stock": 0.0, "price": 0.0}, "zappa black": {"stock": 1.0, "price": 1750.0}, "zappa original": {"stock": 1.0, "price": 1750.0}, "zappa blue": {"stock": 1.0, "price": 1750.0}, "# 7": {"stock": 1.0, "price": 1200.0}, "58 gin": {"stock": 1.0, "price": 1450.0}, " miniute maid ": {"stock": 8.0, "price": 160.0}, "water 500ml ": {"stock": 12.0, "price": 30.0}, "water  dasani": {"stock": 5.0, "price": 70.0}, "soda 2litre": {"stock": 6.0, "price": 200.0}, "sodalitre 1litre": {"stock": 8.0, "price": 120.0}, "dunhill double switch": {"stock": 0.0, "price": 600.0}, "dunhill single switch": {"stock": 0.0, "price": 600.0}, "pall mall (king safari)": {"stock": 0.0, "price": 300.0}, "pall mall ( menthol)": {"stock": 0.0, "price": 300.0}, "oris milano": {"stock": 0.0, "price": 400.0}, "oris menthol": {"stock": 0.0, "price": 400.0}, "rothmans red ": {"stock": 0.0, "price": 500.0}, "rothmans blue": {"stock": 0.0, "price": 500.0}, "dunhill embassy": {"stock": 0.0, "price": 600.0}, "lemonade": {"stock": 3.0, "price": 50.0}, "predator": {"stock": 3.0, "price": 70.0}}

# In-memory storage
inventory_data = {}
sales_data = []
restocks_data = []

def init_inventory():
    global inventory_data
    inventory_data = json.loads(json.dumps(initial_inventory))

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return jsonify({'success': True, 'message': 'Login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/check-auth')
def check_auth():
    return jsonify({'authenticated': session.get('logged_in', False)})

@app.route('/api/inventory')
def get_inventory():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify(inventory_data)

@app.route('/api/sale', methods=['POST'])
def record_sale():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

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

    return jsonify({'success': True})

@app.route('/api/restock', methods=['POST'])
def record_restock():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

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
        return jsonify({'success': True})
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/transactions')
def get_transactions():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

    all_transactions = sales_data + restocks_data
    return jsonify(sorted(all_transactions, key=lambda x: x['date'], reverse=True))

@app.route('/api/stats')
def get_stats():
    if not session.get('logged_in'):
        return jsonify({'error': 'Not authenticated'}), 401

    today = datetime.now().strftime('%Y-%m-%d')
    today_sales = sum(s['total'] for s in sales_data if s['date'] == today)

    return jsonify({
        'totalSales': len(sales_data),
        'totalRevenue': sum(s['total'] for s in sales_data),
        'totalItems': sum(s['quantity'] for s in sales_data),
        'todaySales': today_sales
    })

# HTML Template embedded in Python file
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerrit POS System</title>
    <script src="https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            display: none;
        }
        .container.active { display: block; }

        .login-container {
            max-width: 400px;
            margin: 100px auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            animation: slideUp 0.5s ease;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .login-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .login-header h1 { font-size: 2em; margin-bottom: 10px; }
        .login-body { padding: 40px; }

        .form-group { margin-bottom: 25px; }
        label {
            display: block;
            margin-bottom: 8px;
            color: #495057;
            font-weight: 600;
            font-size: 0.95em;
        }
        input, select {
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .btn-primary {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 100%;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(17, 153, 142, 0.4);
        }
        .btn-danger {
            background: linear-gradient(90deg, #eb3349 0%, #f45c43 100%);
            color: white;
        }
        .btn-secondary {
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .btn-secondary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(79, 172, 254, 0.4);
        }
        .btn-sm { padding: 10px 20px; font-size: 0.9em; }

        .header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .user-info { display: flex; align-items: center; gap: 20px; }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 0;
            min-height: 600px;
        }
        .left-panel { padding: 30px; background: #f8f9fa; }
        .right-panel { background: #fff; border-left: 3px solid #e9ecef; padding: 30px; }

        .section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        .section-title {
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title::before {
            content: '';
            width: 4px;
            height: 24px;
            background: #667eea;
            border-radius: 2px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            border-bottom: 3px solid #e9ecef;
            padding: 20px 30px 15px;
            background: white;
        }
        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            color: #6c757d;
            font-weight: 600;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .tab.active { background: #667eea; color: white; }
        .tab:hover:not(.active) { background: #f8f9fa; color: #495057; }

        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            max-height: 400px;
            overflow-y: auto;
            padding: 10px;
        }
        .product-card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .product-card:hover {
            border-color: #667eea;
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
        }
        .product-card.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .product-card-name {
            font-size: 0.9em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .product-card-price {
            color: #667eea;
            font-weight: 700;
            font-size: 1.1em;
        }
        .product-card-stock {
            font-size: 0.8em;
            color: #6c757d;
            margin-top: 5px;
        }
        .low-stock { color: #dc3545; font-weight: 600; }

        .cart-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #667eea;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .cart-item-info { flex: 1; }
        .cart-item-name { font-weight: 600; color: #2c3e50; margin-bottom: 4px; }
        .cart-item-details { font-size: 0.9em; color: #6c757d; }
        .cart-item-total { font-weight: 700; color: #667eea; font-size: 1.1em; margin-right: 15px; }

        .cart-summary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
        }
        .cart-summary-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 1.1em;
        }
        .cart-summary-total {
            font-size: 1.5em;
            font-weight: 700;
            border-top: 2px solid rgba(255,255,255,0.3);
            padding-top: 15px;
            margin-top: 15px;
        }

        .sales-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .sales-table th {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        .sales-table td {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        .sales-table tr:hover { background: #f8f9fa; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-value { font-size: 2.5em; font-weight: 700; color: #667eea; margin-bottom: 5px; }
        .stat-label { color: #6c757d; font-size: 0.95em; text-transform: uppercase; letter-spacing: 1px; }

        .badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }

        .search-box {
            position: relative;
            margin-bottom: 20px;
        }
        .search-box input {
            width: 100%;
            padding: 15px 20px 15px 50px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 1em;
        }
        .search-box::before {
            content: '🔍';
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.2em;
        }

        .empty-state { text-align: center; padding: 60px 20px; color: #6c757d; }
        .empty-state-icon { font-size: 4em; margin-bottom: 20px; opacity: 0.5; }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 20px 25px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1000;
        }
        .notification.show { transform: translateX(0); }
        .notification.success { background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); }
        .notification.error { background: linear-gradient(90deg, #eb3349 0%, #f45c43 100%); }

        .download-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
        }
        .download-section h3 { margin-bottom: 15px; font-size: 1.3em; }
        .download-buttons { display: flex; gap: 15px; flex-wrap: wrap; }

        @media (max-width: 968px) {
            .main-content { grid-template-columns: 1fr; }
            .right-panel { border-left: none; border-top: 3px solid #e9ecef; }
            .header { flex-direction: column; gap: 20px; text-align: center; }
        }
    </style>
</head>
<body>
    <div id="loginScreen" class="login-container">
        <div class="login-header">
            <h1>🍷 Gerrit POS</h1>
            <p>Secure Point of Sale System</p>
        </div>
        <div class="login-body">
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="username" placeholder="Enter username..." value="admin">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="password" placeholder="Enter password...">
            </div>
            <button class="btn btn-primary" onclick="login()">🔐 Login</button>
            <p style="text-align: center; margin-top: 20px; color: #6c757d; font-size: 0.9em;">Default: admin / padmin123</p>
        </div>
    </div>

    <div id="mainApp" class="container">
        <div class="header">
            <div>
                <h1>🍷 Gerrit POS System</h1>
                <p style="opacity: 0.9;">Professional Point of Sale & Inventory Management</p>
            </div>
            <div class="user-info">
                <span>👤 Admin</span>
                <button class="btn btn-danger btn-sm" onclick="logout()">Logout</button>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('pos')">💰 Point of Sale</button>
            <button class="tab" onclick="switchTab('restock')">📦 Restock</button>
            <button class="tab" onclick="switchTab('reports')">📊 Reports</button>
            <button class="tab" onclick="switchTab('inventory')">📋 Inventory</button>
        </div>

        <div id="pos" class="tab-content active">
            <div class="main-content">
                <div class="left-panel">
                    <div class="section">
                        <div class="section-title">Select Products</div>
                        <div class="search-box">
                            <input type="text" id="productSearch" placeholder="Search products..." onkeyup="filterProducts()">
                        </div>
                        <div class="form-group">
                            <label>Date</label>
                            <select id="saleDate"></select>
                        </div>
                        <div class="product-grid" id="productGrid"></div>
                    </div>
                </div>

                <div class="right-panel">
                    <div class="section">
                        <div class="section-title">Current Cart</div>
                        <div id="cartItems">
                            <div class="empty-state">
                                <div class="empty-state-icon">🛒</div>
                                <p>Your cart is empty</p>
                            </div>
                        </div>
                        <div class="cart-summary" id="cartSummary" style="display: none;">
                            <div class="cart-summary-row">
                                <span>Items:</span>
                                <span id="totalItems">0</span>
                            </div>
                            <div class="cart-summary-row cart-summary-total">
                                <span>Total:</span>
                                <span id="totalAmount">KES 0.00</span>
                            </div>
                            <button class="btn btn-success" onclick="completeSale()" style="margin-top: 20px; width: 100%;">✅ Complete Sale</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="restock" class="tab-content">
            <div class="main-content" style="grid-template-columns: 1fr 1fr;">
                <div class="left-panel">
                    <div class="section">
                        <div class="section-title">Restock Inventory</div>
                        <div class="form-group">
                            <label>Date</label>
                            <select id="restockDate"></select>
                        </div>
                        <div class="form-group">
                            <label>Product</label>
                            <select id="restockProduct" onchange="updateRestockInfo()">
                                <option value="">Select a product...</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Current Stock: <span id="currentStock" style="color: #667eea; font-weight: 700;">-</span></label>
                        </div>
                        <div class="form-group">
                            <label>Quantity to Add</label>
                            <input type="number" id="restockQuantity" min="1" placeholder="Enter quantity...">
                        </div>
                        <button class="btn btn-primary" onclick="addRestock()">📦 Add Stock</button>
                    </div>
                </div>

                <div class="right-panel">
                    <div class="section">
                        <div class="section-title">Recent Restocks</div>
                        <div id="restockHistory">
                            <div class="empty-state">
                                <div class="empty-state-icon">📦</div>
                                <p>No restocks recorded yet</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="reports" class="tab-content">
            <div class="left-panel" style="padding: 30px;">
                <div class="download-section">
                    <h3>📥 Download Reports</h3>
                    <p style="margin-bottom: 15px; opacity: 0.9;">Export your data to Excel format</p>
                    <div class="download-buttons">
                        <button class="btn btn-secondary" onclick="downloadSalesReport()">💰 Sales Report</button>
                        <button class="btn btn-secondary" onclick="downloadInventoryReport()">📦 Inventory Report</button>
                        <button class="btn btn-secondary" onclick="downloadFullReport()">📊 Full Report</button>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="statTotalSales">0</div>
                        <div class="stat-label">Total Sales</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="statTotalRevenue">KES 0</div>
                        <div class="stat-label">Total Revenue</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="statTotalItems">0</div>
                        <div class="stat-label">Items Sold</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="statTodaySales">KES 0</div>
                        <div class="stat-label">Today's Sales</div>
                    </div>
                </div>

                <div class="section">
                    <div class="section-title">Sales by Date</div>
                    <div class="form-group" style="max-width: 300px;">
                        <label>Filter by Date</label>
                        <select id="reportDateFilter" onchange="filterReports()">
                            <option value="all">All Dates</option>
                        </select>
                    </div>
                    <table class="sales-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Product</th>
                                <th>Qty</th>
                                <th>Unit Price</th>
                                <th>Total</th>
                                <th>Type</th>
                            </tr>
                        </thead>
                        <tbody id="salesTableBody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="inventory" class="tab-content">
            <div class="left-panel" style="padding: 30px;">
                <div class="section">
                    <div class="section-title">Current Inventory</div>
                    <div class="search-box">
                        <input type="text" id="inventorySearch" placeholder="Search inventory..." onkeyup="filterInventory()">
                    </div>
                    <table class="sales-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Current Stock</th>
                                <th>Unit Price (KES)</th>
                                <th>Stock Value</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="inventoryTableBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div id="notification" class="notification"></div>

    <script>
        // Application state
        let inventory = {};
        let cart = [];
        let transactions = [];
        let API_URL = window.location.origin;

        window.onload = async function() {
            await checkAuth();
        };

        async function checkAuth() {
            try {
                const response = await fetch(`${API_URL}/api/check-auth`, { credentials: 'include' });
                const data = await response.json();
                if (data.authenticated) {
                    showMainApp();
                } else {
                    showLoginScreen();
                }
            } catch (error) {
                showLoginScreen();
            }
        }

        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch(`${API_URL}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification('Login successful!', 'success');
                    showMainApp();
                } else {
                    showNotification('Invalid credentials!', 'error');
                }
            } catch (error) {
                showNotification('Connection error!', 'error');
            }
        }

        async function logout() {
            try {
                await fetch(`${API_URL}/api/logout`, { method: 'POST', credentials: 'include' });
                showLoginScreen();
                showNotification('Logged out successfully', 'success');
            } catch (error) {
                showNotification('Error logging out', 'error');
            }
        }

        function showLoginScreen() {
            document.getElementById('loginScreen').style.display = 'block';
            document.getElementById('mainApp').classList.remove('active');
        }

        async function showMainApp() {
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('mainApp').classList.add('active');
            await loadInventory();
            initDates();
            initProductGrid();
            initRestockDropdown();
            updateInventoryTable();
            await updateReports();
        }

        async function loadInventory() {
            try {
                const response = await fetch(`${API_URL}/api/inventory`, { credentials: 'include' });
                inventory = await response.json();
            } catch (error) {
                showNotification('Error loading inventory', 'error');
            }
        }

        function initDates() {
            const dateSelects = ['saleDate', 'restockDate'];
            const today = new Date();
            const dates = [];

            for (let i = -30; i <= 7; i++) {
                const date = new Date(today);
                date.setDate(date.getDate() + i);
                const dateStr = date.toISOString().split('T')[0];
                const displayStr = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
                dates.push({ value: dateStr, display: displayStr });
            }

            dateSelects.forEach(selectId => {
                const select = document.getElementById(selectId);
                select.innerHTML = '';
                dates.forEach(date => {
                    const option = document.createElement('option');
                    option.value = date.value;
                    option.textContent = date.display;
                    if (date.value === today.toISOString().split('T')[0]) option.selected = true;
                    select.appendChild(option);
                });
            });
        }

        function initProductGrid() {
            const grid = document.getElementById('productGrid');
            grid.innerHTML = '';
            Object.entries(inventory).forEach(([name, data]) => {
                const card = document.createElement('div');
                card.className = 'product-card' + (data.stock <= 0 ? ' disabled' : '');
                card.onclick = () => data.stock > 0 && selectProduct(name);
                card.innerHTML = `
                    <div class="product-card-name">${name}</div>
                    <div class="product-card-price">KES ${data.price.toFixed(2)}</div>
                    <div class="product-card-stock ${data.stock < 5 ? 'low-stock' : ''}">Stock: ${data.stock}</div>
                `;
                grid.appendChild(card);
            });
        }

        function filterProducts() {
            const search = document.getElementById('productSearch').value.toLowerCase();
            document.querySelectorAll('.product-card').forEach(card => {
                const name = card.querySelector('.product-card-name').textContent.toLowerCase();
                card.style.display = name.includes(search) ? 'block' : 'none';
            });
        }

        function selectProduct(name) {
            const data = inventory[name];
            if (data.stock <= 0) {
                showNotification('Product out of stock!', 'error');
                return;
            }

            const existing = cart.find(item => item.name === name);
            if (existing) {
                if (existing.quantity < data.stock) {
                    existing.quantity++;
                } else {
                    showNotification('Maximum stock reached!', 'error');
                    return;
                }
            } else {
                cart.push({ name: name, price: data.price, quantity: 1 });
            }

            updateCart();
            showNotification(`${name} added to cart`, 'success');
        }

        function updateCart() {
            const container = document.getElementById('cartItems');
            const summary = document.getElementById('cartSummary');

            if (cart.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">🛒</div>
                        <p>Your cart is empty</p>
                    </div>
                `;
                summary.style.display = 'none';
                return;
            }

            let totalItems = 0;
            let totalAmount = 0;

            container.innerHTML = cart.map((item, index) => {
                totalItems += item.quantity;
                totalAmount += item.price * item.quantity;

                return `
                    <div class="cart-item">
                        <div class="cart-item-info">
                            <div class="cart-item-name">${item.name}</div>
                            <div class="cart-item-details">KES ${item.price.toFixed(2)} × ${item.quantity}</div>
                        </div>
                        <div class="cart-item-total">KES ${(item.price * item.quantity).toFixed(2)}</div>
                        <button class="btn btn-danger btn-sm" onclick="removeFromCart(${index})">✕</button>
                    </div>
                `;
            }).join('');

            document.getElementById('totalItems').textContent = totalItems;
            document.getElementById('totalAmount').textContent = `KES ${totalAmount.toFixed(2)}`;
            summary.style.display = 'block';
        }

        function removeFromCart(index) {
            cart.splice(index, 1);
            updateCart();
        }

        async function completeSale() {
            if (cart.length === 0) return;

            const date = document.getElementById('saleDate').value;

            try {
                const response = await fetch(`${API_URL}/api/sale`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ items: cart, date: date })
                });

                if (response.ok) {
                    let totalAmount = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
                    showNotification(`Sale completed! Total: KES ${totalAmount.toFixed(2)}`, 'success');
                    cart = [];
                    updateCart();
                    await loadInventory();
                    initProductGrid();
                    initRestockDropdown();
                    updateInventoryTable();
                    await updateReports();
                } else {
                    const data = await response.json();
                    showNotification(data.error || 'Error completing sale', 'error');
                }
            } catch (error) {
                showNotification('Connection error', 'error');
            }
        }

        function initRestockDropdown() {
            const select = document.getElementById('restockProduct');
            select.innerHTML = '<option value="">Select a product...</option>';
            Object.entries(inventory).forEach(([name, data]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${name} (Stock: ${data.stock})`;
                select.appendChild(option);
            });
        }

        function updateRestockInfo() {
            const product = document.getElementById('restockProduct').value;
            document.getElementById('currentStock').textContent = product && inventory[product] ? inventory[product].stock : '-';
        }

        async function addRestock() {
            const product = document.getElementById('restockProduct').value;
            const quantity = parseInt(document.getElementById('restockQuantity').value);
            const date = document.getElementById('restockDate').value;

            if (!product || !quantity || quantity <= 0) {
                showNotification('Please fill all fields correctly', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_URL}/api/restock`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ product, quantity, date })
                });

                if (response.ok) {
                    showNotification(`Restocked ${quantity} units of ${product}`, 'success');
                    document.getElementById('restockProduct').value = '';
                    document.getElementById('restockQuantity').value = '';
                    updateRestockInfo();
                    await loadInventory();
                    initProductGrid();
                    initRestockDropdown();
                    updateRestockHistory();
                    updateInventoryTable();
                    await updateReports();
                } else {
                    showNotification('Error recording restock', 'error');
                }
            } catch (error) {
                showNotification('Connection error', 'error');
            }
        }

        async function updateRestockHistory() {
            try {
                const response = await fetch(`${API_URL}/api/transactions`, { credentials: 'include' });
                const allTransactions = await response.json();
                const restocks = allTransactions.filter(t => t.type === 'Restock').slice(-10).reverse();

                const container = document.getElementById('restockHistory');
                if (restocks.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📦</div>
                            <p>No restocks recorded yet</p>
                        </div>
                    `;
                    return;
                }

                container.innerHTML = restocks.map(r => `
                    <div class="cart-item" style="border-left-color: #11998e;">
                        <div class="cart-item-info">
                            <div class="cart-item-name">${r.product}</div>
                            <div class="cart-item-details">${new Date(r.date).toLocaleDateString('en-GB')} • ${r.quantity} units</div>
                        </div>
                        <div class="cart-item-total" style="color: #11998e;">+${r.quantity}</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading restock history');
            }
        }

        function updateInventoryTable() {
            const tbody = document.getElementById('inventoryTableBody');
            const search = document.getElementById('inventorySearch').value.toLowerCase();

            let html = '';
            Object.entries(inventory).forEach(([name, data]) => {
                if (name.toLowerCase().includes(search)) {
                    const stockValue = data.stock * data.price;
                    let status = '<span class="badge badge-success">In Stock</span>';
                    if (data.stock === 0) status = '<span class="badge badge-danger">Out of Stock</span>';
                    else if (data.stock < 5) status = '<span class="badge badge-warning">Low Stock</span>';

                    html += `
                        <tr>
                            <td><strong>${name}</strong></td>
                            <td>${data.stock}</td>
                            <td>KES ${data.price.toFixed(2)}</td>
                            <td>KES ${stockValue.toFixed(2)}</td>
                            <td>${status}</td>
                        </tr>
                    `;
                }
            });

            tbody.innerHTML = html || '<tr><td colspan="5" style="text-align: center; padding: 40px;">No products found</td></tr>';
        }

        function filterInventory() {
            updateInventoryTable();
        }

        async function updateReports() {
            try {
                const statsResponse = await fetch(`${API_URL}/api/stats`, { credentials: 'include' });
                const stats = await statsResponse.json();

                document.getElementById('statTotalSales').textContent = stats.totalSales;
                document.getElementById('statTotalRevenue').textContent = `KES ${stats.totalRevenue.toFixed(0)}`;
                document.getElementById('statTotalItems').textContent = stats.totalItems;
                document.getElementById('statTodaySales').textContent = `KES ${stats.todaySales.toFixed(0)}`;

                const transResponse = await fetch(`${API_URL}/api/transactions`, { credentials: 'include' });
                transactions = await transResponse.json();

                const dateFilter = document.getElementById('reportDateFilter');
                const uniqueDates = [...new Set(transactions.map(t => t.date))].sort().reverse();

                let dateOptions = '<option value="all">All Dates</option>';
                uniqueDates.forEach(date => {
                    dateOptions += `<option value="${date}">${new Date(date).toLocaleDateString('en-GB')}</option>`;
                });
                dateFilter.innerHTML = dateOptions;

                filterReports();
            } catch (error) {
                console.error('Error loading reports');
            }
        }

        function filterReports() {
            const filterDate = document.getElementById('reportDateFilter').value;
            const tbody = document.getElementById('salesTableBody');

            let filtered = transactions;
            if (filterDate !== 'all') filtered = transactions.filter(t => t.date === filterDate);

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No transactions found</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map(t => {
                const typeClass = t.type === 'Sale' ? 'badge-success' : 'badge-warning';
                return `
                    <tr>
                        <td>${new Date(t.date).toLocaleDateString('en-GB')}</td>
                        <td><strong>${t.product}</strong></td>
                        <td>${t.quantity}</td>
                        <td>KES ${t.unitPrice.toFixed(2)}</td>
                        <td>KES ${t.total.toFixed(2)}</td>
                        <td><span class="badge ${typeClass}">${t.type}</span></td>
                    </tr>
                `;
            }).join('');
        }

        function downloadSalesReport() {
            const sales = transactions.filter(t => t.type === 'Sale');
            if (sales.length === 0) {
                showNotification('No sales data to download', 'error');
                return;
            }

            const data = sales.map(s => ({
                'Date': new Date(s.date).toLocaleDateString('en-GB'),
                'Product': s.product,
                'Quantity': s.quantity,
                'Unit Price (KES)': s.unitPrice,
                'Total (KES)': s.total
            }));

            const worksheet = XLSX.utils.json_to_sheet(data);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Sales Report');
            worksheet['!cols'] = [{ wch: 12 }, { wch: 30 }, { wch: 10 }, { wch: 15 }, { wch: 15 }];

            XLSX.writeFile(workbook, `Sales_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
            showNotification('Sales report downloaded!', 'success');
        }

        function downloadInventoryReport() {
            const data = Object.entries(inventory).map(([name, data]) => ({
                'Product': name,
                'Current Stock': data.stock,
                'Unit Price (KES)': data.price,
                'Stock Value (KES)': data.stock * data.price,
                'Status': data.stock === 0 ? 'Out of Stock' : data.stock < 5 ? 'Low Stock' : 'In Stock'
            }));

            const worksheet = XLSX.utils.json_to_sheet(data);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Inventory Report');
            worksheet['!cols'] = [{ wch: 30 }, { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 }];

            XLSX.writeFile(workbook, `Inventory_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
            showNotification('Inventory report downloaded!', 'success');
        }

        function downloadFullReport() {
            if (transactions.length === 0) {
                showNotification('No data to download', 'error');
                return;
            }

            const data = transactions.map(t => ({
                'Date': new Date(t.date).toLocaleDateString('en-GB'),
                'Product': t.product,
                'Type': t.type,
                'Quantity': t.quantity,
                'Unit Price (KES)': t.unitPrice,
                'Total (KES)': t.total
            }));

            const worksheet = XLSX.utils.json_to_sheet(data);
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, 'Full Report');
            worksheet['!cols'] = [{ wch: 12 }, { wch: 30 }, { wch: 10 }, { wch: 10 }, { wch: 15 }, { wch: 15 }];

            XLSX.writeFile(workbook, `Full_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
            showNotification('Full report downloaded!', 'success');
        }

        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');

            if (tabName === 'inventory') updateInventoryTable();
            else if (tabName === 'reports') updateReports();
            else if (tabName === 'restock') updateRestockHistory();
        }

        function showNotification(message, type) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type} show`;
            setTimeout(() => notification.classList.remove('show'), 3000);
        }

        document.addEventListener('DOMContentLoaded', function() {
            const passwordInput = document.getElementById('password');
            if (passwordInput) {
                passwordInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') login();
                });
            }
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    init_inventory()
    app.run(debug=True)
