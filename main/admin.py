from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(EmailSettings)
admin.site.register(EmailMessage)
admin.site.register(Attachment)