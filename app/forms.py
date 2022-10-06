from django.forms import modelformset_factory
from django import forms
from .models import *
from .widget import *
from django.utils.translation import gettext_lazy as _

TimeSheetFormSet = modelformset_factory(TblTimeSheet,
                                        fields=(
                                            "date", "provider_id", "time_code", "hours", "type_id",
                                            "fye", "note"),
                                        extra=2, min_num=1,
                                        widgets={'date': DatePickerInput,
                                                 'hours': forms.NumberInput(attrs={'size': 5}),
                                                 'fye': DatePickerInput})

ToDoListFormSet = modelformset_factory(TblToDoList,
                                       fields=("date", "end", "provider_id", "time_code", "fye", "note"),
                                       extra=2, min_num=1,
                                       widgets={'date': DatePickerInput,
                                                'fye': DatePickerInput,
                                                'end': DatePickerInput,
                                                'note': forms.TextInput(attrs={'size': 50})})


class EditFormToDo(forms.ModelForm):
    class Meta:
        model = TblToDoList

        fields = ['employee_id', 'date', 'end', 'provider_id', 'time_code', 'fye', 'note']

        labels = {
            'employee_id': _('Employee'),
            'date': _('Date'),
            'end': _('End'),
            'provider_id': _('Provider'),
            'time_code': _('Time Code'),
            'fye': _('FYE'),
            'note': _('Note')
        }
