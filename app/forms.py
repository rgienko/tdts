from django.forms import modelformset_factory, PasswordInput
from django import forms

from . import widget
from .models import *
from .widget import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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


class RegisterForm(forms.Form):
    username = forms.CharField(help_text='First.Last ex: Randall.Gienko', required=True)
    password1 = forms.CharField(widget=PasswordInput(), required=True)
    password2 = forms.CharField(widget=PasswordInput(), required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    # def clean(self):
    #    cleaned_data = super().clean()
    #    password1 = cleaned_data.get("password1")
    #    password2 = cleaned_data.get("password2")

    # if password1 != password2:
    #   raise ValidationError(
    #      "Passwords do not match."
    # )
