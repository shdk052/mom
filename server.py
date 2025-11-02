from flask import Flask, request, render_template, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
import json
import sys

# --- הגדרות הגיליון - חובה לעדכן את השם! ---
SPREADSHEET_NAME = "שם הגיליון המדויק שלך" # שנה לשם ה-Google Sheet שלך
# ----------------------------------------

# ----------------------------------------
# הגדרת הנתיבים המוחלטים (התיקון הקריטי)
# ----------------------------------------
# משיג את הנתיב המוחלט של התיקייה הנוכחית
base_dir = os.path.dirname(os.path.abspath(__file__))

# *** שימו לב לשינוי הקריטי ב-static_folder ***
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static')) # הפניה לתיקייה 'static' בתיקיית הבסיס


# --- פונקציית write_to_sheet נשארת זהה ---
def write_to_sheet(data_list):
    # ... (הקוד נשאר ללא שינוי, קריאה מ-GOOGLE_CREDENTIALS) ...
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not creds_json:
        print("שגיאה קריטית: משתנה הסביבה GOOGLE_CREDENTIALS אינו מוגדר.", file=sys.stderr)
        return False

    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds_info = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)

        sheet = client.open(SPREADSHEET_NAME).sheet1 
        sheet.append_row(data_list)
        return True
    
    except Exception as e:
        print(f"שגיאה בכתיבה ל-Google Sheets: {e}", file=sys.stderr)
        return False
# --- סוף פונקציית write_to_sheet ---


# --- ניתובים (Routes) נשארים זהים ---
@app.route('/')
def index():
    status = request.args.get('status', 'form')
    return render_template('form.html', status=status)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        שם_מלא = request.form.get('full_name')
        אימייל = request.form.get('email')
        טלפון = request.form.get('phone')
        תאריך_רישום = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row_data = [שם_מלא, אימייל, טלפון, תאריך_רישום]
        
        if write_to_sheet(row_data):
            return redirect(url_for('index', status='success'))
        else:
            return redirect(url_for('index', status='error'))

# --- הרצה נשארת זהה ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
