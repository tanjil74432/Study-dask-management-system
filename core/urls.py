from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path("settings/password/", views.password_change_view, name="password_change"),

    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    path('goals/', views.goal_list, name='goal_list'),
    path('goals/add/', views.goal_add, name='goal_add'),
    path('goals/<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:pk>/delete/', views.goal_delete, name='goal_delete'),

    path('sessions/', views.session_list, name='session_list'),
    path('sessions/add/', views.session_add, name='session_add'),
    path('sessions/<int:pk>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<int:pk>/delete/', views.session_delete, name='session_delete'),

    # Live study timer
    path('sessions/start/<int:subject_pk>/', views.session_start, name='session_start'),
    path('sessions/<int:pk>/stop/', views.session_stop, name='session_stop'),

    path('notes/', views.note_list, name='note_list'),
    path('notes/add/', views.note_add, name='note_add'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),

    path('resources/', views.resource_list, name='resource_list'),
    path('resources/add/', views.resource_add, name='resource_add'),
    path('resources/<int:pk>/open/', views.resource_open_pdf, name='resource_open_pdf'),
    path('resources/<int:pk>/edit/', views.resource_edit, name='resource_edit'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),

    path('reminders/', views.reminder_list, name='reminder_list'),
    path('reminders/add/', views.reminder_add, name='reminder_add'),
    path('reminders/<int:pk>/edit/', views.reminder_edit, name='reminder_edit'),
    path('reminders/<int:pk>/delete/', views.reminder_delete, name='reminder_delete'),
]