from django.contrib import admin
from .models import Software,Order,OrderClientFile

@admin.register(Software)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_in_credits',)
@admin.register(Order)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'price_paid')
admin.site.register(OrderClientFile)
# Register your models here.
