from flask import Flask, request, render_template, redirect, url_for
import os
from datetime import datetime
from markupsafe import escape
import sys
import json
import base64

# ייבוא ספריות Google API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
import http.client as httplib

# ----------------------------------------
# הגדרות כלליות
# ----------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# היקפי הרשאה
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def create_message(sender, to, subject, message_text_html):
    """בניית הודעת מייל בפורמט MIME מוכן לשליחה באמצעות API."""
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    message.attach(MIMEText(message_text_html, 'html'))
    
    # הפיכת המייל לפורמט Base64 URL-safe
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_gmail_service_account_email(subject, email_body_html, receiver_email):
    """שולחת מייל באמצעות Gmail API ו-Service Account."""

    # 1. קריאת אישורי חשבון שירות
    CREDENTIALS_JSON = os.environ.get('SERVICE_ACCOUNT_CREDENTIALS')
    user_email = os.environ.get('RECEIVER_EMAIL') 
    
    # כתובת חשבון השירות ששלחת (משמשת לאימות)
    SERVICE_ACCOUNT_EMAIL = 'railwaymailer-601@charged-sled-477314-d8.iam.gserviceaccount.com'

    if not CREDENTIALS_JSON or not user_email:
        print("שגיאה: חסרים משתני סביבה (SERVICE_ACCOUNT_CREDENTIALS או RECEIVER_EMAIL).", file=sys.stderr)
        return False
    
    # 2. יצירת אישורי Service Account
    try:
        # הטעינה מתבצעת ישירות מה-JSON שבמשתנה הסביבה
        info = json.loads(CREDENTIALS_JSON)
        
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=SCOPES
            # חשבון השירות מנסה לשלוח "בשם" המשתמש האישי (Impersonate)
            # **זה דורש הרשאת Google Workspace (Domain-wide Delegation)!**
            # אם אין לך חשבון Workspace, זה ייכשל!
            ,subject=user_email 
        )
        
    except Exception as e:
        print(f"שגיאה בהמרת אישורי חשבון שירות: {e}", file=sys.stderr)
        return False

    # 3. שליחת המייל
    if not creds:
        print("שגיאה סופית: אימות Service Account נכשל.", file=sys.stderr)
        return False

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # יצירת ההודעה
        message = create_message(user_email, receiver_email, subject, email_body_html)
        
        # שליחת ההודעה - userId הוא האימייל שחשבון השירות מחקה (momemail053@gmail.com)
        send_message = service.users().messages().send(userId=user_email, body=message).execute() 
        print(f"המייל נשלח בהצלחה, ID: {send_message.get('id')}", file=sys.stdout)
        return True
        
    except Exception as e:
        print(f"שגיאה קריטית בשליחת המייל: {e}", file=sys.stderr)
        # אם יש שגיאה, חפש בלוגים הודעה כמו "Client is unauthorized to retrieve access token"
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
        
        if send_gmail_service_account_email(subject, email_body_html, receiver_email):
            return redirect(url_for('index', status='success'))
        else:
            return redirect(url_for('index', status='error'))


# ----------------- הרצה -----------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
