from django.contrib import admin
from .models import Software

@admin.register(Software)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_in_credits', 'file',)
# Register your models here.
