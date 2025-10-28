from django import forms
from tinymce.widgets import TinyMCE


class NewsletterForm(forms.Form):
    subject = forms.CharField(max_length=100)
    receivers = forms.CharField()
    message = forms.CharField(widget=TinyMCE(), label="Email content")
