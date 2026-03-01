import os
from dotenv import load_dotenv
import mailtrap as mt
import imaplib as iml
import email

_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"))
load_dotenv()
MAILTRAP_TOKEN = os.environ.get("MAILTRAP_TOKEN")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
MAIL_SENDER = os.environ.get("MAIL_SENDER", "hello@demomailtrap.co")
MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME", "BlueMesh")

def send(receiver, subj, text, category=None, sender_email=None, sender_name=None):
    if not MAILTRAP_TOKEN:
        raise RuntimeError("MAILTRAP_TOKEN is not set. Add it to .env.")
    if not receiver:
        raise ValueError("receiver is required.")

    mail = mt.Mail(
        sender=mt.Address(
            email=sender_email or MAIL_SENDER,
            name=sender_name or MAIL_SENDER_NAME,
        ),
        to=[mt.Address(receiver)],
        subject=subj,
        text=text,
        category=category,
    )

    client = mt.MailtrapClient(token=MAILTRAP_TOKEN)
    return client.send(mail)

def receive():
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise RuntimeError("GMAIL_USER/GMAIL_APP_PASSWORD are not set. Add them to .env.")

    mail = iml.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")
    result, data = mail.search(None, "UNSEEN")
    receivedMail = []
    for num in data[0].split():
        result, msg_data = mail.fetch(num, "(RFC822)")
        raw_email_bytes = msg_data[0][1]
        
        # 1. Convert the raw bytes into a readable Email object
        parsed_email = email.message_from_bytes(raw_email_bytes)
        
        # print(f"\n--- New Email: {parsed_email.get('Subject')} ---")
        sender = parsed_email.get('From')
        subject = parsed_email.get('Subject')
        
        # 2. Extract the plain text body
        if parsed_email.is_multipart():
            # 'walk' loops through the text/plain, text/html, and attachments
            for part in parsed_email.walk():
                if part.get_content_type() == "text/plain":
                    # decode=True handles base64/quoted-printable encoding
                    body = part.get_payload(decode=True).decode('utf-8')
                    receivedMail.append({
                        "from" : sender,
                        "subject" : subject,
                        "body" : body

                    })
                    # print("Message:")
                    # print(body)

    mail.logout()
    return receivedMail

def main():
    send(GMAIL_USER, "test", "testing 2", None)
    print(receive())

if (__name__ == "__main__"):
    main()
