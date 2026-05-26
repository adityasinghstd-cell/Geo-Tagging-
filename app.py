import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app) 

# ==========================================
# 1. PATHS & INITIALIZATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# File Paths
LISTINGS_FILE = os.path.join(DATA_DIR, 'user_listings.csv')
INQUIRIES_FILE = os.path.join(DATA_DIR, 'inquiries.csv')

# Ensure Data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# Standardized headers WITHOUT AI_Value_Cr
CSV_HEADERS = ['Mobile', 'Acres', 'Expected_Price_Cr', 'Lat', 'Lng', 'Status']

# Initialize CSV Files with updated headers if they don't exist
if not os.path.exists(LISTINGS_FILE):
    pd.DataFrame(columns=CSV_HEADERS).to_csv(LISTINGS_FILE, index=False)

if not os.path.exists(INQUIRIES_FILE):
    inquiry_headers = ['Buyer_Mobile', 'Farmer_Mobile', 'Acres', 'Message', 'Status']
    pd.DataFrame(columns=inquiry_headers).to_csv(INQUIRIES_FILE, index=False)

# ==========================================
# 2. LAND LISTING ROUTES
# ==========================================

@app.route('/add-listing', methods=['POST'])
def add_listing():
    try:
        data = request.json
        write_header = not os.path.exists(LISTINGS_FILE) or os.stat(LISTINGS_FILE).st_size == 0
        
        # New row without AI_Value_Cr
        new_row = pd.DataFrame([{
            'Mobile': str(data.get('Mobile')).strip(),
            'Acres': data.get('Acres'),
            'Expected_Price_Cr': data.get('Expected_Price_Cr'),
            'Lat': data.get('Lat'),
            'Lng': data.get('Lng'),
            'Status': 'Active'
        }])
        
        new_row.to_csv(LISTINGS_FILE, mode='a', header=write_header, index=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-listings', methods=['GET'])
def get_listings():
    try:
        mobile = request.args.get('mobile')
        if not mobile:
            return jsonify({'status': 'error', 'message': 'Mobile number required'}), 400

        if not os.path.exists(LISTINGS_FILE) or os.stat(LISTINGS_FILE).st_size == 0:
            return jsonify({'status': 'success', 'data': []})

        df = pd.read_csv(LISTINGS_FILE, dtype={'Mobile': str})
        df['Mobile'] = df['Mobile'].str.strip()
        user_listings = df[df['Mobile'] == str(mobile).strip()]
        
        return jsonify({'status': 'success', 'data': user_listings.to_dict('records')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-all-listings', methods=['GET'])
def get_all_listings():
    try:
        if not os.path.exists(LISTINGS_FILE) or os.stat(LISTINGS_FILE).st_size == 0:
            return jsonify({'status': 'success', 'data': []})

        df = pd.read_csv(LISTINGS_FILE, dtype={'Mobile': str})
        active_listings = df[df['Status'] == 'Active']
        return jsonify({'status': 'success', 'data': active_listings.to_dict('records')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==========================================
# 3. INQUIRY SYSTEM ROUTES
# ==========================================

@app.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    try:
        data = request.json
        write_header = not os.path.exists(INQUIRIES_FILE) or os.stat(INQUIRIES_FILE).st_size == 0
        
        new_inquiry = pd.DataFrame([{
            'Buyer_Mobile': str(data.get('buyer_mobile')).strip(),
            'Farmer_Mobile': str(data.get('farmer_mobile')).strip(),
            'Acres': data.get('acres'),
            'Message': data.get('message'),
            'Status': 'New'
        }])
        
        new_inquiry.to_csv(INQUIRIES_FILE, mode='a', header=write_header, index=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-farmer-inquiries', methods=['GET'])
def get_farmer_inquiries():
    try:
        mobile = request.args.get('mobile')
        if not mobile:
            return jsonify({'status': 'error', 'message': 'Mobile number required'}), 400

        if not os.path.exists(INQUIRIES_FILE) or os.stat(INQUIRIES_FILE).st_size == 0:
            return jsonify({'status': 'success', 'data': []})

        df = pd.read_csv(INQUIRIES_FILE, dtype={'Farmer_Mobile': str, 'Buyer_Mobile': str})
        df['Farmer_Mobile'] = df['Farmer_Mobile'].str.strip()
        farmer_leads = df[df['Farmer_Mobile'] == str(mobile).strip()]
        
        farmer_leads = farmer_leads.iloc[::-1] # Newest first
        return jsonify({'status': 'success', 'data': farmer_leads.to_dict('records')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==========================================
# 4. AUTHENTICATION & STATUS MANAGEMENT
# ==========================================

@app.route('/send-otp', methods=['POST'])
def send_otp():
    return jsonify({'status': 'success'})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        role = data.get('role', 'farmer')
        if data.get('otp') == "1234":
            redirect_page = 'dashboard.html' if role == 'farmer' else 'buyer-dashboard.html'
            return jsonify({'status': 'success', 'role': role, 'redirect_url': redirect_page})
        return jsonify({'status': 'error', 'message': 'Invalid OTP'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update-status', methods=['POST'])
def update_status():
    try:
        data = request.json
        df = pd.read_csv(LISTINGS_FILE, dtype={'Mobile': str})
        mask = (df['Mobile'] == str(data['mobile'])) & \
               (df['Lat'].astype(str) == str(data['lat'])) & \
               (df['Lng'].astype(str) == str(data['lng']))
        
        df.loc[mask, 'Status'] = data['status']
        df.to_csv(LISTINGS_FILE, index=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete-listing', methods=['POST'])
def delete_listing():
    try:
        data = request.json
        df = pd.read_csv(LISTINGS_FILE, dtype={'Mobile': str})
        mask = (df['Mobile'] == str(data['mobile'])) & \
               (df['Lat'].astype(str) == str(data['lat'])) & \
               (df['Lng'].astype(str) == str(data['lng']))
        
        df = df[~mask]
        df.to_csv(LISTINGS_FILE, index=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
if __name__ == '__main__':
    app.run(debug=True, port=5000)