from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.http import HttpResponse
from .models import EmailSettings

def send_email_with_encrypted_settings(request, settings_id):
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
            subject='Your Subject Here',
            body='Your email body here.',
            from_email=settings.email_username,
            to=['recipient@example.com'],  # List of recipient email addresses
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
