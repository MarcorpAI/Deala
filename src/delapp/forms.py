from django import forms
from .models import UserQuery, Waitlist


class EnterQueryForm(forms.ModelForm):
    class Meta:
        model = UserQuery
        fields  = ["query"]



class WaitlistForm(forms.ModelForm):
    class Meta:
        model = Waitlist
        fields = ["name", "email",]