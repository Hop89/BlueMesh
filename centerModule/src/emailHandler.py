import os
from dotenv import load_dotenv
import mailtrap as mt
import imaplib as iml
import email

load_dotenv()
MAILTRAP_TOKEN = os.environ.get("MAILTRAP_TOKEN")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

def send(receiver, subj, text, category):
    mail = mt.Mail(
        sender=mt.Address(email="hello@demomailtrap.co", name="BlueMesh"),
        to=[mt.Address(receiver)],
        subject=subj,
        text=text,
        category=category,
    )

    client = mt.MailtrapClient(token=MAILTRAP_TOKEN)
    response = client.send(mail)

    print(response)

def receive():
    mail = iml.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")
    result, data = mail.search(None, "UNSEEN")
    for num in data[0].split():
        result, msg_data = mail.fetch(num, "(RFC822)")
        raw_email_bytes = msg_data[0][1]
        
        # 1. Convert the raw bytes into a readable Email object
        parsed_email = email.message_from_bytes(raw_email_bytes)
        
        print(f"\n--- New Email: {parsed_email.get('Subject')} ---")
        print(f"{parsed_email.get('Body')}")
        
        # 2. Extract the plain text body
        if parsed_email.is_multipart():
            # 'walk' loops through the text/plain, text/html, and attachments
            for part in parsed_email.walk():
                if part.get_content_type() == "text/plain":
                    # decode=True handles base64/quoted-printable encoding
                    body = part.get_payload(decode=True).decode('utf-8')
                    print("Message:")
                    print(body)
    mail.logout()

def main():
    send(GMAIL_USER, "test", "testing", None)
    receive()

if (__name__ == "__main__"):
    main()