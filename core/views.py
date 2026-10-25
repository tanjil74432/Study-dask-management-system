from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from django.db.models import Sum , Q

from django.utils import timezone

from django.contrib.auth.forms import PasswordChangeForm

from django.contrib.auth import update_session_auth_hash

from django.http import FileResponse,Http404
import datetime
import os
import mimetypes

from .forms import (

    RegisterForm, SubjectForm, GoalForm, StudySessionForm,

    NoteForm, ResourceForm, ReminderForm, ProfileForm,

    EmailChangeForm,

)

from .models import Profile, Subject, Goal, StudySession, Note, Resource, Reminder

MAX_SESSION_HOURS = 12


def discard_stale_sessions(user):
    """Remove timers that were started but never stopped (forgotten tabs)."""
    cutoff = timezone.now() - datetime.timedelta(hours=MAX_SESSION_HOURS)
    StudySession.objects.filter(
        user=user, end_time__isnull=True, start_time__lt=cutoff
    ).delete()

def format_minutes(minutes):
    """Turn a minute count into a short '2h 15m' style label."""
    minutes = minutes or 0
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f'{hours}h {mins}m'
    if hours:
        return f'{hours}h'
    return f'{mins}m'

def register_view(request):

    if request.user.is_authenticated:

        return redirect('dashboard')

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(form.cleaned_data['password'])

            user.save()

            Profile.objects.create(user=user, full_name=form.cleaned_data.get('full_name', ''))

            messages.success(request, 'Account created successfully, please login')

            return redirect('login')

        messages.error(request, 'Please fix the errors below')

    else:

        form = RegisterForm()

    return render(request, 'core/register.html', {'form': form})

def login_view(request):

    if request.user.is_authenticated:

        return redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username')

        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:

            login(request, user)

            return redirect('dashboard')

        else:

            messages.error(request, 'Invalid username or password')

    return render(request, 'core/login.html')

def logout_view(request):

    """Logout only accepts POST so it cannot be triggered by a stray link/image."""

    if request.method == 'POST':

        logout(request)

        messages.success(request, 'You have been logged out successfully')

    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    discard_stale_sessions(user)

    total_subjects = Subject.objects.filter(user=user).count()
    total_goals = Goal.objects.filter(user=user).count()

    total_minutes = StudySession.objects.filter(user=user).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
    total_hours = round(total_minutes / 60, 2)
    total_time_label = format_minutes(total_minutes)

    today = timezone.localtime().date()
    today_minutes = StudySession.objects.filter(user=user, start_time__date=today).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
    today_hours = round(today_minutes / 60, 2)
    today_time_label = format_minutes(today_minutes)

    recent_sessions = StudySession.objects.filter(user=user).order_by('-start_time')[:5]

    subjects = Subject.objects.filter(user=user).order_by('subject_name').annotate(
        studied_total=Sum('studysession__duration_minutes'),
        studied_today=Sum(
            'studysession__duration_minutes',
            filter=Q(studysession__start_time__date=today)
        ),
    )

    running = StudySession.objects.filter(user=user, end_time__isnull=True)
    running_map = {s.subject_id: s for s in running}

    subject_data = [
        {
            'subject': s,
            'active_session': running_map.get(s.id),
            'today_label': format_minutes(s.studied_today),
            'total_label': format_minutes(s.studied_total),
            'total_minutes': s.studied_total or 0,
        }
        for s in subjects
    ]

    # Breakdown bars: longest-studied subject fills the bar, rest scale against it
    busiest = max([d['total_minutes'] for d in subject_data], default=0)

    for d in subject_data:
        d['percent'] = round(d['total_minutes'] / busiest * 100) if busiest else 0

    time_breakdown = sorted(
        subject_data, key=lambda d: d['total_minutes'], reverse=True
    )

    context = {
        'subject_data': subject_data,
        'time_breakdown': time_breakdown,
        'total_subjects': total_subjects,
        'total_goals': total_goals,
        'total_hours': total_hours,
        'total_time_label': total_time_label,
        'today_time_label': today_time_label,
        'today_minutes': today_minutes,
        'today_hours': today_hours,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'core/dashboard.html', context)

@login_required

def profile_view(request):

    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        form = ProfileForm(

            request.POST,

            request.FILES,

            instance=profile,

            user=request.user,

        )

        if form.is_valid():

            profile = form.save(commit=False)

            request.user.username = form.cleaned_data["username"]

            request.user.save()

            profile.save()

            messages.success(request, "Profile updated successfully.")

            return redirect("profile")

    else:

        form = ProfileForm(

            instance=profile,

            user=request.user,

        )

    return render(

        request,

        "core/profile.html",

        {

            "form": form,

        },

    )

@login_required

def settings_view(request):

    if request.method == "POST":

        email_form = EmailChangeForm(

            request.POST,

            instance=request.user

        )

        if email_form.is_valid():

            email_form.save()

            messages.success(

                request,

                "Email updated successfully."

            )

            return redirect("settings")

    else:

        email_form = EmailChangeForm(

            instance=request.user

        )

    return render(

        request,

        "core/settings.html",

        {

            "email_form": email_form,

        },

    )

@login_required

def password_change_view(request):

    if request.method == "POST":

        form = PasswordChangeForm(

            request.user,

            request.POST

        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(

                request,

                user

            )

            messages.success(

                request,

                "Password changed successfully."

            )

            return redirect("settings")

    else:

        form = PasswordChangeForm(

            request.user

        )

    return render(

        request,

        "core/password_change.html",

        {

            "form": form

        },

    )

@login_required
def subject_list(request):
    today = timezone.now().date()

    subjects = Subject.objects.filter(user=request.user).annotate(
        studied_total=Sum('studysession__duration_minutes'),
        studied_today=Sum(
            'studysession__duration_minutes',
            filter=Q(studysession__start_time__date=today)
        ),
    )

    subject_data = [
        {
            'subject': s,
            'today_label': format_minutes(s.studied_today),
            'total_label': format_minutes(s.studied_total),
        }
        for s in subjects
    ]

    return render(request, 'core/subject_list.html', {'subject_data': subject_data})

@login_required

def subject_add(request):

    if request.method == 'POST':

        form = SubjectForm(request.POST)

        if form.is_valid():

            subject = form.save(commit=False)

            subject.user = request.user

            subject.save()

            messages.success(request, 'Subject added successfully')

            return redirect('subject_list')

    else:

        form = SubjectForm()

    return render(request, 'core/subject_form.html', {'form': form, 'title': 'Add Subject'})

@login_required

def subject_edit(request, pk):

    subject = get_object_or_404(Subject, pk=pk, user=request.user)

    if request.method == 'POST':

        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():

            form.save()

            messages.success(request, 'Subject updated successfully')

            return redirect('subject_list')

    else:

        form = SubjectForm(instance=subject)

    return render(request, 'core/subject_form.html', {'form': form, 'title': 'Edit Subject'})

@login_required

def subject_delete(request, pk):

    subject = get_object_or_404(Subject, pk=pk, user=request.user)

    subject.delete()

    messages.success(request, 'Subject deleted successfully')

    return redirect('subject_list')

@login_required

def goal_list(request):

    goals = Goal.objects.filter(user=request.user)

    return render(request, 'core/goal_list.html', {'goals': goals})

@login_required

def goal_add(request):

    if request.method == 'POST':

        form = GoalForm(request.POST, user=request.user)

        if form.is_valid():

            goal = form.save(commit=False)

            goal.user = request.user

            goal.save()

            messages.success(request, 'Goal added successfully')

            return redirect('goal_list')

    else:

        form = GoalForm(user=request.user)

    return render(request, 'core/goal_form.html', {'form': form, 'title': 'Add Goal'})

@login_required

def goal_edit(request, pk):

    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == 'POST':

        form = GoalForm(request.POST, instance=goal, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Goal updated successfully')

            return redirect('goal_list')

    else:

        form = GoalForm(instance=goal, user=request.user)

    return render(request, 'core/goal_form.html', {'form': form, 'title': 'Edit Goal'})

@login_required

def goal_delete(request, pk):

    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    goal.delete()

    messages.success(request, 'Goal deleted successfully')

    return redirect('goal_list')

@login_required

def session_list(request):

    sessions = StudySession.objects.filter(user=request.user).order_by('-start_time')

    return render(request, 'core/session_list.html', {'sessions': sessions})

@login_required

def session_add(request):

    if request.method == 'POST':

        form = StudySessionForm(request.POST, user=request.user)

        if form.is_valid():

            session = form.save(commit=False)

            session.user = request.user

            if session.start_time and session.end_time:

                delta = session.end_time - session.start_time

                session.duration_minutes = int(delta.total_seconds() / 60)

            session.save()

            messages.success(request, 'Study session saved successfully')

            return redirect('session_list')

    else:

        form = StudySessionForm(user=request.user)

    return render(request, 'core/session_form.html', {'form': form, 'title': 'Add Study Session'})

@login_required

def session_edit(request, pk):

    session = get_object_or_404(StudySession, pk=pk, user=request.user)

    if request.method == 'POST':

        form = StudySessionForm(request.POST, instance=session, user=request.user)

        if form.is_valid():

            session = form.save(commit=False)

            if session.start_time and session.end_time:

                delta = session.end_time - session.start_time

                session.duration_minutes = int(delta.total_seconds() / 60)

            session.save()

            messages.success(request, 'Study session updated successfully')

            return redirect('session_list')

    else:

        form = StudySessionForm(instance=session, user=request.user)

    return render(request, 'core/session_form.html', {'form': form, 'title': 'Edit Study Session'})

@login_required

def session_delete(request, pk):

    session = get_object_or_404(StudySession, pk=pk, user=request.user)

    session.delete()

    messages.success(request, 'Study session deleted successfully')

    return redirect('session_list')

@login_required

def session_start(request, subject_pk):

    subject = get_object_or_404(Subject, pk=subject_pk, user=request.user)

    if request.method != 'POST':

        return redirect('dashboard')

    running = StudySession.objects.filter(user=request.user, end_time__isnull=True).first()

    if running:

        messages.error(request, f'A timer is already running for {running.subject.subject_name}. Stop it first.')

        return redirect('dashboard')

    StudySession.objects.create(user=request.user, subject=subject, start_time=timezone.now())

    messages.success(request, f'Timer started for {subject.subject_name}')

    return redirect('dashboard')

@login_required

def session_stop(request, pk):

    session = get_object_or_404(StudySession, pk=pk, user=request.user, end_time__isnull=True)

    if request.method != 'POST':

        return redirect('dashboard')

    session.end_time = timezone.now()

    delta = session.end_time - session.start_time

    session.duration_minutes = max(0, int(delta.total_seconds() // 60))

    session.save()

    messages.success(request, f'Saved {session.duration_minutes} min on {session.subject.subject_name}')

    return redirect('dashboard')

@login_required

def note_list(request):

    notes = Note.objects.filter(subject__user=request.user)

    return render(request, 'core/note_list.html', {'notes': notes})

@login_required

def note_add(request):

    if request.method == 'POST':

        form = NoteForm(request.POST, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Note added successfully')

            return redirect('note_list')

    else:

        form = NoteForm(user=request.user)

    return render(request, 'core/note_form.html', {'form': form, 'title': 'Add Note'})

@login_required

def note_edit(request, pk):

    note = get_object_or_404(Note, pk=pk, subject__user=request.user)

    if request.method == 'POST':

        form = NoteForm(request.POST, instance=note, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Note updated successfully')

            return redirect('note_list')

    else:

        form = NoteForm(instance=note, user=request.user)

    return render(request, 'core/note_form.html', {'form': form, 'title': 'Edit Note'})

@login_required

def note_delete(request, pk):

    note = get_object_or_404(Note, pk=pk, subject__user=request.user)

    note.delete()

    messages.success(request, 'Note deleted successfully')

    return redirect('note_list')

@login_required

def resource_list(request):

    resources = Resource.objects.filter(subject__user=request.user)

    return render(request, 'core/resource_list.html', {'resources': resources})

@login_required

def resource_add(request):

    if request.method == 'POST':

        form = ResourceForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Resource added successfully')

            return redirect('resource_list')

    else:

        form = ResourceForm(user=request.user)

    return render(request, 'core/resource_form.html', {'form': form, 'title': 'Add Resource'})

@login_required

def resource_edit(request, pk):

    resource = get_object_or_404(Resource, pk=pk, subject__user=request.user)

    if request.method == 'POST':

        form = ResourceForm(request.POST, request.FILES, instance=resource, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Resource updated successfully')

            return redirect('resource_list')

    else:

        form = ResourceForm(instance=resource, user=request.user)

    return render(request, 'core/resource_form.html', {'form': form, 'title': 'Edit Resource'})

@login_required

def resource_delete(request, pk):

    resource = get_object_or_404(Resource, pk=pk, subject__user=request.user)

    resource.delete()

    messages.success(request, 'Resource deleted successfully')

    return redirect('resource_list')

@login_required

def reminder_list(request):

    reminders = Reminder.objects.filter(user=request.user).order_by('remind_time')

    return render(request, 'core/reminder_list.html', {'reminders': reminders})

@login_required

def reminder_add(request):

    if request.method == 'POST':

        form = ReminderForm(request.POST, user=request.user)

        if form.is_valid():

            reminder = form.save(commit=False)

            reminder.user = request.user

            reminder.save()

            messages.success(request, 'Reminder added successfully')

            return redirect('reminder_list')

    else:

        form = ReminderForm(user=request.user)

    return render(request, 'core/reminder_form.html', {'form': form, 'title': 'Add Reminder'})

@login_required

def reminder_edit(request, pk):

    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)

    if request.method == 'POST':

        form = ReminderForm(request.POST, instance=reminder, user=request.user)

        if form.is_valid():

            form.save()

            messages.success(request, 'Reminder updated successfully')

            return redirect('reminder_list')

    else:

        form = ReminderForm(instance=reminder, user=request.user)

    return render(request, 'core/reminder_form.html', {'form': form, 'title': 'Edit Reminder'})

@login_required

def reminder_delete(request, pk):

    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)

    reminder.delete()

    messages.success(request, 'Reminder deleted successfully')

    return redirect('reminder_list')


@login_required
def resource_open_pdf(request, pk):
    """Serve an uploaded resource file, but only to the user who owns it."""
    resource = get_object_or_404(Resource, pk=pk, subject__user=request.user)

    if not resource.file:
        raise Http404('This resource has no file attached.')

    try:
        handle = resource.file.open('rb')
    except (FileNotFoundError, ValueError):
        raise Http404('The file is missing from the server.')

    filename = os.path.basename(resource.file.name)

    content_type, _ = mimetypes.guess_type(filename)
    content_type = content_type or 'application/octet-stream'

    # ?download=1 forces a save-as instead of opening in the browser
    as_attachment = request.GET.get('download') == '1'

    return FileResponse(
        handle,
        content_type=content_type,
        as_attachment=as_attachment,
        filename=filename,
    )