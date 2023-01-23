from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from Website.views import *

urlpatterns = [
    path('', home, name='home'),
    path('register/', register_page, name='register'),
    path('login/', login_page, name='login'),
    path('profile/', profile_page, name='profile'),
    path('profile/settings/', edit_profile, name='profile_settings'),
    path('logout/', logout_user, name='logout'),
    path('profile/settings/password_change/', change_password, name='change_password'),
    path('profile/team/view/<int:team_id>/', view_team, name='view_team'),
    path('profile/team/invite/<int:team_id>/', invite, name='invite'),
    path('profile/team/accept_invitation/', accept_invitation, name='accept_invitation'),
    path('torunaments/open/', show_open_tournaments, name='open_tournament'),
    path('torunaments/view/<int:tournament_id>/', details_tournament, name='details_tournament'),
    path('torunaments/view/<int:tournament_id>/rules/', rules_tournament, name='rules_tournament'),
    path('torunaments/view/<int:tournament_id>/teams/', show_tournament_teams, name='teams_in_tournament'),
    path('torunaments/view/<int:tournament_id>/bracket/', show_tournament_bracket, name='bracket_in_tournament'),
    path('torunaments/view/<int:tournament_id>/match/<int:match_id>/', show_match_in_tournament,
         name='show_match_in_tournament'),
    path('ranking/', show_ranking_view, name='ranking-view'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
