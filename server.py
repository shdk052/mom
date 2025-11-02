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

app = Flask(__name__, 
            # מגדיר את הנתיב המוחלט לתיקיית templates
            template_folder=os.path.join(base_dir, 'templates'),
            # מגדיר את הנתיב המוחלט לתיקיית static
            static_folder=os.path.join(base_dir, 'templates', 'static'))


def write_to_sheet(data_list):
    """מתחברת ל-Google Sheet ומוסיפה שורה חדשה באמצעות משתנה סביבה."""
    
    # 1. קריאת אישורי המפתח ממשתנה הסביבה (GOOGLE_CREDENTIALS)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not creds_json:
        print("שגיאה קריטית: משתנה הסביבה GOOGLE_CREDENTIALS אינו מוגדר.", file=sys.stderr)
        return False

    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds_info = json.loads(creds_json)
        
        # אימות באמצעות המידע שבזיכרון
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)

        # פתיחת הגיליון
        sheet = client.open(SPREADSHEET_NAME).sheet1 
        
        sheet.append_row(data_list)
        return True
    
    except Exception as e:
        print(f"שגיאה בכתיבה ל-Google Sheets: {e}", file=sys.stderr)
        return False

# ----------------- ניתובים (Routes) של Flask -----------------

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # קבלת הנתונים
        שם_מלא = request.form.get('full_name')
        אימייל = request.form.get('email')
        טלפון = request.form.get('phone')
        תאריך_רישום = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row_data = [שם_מלא, אימייל, טלפון, תאריך_רישום]
        
        if write_to_sheet(row_data):
            return redirect(url_for('thank_you'))
        else:
            return redirect(url_for('error_page'))

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/error')
def error_page():
    return render_template('error.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
