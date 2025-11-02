from flask import Flask, request, render_template, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
import json
import sys

# --- הגדרות הגיליון - סופיות ---
# המזהה הייחודי של הגיליון (הדרך הבטוחה להתחברות)
SPREADSHEET_ID = "1WdT3uh2Ll4HwdzYqQzuUKY83bnAmqJy9alLyPOfjXw8"
# שם הגיליון לצורך תיעוד (השם שבו השתמשת)
SPREADSHEET_NAME = "mom" 
# ----------------------------------------

# ----------------------------------------
# הגדרת הנתיבים המוחלטים (לצורך פריסה ב-Railway)
# ----------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))


def write_to_sheet(data_list):
    """מתחברת ל-Google Sheet באמצעות המזהה (ID) ומוסיפה שורה."""
    
    # קריאת אישורי המפתח ממשתנה הסביבה
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not creds_json:
        print("שגיאה קריטית: משתנה הסביבה GOOGLE_CREDENTIALS אינו מוגדר.", file=sys.stderr)
        return False

    try:
        # הגדרת היקף האימות
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # המרת תוכן JSON לזיכרון והתחברות
        creds_info = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)

        # *** שימוש ב-ID להתחברות ***
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1 
        
        # הוספת שורה חדשה
        sheet.append_row(data_list)
        return True
    
    except Exception as e:
        # זו ההודעה שהופיעה לך (כעת היא מציגה את השגיאה המדויקת אם יש):
        print(f"שגיאה בכתיבה ל-Google Sheets: {e}", file=sys.stderr)
        return False

# ----------------- ניתובים (Routes) של Flask -----------------

@app.route('/')
def index():
    # מקבל את פרמטר הסטטוס (success/error/form)
    status = request.args.get('status', 'form')
    return render_template('form.html', status=status)

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
            # הצלחה
            return redirect(url_for('index', status='success'))
        else:
            # כישלון
            return redirect(url_for('index', status='error'))

# ----------------- הרצה -----------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
