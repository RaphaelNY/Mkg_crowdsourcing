from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(NormalUser)
admin.site.register(Asker)
admin.site.register(Expert)
admin.site.register(Question)