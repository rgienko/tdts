from .models import *
import django_filters


class TimeSheetFilter(django_filters.FilterSet):
    class Meta:
        model = TblTimeSheet
        fields = ['employee_id']

    def __init__(self, *args, **kwargs):
        super(TimeSheetFilter, self).__init__(*args, **kwargs)
        if self.data == {}:
            self.queryset = self.queryset.none()
