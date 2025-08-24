from django.urls import path
from .views import (
    UserProfileView,
    InitializeUserPhasesView,
    UserPhaseListView,
    AnswerPhaseView,
    UserPhaseDetailView,
    EnterPhaseView,
    HintView,
)

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('init-phases/', InitializeUserPhasesView.as_view(), name='init-phases'),
    path('phases/', UserPhaseListView.as_view(), name='user-phases'),
    path('phases/<int:phase_number>/', UserPhaseDetailView.as_view(), name='user-phase-detail'),
    path("phases/<int:phase_number>/enter/", EnterPhaseView.as_view(), name="enter-phase"),
    path('phases/<int:phase_number>/answer/', AnswerPhaseView.as_view(), name='answer-phase'),
    path("hint/<int:phase_number>/", HintView.as_view(), name="phase-hint"),
]
