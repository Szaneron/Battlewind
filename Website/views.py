import datetime
import json
import random
from datetime import date, datetime

import pandas as pd
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404

from Website import image_verification
from .decorators import unauthenticated_user
from .forms import CreateUserForm, EditUserProfileSettingsForm, CreateTeamForm, UploadImageToVeryficate
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
                if user.profile.summonerName != None:
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
                else:
                    messages.error(request, "Użytkownik musi podać nazwę przywoływacza w swoim profilu")
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


def show_open_tournaments(request):
    tournaments = Tournament.objects.filter(status='in_progress').order_by('time' and 'date')
    context = {'tournaments': tournaments}

    return render(request, 'tournaments/tournaments_open.html', context)


def show_closed_tournaments(request):
    tournaments = Tournament.objects.filter(status='completed').order_by('time' and 'date')
    context = {'tournaments': tournaments}

    return render(request, 'tournaments/tournament_close.html', context)


@login_required
def details_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    teams = Team.objects.filter(createdBy=request.user)

    def check_teams():
        teamsInTournament = 0
        for _ in teams:
            if tournament.registeredTeams.filter(registeredTeams__registeredTeams=_.id):
                teamsInTournament += 1
        return teamsInTournament

    dateTime = tournament.date.strftime("%d-%m-%Y")
    hourTime = tournament.time.strftime("%H:%M:%S")
    currentDate = date.today()
    currentDate = pd.to_datetime(currentDate).date()
    currentDate = currentDate.strftime("%d-%m-%Y")
    currentTime = datetime.now()
    currentTime = pd.to_datetime(currentTime).time()
    currentTime = currentTime.strftime("%H:%M:%S")

    teamsInTournament = check_teams()

    if request.method == 'POST':
        if 'join' in request.POST:

            if currentDate <= dateTime and currentTime < hourTime:
                team = Team.objects.get(teamName=request.POST.get('teamName'))
                if teamsInTournament == 0:
                    if tournament.registeredTeams.count() < 4:
                        tournament.registeredTeams.add(team.id)
                        tournament.save()
                        messages.success(request, "Drużyna dołączyła do turnieju")
                    else:
                        messages.error(request, 'Nie ma już wolnych miejsc dla nowej drużyny')
                else:
                    messages.error(request, 'Zapisałeś już jedną swoją drużynę')
            else:
                messages.error(request, 'Turniej się już rozpoczął. Nie ma już możliwości dołączenia')

    context = {'tournament': tournament, 'teams': teams, 'dateTime': dateTime, 'hourTime': hourTime,
               'currentTime': currentTime, 'currentDate': currentDate}
    return render(request, 'tournaments/tournament_view.html', context)


@login_required
def show_tournament_teams(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    teams = Team.objects.filter(createdBy=request.user)
    dateTime = tournament.date.strftime("%d-%m-%Y")
    hourTime = tournament.time.strftime("%H:%M:%S")
    currentDate = date.today()
    currentDate = pd.to_datetime(currentDate).date()
    currentDate = currentDate.strftime("%d-%m-%Y")
    currentTime = datetime.now()
    currentTime = pd.to_datetime(currentTime).time()
    currentTime = currentTime.strftime("%H:%M:%S")

    def check_teams():
        teamInfo = ['name', 0]
        for _ in teams:
            if tournament.registeredTeams.filter(registeredTeams__registeredTeams=_.id):
                teamInfo[0] = _
                teamInfo[1] = 1
        return teamInfo

    if request.method == 'POST':
        if 'leave' in request.POST:
            if currentDate <= dateTime and currentTime < hourTime:
                teamName = check_teams()[0]
                tournament.registeredTeams.remove(teamName.id)
                messages.success(request, 'Drużyna wypisana z turnieju')

            else:
                messages.error(request, 'Turniej się już rozpoczął. Nie ma już możliwości opuszczenia')

        if 'join' in request.POST:
            if currentDate <= dateTime and currentTime < hourTime:
                team = Team.objects.get(teamName=request.POST.get('teamName'))
                if team.members.count() != 5:
                    messages.error(request, 'Drużyna nie posaida 5 zawodników')
                else:
                    teamInTournament = check_teams()[1]
                    if teamInTournament == 0:
                        if tournament.registeredTeams.count() < tournament.maxTeams:
                            tournament.registeredTeams.add(team.id)
                            tournament.save()
                            messages.success(request, "Drużyna dołączyła do turnieju")
                        else:
                            messages.error(request, 'Nie ma już wolnych miejsc dla nowej drużyny')
                    else:
                        messages.error(request, 'Zapisałeś już jedną swoją drużynę')
            else:
                messages.error(request, 'Turniej się już rozpoczął. Nie ma już możliwości dołączenia')

    context = {'tournament': tournament, 'teams': teams, 'dateTime': dateTime, 'hourTime': hourTime,
               'currentTime': currentTime, 'currentDate': currentDate}

    return render(request, 'tournaments/teams_in_tournament.html', context)


@login_required
def show_tournament_bracket(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    matches = Match.objects.filter(tournamentName=tournament.id)
    teams = Team.objects.filter(members__in=[request.user])
    dateTime = tournament.date.strftime("%d-%m-%Y")
    hourTime = tournament.time.strftime("%H:%M:%S")
    currentDate = date.today()
    currentDate = pd.to_datetime(currentDate).date()
    currentDate = currentDate.strftime("%d-%m-%Y")
    currentTime = datetime.now()
    currentTime = pd.to_datetime(currentTime).time()
    currentTime = currentTime.strftime("%H:%M:%S")

    if currentDate <= dateTime and currentTime < hourTime:
        messages.error(request, 'Drabinka nie jest jeszcze gotowa, poczekaj na rozpoczęcie turnieju')
    else:
        if not matches:
            tournament = get_object_or_404(Tournament, pk=tournament.id)
            tournamentTeamList = [tournament for tournament in tournament.registeredTeams.all()]

            def grouped(iterable, n):
                "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
                return zip(*[iter(iterable)] * n)

            if tournament.registeredTeams.count() <= 4:
                matchCounter = 0
                counter = 1
                if len(tournamentTeamList) % 2 == 0:
                    for team1, team2 in grouped(tournamentTeamList, 2):
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.teamsInMatch.add(team1, team2)
                        teams.save
                        matchCounter += 1
                        counter += 1

                    while matchCounter != 4:
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.save()
                        matchCounter += 1
                        counter += 1
                else:
                    for team1, team2 in grouped(tournamentTeamList, 2):
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.teamsInMatch.add(team1, team2)
                        teams.save
                        matchCounter += 1
                        counter += 1

                    while matchCounter != 4:
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.save()
                        matchCounter += 1
                        counter += 1

                    lastTeam = str(tournamentTeamList[len(tournamentTeamList) - 1])
                    print(lastTeam)
                    lastTeamObject = Team.objects.get(teamName=lastTeam)

                    nextEmptyCreatedMatch = Match.objects.filter(tournamentName=tournament.id,
                                                                 teamsInMatch__teamsInMatch=None)
                    print('to to:')
                    print(nextEmptyCreatedMatch[0])
                    nextEmptyCreatedMatch[0].teamsInMatch.add(lastTeamObject.id)
                    nextEmptyCreatedMatch[0].save()
                    print(lastTeamObject)
            else:
                matchCounter = 0
                counter = 1
                if len(tournamentTeamList) % 2 == 0:
                    for team1, team2 in grouped(tournamentTeamList, 2):
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.teamsInMatch.add(team1, team2)
                        teams.save
                        matchCounter += 1
                        counter += 1

                    while matchCounter != 8:
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.save()
                        matchCounter += 1
                        counter += 1
                else:
                    for team1, team2 in grouped(tournamentTeamList, 2):
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.teamsInMatch.add(team1, team2)
                        teams.save
                        matchCounter += 1
                        counter += 1

                    while matchCounter != 8:
                        matchName = counter
                        teams = Match.objects.create(tournamentName=tournament, matchName=matchName)
                        teams.save()
                        matchCounter += 1
                        counter += 1

                    lastTeam = str(tournamentTeamList[len(tournamentTeamList) - 1])
                    print(lastTeam)
                    lastTeamObject = Team.objects.get(teamName=lastTeam)

                    nextEmptyCreatedMatch = Match.objects.filter(tournamentName=tournament.id,
                                                                 teamsInMatch__teamsInMatch=None)
                    print('to to:')
                    print(nextEmptyCreatedMatch[0])
                    nextEmptyCreatedMatch[0].teamsInMatch.add(lastTeamObject.id)
                    nextEmptyCreatedMatch[0].save()
                    print(lastTeamObject)

            return redirect('bracket_in_tournament', tournament.id)

        else:
            if tournament.registeredTeams.count() <= 4:
                print('mała drabinka')

                def set_status_for_empty_matches():
                    for match in matches:
                        if match.teamsInMatch.count() == 0:
                            match.status = Match.COMPLETED
                            match.save()

                set_status_for_empty_matches()

                def set_matches_with_one_team():
                    print('Robimy check solo')
                    for match in matches:
                        if match.teamsInMatch.count() == 1:
                            currentMatch = Match.objects.get(matchName=match.matchName, tournamentName=tournament.id)
                            teamObject = currentMatch.teamsInMatch.all().values_list('teamName')
                            team = Team.objects.get(teamName=teamObject[0][0])
                            if match.matchName == 2 and match.status == 'active':
                                currentMatch.status = Match.COMPLETED
                                currentMatch.save()
                                nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                nextMatch.teamsInMatch.add(team.id)
                                nextMatch.status = Match.ACTIVE
                                nextMatch.save()

                set_matches_with_one_team()

                def get_team_list():
                    teams = []

                    for team in tournament.registeredTeams.all():
                        teams.append(team.teamName)

                    while len(teams) != 4:
                        teams.append(None)

                    return teams

                teamList = get_team_list()

                def get_match_results():
                    results = []
                    for match in matches:
                        results.append(match.pointBlue)
                        results.append(match.pointRed)

                    while len(results) < (2 * len(teamList)):
                        results.append(None)

                    return results
            else:
                print('duża drabinka')

                def set_status_for_empty_matches():
                    for match in matches:
                        if match.teamsInMatch.count() == 0:
                            match.status = Match.COMPLETED
                            match.save()

                set_status_for_empty_matches()

                def set_matches_with_one_team():
                    print('Robimy check solo')
                    for match in matches:
                        if match.teamsInMatch.count() == 1:
                            currentMatch = Match.objects.get(matchName=match.matchName)
                            teamObject = currentMatch.teamsInMatch.all().values_list('teamName')
                            team = Team.objects.get(teamName=teamObject[0][0])
                            if match.matchName == 4:
                                currentMatch.status = Match.COMPLETED
                                currentMatch.save()
                                nextMatch = Match.objects.get(matchName=6)
                                nextMatch.teamsInMatch.add(team.id)
                                nextMatch.status = Match.ACTIVE
                                nextMatch.save()
                            if match.matchName == 3:
                                currentMatch.status = Match.COMPLETED
                                currentMatch.save()
                                nextMatch = Match.objects.get(matchName=7)
                                nextMatch.teamsInMatch.add(team.id)
                                nextMatch.status = Match.ACTIVE
                                nextMatch.save()
                        else:
                            pass

                set_matches_with_one_team()

                def get_team_list():
                    teams = []

                    for team in tournament.registeredTeams.all():
                        teams.append(team.teamName)

                    while len(teams) != 8:
                        teams.append(None)

                    return teams

                teamList = get_team_list()

                def get_match_results():
                    results = []
                    for match in matches:
                        results.append(match.pointBlue)
                        results.append(match.pointRed)

                    while len(results) < (2 * len(teamList)):
                        results.append(None)

                    return results

            resusltsList = get_match_results()
            teamList = json.dumps(teamList)
            print(teamList)
            resusltsList = json.dumps(resusltsList)
            print(resusltsList)

            def if_team_is_registered():
                for name in teams:
                    val = True
                    if tournament.registeredTeams.filter(registeredTeams__registeredTeams=name.id):
                        val = True
                    else:
                        pass
                    return val

            if if_team_is_registered():
                def get_team_registered_by_user():
                    for name in teams:
                        if tournament.registeredTeams.filter(registeredTeams__registeredTeams=name.id):
                            teamRegisteredByUser = name

                            return teamRegisteredByUser

                teamRegisteredByUser = get_team_registered_by_user()

                def get_match_object():
                    for _ in matches:
                        for match in matches:
                            if match.teamsInMatch.filter(teamsInMatch__teamsInMatch=teamRegisteredByUser.id,
                                                         teamsInMatch__status='active'):
                                matchObject = match

                                return matchObject

                matchObject = get_match_object()

                def get_teams_for_summary():
                    if tournament.registeredTeams.count() <= 4:
                        summaryListOfTeams = []
                        firstPlace = matches.get(matchName=3, tournamentName=tournament.id)
                        firstPlace = firstPlace.winner
                        summaryListOfTeams.append(firstPlace)
                        secondPlace = matches.get(matchName=3, tournamentName=tournament.id)
                        secondPlace = secondPlace.losser
                        summaryListOfTeams.append(secondPlace)
                        thirdPlace = matches.get(matchName=4, tournamentName=tournament.id)
                        thirdPlace = thirdPlace.winner
                        summaryListOfTeams.append(thirdPlace)
                        fourthPlace = matches.get(matchName=4, tournamentName=tournament.id)
                        fourthPlace = fourthPlace.losser
                        summaryListOfTeams.append(fourthPlace)
                        return summaryListOfTeams

                summaryListOfTeams = get_teams_for_summary()
                firstPlace = summaryListOfTeams[0]
                secondPlace = summaryListOfTeams[1]
                thirdPlace = summaryListOfTeams[2]
                fourthPlace = summaryListOfTeams[3]
                print(firstPlace)

                def end_tournament():
                    completedMatches = matches.filter(status='completed')
                    if tournament.registeredTeams.count() <= 4 and len(completedMatches) == 4:
                        tournament.status = tournament.COMPLETED
                        tournament.save()
                    elif tournament.registeredTeams.count() <= 8 and len(completedMatches) == 8:
                        tournament.status = tournament.COMPLETED
                        tournament.save()

                end_tournament()

                context = {'tournament': tournament, 'teamRegisteredByUser': teamRegisteredByUser,
                           'matchObject': matchObject, 'teamList': teamList, 'resusltsList': resusltsList,
                           'dateTime': dateTime, "hourTime": hourTime, 'firstPlace': firstPlace,
                           'secondPlace': secondPlace, 'thirdPlace': thirdPlace, 'fourthPlace': fourthPlace}

                return render(request, 'tournaments/bracket_in_tournament.html', context)

            context = {'tournament': tournament, 'teamList': teamList, 'resusltsList': resusltsList}
            return render(request, 'tournaments/bracket_in_tournament.html', context)

    context = {'tournament': tournament, 'dateTime': dateTime, "hourTime": hourTime, 'matches': matches,
               'currentTime': currentTime, 'currentDate': currentDate}
    return render(request, 'tournaments/bracket_in_tournament.html', context)


@login_required
def show_match_in_tournament(request, tournament_id, match_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    match = get_object_or_404(Match, pk=match_id)
    requestTeam = Team.objects.filter(createdBy=request.user)
    teamNames = [team for team in match.teamsInMatch.all()]
    print(teamNames)
    teamNamesList = [team.teamName for team in teamNames]
    print(teamNamesList)
    teamBlue = Team.objects.get(teamName=teamNamesList[0])
    teamRed = Team.objects.get(teamName=teamNamesList[1])
    blueUsers = User.objects.filter(teams__teamName=teamNamesList[0])
    redUsers = User.objects.filter(teams__teamName=teamNamesList[1])

    form = UploadImageToVeryficate(instance=Match)
    if match.status == 'active':
        if request.method == 'POST':
            form = UploadImageToVeryficate(request.POST, request.FILES, instance=match)
            if form.is_valid():
                try:
                    form.save()
                    winnerTeamName = image_verification.verify_iamge(request, match.id)

                    if teamNamesList[0] == winnerTeamName:
                        winnerTeamName = teamNamesList[0]
                        losserTeamName = teamNamesList[1]
                    elif teamNamesList[1] == winnerTeamName:
                        winnerTeamName = teamNamesList[1]
                        losserTeamName = teamNamesList[0]

                    print('win team: ', winnerTeamName)
                    print('loss team: ', losserTeamName)

                    messages.success(request, 'Zrzut ekranu został wysłany')
                    messages.info(request, "Zwyciężyła drużyna: " + winnerTeamName)

                    if teamNamesList[0] == winnerTeamName:
                        match.pointBlue = 1

                        match.status = Match.COMPLETED
                        match.winner = winnerTeamName
                        match.losser = losserTeamName
                        match.save()
                        if match.winner == winnerTeamName:
                            if tournament.registeredTeams.count() <= 4:
                                print(match.matchName)
                                if match.matchName == 1:
                                    print('przenoszenie')
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 2:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()

                            elif tournament.registeredTeams.count() > 4:
                                print(match.matchName)
                                if match.matchName == 1:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 2:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 3 and tournament.registeredTeams.count() == 6:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 3 and tournament.registeredTeams.count() > 6:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 4:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 5:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 6:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()

                        if match.losser == losserTeamName:
                            if tournament.registeredTeams.count() <= 4:
                                print(match.matchName)
                                if match.matchName == 1 and tournament.registeredTeams.count() < 4:
                                    print('przenoszenie')
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.winner = team.teamName
                                    nextMatch.status = nextMatch.COMPLETED
                                    nextMatch.save()
                                if match.matchName == 1 and tournament.registeredTeams.count() == 4:
                                    print('przenoszenie')
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 2:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()

                            elif tournament.registeredTeams.count() > 4:
                                print(match.matchName)
                                if match.matchName == 5 and tournament.registeredTeams.count() > 6:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 5 and tournament.registeredTeams.count() <= 6:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.winner = team.teamName
                                    nextMatch.save()
                                elif match.matchName == 6 and tournament.registeredTeams.count() > 6:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                        return redirect('bracket_in_tournament', tournament.id)

                    elif teamNamesList[1] == winnerTeamName:
                        match.pointRed = 1
                        match.winner = winnerTeamName
                        match.losser = losserTeamName
                        match.status = Match.COMPLETED
                        match.save()
                        if match.winner == winnerTeamName:
                            if tournament.registeredTeams.count() <= 4:
                                print(match.matchName)
                                if match.matchName == 1:
                                    print('przenoszenie')
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 2:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()

                            elif tournament.registeredTeams.count() > 4:
                                print(match.matchName)
                                if match.matchName == 1:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 2:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 3 and tournament.registeredTeams.count() == 6:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 3 and tournament.registeredTeams.count() > 6:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 4:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 5:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 6:
                                    team = Team.objects.get(teamName=winnerTeamName)
                                    nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()

                        if match.losser == losserTeamName:
                            if tournament.registeredTeams.count() <= 4:
                                if match.matchName == 1 and tournament.registeredTeams.count() < 4:
                                    print('przenoszenie')
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.winner = team.teamName
                                    nextMatch.status = nextMatch.COMPLETED
                                    nextMatch.save()
                                if match.matchName == 1 and tournament.registeredTeams.count() == 4:
                                    print('przenoszenie')
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 2:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()

                            elif tournament.registeredTeams.count() > 4:
                                if match.matchName == 5 and tournament.registeredTeams.count() > 6:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                                elif match.matchName == 5 and tournament.registeredTeams.count() <= 6:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.winner = team.teamName
                                    nextMatch.save()
                                elif match.matchName == 6:
                                    team = Team.objects.get(teamName=losserTeamName)
                                    nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                    nextMatch.status = nextMatch.ACTIVE
                                    nextMatch.teamsInMatch.add(team.id)
                                    nextMatch.save()
                    else:
                        messages.error(request, 'Nie udało się dodać wyniku')

                    return redirect('bracket_in_tournament', tournament.id)
                except:
                    messages.error(request, 'Screen nie został poprawnie zwryfikowany, prześlij ponownie plik')

    else:
        messages.error(request, 'Mecz zakończony')

    context = {'tournament': tournament, 'form': form, 'match': match, 'teamBlue': teamBlue, 'teamRed': teamRed,
               'blueUsers': blueUsers,
               'redUsers': redUsers, 'requestTeam': requestTeam}

    return render(request, 'tournaments/match_view.html', context)
