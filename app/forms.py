from django.forms import modelformset_factory
from django import forms
from .models import *
from .widget import *

TimeSheetFormSet = modelformset_factory(TblTimeSheet,
                                        fields=(
                                            "date", "provider_id", "time_code", "hours", "type_id",
                                            "fye", "note"),
                                        extra=2, min_num=1,
                                        widgets={'date': DatePickerInput,
                                                 'hours': forms.NumberInput(attrs={'size': 5}),
                                                 'fye': DatePickerInput})

ToDoListFormSet = modelformset_factory(TblToDoList,
                                       fields=("date", "provider_id", "time_code", "fye", "note"),
                                       extra=2, min_num=1,
                                       widgets={'date': DatePickerInput,
                                                'note': forms.TextInput(attrs={'size': 50}),
                                                'fye': DatePickerInput})
