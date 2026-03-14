from django.contrib import admin
from .models import Software,Order

@admin.register(Software)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_in_credits',)
@admin.register(Order)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'price_paid','duration')
# Register your models here.
