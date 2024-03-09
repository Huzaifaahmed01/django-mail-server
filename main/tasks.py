from celery import shared_task
from django.core.files.base import ContentFile
from .models import EmailSettings, EmailMessage, Attachment
import imaplib, poplib, email
from email.header import decode_header

@shared_task
def fetch_emails():
    for settings in EmailSettings.objects.all():
        decrypted_password = settings.get_password()  # Decrypt the password

        if settings.email_protocol == 'IMAP':
            mail = imaplib.IMAP4_SSL(settings.email_server, settings.email_port)
            mail.login(settings.email_username, decrypted_password)  # Use decrypted password
            mail.select("inbox")

            _, search_data = mail.search(None, 'ALL')
            for num in search_data[0].split():
                _, data = mail.fetch(num, '(RFC822)')
                process_email(data, settings)
                
        elif settings.email_protocol == 'POP3':
            mail = poplib.POP3_SSL(settings.email_server, settings.email_port)
            mail.user(settings.email_username)
            mail.pass_(decrypted_password)  # Use decrypted password

            numMessages = len(mail.list()[1])
            for i in range(numMessages):
                _, data, _ = mail.retr(i+1)
                process_email(data, settings)

def process_email(data, settings):
    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject, encoding = decode_header(msg["subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')
                
            # Save the email message to your model
            email_message = EmailMessage.objects.create(
                settings=settings,
                sender=msg["from"],
                recipient=msg["to"],
                subject=subject,
                body=msg.get_payload(),
                date_received=email.utils.parsedate_to_datetime(msg['Date'])
            )
            
            # Check for attachments and save them
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue
                file_name = part.get_filename()
                if bool(file_name):
                    attachment = ContentFile(part.get_payload(decode=True), name=file_name)
                    Attachment.objects.create(email=email_message, file=attachment)
