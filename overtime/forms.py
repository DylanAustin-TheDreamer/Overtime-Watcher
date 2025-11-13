from django import forms
from .utils.timezones import timezone_choices

class TimezoneForm(forms.Form):
    timezone = forms.ChoiceField(choices=timezone_choices(), label="Time zone", required=True)