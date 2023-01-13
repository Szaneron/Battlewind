from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(Profile)
admin.site.register(Team)
admin.site.register(Invitation)
admin.site.register(Organizer)
admin.site.register(Tournament)
admin.site.register(Match)
