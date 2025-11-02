from flask import Flask, request, render_template, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
import json
import sys

# הגדרות הליבה של האפליקציה
app = Flask(__name__)

# --- הגדרות הגיליון - חובה לעדכן את השם! ---
SPREADSHEET_NAME = "שם הגיליון המדויק שלך" # שנה לשם המדויק של ה-Google Sheet שלך
# ----------------------------------------

def write_to_sheet(data_list):
    """מתחברת ל-Google Sheet ומוסיפה שורה חדשה עם הנתונים, באמצעות משתנה סביבה."""
    
    # 1. קריאת אישורי המפתח ממשתנה הסביבה
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not creds_json:
        # הודעת שגיאה קריטית אם המשתנה לא הוגדר ב-Railway
        print("שגיאה קריטית: משתנה הסביבה GOOGLE_CREDENTIALS אינו מוגדר.", file=sys.stderr)
        return False

    try:
        # הגדרת הטווחים והיקף האימות
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # המרת תוכן הטקסט מ-JSON למבנה נתונים של פייתון
        creds_info = json.loads(creds_json)
        
        # אימות באמצעות המידע שבזיכרון (במקום קריאה מקובץ)
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
        # קבלת הנתונים משדות הטופס (השמות חייבים להתאים ל-form.html)
        שם_מלא = request.form.get('full_name')
        אימייל = request.form.get('email')
        טלפון = request.form.get('phone')
        
        # הוספת תאריך וזמן הרישום
        תאריך_רישום = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # איסוף הנתונים לרשימה: סדר השדות חייב להתאים לסדר העמודות בגיליון!
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

if __name__ == '__main__':
    # משיג את הפורט ממשתני הסביבה (חשוב עבור Railway)
    port = int(os.environ.get('PORT', 5000))
    # מאזין לכל הממשקים (חשוב עבור סביבת ענן)
    app.run(host='0.0.0.0', port=port, debug=True)
