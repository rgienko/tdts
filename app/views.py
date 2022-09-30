from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
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

    context['today'] = today
    context['week_beg'] = week_beg
    context['week_end'] = week_end

    return render(request, 'index.html', context)


class TimesheetView(TemplateView):
    template_name = 'timesheet.html'

    today = date.today()
    week_beg = today - timedelta(days=today.weekday())
    week_end = week_beg + timedelta(days=5)

    def get(self, *args, **kwargs):
        formset = TimeSheetFormSet(queryset=TblTimeSheet.objects.none(),
                                   initial=[{'employee_id': self.request.user.username}])

        current_timesheet = TblTimeSheet.objects.filter(employee_id=self.request.user.username).filter(
            date__lte=self.week_end).filter(date__gte=self.week_beg).order_by('date')

        fixed_hours = current_timesheet.filter(type_id='F').aggregate(sum_of_hours=Sum('hours'))
        hourly_hours = current_timesheet.filter(type_id='H').aggregate(sum_of_hours=Sum('hours'))
        contigency_hours = current_timesheet.filter(type_id='C').aggregate(sum_of_hours=Sum('hours'))
        non_hours = current_timesheet.filter(type_id='N').aggregate(sum_of_hours=Sum('hours'))

        total_hours = current_timesheet.aggregate(sum_of_hours=Sum('hours'))

        return self.render_to_response({'timesheet_formset': formset, 'current_timesheet': current_timesheet,
                                        'today': self.today, 'week_beg': self.week_beg, 'week_end': self.week_end,
                                        'fixed_hours': fixed_hours, 'total_hours': total_hours, 'hourly_hours': hourly_hours,
                                        'contigency_hours': contigency_hours, 'non_hours': non_hours})

    def post(self, *args, **kwargs):
        formset = TimeSheetFormSet(data=self.request.POST,
                                   initial=[{'employee_id': self.request.user.username}])

        if formset.is_valid():
            formset.save()
            return redirect(reverse_lazy('timesheet'))

        return self.render_to_response({'timesheet_formset': formset})
