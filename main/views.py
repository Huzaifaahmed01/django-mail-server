from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.http import HttpResponse
from .models import *
import imaplib, poplib, email
from email.header import decode_header
from django.core.files.base import ContentFile


def send_email(request, settings_id):
    try:
        # Fetch the EmailSettings object using settings_id
        settings = EmailSettings.objects.get(id=settings_id)

        # Decrypt the email password for use in SMTP backend
        decrypted_password = settings.get_password()

        # Initialize the EmailBackend with settings from the EmailSettings object
        backend = EmailBackend(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.email_username,
            password=decrypted_password,
            use_tls=settings.use_tls,
            use_ssl=settings.use_ssl,
            fail_silently=False,
        )

        # Prepare the email message
        email = EmailMessage(
            subject='Test email from Django app.',
            body='This is a test email sent from a Django app.',
            from_email=settings.email_username,
            to=['huzaifa.ahmed01@gmail.com'],  # List of recipient email addresses
            connection=backend,
        )

        # Optionally attach files, if any
        # email.attach_file('/path/to/your/file.pdf')

        # Send the email
        email.send()

        return HttpResponse("Email sent successfully.")
    except EmailSettings.DoesNotExist:
        return HttpResponse("Email settings not found.", status=404)
    except Exception as e:
        # Handle any other exceptions
        return HttpResponse(f"Error sending email: {str(e)}", status=500)

def fetch_emails(request):
    for settings in EmailSettings.objects.all():
        decrypted_password = settings.get_password()  # Decrypt the password

        if settings.email_protocol == 'IMAP':
            mail = imaplib.IMAP4_SSL(settings.imap_pop3_host, settings.imap_pop3_port)
            mail.login(settings.email_username, decrypted_password)  # Use decrypted password
            mail.select("inbox")

            _, search_data = mail.search(None, 'ALL')
            for num in search_data[0].split():
                _, data = mail.fetch(num, '(RFC822)')
                process_email(data, settings)
                
        elif settings.email_protocol == 'POP3':
            # mail = poplib.POP3_SSL(settings.imap_pop3_host, settings.imap_pop3_port)
            mail = poplib.POP3(settings.imap_pop3_host, settings.imap_pop3_port)
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
