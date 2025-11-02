from flask import Flask, request, render_template, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

# --- הגדרות הגישה שלך - חובה לעדכן! ---
# ודא שקובץ ה-JSON נמצא באותה תיקייה או עדכן את הנתיב המלא
CREDENTIALS_FILE = 'service_account_key.json' 
SPREADSHEET_NAME = "שם הגיליון שלי ברישום" # שנה לשם המדויק של ה-Google Sheet שלך
# ------------------------------------

app = Flask(__name__)

def write_to_sheet(data_list):
    """מתחברת ל-Google Sheet ומוסיפה שורה חדשה עם הנתונים."""
    try:
        # הגדרת הטווחים והיקף האימות
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # אימות עם קובץ המפתח JSON
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)

        # פתיחת הגיליון (לפי השם) והגיליון הפנימי (Worksheet) הראשון
        sheet = client.open(SPREADSHEET_NAME).sheet1 
        
        # הוספת שורה חדשה בתחתית הגיליון
        sheet.append_row(data_list)
        return True
    
    except Exception as e:
        print(f"שגיאה בכתיבה ל-Google Sheets: {e}")
        return False

# ----------------- ניתובים (Routes) של Flask -----------------

@app.route('/')
def index():
    # מציג את קובץ הטופס המעוצב
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # קבלת הנתונים משדות הטופס. שים לב לשמות השדות (name) ב-HTML!
        שם_מלא = request.form.get('full_name')
        אימייל = request.form.get('email')
        טלפון = request.form.get('phone')
        
        # הוספת תאריך וזמן הרישום
        תאריך_רישום = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # איסוף הנתונים לרשימה: סדר השדות חייב להתאים לסדר העמודות בגיליון שלך!
        row_data = [שם_מלא, אימייל, טלפון, תאריך_רישום]
        
        # שליחת הנתונים ל-Google Sheet
        if write_to_sheet(row_data):
            return redirect(url_for('thank_you'))
        else:
            # אם יש שגיאה (למשל, בעיית אימות או שם גיליון שגוי)
            return render_template('error.html')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    # ודא שאתה משתמש ב-debug=True רק במהלך הפיתוח
    app.run(debug=True)