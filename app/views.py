import calendar
import os
import random
from datetime import date, timedelta, datetime
from io import BytesIO

import numpy
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import logout
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Sum, Count
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import TemplateView
import pandas
import xlsxwriter
from django_pandas.io import read_frame
from itertools import chain

from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .filters import TimeSheetFilter
from .forms import *
from .models import *

from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.platypus import *


# Create your views here.
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('timesheet')
        else:
            messages.error(request, 'Error, wrong username or password')
        return render(request, 'login.html')

    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        username = first_name + "." + last_name
        email = username + "@srgroupllc.com"
        if password1 == password2:
            new_user = User.objects.create_user(username, email, password1)
            new_user.first_name = first_name
            new_user.last_name = last_name
            new_user.save()

            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
    else:
        pass

    return render(request, 'register.html')


@login_required
def main(request):
    context = {}
    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = today + timedelta(days=5)

    current_timesheet = TblTimeSheet.objects.filter(employee_id=request.user.username).filter(
        date__lte=week_end).filter(date__gte=week_beg).order_by('date')

    context['today'] = today
    context['week_beg'] = week_beg
    context['week_end'] = week_end
    context['current_timesheet'] = current_timesheet

    return render(request, 'index.html', context)


@login_required()
def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split("-"))
        return date(year, month, day=1)
    return datetime.today()


@login_required()
def deleteToDoListEntry(request, pk):
    entry_instance = get_object_or_404(TblToDoList, pk=pk)
    if request.method == 'POST':
        entry_instance.delete()
        return redirect('todolist')

    context = {'entry_instance': entry_instance}

    return render(request, 'deltodolistentry.html', context)

def addEngagement(request):

    if request.method == 'POST':
        form = EngagementForm(request.POST)

        # first_name = request.POST.get('first_name')

        who = request.POST.get('provider')
        what = request.POST.get('time_code')
        when = request.POST.get('fye')
        when = when[:4]
        how = request.POST.get('type')
        srgid = who + "." + str(what) + "." + str(
            when) + "." + how
        print(srgid)


        if form.is_valid():
            new_engagement = form.save(commit=False)
            new_engagement.srg_id = srgid
            new_engagement.save()

            return redirect('add-engagement')
    else:
        form = EngagementForm()

    context = {'form':form}

    return render(request, 'add_engagement.html', context)


@login_required()
def editToDoListEntry(request, pk):
    entry_instance = get_object_or_404(TblToDoList, pk=pk)
    context = {}
    if request.method == 'POST':
        form = EditFormToDo(request.POST, instance=entry_instance)

        if form.is_valid():
            entry_instance = form.save(commit=False)
            entry_instance.save()

            return redirect('todolist')
    else:
        form = EditFormToDo(instance=entry_instance)

    context['form'] = form
    context['entry_instance'] = entry_instance

    return render(request, 'editentry.html', context)


class ToDoListView(PermissionRequiredMixin, TemplateView):
    permission_required = ('app.view_tbltodolist', 'app.add_tbltodolist',
                           'app.change_tbltodolist', 'app.delete_tbltodolist')
    template_name = 'todolist.html'

    today = date.today()
    thirty_date = today + timedelta(days=30)
    thru_date = today + timedelta(days=60)
    context = {'today': today, 'thru_date': thru_date}

    def get(self, *args, **kwargs):
        # formset = ToDoListFormSet(queryset=TblToDoList.objects.none())

        form = ToDoForm(self.request.POST)
        current_todolist = TblToDoList.objects.filter(employee_id=self.request.user.username).filter(
            date__lte=self.thru_date).filter(date__gte=self.today).order_by('date')

        upcoming_projects = current_todolist.values('date', 'provider_id', 'provider_id__provider_name', 'time_code',
                                                    'time_code_id__time_code_description', 'fye').annotate()
        todlist_items = []
        for item in current_todolist:
            todo_title = str(item.provider_id) + " " + str(item.time_code)
            items_dict = {'title': todo_title, 'start': item.date}

            todlist_items.append(items_dict)

        self.context['form'] = form
        self.context['current_todolist'] = current_todolist
        self.context['upcoming_projects'] = upcoming_projects
        self.context['todlist_items'] = todlist_items
        return self.render_to_response(self.context)

    def post(self, *args, **kwargs):
        form = ToDoForm(self.request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.employee_id = get_object_or_404(TblEmployee, pk=self.request.user.username)
            instance.save()
            return redirect(reverse_lazy('todolist'))

        return self.render_to_response({'form': form})


@login_required()
def deleteToDoEntry(request, pk):
    entry_instance = get_object_or_404(TblToDoList, pk=pk)
    entry_instance.delete()


class BulkToDoList(TemplateView):
    template_name = 'bulktodolist.html'

    today = date.today()
    thirty_date = today + timedelta(days=30)
    thru_date = today + timedelta(days=60)
    context = {'today': today, 'thru_date': thru_date}

    def get(self, *args, **kwargs):
        formset = ToDoListFormSet(queryset=TblToDoList.objects.none())
        self.context['formset'] = formset

        return self.render_to_response(self.context)

    def post(self, *args, **kwargs):
        formset = ToDoListFormSet(data=self.request.POST)

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.employee_id = get_object_or_404(TblEmployee, pk=self.request.user.username)
                instance.save()
            return redirect(reverse_lazy('todolist'))

        return self.render_to_response({'formset': formset})


class BulkTimeSheet(TemplateView):
    template_name = 'bulktimesheet.html'

    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)
    thirty = date.today() - timedelta(days=30)

    def get(self, *args, **kwargs):
        formset = TimeSheetFormSet(queryset=TblTimeSheet.objects.none())

        current_timesheet = TblTimeSheet.objects.filter(employee_id=self.request.user.username).filter(
            date__lte=self.week_end).filter(date__gte=self.week_beg).order_by('date')

        return self.render_to_response({'timesheet_formset': formset, 'today': self.today,
                                        'week_beg': self.week_beg, 'week_end': self.week_end,
                                        'current_timesheet': current_timesheet})

    def post(self, *args, **kwargs):
        formset = TimeSheetFormSet(data=self.request.POST)

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.employee_id = get_object_or_404(TblEmployee, pk=self.request.user.username)
                instance.save()
            return redirect(reverse_lazy('timesheet'))

        return self.render_to_response({'timesheet_formset': formset})

class StaffDashboard(TemplateView):

    template_name = 'timesheet_v2.html'

    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)
    thirty = date.today() - timedelta(days=30)

    def get(self, *args, **kwargs):

        add_time_form = TimeForm(self.request.POST)
        my_current_engagements = TblEngagements.objects.filter(employee_id=self.request.user.username)

        timesheet_total = TblTime.objects.filter(employee_id=self.request.user.username).order_by('-date')

        top_engagements_agg = timesheet_total.values('engagement', 'engagement__srg_id',
                                                     'engagement__provider',
                                                     'engagement__provider__provider_name',
                                                     'engagement__time_code',
                                                     'engagement__time_code__time_code_description',
                                                     'engagement__fye', 'engagement__proj_manager__username',
                                                     'engagement__employee', 'engagement__is_complete').annotate(
            sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')

        current_timesheet = timesheet_total.filter(employee_id=self.request.user.username).filter(
            date__lte=self.week_end).filter(date__gte=self.week_beg).order_by('date')

        fixed_hours = current_timesheet.filter(engagement__type_id='F').aggregate(sum_of_hours=Sum('hours'))
        hourly_hours = current_timesheet.filter(engagement__type_id='H').aggregate(sum_of_hours=Sum('hours'))
        contingency_hours = current_timesheet.filter(engagement__type_id='C').aggregate(sum_of_hours=Sum('hours'))
        non_hours = current_timesheet.filter(engagement__type_id='N').aggregate(sum_of_hours=Sum('hours'))

        total_hours = current_timesheet.aggregate(sum_of_hours=Sum('hours'))





        context = {'today': self.today, 'week_beg': self.week_beg,
                   'week_end': self.week_end, 'my_current_engagements': my_current_engagements,
                   'top_engagements_agg': top_engagements_agg, 'fixed_hours': fixed_hours,
                   'hourly_hours':hourly_hours, 'contingency_hours': contingency_hours,
                   'non_hours':non_hours, 'total_hours': total_hours, 'add_time_form': add_time_form}



        return  self.render_to_response(context)


    def post(self, *args, **kwargs):

        add_time_form = TimeForm(self.request.POST)
        engagement_id = self.request.POST.get('engagement-input')
        print(engagement_id)

        engagement_instance = get_object_or_404(TblEngagements, srg_id=engagement_id)

        if add_time_form.is_valid():
            new_entry = add_time_form.save(commit=False)
            new_entry.employee_id = get_object_or_404(TblEmployee, pk=self.request.user.username)
            new_entry.date = self.today
            new_entry.engagement = engagement_instance
            new_entry.save()
            return redirect(reverse_lazy('staff-dashboard'))

        context={'add_time_form': add_time_form}
        return self.render_to_response(context)


class TimesheetView(PermissionRequiredMixin, TemplateView):
    permission_required = ('app.view_tbltimesheet', 'app.add_tbltimesheet',
                           'app.change_tbltimesheet', 'app.delete_tbltimesheet')
    template_name = 'timesheet.html'

    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)
    thirty = date.today() - timedelta(days=30)

    def get(self, *args, **kwargs):
        # formset = TimeSheetFormSet(queryset=TblTimeSheet.objects.none(),
        #                          initial=[{'employee_id': self.request.user.username}])

        form = TimeSheetForm(self.request.POST)

        current_timesheet = TblTimeSheet.objects.filter(employee_id=self.request.user.username).filter(
            date__lte=self.week_end).filter(date__gte=self.week_beg).order_by('date')

        fixed_hours = current_timesheet.filter(type_id='F').aggregate(sum_of_hours=Sum('hours'))
        hourly_hours = current_timesheet.filter(type_id='H').aggregate(sum_of_hours=Sum('hours'))
        contingency_hours = current_timesheet.filter(type_id='C').aggregate(sum_of_hours=Sum('hours'))
        non_hours = current_timesheet.filter(type_id='N').aggregate(sum_of_hours=Sum('hours'))

        total_hours = current_timesheet.aggregate(sum_of_hours=Sum('hours'))

        thirty_timesheet = TblTimeSheet.objects.filter(employee_id=self.request.user.username).filter(
            date__lte=self.week_end).filter(date__gte=self.thirty).order_by('date')

        thirty_fixed_hours = thirty_timesheet.filter(type_id='F').aggregate(sum_of_hours=Sum('hours'))
        thirty_hourly_hours = thirty_timesheet.filter(type_id='H').aggregate(sum_of_hours=Sum('hours'))
        thirty_contingency_hours = thirty_timesheet.filter(type_id='C').aggregate(sum_of_hours=Sum('hours'))
        thirty_non_hours = thirty_timesheet.filter(type_id='N').aggregate(sum_of_hours=Sum('hours'))

        # top_projects = thirty_timesheet.values('provider_id', 'provider_id__provider_name', 'time_code', 'fye',
        #                                      'time_code_id__time_code_description').annotate(
        #   sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')[:5]

        timesheet_total = TblTimeSheet.objects.filter(employee_id=self.request.user.username).order_by('-date')

        top_projects_agg = timesheet_total.values('provider_id', 'provider_id__provider_name', 'time_code', 'fye',
                                                  'time_code_id__time_code_description').annotate(
            sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')[:5]

        return self.render_to_response({'form': form, 'current_timesheet': current_timesheet,
                                        'today': self.today, 'week_beg': self.week_beg, 'week_end': self.week_end,
                                        'total_hours': total_hours, 'fixed_hours': fixed_hours,
                                        'hourly_hours': hourly_hours,
                                        'contingency_hours': contingency_hours, 'non_hours': non_hours,
                                        'thirty_fixed_hours': thirty_fixed_hours,
                                        'thirty_hourly_hours': thirty_hourly_hours,
                                        'thirty_contingency_hours': thirty_contingency_hours,
                                        'thirty_non_hours': thirty_non_hours,
                                        # 'top_projects': top_projects,
                                        'top_projects_agg': top_projects_agg})

    def post(self, *args, **kwargs):
        form = TimeSheetForm(self.request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.employee_id = get_object_or_404(TblEmployee, pk=self.request.user.username)
            instance.save()
            return redirect(reverse_lazy('timesheet'))

        return self.render_to_response({'form': form})


def addExpense(request, pk):
    timesheet_entry = get_object_or_404(TblTimeSheet, pk=pk)

    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)

    current_timesheet = TblTimeSheet.objects.filter(employee_id=request.user.username).filter(
        date__lte=week_end).filter(date__gte=week_beg).order_by('date')

    current_expense = TblExpense.objects.filter(expense_amount__gt=0).filter(
        timesheet_id_id__date__gte=week_beg).filter(timesheet_id_id__date__lt=week_end)

    total_expense = current_expense.aggregate(sum_of_expense=Sum('expense_amount'))

    # total_expense = current_timesheet.aggregate(sum_of_expense=Sum('expense_amount'))

    # current_expense = TblTimeSheet.objects.raw('SELECT * ' 'FROM app_tbltimesheet ' 'JOIN app_tblexpense ON
    # app_tbltimesheet.id = app_tblexpense.timesheet_id_id ' 'JOIN app_expensecategory ON
    # app_expensecategory.expense_category_id = app_tblexpense.expense_category_id_id ' 'WHERE
    # app_tbltimesheet.employee_id_id = %s AND app_tbltimesheet.date ' '>= %s AND app_tbltimesheet.date < %s',
    # [request.user.username, week_beg, week_end] )

    if request.method == 'POST':
        expense_form = ExpenseForm(request.POST)

        if expense_form.is_valid():
            expense_entry = expense_form.save(commit=False)
            expense_entry.timesheet_id = timesheet_entry
            expense_entry.save()
            return redirect(reverse_lazy('timesheet'))

    else:
        expense_form = ExpenseForm()

    return render(request, 'add_expense.html', {'expense_form': expense_form, 'timesheet_entry': timesheet_entry,
                                                'current_expense': current_expense, 'total_expense': total_expense})


def expenseReport(request):
    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)

    current_expense = TblExpense.objects.filter(expense_amount__gt=0).filter(timesheet_id_id__date__gte=week_beg)

    total_expense = current_expense.aggregate(sum_of_expense=Sum('expense_amount'))

    return render(request, 'my_expense_report.html',
                  {'current_expense': current_expense, 'total_expense': total_expense})


def SRGExpenseReport(request):
    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=14)

    current_expense = TblExpense.objects.filter(expense_amount__gt=0).filter(timesheet_id_id__date__gte=week_beg)

    total_expense = current_expense.aggregate(sum_of_expense=Sum('expense_amount'))

    return render(request, 'srg_expense_report.html',
                  {'current_expense': current_expense, 'total_expense': total_expense})


@login_required()
def editTimesheetEntry(request, pk):
    entry_instance = get_object_or_404(TblTimeSheet, pk=pk)
    context = {}
    if request.method == 'POST':
        form = TimeSheetForm(request.POST, instance=entry_instance)

        if form.is_valid():
            entry_instance = form.save(commit=False)
            entry_instance.save()

            return redirect('timesheet')
    else:
        form = TimeSheetForm(instance=entry_instance)

    context['form'] = form
    context['entry_instance'] = entry_instance

    return render(request, 'edittimesheet.html', context)


def analytics_detail(request, prov, tc, fy):
    if fy == 'None':
        proj_emp_detail = TblTimeSheet.objects.filter(provider_id=prov, time_code=tc)
    else:
        proj_emp_detail = TblTimeSheet.objects.filter(provider_id=prov, time_code=tc, fye=fy)

    proj_emp_detail_aggr = proj_emp_detail.values('employee_id', 'employee_id__employee_title__rate').annotate(
        emp_sum_of_project_hours=Sum('hours')).order_by('-emp_sum_of_project_hours')

    proj_detail = proj_emp_detail[:1]

    proj_hours = proj_emp_detail.values('provider_id', 'provider_id__provider_name', 'time_code', 'fye',
                                        'time_code_id__time_code_description',
                                        'time_code_id__time_code_hours_budget').annotate(
        sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')

    labels = []
    data = []
    color = []
    proj_dollars = []

    for h in proj_hours:
        h['project_hours_remain'] = h['time_code_id__time_code_hours_budget'] - h['sum_of_project_hours']
        proj_dollars.append(h['sum_of_project_hours'] * 250)
        proj_dollars.append((h['time_code_id__time_code_hours_budget'] - h['sum_of_project_hours']) * 250)

    proj_emp = proj_emp_detail.values('employee_id', 'provider_id', 'time_code', 'fye',
                                      'time_code_id__time_code_hours_budget').annotate(
        emp_sum_of_project_hours=Sum('hours')).order_by('-emp_sum_of_project_hours')

    for e in proj_emp:
        labels.append(e['employee_id'])
        data.append(e['emp_sum_of_project_hours'])
        # proj_dollars.append(e['time_code_id__time_code_hours_budget'] * 250)
        color.append((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    context = {'proj_emp_detail': proj_emp_detail,
               'proj_detail': proj_detail,
               'labels': labels,
               'data': data,
               'color': color,
               'proj_dollars': proj_dollars,
               'proj_hours': proj_hours,
               'proj_emp_detail_aggr': proj_emp_detail_aggr}

    return render(request, 'analytics_detail.html', context)


@login_required()
def analytics(request):
    today = date.today()

    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)
    thirty = date.today() - timedelta(days=30)

    thirty_timesheet = TblTimeSheet.objects.filter(
        date__lte=week_end).filter(date__gte=thirty).order_by('date')

    all_projects = TblTimeSheet.objects.all()

    top_projects = all_projects.values('provider_id', 'provider_id__provider_name', 'time_code', 'fye',
                                       'time_code_id__time_code_description',
                                       'time_code_id__time_code_hours_budget').annotate(
        sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')

    labels = []
    data = []
    color = []
    proj_dollars = []

    for item in top_projects:
        proj_emp = TblTimeSheet.objects.filter(provider_id=item['provider_id'], time_code=item['time_code'],
                                               fye=item['fye'])

        proj_emp_agg = proj_emp.values('employee_id', 'provider_id', 'time_code', 'fye',
                                       'time_code_id__time_code_hours_budget').annotate(
            emp_sum_of_project_hours=Sum('hours')).order_by('-emp_sum_of_project_hours')

        item['proj_emp'] = proj_emp
        item['proj_emp_agg'] = proj_emp_agg
        item['hours_left'] = item['time_code_id__time_code_hours_budget'] - item['sum_of_project_hours']
        item['percent_to_budget'] = round(
            (item['sum_of_project_hours'] / item['time_code_id__time_code_hours_budget'] * 100))

    context = {'today': today, 'top_projects': top_projects[:5], 'all_projects': all_projects, 'labels': labels,
               'data': data, 'color': color}

    return render(request, 'analytics_v2.html', context)


@login_required()
def comparison(request):
    # employee_timesheet = TblTimeSheet.objects.filter(employee_id=request.user.username)
    employee_timesheet = TblTimeSheet.objects.all()
    employee_timesheet_projects = employee_timesheet.values('employee_id', 'provider_id', 'provider_id__provider_name',
                                                            'time_code', 'fye',
                                                            'time_code_id__time_code_description',
                                                            'time_code_id__time_code_hours_budget').annotate(
        sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')
    # employee_todolist = TblToDoList.objects.filter(employee_id=request.user.username)
    employee_todolist = TblToDoList.objects.all()

    employee_todolist_projects = employee_todolist.values('employee_id', 'provider_id', 'provider_id__provider_name',
                                                          'time_code', 'fye',
                                                          'time_code_id__time_code_description').annotate(
        count_of_project=Count('provider_id'))

    comparison_projects = []

    for item in employee_timesheet_projects:
        item_todo = employee_todolist_projects.filter(employee_id=item['employee_id'], provider_id=item['provider_id'],
                                                      time_code=item['time_code'],
                                                      fye=item['fye'])
        for todo in item_todo:
            item['todo_count'] = todo['count_of_project']
            item['todo_hours'] = todo['count_of_project'] * 8
            item['accuracy'] = round(item['sum_of_project_hours'] / (todo['count_of_project'] * 8) * 100)
    # print(employee_timesheet_projects)

    timesheet_filter = TimeSheetFilter(request.GET, queryset=employee_timesheet_projects)

    context = {
        'employee_timesheet_projects': employee_timesheet_projects,
        'employee_todolist_projects': employee_todolist_projects,
        'comparison_projects': comparison_projects,
        'timesheet_filter': timesheet_filter
    }

    return render(request, 'comparison.html', context)


@login_required()
def billableHoursCompilation(request):
    today = date.today()
    first = today.replace(day=1)
    last_month = first - timedelta(days=1)

    last_month_ts = TblTimeSheet.objects.filter(date__year=str(last_month.year)).filter(
        date__month=str(last_month.month)).order_by('employee_id')

    employees = TblEmployee.objects.all().order_by('employee_id')
    compilation = []

    for emp in employees:
        emp_last_month_ts = last_month_ts.filter(employee_id=emp.employee_id)
        fhours = emp_last_month_ts.filter(type_id='F').aggregate(fhours_sum=Sum('hours'))
        hhours = emp_last_month_ts.filter(type_id='H').aggregate(hhours_sum=Sum('hours'))
        chours = emp_last_month_ts.filter(type_id='C').aggregate(chours_sum=Sum('hours'))
        nhours = emp_last_month_ts.filter(type_id='N').aggregate(nhours_sum=Sum('hours'))

        if fhours['fhours_sum'] is None:
            fhours['fhours_sum'] = 0

        if hhours['hhours_sum'] is None:
            hhours['hhours_sum'] = 0

        if chours['chours_sum'] is None:
            chours['chours_sum'] = 0

        if nhours['nhours_sum'] is None:
            nhours['nhours_sum'] = 0

        total_hours = emp_last_month_ts.aggregate(total_hours_sum=Sum('hours'))

        if total_hours['total_hours_sum'] is None:
            total_hours['total_hours_sum'] = 0
            billability = 0
        else:

            billable_hours = total_hours['total_hours_sum'] - nhours['nhours_sum']

            billability = round((billable_hours / total_hours['total_hours_sum']) * 100)

        employee_dict = {'employee_id': emp,
                         'fhours': int(fhours['fhours_sum']),
                         'hhours': int(hhours['hhours_sum']),
                         'chours': int(chours['chours_sum']),
                         'nhours': int(nhours['nhours_sum']),
                         'total_hours': int(total_hours['total_hours_sum']),
                         'billability': billability
                         }

        compilation.append(employee_dict)

    srg_total_fhours = last_month_ts.filter(type_id='F').aggregate(srg_fhours_sum=Sum('hours'))

    srg_total_hhours = last_month_ts.filter(type_id='H').aggregate(srg_hhours_sum=Sum('hours'))

    srg_total_chours = last_month_ts.filter(type_id='C').aggregate(srg_chours_sum=Sum('hours'))

    srg_total_nhours = last_month_ts.filter(type_id='N').aggregate(srg_nhours_sum=Sum('hours'))

    srg_total_hours = last_month_ts.aggregate(srg_total_hours_sum=Sum('hours'))

    if request.method == 'POST' and 'excel_extract' in request.POST:
        df = pandas.DataFrame(compilation)
        # compilation_data = read_frame(df)
        fname = 'Employee Hours Compilation Report~' + str(last_month.month) + " " + str(last_month.year)

        response = HttpResponse(content_type='application/vns.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + fname + '.xlsx'
        with pandas.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=(str(last_month.month) + " " + str(last_month.year)),
                        index=False, header=True)
            # df_hfy.to_excel(writer, sheet_name=('PFY ' + fye), index=False, header=True)
            return response

    elif request.method == 'POST' and 'pdf_extract' in request.POST:
        fname = 'Employee Hours Compilation Report~' + calendar.month_name[last_month.month] + " " + str(
            last_month.year)
        documentTitleLineOne = 'Employee Billable Hours Report'
        documentTitleLineTwo = (str(last_month.month) + " " + str(last_month.year))

        elements = []

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_LEFT))

        titleOne = '<font size="24">Employee Billable Hours Compilation</font>'
        titleTwo = '<font size="24">' + calendar.month_name[last_month.month] + " " + str(last_month.year) + '</font>'

        elements.append(Paragraph(titleOne, styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(titleTwo, styles['Normal']))
        elements.append(Spacer(1, 48))

        df = pandas.DataFrame(compilation)

        columnHeaderEmployee = Paragraph('<para align=center>Employee</para>', styles["Normal"])
        columnHeaderF = Paragraph('<para align=center>Fixed-Fee</para>', styles["Normal"])
        columnHeaderH = Paragraph('<para align=center>Hourly</para>', styles["Normal"])
        columnHeaderC = Paragraph('<para align=center>Contingency</para>', styles["Normal"])
        columnHeaderN = Paragraph('<para align=center>Non-Billable</para>', styles["Normal"])
        columnHeaderT = Paragraph('<para align=center>Total</para>', styles["Normal"])
        columnHeaderBillable = Paragraph('<para align=center>% Billable</para>', styles["Normal"])

        pdfStory = [[columnHeaderEmployee, columnHeaderF, columnHeaderH, columnHeaderC,
                     columnHeaderN, columnHeaderT, columnHeaderBillable]]

        for row in compilation:
            employee = row['employee_id']
            columnFdata = row['fhours']
            columnHdata = row['hhours']
            columnCdata = row['chours']
            columnNdata = row['nhours']
            columnTdata = row['total_hours']
            columnBillable = row['billability']

            pdfStory.append([employee, columnFdata, columnHdata, columnCdata,
                        columnNdata, columnTdata, columnBillable])

        total = "Total:"

        fhours = srg_total_fhours['srg_fhours_sum']
        thhours = srg_total_hhours['srg_hhours_sum']
        chours = srg_total_chours['srg_chours_sum']
        nhours = srg_total_nhours['srg_nhours_sum']
        srg_total = srg_total_hours['srg_total_hours_sum']

        pdfStory.append([
            total,
            fhours,
            thhours,
            chours,
            nhours,
            srg_total
        ])

        t1 = Table(pdfStory)
        t1.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                # ('GRID', (0, 1), (-1, -1), 0.25, colors.black),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.blue),
                # ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ]
        ))
        elements.append(t1)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pageSize=letter, leftMargin=1 * cm, topMargin=1 * cm, bottomMargin=.5)
        doc.build(elements)
        pdf_value = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename={}'.format(fname)

        response.write(pdf_value)
        return response

    context = {'compilation': compilation,
               'last_month': last_month,
               'srg_total_fhours': srg_total_fhours,
               'srg_total_hhours': srg_total_hhours,
               'srg_total_chours': srg_total_chours,
               'srg_total_nhours': srg_total_nhours,
               'srg_total_hours': srg_total_hours['srg_total_hours_sum']
               }
    return render(request, 'emp_hours_comp.html', context)


@login_required()
def extractBillableHoursCompilation(request, dt):
    date_time_obj = datetime.strptime(dt, '%Y-%m-%d')
    ts_month = date_time_obj.month
    ts_year = date_time_obj.year

    ts = TblTimeSheet.objects.filter(date__year=ts_year).filter(date__month=ts_month)

    ts_data = read_frame(ts)

    fname = 'Hours Report~' + str(ts_month) + " " + str(ts_year)

    response = HttpResponse(content_type='application/vns.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + fname + '.xlsx'
    with pandas.ExcelWriter(response, engine='xlsxwriter') as writer:
        ts_data.to_excel(writer, sheet_name=(str(ts_month) + " " + str(ts_year)), index=False, header=True)
        # df_hfy.to_excel(writer, sheet_name=('PFY ' + fye), index=False, header=True)

        return response


@login_required()
def hoursReport(request):
    today = date.today()
    first = today.replace(day=1)
    last_month = first - timedelta(days=1)
    month = date.today().month

    timesheets = TblTimeSheet.objects.filter(date__year=last_month.year).filter(date__month=last_month.month)

    context = {
        'title': 'Hours Report',
        'timesheets': timesheets,
        'last_month': first - timedelta(days=1)

    }

    return render(request, 'srg_hours_report.html', context)


@login_required()
def extractHoursReport(request, dt):
    date_time_obj = datetime.strptime(dt, '%Y-%m-%d')
    ts_month = date_time_obj.month
    ts_year = date_time_obj.year

    ts = TblTimeSheet.objects.filter(date__year=ts_year).filter(date__month=ts_month)

    ts_data = read_frame(ts)

    fname = 'Hours Report~' + str(ts_month) + " " + str(ts_year)

    response = HttpResponse(content_type='application/vns.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + fname + '.xlsx'
    with pandas.ExcelWriter(response, engine='xlsxwriter') as writer:
        ts_data.to_excel(writer, sheet_name=(str(ts_month) + " " + str(ts_year)), index=False, header=True)
        # df_hfy.to_excel(writer, sheet_name=('PFY ' + fye), index=False, header=True)

        return response


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    name = user.first_name
                    email_template_name = "password_reset_email.txt"
                    protocol = "http://"
                    email = user.email
                    domain = '127.0.0.1:8000/reset/'
                    site_name = 'Website'
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    user = user
                    token = default_token_generator.make_token(user)

                    reset_url = protocol + domain + uid + "/" + token

                    message = Mail(
                        from_email='Randall.Gienko@srgroupllc.com',
                        to_emails='Randall.Gienko@srgroupllc.com',
                        subject='Reset Password Request',
                        html_content='Hello, '
                                     + 'We received a request to reset the password for your account for this email '
                                       'address. To initiate the password reset process for your account, '
                                       'click the link: '
                                     + reset_url
                                     + ' This link can only be used once. If you need to reset your password again, '
                                       'please request another reset. '
                                     + 'If you did not make this request, you can simply ignore this email.'
                                     + 'Sincerely,'
                                     + 'The Website Team'
                    )
                    try:
                        sg = SendGridAPIClient(os.environ.get('SENDGRID_KEY'))
                        response = sg.send(message)
                        print(response.status_code)
                        print(response.body)
                        print(response.headers)
                    except Exception as e:
                        print(e)
                    return redirect("/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password_reset.html",
                  context={"password_reset_form": password_reset_form})
