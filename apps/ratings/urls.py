from django.urls import path

from . import views

urlpatterns = [
    # uuid converter: a malformed id 404s at routing instead of raising
    # ValidationError inside the view.
    path("<uuid:profile_id>/", views.create_agent_review, name="create-rating"),
]
