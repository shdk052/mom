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
# הגדרת הנתיבים המוחלטים (פותר את שגיאת TemplateNotFound ב-Railway)
# ----------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            # מגדיר את הנתיב המוחלט לתיקיית templates
            template_folder=os.path.join(base_dir, 'templates'),
            # מגדיר את הנתיב המוחלט לתיקיית static
            static_folder=os.path.join(base_dir, 'templates', 'static'))


def write_to_sheet(data_list):
    """מתחברת ל-Google Sheet ומוסיפה שורה חדשה עם הנתונים, באמצעות משתנה סביבה."""
    
    # 1. קריאת אישורי המפתח ממשתנה הסביבה (GOOGLE_CREDENTIALS)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not creds_json:
        print("שגיאה קריטית: משתנה הסביבה GOOGLE_CREDENTIALS אינו מוגדר.", file=sys.stderr)
        return False

    try:
        # הגדרת היקף האימות
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # המרת תוכן הטקסט מ-JSON למבנה נתונים
        creds_info = json.loads(creds_json)
        
        # אימות באמצעות המידע שבזיכרון
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)

        # פתיחת הגיליון
        sheet = client.open(SPREADSHEET_NAME).sheet1 
        
        # הוספת שורה חדשה בתחתית הגיליון
        sheet.append_row(data_list)
        return True
    
    except Exception as e:
        print(f"שגיאה בכתיבה ל-Google Sheets: {e}", file=sys.stderr)
        return False

# ----------------- ניתובים (Routes) של Flask -----------------

@app.route('/')
def index():
    # מציג את הטופס
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # קבלת הנתונים משדות הטופס
        שם_מלא = request.form.get('full_name')
        אימייל = request.form.get('email')
        טלפון = request.form.get('phone')
        
        # הוספת תאריך וזמן הרישום
        תאריך_רישום = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # איסוף הנתונים לרשימה (סדר העמודות בגיליון!)
        row_data = [שם_מלא, אימייל, טלפון, תאריך_רישום]
        
        # שליחת הנתונים ל-Google Sheet
        if write_to_sheet(row_data):
            return redirect(url_for('thank_you'))
        else:
            # הפניה לדף שגיאה
            return render_template('error.html')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/error')
def error_page():
    return render_template('error.html')

if __name__ == '__main__':
    # מיועד להרצה מקומית בלבד
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
