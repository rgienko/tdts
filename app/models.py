from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404


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

    def __str__(self):
        return self.parent_id


class TblProvider(models.Model):
    provider_id = models.CharField(max_length=6, primary_key=True)
    provider_name = models.CharField(max_length=100)
    parent = models.ForeignKey(TblParent, on_delete=models.CASCADE)

    def __str__(self):
        return self.provider_id + "-" + self.provider_name


class TblTimeCode(models.Model):
    time_code = models.IntegerField(primary_key=True)
    time_code_description = models.TextField(max_length=75)
    time_code_hours_budget = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.time_code) + "-" + self.time_code_description


class TblTimeSheet(models.Model):
    id = models.AutoField(primary_key=True)
    employee_id = models.ForeignKey(TblEmployee, on_delete=models.CASCADE)
    date = models.DateField()
    provider_id = models.ForeignKey(TblProvider, on_delete=models.CASCADE)
    time_code = models.ForeignKey(TblTimeCode, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    type_id = models.ForeignKey(TblTypes, on_delete=models.CASCADE)
    fye = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=100, null=True, blank=True)

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


class TblToDoList(models.Model):
    id = models.AutoField(primary_key=True)
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
