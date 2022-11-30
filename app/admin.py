from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(TblEmployee)

admin.site.register(TblParent)


class ProviderAdmin(admin.ModelAdmin):
    list_display = ('provider_id', 'provider_name', 'parent')


class TypesAdmin(admin.ModelAdmin):
    list_display = ('type_id', 'type_name',)


class TimeSheetAdmin(admin.ModelAdmin):
    list_display = ('timesheet_id', 'employee_id', 'date', 'provider_id', 'time_code', 'hours',
                    'type_id', 'fye', 'note')


class TimeCodeAdmin(admin.ModelAdmin):
    list_display = ('time_code', 'time_code_description', 'time_code_hours_budget')


class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('expense_category_id', 'expense_category')


admin.site.register(TblProvider, ProviderAdmin)
admin.site.register(TblTypes, TypesAdmin)
admin.site.register(TblTimeSheet, TimeSheetAdmin)
admin.site.register(TblTimeCode, TimeCodeAdmin)
admin.site.register(TblExpenseCategory, ExpenseCategoryAdmin)
