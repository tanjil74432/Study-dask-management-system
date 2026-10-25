
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import (
    Profile,
    Subject,
    Goal,
    StudySession,
    Note,
    Resource,
    Reminder,
)


# ==========================================
# Base Form Styling
# ==========================================

class BaseStyledForm:

    def apply_bootstrap_classes(self):

        for field in self.fields.values():

            css_class = "form-control"

            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                css_class = "form-select"

            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"

            if isinstance(field.widget, forms.ClearableFileInput):
                css_class = "form-control"

            old_class = field.widget.attrs.get("class", "")

            field.widget.attrs.update({
                "class": f"{old_class} {css_class}".strip(),
                "placeholder": field.label
            })


# ==========================================
# Register Form
# ==========================================

class RegisterForm(BaseStyledForm, forms.ModelForm):

    full_name = forms.CharField(
        max_length=100,
        required=False,
        label="Full name",
        help_text="Optional — shown on your profile."
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(),
        help_text="At least 8 characters, not all numbers, not a common password."
    )

    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email'
        ]

    def _init_(self, *args, **kwargs):

        super()._init_(*args, **kwargs)

        self.fields['email'].required = True

        self.order_fields([
            'full_name',
            'username',
            'email',
            'password',
            'confirm_password'
        ])

        self.apply_bootstrap_classes()

    def clean_username(self):

        username = self.cleaned_data.get('username', '').strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")

        return username

    def clean_email(self):

        email = self.cleaned_data.get('email', '').strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:

            self.add_error("confirm_password", "Passwords do not match.")

        # Run Django's AUTH_PASSWORD_VALIDATORS
        if password:
            temp_user = User(
                username=cleaned_data.get("username") or "",
                email=cleaned_data.get("email") or ""
            )
            try:
                validate_password(password, temp_user)
            except forms.ValidationError as error:
                self.add_error("password", error)

        return cleaned_data


# ==========================================
# Subject Form
# ==========================================

class SubjectForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = Subject

        fields = [
            "subject_name",
            "description"
        ]

        widgets = {

            "description": forms.Textarea(
                attrs={
                    "rows": 4
                }
            )

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()


# ==========================================
# Goal Form
# ==========================================

class GoalForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = Goal

        fields = [

            "subject",

            "goal_title",

            "deadline",

            "status"

        ]

        widgets = {

            "deadline": forms.DateInput(

                attrs={

                    "type": "date"

                }

            )

        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:

            self.fields["subject"].queryset = Subject.objects.filter(user=user)

        self.apply_bootstrap_classes()


# ==========================================
# Study Session Form
# ==========================================

class StudySessionForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = StudySession

        fields = [

            "subject",

            "start_time",

            "end_time"

        ]

        widgets = {

            "start_time": forms.DateTimeInput(

                attrs={

                    "type": "datetime-local"

                }

            ),

            "end_time": forms.DateTimeInput(

                attrs={

                    "type": "datetime-local"

                }

            )

        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:

            self.fields["subject"].queryset = Subject.objects.filter(user=user)

        self.apply_bootstrap_classes()

    def clean(self):

        cleaned_data = super().clean()

        start = cleaned_data.get("start_time")

        end = cleaned_data.get("end_time")

        if start and start > timezone.now():
            self.add_error("start_time", "Start time cannot be in the future.")

        if start and end:

            if end <= start:
                self.add_error("end_time", "End time must be after the start time.")

            elif (end - start).total_seconds() > 24 * 3600:
                self.add_error("end_time", "A single session cannot be longer than 24 hours.")

        return cleaned_data

        # ==========================================
# Note Form
# ==========================================

class NoteForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = Note

        fields = [

            "subject",

            "title",

            "content"

        ]

        widgets = {

            "content": forms.Textarea(

                attrs={

                    "rows": 6

                }

            )

        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:

            self.fields["subject"].queryset = Subject.objects.filter(user=user)

        self.apply_bootstrap_classes()


# ==========================================
# Resource Form
# ==========================================

class ResourceForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = Resource

        fields = [

            "subject",

            "type",

            "title",

            "link",

            "file"

        ]

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:

            self.fields["subject"].queryset = Subject.objects.filter(user=user)

        self.fields["link"].required = False

        self.fields["file"].required = False

        self.apply_bootstrap_classes()

    def clean(self):

        cleaned_data = super().clean()

        r_type = cleaned_data.get("type")

        link = cleaned_data.get("link")

        uploaded_file = cleaned_data.get("file")

        existing_file = self.instance.file if self.instance and self.instance.pk else None

        if r_type == "pdf" and not uploaded_file and not existing_file:

            raise forms.ValidationError(

                "Please upload a PDF file."

            )

        if r_type in ["youtube", "github", "other"] and not link:

            raise forms.ValidationError(

                "Please provide a valid link."

            )

        return cleaned_data


# ==========================================
# Reminder Form
# ==========================================

class ReminderForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = Reminder

        fields = [

            "goal",

            "remind_time",

            "message"

        ]

        widgets = {

            "remind_time": forms.DateTimeInput(

                attrs={

                    "type": "datetime-local"

                }

            ),

            "message": forms.Textarea(

                attrs={

                    "rows": 4

                }

            )

        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:

            self.fields["goal"].queryset = Goal.objects.filter(user=user)

        self.apply_bootstrap_classes()

        # ==========================================
# Profile Form
# ==========================================

class ProfileForm(BaseStyledForm, forms.ModelForm):

    username = forms.CharField(
        max_length=150,
        label="Username"
    )

    class Meta:

        model = Profile

        fields = [
            "photo",
            "full_name",
            "bio",
        ]

        widgets = {

            "bio": forms.Textarea(
                attrs={
                    "rows": 4
                }
            )

        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:
            self.fields["username"].initial = user.username

        self.apply_bootstrap_classes()

    def save(self, commit=True):

        profile = super().save(commit=False)

        if commit:
            profile.save()

        return profile


# ==========================================
# Email Change Form
# ==========================================

class EmailChangeForm(BaseStyledForm, forms.ModelForm):

    class Meta:

        model = User

        fields = [
            "email"
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()