from django.db import models
from cryptography.fernet import Fernet

# Generate a key and keep it somewhere safe
# FERNET_KEY should be generated once and stored securely
FERNET_KEY = b'BNR66rlVfGPp_l67ytWbZzBBVcy_r-M-n-ow6mp_n2c='  # Use Fernet.generate_key() to generate
cipher_suite = Fernet(FERNET_KEY)

class EmailSettings(models.Model):
    """
    Model to store email settings for law firms
    """
    PROTOCOL_CHOICES = (
        ('IMAP', 'IMAP'),
        ('POP3', 'POP3'),
    )
    firm = models.CharField(max_length=255)
    email_username = models.CharField(max_length=255)
    email_password = models.CharField(max_length=255)
    smtp_host = models.CharField(max_length=255)
    smtp_port = models.IntegerField()
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)  # Typically for SMTP
    imap_pop3_host = models.CharField(max_length=255, blank=True, null=True)  # Host for IMAP/POP3
    imap_pop3_port = models.IntegerField(blank=True, null=True)  # Port for IMAP/POP3
    email_protocol = models.CharField(max_length=4, choices=PROTOCOL_CHOICES, blank=True, null=True)  # Protocol choice for receiving emails

    def set_password(self, raw_password):
        if raw_password is not None:
            self.email_password = cipher_suite.encrypt(raw_password.encode()).decode()

    def get_password(self):
        if self.email_password:
            return cipher_suite.decrypt(self.email_password.encode()).decode()
        return None

    # Override save method if you want to automatically encrypt passwords on save
    def save(self, *args, **kwargs):
        self.set_password(self.email_password)
        super(EmailSettings, self).save(*args, **kwargs)

class EmailMessage(models.Model):
    """
    Model to store email messages
    """
    settings = models.ForeignKey(EmailSettings, on_delete=models.CASCADE)
    sender = models.EmailField()
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    date_received = models.DateTimeField()

class Attachment(models.Model):
    """
    Model to store email attachments
    """
    email = models.ForeignKey(EmailMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
