from flask import Flask, request, render_template, redirect, url_for
import os
from datetime import datetime
from markupsafe import escape
import smtplib
from email.message import EmailMessage
import sys

# הגדרות נתיבים...
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))


def send_email(subject, body, receiver_email):
    """שולחת מייל באמצעות SMTP של Gmail, עם Timeout מוגדל."""
    
    # קריאת משתני סביבה
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    SMTP_SERVER = os.environ.get('SMTP_SERVER') # נקרא כעת מ-Railway: smtp.gmail.com
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    
    if not all([EMAIL_USER, EMAIL_PASSWORD, SMTP_SERVER]):
        print("שגיאה קריטית: משתני סביבה של Gmail חסרים או לא הוגדרו.", file=sys.stderr)
        return False
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = receiver_email
    msg.set_content(body, subtype='html') 
    
    try:
        # *** התיקון הקריטי: הוספת timeout=60 לשלב החיבור ***
        # פורט 587, ונותנים 60 שניות לחיבור לפני Worker Timeout
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=60)
        server.ehlo()
        server.starttls()
        
        # התחברות עם סיסמת האפליקציה של גוגל
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        
        return True
    
    except Exception as e:
        print(f"שגיאה בשליחת מייל: {e}", file=sys.stderr)
        return False

# ----------------- ניתובים (Routes) של Flask -----------------

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
