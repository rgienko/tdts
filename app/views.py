from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.db.models import Sum
import pendulum
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from .forms import *
from .models import *


# Create your views here.
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('main')
        else:
            messages.error(request, 'Error, wrong username or password')
        return render(request, 'login.html')

    return render(request, 'login.html')


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


class TimesheetView(TemplateView):
    template_name = 'timesheet.html'

    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)
    thirty = date.today() - timedelta(days=30)

    def get(self, *args, **kwargs):
        # formset = TimeSheetFormSet(queryset=TblTimeSheet.objects.none(),
        #                          initial=[{'employee_id': self.request.user.username}])

        formset = TimeSheetFormSet(queryset=TblTimeSheet.objects.none())

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

        top_projects = thirty_timesheet.values('provider_id', 'provider_id__provider_name', 'time_code', 'fye', 'time_code_id__time_code_description').annotate(sum_of_project_hours=Sum('hours')).order_by('-sum_of_project_hours')[:5]

        return self.render_to_response({'timesheet_formset': formset, 'current_timesheet': current_timesheet,
                                        'today': self.today, 'week_beg': self.week_beg, 'week_end': self.week_end,
                                        'total_hours': total_hours, 'fixed_hours': fixed_hours,
                                        'hourly_hours': hourly_hours,
                                        'contingency_hours': contingency_hours, 'non_hours': non_hours,
                                        'thirty_fixed_hours': thirty_fixed_hours,
                                        'thirty_hourly_hours': thirty_hourly_hours,
                                        'thirty_contingency_hours': thirty_contingency_hours,
                                        'thirty_non_hours': thirty_non_hours,
                                        'top_projects': top_projects})

    def post(self, *args, **kwargs):
        formset = TimeSheetFormSet(data=self.request.POST)
        print(get_object_or_404(TblEmployee, pk=self.request.user.username).employee_id)

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.employee_id = get_object_or_404(TblEmployee, pk=self.request.user.username)
                instance.save()
            return redirect(reverse_lazy('timesheet'))

        return self.render_to_response({'timesheet_formset': formset})
