from flask import Flask, render_template, request, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("SmartExpenseTracker").sheet1  
except Exception as e:
    print("Google Sheets setup error (using local fallback mode):", e)
    sheet = None

MONTHLY_BUDGET = 500.0

@app.route('/')
def index():
    try:
        records = sheet.get_all_records() if sheet else []
    except Exception as e:
        print("Error fetching records:", e)
        records = []

    current_month = datetime.now().strftime('%Y-%m')
    
    monthly_spent = 0
    category_summary = {}

    for row in records:
        try:
            amount = float(row.get('Amount', 0))
        except ValueError:
            amount = 0
        category = row.get('Category', 'Other')
        
        monthly_spent += amount
        category_summary[category] = category_summary.get(category, 0) + amount

    alert = None
    if monthly_spent >= MONTHLY_BUDGET:
        alert = "🚨 Warning: You have exceeded your monthly budget!"
    elif monthly_spent >= MONTHLY_BUDGET * 0.8:
        alert = "⚠️ Alert: You have reached 80% of your monthly budget!"

    return render_template(
        'index.html', 
        expenses=records[::-1], 
        monthly_spent=monthly_spent, 
        monthly_budget=MONTHLY_BUDGET,
        category_summary=category_summary,
        alert=alert
    )

@app.route('/add', methods=['POST'])
def add_expense():
    category = request.form.get('category')
    amount = request.form.get('amount')
    date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
    
    if category and amount:
        if sheet:
            try:
                sheet.append_row([date, category, float(amount)])
                print("Expense added to Google Sheet successfully!")
            except Exception as e:
                print("Failed to append row to Google Sheet:", e)
        else:
            print("Error: Sheet object is None. Check credentials or sheet name.")
            
    return redirect(url_for('index'))

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True)
    return {"status": "success"}

if __name__ == '__main__':
    app.run(debug=True)