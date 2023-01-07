import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group, User
from django.shortcuts import render, redirect, get_object_or_404
import random

from .decorators import unauthenticated_user
from .forms import CreateUserForm, EditUserProfileSettingsForm, CreateTeamForm
from .models import *
from .utilities import send_invitation, send_invitation_accepted


# from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    context = {}
    return render(request, 'index.html', context)


@unauthenticated_user
def register_page(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.get(name='user')
            user.groups.add(group)
            Profile.objects.create(
                user=user,
            )
            # user = form.cleaned_data.get('username')
            messages.success(request, 'Account created')
            return redirect('login')

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


@unauthenticated_user
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        print(username)
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            email = request.user.email
            invitations = Invitation.objects.filter(email=email, status=Invitation.INVITED)

            if invitations:
                return redirect('home')
            else:
                return redirect('home')
        else:
            messages.info(request, 'Username or password is incorrect')

    context = {}
    return render(request, 'accounts/login.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def profile_page(request):
    form = CreateTeamForm(request.POST)
    teams = request.user.teams.all()
    gamesWon = request.user.profile.gamesWon
    gamesPlayed = request.user.profile.gamesPlayed
    invitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    if invitations:
        messages.info(request, 'Masz oczekujące zaproszenie do drużyny')

    def check_winrate():
        if gamesPlayed > 0:
            value = "%.2f" % ((gamesWon / gamesPlayed) * 100)
        else:
            value = 0
        return value

    winratePercentage = check_winrate()

    if request.method == 'POST':
        teamName = request.POST.get('teamName')
        nameExists = Team.objects.filter(teamName=teamName).count()
        if form.is_valid() and nameExists == 0:
            team = Team.objects.create(teamName=teamName, createdBy=request.user)
            team.members.add(request.user)
            team.save()
            messages.success(request, 'Stworzono drużynę')
            # userprofile = request.user.userprofile
            # userprofile.active_team_id = team.id
            # userprofile.save()
            return redirect('profile')
        else:
            messages.error(request, 'Wprowadzona nazwa jest juz zajęta')
    else:
        form = CreateTeamForm(request.user)

    context = {'form': form,
               'winratePercentage': winratePercentage,
               'teams': teams,
               'invitations': invitations}
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    profile = request.user.profile
    form = EditUserProfileSettingsForm(instance=profile)

    if request.method == 'POST':
        form = EditUserProfileSettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            messages.success(request, 'Pomyślnie zmieniono dane')
            return redirect('profile_settings')
        else:
            messages.error(request, 'Wprowadzona nazwa jest juz zajęta')

    context = {'form': form}
    return render(request, 'accounts/profile_settings.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_settings')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {
        'form': form
    })


@login_required
def view_team(request, team_id):
    team = get_object_or_404(Team, pk=team_id, members__in=[request.user])
    invitations = Invitation.objects.filter(status='Invited', team=team)
    context = {'team': team,
               'invitations': invitations}

    if request.method == 'POST':
        if 'cancel' in request.POST:
            if invitations:
                invitation = invitations[0]
                invitation.status = Invitation.CANCELLED
                invitation.save()
                messages.info(request, 'Zaproszenie anulowane')
                return redirect('view_team', team_id=team_id)

        if 'update' in request.POST:
            teamName = request.POST.get('teamName')

            nameExists = Team.objects.filter(teamName=teamName).count()
            if nameExists == 0:
                team.teamName = teamName
                team.save()

                messages.success(request, 'Nazwa drużyny została zmieniona')
                return redirect('view_team', team_id=team_id)
            else:
                messages.error(request, 'Wprowadzona nazwa jest juz zajęta')
        if 'delete_member' in request.POST:
            try:
                user = User.objects.get(username=request.POST.get('username'))
                if team.members.filter(teams__members__in=[user.id]):
                    team.members.remove(user.id)
                    team.save()

                    invitations = Invitation.objects.filter(team=team, email=user.email)
                    if invitations:
                        Invitation.objects.filter(team=team, email=user.email).delete()

                    messages.success(request, 'Usunięto użytkownika')
                else:
                    messages.error(request, 'Użytkownik nie znajduje sie w drużynie')
            except:
                messages.error(request, 'Nie ma takiego użytkownika')

    return render(request, 'teams/view_team.html', context)


@login_required
def invite(request, team_id):
    team = get_object_or_404(Team, pk=team_id, members__in=[request.user])
    try:
        if request.method == 'POST':
            email = request.POST.get('email')
            user = User.objects.get(email__exact=email)

            if email:
                invitations = Invitation.objects.filter(team=team, email=email)

                if not invitations:
                    code = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz123456789') for _ in range(4))
                    status = 'Invited'
                    Invitation.objects.create(team=team, email=email, code=code, user=user, status=status)

                    messages.info(request, 'Zaproszenie zsotało wysłane')
                    send_invitation(email, code, team)

                    return redirect('view_team', team_id=team_id)
                if invitations:
                    if invitations.filter(status=Invitation.CANCELLED) or invitations.filter(
                            status=Invitation.DECLINED):
                        code = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz123456789') for _ in range(4))
                        status = 'Invited'
                        Invitation.objects.update(team=team, email=email, code=code, user=user, status=status)

                        messages.info(request, 'Zaproszenie zsotało wysłane')
                        send_invitation(email, code, team)

                        return redirect('view_team', team_id=team_id)
                    if invitations.filter(status=Invitation.ACCEPTED):
                        messages.error(request, 'Użytkownik znajduje się już w drużynie')
                    else:
                        messages.error(request, 'Użytkownik został już wcześniej zaproszony')
    except:
        messages.error(request, 'Błędny adres e-mail')
    return render(request, 'teams/invite.html', {'team': team})


@login_required
def accept_invitation(request):
    invitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    if invitations:
        def show_invited_team_names():
            invitations = Invitation.objects.filter(status="Invited")
            listOfTeamsNames = []
            if invitations:
                teamNames = invitations.values('team__teamName')
                for key in range(len(teamNames)):
                    teamName = [a for a in teamNames[key].values()]
                    listOfTeamsNames.append(teamName[0])
            return listOfTeamsNames

        listOfTeamsNames = show_invited_team_names()

        if request.method == 'POST':
            code = request.POST.get('code')

            invitations = Invitation.objects.filter(code=code, email=request.user.email)

            if 'accept' in request.POST:
                if invitations.filter(status='Invited'):
                    invitation = invitations[0]
                    invitation.status = Invitation.ACCEPTED
                    invitation.save()

                    team = invitation.team
                    team.members.add(request.user)
                    team.save()

                    messages.info(request, 'Dołączyłeś do drużyny')

                    send_invitation_accepted(team, invitation)

                    return redirect('profile')
                else:
                    messages.error(request, 'Błędny kod')
                    return redirect('accept_invitation')

            if 'decline' in request.POST:
                if invitations:
                    invitation = invitations[0]
                    invitation.status = Invitation.DECLINED
                    invitation.save()

                    messages.info(request, 'Zaproszenie odrzucone')
                    return redirect('profile')
        else:
            return render(request, 'teams/accept_invitation.html', {'listOfTeamsNames': listOfTeamsNames})

    messages.info(request, 'Nie masz żadnych zaproszeń')
    return redirect('profile')


def show_tournaments(request):
    tournaments = Tournament.objects.all()
    context = {'tournaments': tournaments}

    return render(request, 'tournaments/tournaments.html', context)


def details_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    context = {'tournament': tournament}

    return render(request, 'tournaments/tournament_view.html', context)
