from flask import Flask, request, render_template, redirect, url_for
import os
from datetime import datetime
from markupsafe import escape 
import smtplib
from email.message import EmailMessage
import sys

# ----------------------------------------
# הגדרת הנתיבים המוחלטים
# ----------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))


def send_email(subject, body, receiver_email):
    """שולחת מייל באמצעות SMTP של Gmail, משתמשת בפורט 587 (TLS)."""
    
    # קריאת משתני סביבה
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("שגיאה קריטית: משתני הסביבה EMAIL_USER או EMAIL_PASSWORD אינם מוגדרים.", file=sys.stderr)
        return False
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = receiver_email
    msg.set_content(body, subtype='html') 
    
    try:
        # *** התיקון הקריטי: מעבר ל-SMTP (פורט 587) ושימוש ב-starttls() ***
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()         # שלב חובה: זיהוי לשרת
        server.starttls()     # שלב חובה: הפעלת הצפנת TLS
        
        # התחברות (עם סיסמת האפליקציה)
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # שליחה וסגירה
        server.send_message(msg)
        server.quit()
        
        return True
    
    except Exception as e:
        print(f"שגיאה בשליחת מייל: {e}", file=sys.stderr)
        return False

# ----------------- ניתובים (Routes) של Flask (ללא שינוי) -----------------

@app.route('/')
def index():
    status = request.args.get('status', 'form')
    return render_template('form.html', status=status)

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        
        שם_מלא = str(escape(request.form.get('full_name')))
        תשובה_לשאלה_1 = str(escape(request.form.get('q1')))
        תשובה_לשאלה_2 = str(escape(request.form.get('q2')))
        
        תאריך_רישום = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        email_body_html = f"""
        <html>
        <body dir="rtl">
            <h2>טופס חדש נשלח!</h2>
            <p><b>תאריך ושעה:</b> {תאריך_רישום}</p>
            <hr>
            <p><b>שם מלא:</b> {שם_מלא}</p>
            <h3>שאלה 1: תאר את הניסיון המקצועי שלך:</h3>
            <p style="white-space: pre-wrap;">{תשובה_לשאלה_1}</p>
            <h3>שאלה 2: מהן הציפיות שלך משיתוף הפעולה העתידי:</h3>
            <p style="white-space: pre-wrap;">{תשובה_לשאלה_2}</p>
        </body>
        </html>
        """
        
        receiver_email = os.environ.get('RECEIVER_EMAIL')
        subject = f"טופס חדש התקבל מ: {שם_מלא}"
        
        if send_email(subject, email_body_html, receiver_email):
            return redirect(url_for('index', status='success'))
        else:
            return redirect(url_for('index', status='error'))

# ----------------- הרצה -----------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
