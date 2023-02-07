from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import uuid


# Create your models here.
class TblTypes(models.Model):
    type_id = models.CharField(max_length=1, primary_key=True)
    type_name = models.CharField(max_length=15)

    def __str__(self):
        return self.type_name


class TblEmployeeTitles(models.Model):
    title_id = models.CharField(max_length=5, primary_key=True)
    title_name = models.CharField(max_length=50)
    rate = models.IntegerField()

    def __str__(self):
        return self.title_id


class TblExpenseCategory(models.Model):
    expense_category_id = models.AutoField(primary_key=True)
    expense_category = models.CharField(null=True, blank=True, max_length=40)

    class Meta:
        ordering = ['expense_category_id']

    def __str__(self):
        return str(self.expense_category)


class TblEmployee(models.Model):
    employee_id = models.CharField(max_length=50, primary_key=True)
    employee_fname = models.CharField(max_length=25)
    employee_lname = models.CharField(max_length=25)
    employee_title = models.ForeignKey(TblEmployeeTitles, on_delete=models.CASCADE)

    def __str__(self):
        return self.employee_id

    def EmployeeEmail(self):
        return "%s@srgroupllc.com" % self.employee_id

    def getRate(self):
        return self.employee_title.rate


class TblParent(models.Model):
    parent_id = models.CharField(max_length=15, primary_key=True)
    parent_name = models.CharField(max_length=100)


    class Meta:
        ordering = ['parent_id']

    def __str__(self):
        return self.parent_id


class TblProvider(models.Model):
    provider_id = models.CharField(max_length=6, primary_key=True)
    provider_name = models.CharField(max_length=100)
    parent = models.ForeignKey(TblParent, on_delete=models.CASCADE)

    class Meta:
        ordering = ['provider_id', ]

    def __str__(self):
        return self.provider_id + "-" + self.provider_name


class TblTimeCode(models.Model):
    time_code = models.IntegerField(primary_key=True)
    time_code_description = models.TextField(max_length=75)
    time_code_hours_budget = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['time_code']

    def __str__(self):
        return str(self.time_code) + "-" + self.time_code_description


class TblTimeSheet(models.Model):
    timesheet_id = models.AutoField(primary_key=True)
    # expense_id = models.ForeignKey(TblExpense, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.ForeignKey(TblEmployee, on_delete=models.CASCADE)
    date = models.DateField()
    provider_id = models.ForeignKey(TblProvider, on_delete=models.CASCADE)
    time_code = models.ForeignKey(TblTimeCode, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    type_id = models.ForeignKey(TblTypes, on_delete=models.CASCADE)
    fye = models.DateField(null=True, blank=True)
    note = models.TextField(max_length=500, null=True, blank=True)

    def get_timcodedescription(self):
        return self.time_code.time_code_description

    def get_providername(self):
        return self.provider_id.provider_name

    def get_rate(self):
        title = get_object_or_404(TblEmployee, pk=self.employee_id)
        # emp_rate = get_object_or_404(TblEmployeeTitles, pk=title)
        emp_rate = get_object_or_404(TblEmployeeTitles, pk=title.employee_title_id)
        return emp_rate.rate

    def get_project_budget(self):
        return self.time_code.time_code_hours_budget

    class Meta:
        default_permissions = ('view', 'add', 'delete', 'change')


class TblExpense(models.Model):
    expense_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    expense_category_id = models.ForeignKey(TblExpenseCategory, on_delete=models.CASCADE)
    expense_amount = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    timesheet_id = models.ForeignKey(TblTimeSheet, on_delete=models.CASCADE, blank=False, null=False)

    def get_timesheet_date(self):
        return self.timesheet_id.date

    def get_timesheet_code(self):
        return self.timesheet_id.time_code

    def get_timesheet_provider(self):
        return self.timesheet_id.provider_id

    def get_timesheet_fye(self):
        return self.timesheet_id.fye

    def get_category(self):
        return self.expense_category_id.expense_category

    def get_employee(self):
        return self.timesheet_id.employee_id


class TblToDoList(models.Model):
    todolist_id = models.AutoField(primary_key=True)
    employee_id = models.ForeignKey(TblEmployee, on_delete=models.CASCADE)
    date = models.DateField()
    end = models.DateField(null=True, blank=True)
    provider_id = models.ForeignKey(TblProvider, on_delete=models.CASCADE)
    time_code = models.ForeignKey(TblTimeCode, on_delete=models.CASCADE)
    # hours = models.DecimalField(max_digits=4, decimal_places=2)
    # type_id = models.ForeignKey(TblTypes, on_delete=models.CASCADE)
    fye = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=100, null=True, blank=True)

    def get_providername(self):
        return self.provider_id.provider_name


class TblEngagements(models.Model):
    engagement_id = models.AutoField(primary_key=True)
    srg_id = models.CharField(max_length=20)
    start_date = models.DateField()
    # target_end_date = models.DateField()
    fye = models.DateField(null=True, blank=True)
    budget_amount = models.IntegerField(null=True, default=10000)
    budget_hours = models.IntegerField(default=120)
    is_complete = models.BooleanField(default=False)
    complete_date = models.DateField(blank=True, default=date.today)
    parent = models.ForeignKey(TblParent, on_delete=models.CASCADE)
    provider = models.ForeignKey(TblProvider, on_delete=models.CASCADE)
    time_code = models.ForeignKey(TblTimeCode, on_delete=models.CASCADE)
    type = models.ForeignKey(TblTypes, on_delete=models.CASCADE)
    proj_manager = models.ForeignKey(User, related_name='manager', on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(TblEmployee, related_name='employee', db_column='employee_id', on_delete=models.CASCADE, default='')

    def __str__(self):
        return self.srg_id

    def getProviderName(self):
        return self.provider.provider_name

    def getParentName(self):
        return self.parent.parent_name


class TblTime(models.Model):
    timesheet_id = models.AutoField(primary_key=True)
    # expense_id = models.ForeignKey(TblExpense, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(TblEmployee, on_delete=models.CASCADE)
    engagement = models.ForeignKey(TblEngagements, db_column='srg_id', on_delete=models.CASCADE)
    date = models.DateField()
    # provider_id = models.ForeignKey(TblProvider, on_delete=models.CASCADE)
    # time_code = models.ForeignKey(TblTimeCode, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    # type_id = models.ForeignKey(TblTypes, on_delete=models.CASCADE)
    # fye = models.DateField(null=True, blank=True)
    note = models.TextField(max_length=500, null=True, blank=True)