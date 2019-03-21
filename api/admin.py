from django.contrib import admin

# Register your models here.
from .models import Printer, Check


class PrinterAdmin(admin.ModelAdmin):
    list_display = ("name", "api_key", "check_type", "point_id")
    list_filter = ["check_type"]


class CheckAdmin(admin.ModelAdmin):
    list_display = ("printer_id", "type", "order", "status")
    list_filter = ["printer_id", "type", "status"]


admin.site.register(Printer, PrinterAdmin)
admin.site.register(Check, CheckAdmin)
