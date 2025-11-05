from flask import Flask, request, render_template, redirect, url_for
import os
from datetime import datetime
from markupsafe import escape
import sys
import json
import base64
import http.client as httplib

# ייבוא ספריות Google API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.exceptions import DefaultCredentialsError

# ----------------------------------------
# הגדרת הנתיבים המוחלטים
# ----------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# היקפי הרשאה (Scopes) הנדרשים ל-Gmail API
# אנו צריכים הרשאה לשליחת מייל בלבד
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'token.json' # קובץ לשמירת הטוקן לאחר אימות ראשוני

def create_message(sender, to, subject, message_text_html):
    """בניית הודעת מייל בפורמט MIME מוכן לשליחה באמצעות API."""
    
    # שימוש ב-MIMEMultipart עבור תוכן HTML
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    # הוספת גוף ההודעה כ-HTML
    message.attach(MIMEText(message_text_html, 'html'))
    
    # הפיכת המייל לפורמט Base64 URL-safe
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_gmail_api_email(subject, email_body_html, receiver_email):
    """שולחת מייל באמצעות Gmail API."""

    # כתובת האימייל שלך כמשתמש המאומת (momemail053@gmail.com)
    user_email = os.environ.get('RECEIVER_EMAIL') 
    if not user_email:
        print("שגיאה: RECEIVER_EMAIL אינו מוגדר.", file=sys.stderr)
        return False

    # 1. קריאת האישורים מתוך משתנה הסביבה
    CREDENTIALS_JSON = os.environ.get('GMAIL_CREDENTIALS')
    if not CREDENTIALS_JSON:
        print("שגיאה: GMAIL_CREDENTIALS אינו מוגדר.", file=sys.stderr)
        return False
    
    creds = None
    
    # 2. טעינת טוקן שמור (אם קיים)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 3. תהליך האימות (Authorization)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # רענון הטוקן אם פג תוקפו
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"שגיאה ברענון הטוקן: {e}", file=sys.stderr)
                creds = None # אפס את האישורים ונסה אימות מלא
        else:
            # יצירת קובץ אישורים זמני
            temp_file_path = os.path.join(base_dir, 'temp_credentials.json')
            try:
                with open(temp_file_path, 'w') as f:
                    f.write(CREDENTIALS_JSON)
            except Exception as e:
                print(f"שגיאה בכתיבת קובץ זמני: {e}", file=sys.stderr)
                return False
            
            # ביצוע תהליך האימות המלא
            try:
                flow = InstalledAppFlow.from_client_secrets_file(temp_file_path, SCOPES)
                
                # *** מכיוון שאנחנו בסביבת שרת, נשתמש ב-run_console. ***
                # *** הדבר ידרוש כניסה ידנית ללינק שיוצג בלוגים בפעם הראשונה! ***
                creds = flow.run_console()
            
            except Exception as e:
                print(f"שגיאה בתהליך האימות - יש לבדוק את הלוגים ולבצע אימות ידני: {e}", file=sys.stderr)
                return False
            finally:
                # ניקוי: מחיקת הקובץ הזמני
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        # שמירת האישורים המעודכנים לקובץ טוקן.
        if creds and creds.valid:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

    # 4. שליחת המייל
    if not creds or not creds.valid:
        print("שגיאה סופית: לא ניתן לשלוח - האימות לא הצליח.", file=sys.stderr)
        return False

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # יצירת ההודעה (השולח והמקבל הם אותו אדם, momemail053@gmail.com)
        message = create_message(user_email, receiver_email, subject, email_body_html)
        
        # שליחת ההודעה
        send_message = service.users().messages().send(userId='me', body=message).execute()
        print(f"המייל נשלח בהצלחה, ID: {send_message.get('id')}", file=sys.stdout)
        return True
        
    except httplib.HTTPException as e:
        print(f"שגיאת HTTP בעת שליחה: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"שגיאה בשליחת המייל באמצעות API: {e}", file=sys.stderr)
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
        
        if send_gmail_api_email(subject, email_body_html, receiver_email):
            return redirect(url_for('index', status='success'))
        else:
            return redirect(url_for('index', status='error'))

# ----------------- הרצה -----------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
