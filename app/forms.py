from django.forms import modelformset_factory
from django import forms
from .models import *
from .widget import *

TimeSheetFormSet = modelformset_factory(TblTimeSheet,
                                        fields=(
                                            "employee_id", "date", "provider_id", "time_code", "hours", "type_id",
                                            "fye", "note"),
                                        extra=2, min_num=1,
                                        widgets={'date': DatePickerInput, 'hours': forms.NumberInput,
                                                 'fye': DatePickerInput})
