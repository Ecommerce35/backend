from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm, PasswordResetForm
from userauths.models import User, Profile
from django.contrib.auth import get_user_model
from tinymce.widgets import TinyMCE
from .validators import allow_only_images_validator


from vendor.models import *
# from captcha.fields import ReCaptchaField
# from captcha.widgets import ReCaptchaV2Checkbox

# forms.py
from django import forms

class EmailOrPhoneForm(forms.Form):
    email_or_phone = forms.CharField(max_length=254, required=True)

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")



class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password','password2']

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control my-2'

    def clean(self):
        cleaned_data = super(UserRegisterForm, self).clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password != password2:
            raise forms.ValidationError('Passwords do not match.')
        
class ProfileForm(forms.ModelForm):
    profile_image = forms.FileField(widget=forms.FileInput(attrs={'placeholder': 'profile image', 'style': 'padding-top: 0rem; line-height: 3.2;'}), validators=[allow_only_images_validator])
    cover_image = forms.FileField(widget=forms.FileInput(attrs={'placeholder': 'cover image', 'style': 'padding-top: 0rem; line-height: 3.2;'}), validators=[allow_only_images_validator])
    address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'address'}))

    class Meta:
        model = Profile
        fields = ['profile_image', 'cover_image', 'address']

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control my-2'

class AboutForm(forms.ModelForm):
    profile_image = forms.ImageField(widget=forms.FileInput(attrs={'placeholder': 'profile image', 'style': 'padding-top: 0rem; line-height: 3.2;'}), validators=[allow_only_images_validator])
    cover_image = forms.ImageField(widget=forms.FileInput(attrs={'placeholder': 'cover image', 'style': 'padding-top: 0rem; line-height: 3.2;'}), validators=[allow_only_images_validator])
    address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'address'}))
    shipping_on_time = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'address'}))
    chat_resp_time = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'address'}))
    facebook_url = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Link to your facebook'}))
    instagram_url = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Link to your Instagram'}))
    twitter_url = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Link to your Twitter'}))
    linkedin_url = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Link to your LinkedIn'}))

    class Meta:
        model = About
        fields = ['profile_image', 'cover_image', 'address','shipping_on_time', 'chat_resp_time','facebook_url','instagram_url','linkedin_url','twitter_url']

    def __init__(self, *args, **kwargs):
        super(AboutForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control my-2'


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))

    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}))

    # captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())


class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = get_user_model() 
        fields = ['new_password1', 'new_password2']

class PasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
    # captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

