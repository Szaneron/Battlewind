import datetime
import json
import random
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404

from Website import image_verification
from .decorators import unauthenticated_user
from .forms import CreateUserForm, EditUserProfileSettingsForm, CreateTeamForm, UploadImageToVeryficate, \
    MyPasswordChangeForm
from .models import *
from .utilities import send_invitation, send_invitation_accepted


# Create your views here.

def home(request):
    incomingTournaments = Tournament.objects.filter(status='in_progress').order_by('dateTime')[:4]
    latestTournaments = Tournament.objects.filter(status='completed').order_by('-dateTime')[:4]
    try:
        userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
        if userInvitations:
            context = {'incomingTournaments': incomingTournaments, 'latestTournaments': latestTournaments,
                       'userInvitations': userInvitations}
            return render(request, 'index.html', context)
    except:
        pass

    context = {'incomingTournaments': incomingTournaments, 'latestTournaments': latestTournaments}
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
            messages.success(request, 'Konto utworzone')
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
            messages.error(request, 'Nieprawidłowa nazwa lub hasło')

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
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    if userInvitations:
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
            return redirect('profile')
        else:
            messages.error(request, 'Wprowadzona nazwa jest juz zajęta')
    else:
        form = CreateTeamForm(request.user)

    context = {'form': form, 'winratePercentage': winratePercentage, 'teams': teams, 'userInvitations': userInvitations}
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
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

    context = {'form': form, 'userInvitations': userInvitations}
    return render(request, 'accounts/profile_settings.html', context)


@login_required(login_url='login')
def change_password(request):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    if request.method == 'POST':
        form = MyPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_settings')

    else:
        form = MyPasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form, 'userInvitations': userInvitations})


@login_required(login_url='login')
def view_team(request, team_id):
    team = get_object_or_404(Team, pk=team_id, members__in=[request.user])
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    invitations = Invitation.objects.filter(status='Invited', team=team)
    context = {'team': team, 'invitations': invitations, 'userInvitations': userInvitations}

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

            user = User.objects.get(username=request.POST.get('username'))
            if team.members.filter(teams__members__in=[user.id]):
                if team.createdBy == user:
                    messages.error(request, 'Nie można usunąć twórcy drużyny')
                else:
                    team.members.remove(user.id)
                    team.save()

                    invitations = Invitation.objects.filter(team=team, email=user.email)
                    if invitations:
                        Invitation.objects.filter(team=team, email=user.email).delete()

                    messages.success(request, 'Usunięto użytkownika')

        if 'delete_team' in request.POST:
            print('usuwanie')
            team.delete()
            team.save()

            invitations = Invitation.objects.filter(team=team)
            if invitations:
                Invitation.objects.filter(team=team).delete()

            messages.success(request, 'Pomyślnie usunięto drużynę')

            return redirect('profile')

        if 'leave_team' in request.POST:
            team.members.remove(request.user)
            team.save()

            invitations = Invitation.objects.filter(team=team, email=request.user.email)
            if invitations:
                Invitation.objects.filter(team=team, email=request.user.email).delete()

            messages.success(request, 'Pomyślnie opuszczono drużynę')

            return redirect('profile')

    return render(request, 'teams/view_team.html', context)


@login_required(login_url='login')
def invite(request, team_id):
    team = get_object_or_404(Team, pk=team_id, members__in=[request.user])
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
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
    return render(request, 'teams/invite.html', {'team': team, 'userInvitations': userInvitations})


@login_required(login_url='login')
def accept_invitation(request):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    if userInvitations:
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

            userInvitations = Invitation.objects.filter(code=code, email=request.user.email)

            if 'accept' in request.POST:
                if userInvitations.filter(status='Invited'):
                    invitation = userInvitations[0]
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
                if userInvitations:
                    invitation = userInvitations[0]
                    invitation.status = Invitation.DECLINED
                    invitation.save()

                    messages.info(request, 'Zaproszenie odrzucone')
                    return redirect('profile')
        else:
            return render(request, 'teams/accept_invitation.html',
                          {'listOfTeamsNames': listOfTeamsNames, 'userInvitations': userInvitations})

    messages.info(request, 'Nie masz żadnych zaproszeń')
    return redirect('profile')


def show_open_tournaments(request):
    tournaments = Tournament.objects.filter(status='in_progress').order_by('dateTime')
    try:
        userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
        if userInvitations:
            context = {'tournaments': tournaments, 'userInvitations': userInvitations}
            return render(request, 'tournaments/tournaments_open.html', context)
    except:
        pass

    context = {'tournaments': tournaments}
    return render(request, 'tournaments/tournaments_open.html', context)


@login_required(login_url='login')
def details_tournament(request, tournament_id):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    teams = Team.objects.filter(createdBy=request.user)

    tournamentDateTime = tournament.dateTime.strftime("%d/%m/%Y %H:%M:%S")
    tournamentDate = tournament.dateTime.date().strftime("%d/%m/%Y")
    tournamentTime = tournament.dateTime.time().strftime("%H:%M:%S")

    currentDateTime = datetime.now()
    currentDateTime = currentDateTime.strftime("%d/%m/%Y %H:%M:%S")

    def check_teams():
        teamsInTournament = 0
        for _ in teams:
            if tournament.registeredTeams.filter(registeredTeams__registeredTeams=_.id):
                teamsInTournament += 1
        return teamsInTournament

    def get_registered_teams_summoner_names_list():
        tour = tournament.registeredTeams.all()
        list = []
        for t in tour:
            for x in t.members.all():
                list.append(x.profile.summonerName)

        return list

    registeredMembers = get_registered_teams_summoner_names_list()
    if request.method == 'POST':
        if 'join' in request.POST:

            if tournamentDateTime >= currentDateTime:
                team = Team.objects.get(teamName=request.POST.get('teamName'))
                print(team.members.count())
                members = team.members.all()
                teamSummonerNameList = []
                summnerNameCounter = 0
                for member in members:
                    teamSummonerNameList.append(member.profile.summonerName)

                for elem in teamSummonerNameList:
                    if elem in registeredMembers:
                        summnerNameCounter += 1
                if team.members.count() == 5:
                    if summnerNameCounter == 0:
                        if check_teams() == 0:
                            if tournament.registeredTeams.count() < tournament.maxTeams:
                                tournament.registeredTeams.add(team.id)
                                tournament.save()
                                messages.success(request, "Drużyna dołączyła do turnieju")
                            else:
                                messages.error(request, 'Nie ma już wolnych miejsc dla nowej drużyny')

                        else:
                            messages.error(request, 'Zapisałeś już jedną swoją drużynę')
                    else:
                        messages.error(request, 'Członek twojej drużyny znajduje się już w innej zapisanej drużynie')
                else:
                    messages.error(request, 'W drużynie nie ma 5 zawodników')
            else:
                messages.error(request, 'Turniej się już rozpoczął. Nie ma już możliwości dołączenia')

    context = {'tournament': tournament, 'userInvitations': userInvitations, 'teams': teams,
               'tournamentDate': tournamentDate, 'tournamentTime': tournamentTime,
               'tournamentDateTime': tournamentDateTime, 'currentDateTime': currentDateTime}
    return render(request, 'tournaments/tournament_view.html', context)


@login_required(login_url='login')
def show_tournament_teams(request, tournament_id):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    teams = Team.objects.filter(createdBy=request.user)

    tournamentDateTime = tournament.dateTime.strftime("%d/%m/%Y %H:%M:%S")
    tournamentDate = tournament.dateTime.date().strftime("%d/%m/%Y")
    tournamentTime = tournament.dateTime.time().strftime("%H:%M:%S")

    currentDateTime = datetime.now()
    currentDateTime = currentDateTime.strftime("%d/%m/%Y %H:%M:%S")

    def get_registered_teams_summoner_names_list():
        tour = tournament.registeredTeams.all()
        list = []
        for t in tour:
            for x in t.members.all():
                list.append(x.profile.summonerName)

        return list

    registeredMembers = get_registered_teams_summoner_names_list()

    def check_teams():
        teamInfo = ['name', 0]
        for _ in teams:
            if tournament.registeredTeams.filter(registeredTeams__registeredTeams=_.id):
                teamInfo[0] = _
                teamInfo[1] = 1
        return teamInfo

    if request.method == 'POST':
        if 'leave' in request.POST:
            if tournamentDateTime >= currentDateTime:
                teamName = check_teams()[0]
                tournament.registeredTeams.remove(teamName.id)
                tournament.save()
                messages.success(request, 'Drużyna wypisana z turnieju')

            else:
                messages.error(request, 'Turniej się już rozpoczął. Nie ma już możliwości opuszczenia')

        if 'join' in request.POST:

            if tournamentDateTime >= currentDateTime:
                team = Team.objects.get(teamName=request.POST.get('teamName'))
                members = team.members.all()
                teamSummonerNameList = []
                summnerNameCounter = 0
                for member in members:
                    teamSummonerNameList.append(member.profile.summonerName)

                for elem in teamSummonerNameList:
                    if elem in registeredMembers:
                        summnerNameCounter += 1
                if team.members.count() == 5:
                    if summnerNameCounter == 0:
                        if check_teams()[1] == 0:
                            if tournament.registeredTeams.count() < tournament.maxTeams:
                                tournament.registeredTeams.add(team.id)
                                tournament.save()
                                messages.success(request, "Drużyna dołączyła do turnieju")
                            else:
                                messages.error(request, 'Nie ma już wolnych miejsc dla nowej drużyny')
                        else:
                            messages.error(request, 'Zapisałeś już jedną swoją drużynę')
                    else:
                        messages.error(request, 'Członek twojej drużyny znajduje się już w innej zapisanej drużynie')
                else:
                    messages.error(request, 'W drużynie nie ma 5 zawodników')
            else:
                messages.error(request, 'Turniej się już rozpoczął. Nie ma już możliwości dołączenia')

    context = {'tournament': tournament, 'userInvitations': userInvitations, 'teams': teams,
               'tournamentDate': tournamentDate, 'tournamentTime': tournamentTime,
               'tournamentDateTime': tournamentDateTime, 'currentDateTime': currentDateTime}

    return render(request, 'tournaments/teams_in_tournament.html', context)


@login_required(login_url='login')
def show_tournament_bracket(request, tournament_id):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    matches = Match.objects.filter(tournamentName=tournament.id)
    teams = Team.objects.filter(members__in=[request.user])
    tournamentDateTime = tournament.dateTime.strftime("%d/%m/%Y %H:%M:%S")
    tournamentDate = tournament.dateTime.date().strftime("%d/%m/%Y")
    tournamentTime = tournament.dateTime.time().strftime("%H:%M:%S")

    currentDateTime = datetime.now()
    currentDateTime = currentDateTime.strftime("%d/%m/%Y %H:%M:%S")

    def create_bracket_4(matchCounter, counter):
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

    def create_bracket_8(matchCounter, counter):
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

    if tournamentDateTime >= currentDateTime:
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
                    create_bracket_4(matchCounter, counter)
                else:
                    create_bracket_4(matchCounter, counter)

                    lastTeam = str(tournamentTeamList[len(tournamentTeamList) - 1])
                    lastTeamObject = Team.objects.get(teamName=lastTeam)

                    nextEmptyCreatedMatch = Match.objects.filter(tournamentName=tournament.id,
                                                                 teamsInMatch__teamsInMatch=None)
                    nextEmptyCreatedMatch[0].teamsInMatch.add(lastTeamObject.id)
                    nextEmptyCreatedMatch[0].save()
            else:
                matchCounter = 0
                counter = 1
                if len(tournamentTeamList) % 2 == 0:
                    create_bracket_8(matchCounter, counter)
                else:
                    create_bracket_8(matchCounter, counter)

                    lastTeam = str(tournamentTeamList[len(tournamentTeamList) - 1])
                    lastTeamObject = Team.objects.get(teamName=lastTeam)

                    nextEmptyCreatedMatch = Match.objects.filter(tournamentName=tournament.id,
                                                                 teamsInMatch__teamsInMatch=None)
                    nextEmptyCreatedMatch[0].teamsInMatch.add(lastTeamObject.id)
                    nextEmptyCreatedMatch[0].save()

            return redirect('bracket_in_tournament', tournament.id)

        else:
            if tournament.registeredTeams.count() <= 4:

                def set_status_for_empty_matches():
                    for match in matches:
                        if match.teamsInMatch.count() == 0:
                            match.status = Match.COMPLETED
                            match.save()

                set_status_for_empty_matches()

                def set_matches_with_one_team():
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

                def set_status_for_empty_matches():
                    for match in matches:
                        if match.teamsInMatch.count() == 0:
                            match.status = Match.COMPLETED
                            match.save()

                set_status_for_empty_matches()

                def set_matches_with_one_team():
                    for match in matches:
                        if match.teamsInMatch.count() == 1:
                            currentMatch = Match.objects.get(matchName=match.matchName, tournamentName=tournament.id)
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
            resusltsList = json.dumps(resusltsList)

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
                    if teamRegisteredByUser:
                        for _ in matches:
                            for match in matches:
                                if match.teamsInMatch.filter(teamsInMatch__teamsInMatch=teamRegisteredByUser.id,
                                                             teamsInMatch__status='active'):
                                    matchObject = match

                                    return matchObject
                                else:
                                    pass

                matchObject = get_match_object()

                def get_teams_for_summary():
                    if tournament.registeredTeams.count() <= 4:
                        summaryListOfTeams = []
                        firstPlace = matches.get(matchName=3, tournamentName=tournament.id).winner
                        summaryListOfTeams.append(firstPlace)
                        secondPlace = matches.get(matchName=3, tournamentName=tournament.id).losser
                        summaryListOfTeams.append(secondPlace)
                        thirdPlace = matches.get(matchName=4, tournamentName=tournament.id).winner
                        summaryListOfTeams.append(thirdPlace)
                        fourthPlace = matches.get(matchName=4, tournamentName=tournament.id).losser
                        summaryListOfTeams.append(fourthPlace)
                        return summaryListOfTeams
                    elif tournament.registeredTeams.count() > 4:
                        summaryListOfTeams = []
                        firstPlace = matches.get(matchName=7, tournamentName=tournament.id).winner
                        summaryListOfTeams.append(firstPlace)
                        secondPlace = matches.get(matchName=7, tournamentName=tournament.id).losser
                        summaryListOfTeams.append(secondPlace)
                        thirdPlace = matches.get(matchName=8, tournamentName=tournament.id).winner
                        summaryListOfTeams.append(thirdPlace)
                        fourthPlace = matches.get(matchName=8, tournamentName=tournament.id).losser
                        summaryListOfTeams.append(fourthPlace)
                        return summaryListOfTeams

                summaryListOfTeams = get_teams_for_summary()
                firstPlace = summaryListOfTeams[0]
                secondPlace = summaryListOfTeams[1]
                thirdPlace = summaryListOfTeams[2]
                fourthPlace = summaryListOfTeams[3]

                def end_tournament():
                    completedMatches = matches.filter(status='completed')
                    if tournament.registeredTeams.count() <= 4 and len(completedMatches) == 4:
                        tournament.status = tournament.COMPLETED
                        tournament.save()
                    elif tournament.registeredTeams.count() <= 8 and len(completedMatches) == 8:
                        tournament.status = tournament.COMPLETED
                        tournament.save()

                if matches:
                    end_tournament()

                context = {'tournament': tournament, 'userInvitations': userInvitations,
                           'teamRegisteredByUser': teamRegisteredByUser, 'teamList': teamList,
                           'resusltsList': resusltsList, 'matchObject': matchObject,
                           'tournamentDate': tournamentDate, 'tournamentTime': tournamentTime,
                           'tournamentDateTime': tournamentDateTime, 'currentDateTime': currentDateTime,
                           'firstPlace': firstPlace, 'secondPlace': secondPlace, 'thirdPlace': thirdPlace,
                           'fourthPlace': fourthPlace}

                return render(request, 'tournaments/bracket_in_tournament.html', context)

            context = {'tournament': tournament, 'userInvitations': userInvitations, 'teamList': teamList,
                       'resusltsList': resusltsList}
            return render(request, 'tournaments/bracket_in_tournament.html', context)

    context = {'tournament': tournament, 'userInvitations': userInvitations,
               'matches': matches, 'tournamentDate': tournamentDate, 'tournamentTime': tournamentTime,
               'tournamentDateTime': tournamentDateTime, 'currentDateTime': currentDateTime}
    return render(request, 'tournaments/bracket_in_tournament.html', context)


@login_required(login_url='login')
def rules_tournament(request, tournament_id):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    tournamentDateTime = tournament.dateTime.strftime("%d/%m/%Y %H:%M:%S")
    tournamentDate = tournament.dateTime.date().strftime("%d/%m/%Y")
    tournamentTime = tournament.dateTime.time().strftime("%H:%M:%S")

    currentDateTime = datetime.now()
    currentDateTime = currentDateTime.strftime("%d/%m/%Y %H:%M:%S")

    context = {'userInvitations': userInvitations, 'tournament': tournament, 'tournamentDate': tournamentDate,
               'tournamentTime': tournamentTime, 'tournamentDateTime': tournamentDateTime,
               'currentDateTime': currentDateTime}
    return render(request, 'tournaments/tournament_rules.html', context)


@login_required(login_url='login')
def show_match_in_tournament(request, tournament_id, match_id):
    userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    match = get_object_or_404(Match, pk=match_id)
    requestTeam = Team.objects.filter(createdBy=request.user)
    teamNames = [team for team in match.teamsInMatch.all()]
    teamNamesList = [team.teamName for team in teamNames]
    teamBlue = Team.objects.get(teamName=teamNamesList[0])
    teamRed = Team.objects.get(teamName=teamNamesList[1])
    blueUsers = User.objects.filter(teams__teamName=teamNamesList[0])
    redUsers = User.objects.filter(teams__teamName=teamNamesList[1])

    def player_stats_win(team):
        for member in team.members.all():
            member.profile.gamesPlayed += 1
            member.profile.gamesWon += 1
            member.profile.rating += 10
            member.profile.save()

    def player_stats_loss(team):
        for member in team.members.all():
            member.profile.gamesPlayed += 1
            member.profile.gamesLost += 1
            member.profile.rating += 5
            member.profile.save()

    def bracket_move(nextMatch, team):
        nextMatch.status = nextMatch.ACTIVE
        nextMatch.teamsInMatch.add(team.id)
        nextMatch.save()

    form = UploadImageToVeryficate(instance=Match)

    if match.status == 'active':
        try:
            if request.method == 'POST':
                form = UploadImageToVeryficate(request.POST, request.FILES, instance=match)
                if form.is_valid():
                    form.save()
                    winnerTeamName = image_verification.verify_iamge(request, match.id)
                    if winnerTeamName == 0:
                        messages.error(request, 'Wykryto edycję obrazu, prześlij screen ponownie.')
                    else:

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
                                team = Team.objects.get(teamName=winnerTeamName)
                                player_stats_win(team)

                                if tournament.registeredTeams.count() <= 4:
                                    if match.matchName == 1:
                                        nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 2:
                                        nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)

                                elif tournament.registeredTeams.count() > 4:
                                    if match.matchName == 1:
                                        nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 2:
                                        nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 3 and tournament.registeredTeams.count() == 6:
                                        nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 3 and tournament.registeredTeams.count() > 6:
                                        nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 4:
                                        nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 5:
                                        nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 6:
                                        nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)

                            if match.losser == losserTeamName:
                                team = Team.objects.get(teamName=losserTeamName)
                                player_stats_loss(team)

                                if tournament.registeredTeams.count() <= 4:
                                    if match.matchName == 1 and tournament.registeredTeams.count() < 4:
                                        nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                        nextMatch.teamsInMatch.add(team.id)
                                        nextMatch.winner = team.teamName
                                        nextMatch.status = nextMatch.COMPLETED
                                        nextMatch.save()
                                    if match.matchName == 1 and tournament.registeredTeams.count() == 4:
                                        nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 2:
                                        nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)

                                elif tournament.registeredTeams.count() > 4:
                                    if match.matchName == 5 and tournament.registeredTeams.count() > 6:
                                        nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 5 and tournament.registeredTeams.count() <= 6:
                                        nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 6 and tournament.registeredTeams.count() > 6:
                                        nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                            return redirect('bracket_in_tournament', tournament.id)

                        elif teamNamesList[1] == winnerTeamName:
                            match.pointRed = 1
                            match.winner = winnerTeamName
                            match.losser = losserTeamName
                            match.status = Match.COMPLETED
                            match.save()

                            if match.winner == winnerTeamName:
                                team = Team.objects.get(teamName=winnerTeamName)
                                player_stats_win(team)
                                if tournament.registeredTeams.count() <= 4:
                                    if match.matchName == 1:
                                        nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 2:
                                        nextMatch = Match.objects.get(matchName=3, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)

                                elif tournament.registeredTeams.count() > 4:
                                    if match.matchName == 1:
                                        nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 2:
                                        nextMatch = Match.objects.get(matchName=5, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 3 and tournament.registeredTeams.count() == 6:
                                        nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 3 and tournament.registeredTeams.count() > 6:
                                        nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 4:
                                        nextMatch = Match.objects.get(matchName=6, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 5:
                                        nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 6:
                                        nextMatch = Match.objects.get(matchName=7, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)

                            if match.losser == losserTeamName:
                                team = Team.objects.get(teamName=losserTeamName)
                                player_stats_loss(team)
                                if tournament.registeredTeams.count() <= 4:
                                    if match.matchName == 1 and tournament.registeredTeams.count() < 4:
                                        nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                        nextMatch.teamsInMatch.add(team.id)
                                        nextMatch.winner = team.teamName
                                        nextMatch.status = nextMatch.COMPLETED
                                        nextMatch.save()
                                    if match.matchName == 1 and tournament.registeredTeams.count() == 4:
                                        nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 2:
                                        nextMatch = Match.objects.get(matchName=4, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)

                                elif tournament.registeredTeams.count() > 4:
                                    if match.matchName == 5 and tournament.registeredTeams.count() > 6:
                                        nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 5 and tournament.registeredTeams.count() <= 6:
                                        nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                                    elif match.matchName == 6:
                                        nextMatch = Match.objects.get(matchName=8, tournamentName=tournament.id)
                                        bracket_move(nextMatch, team)
                        else:
                            messages.error(request, 'Nie udało się dodać wyniku')

                        return redirect('bracket_in_tournament', tournament.id)
        except Exception as e:
            print('Error: ', e)
            messages.error(request, 'Dane z obrazu nie zostały poprawnie dopasowane, prześlij ponownie plik')


    else:
        messages.error(request, 'Mecz zakończony')

    context = {'tournament': tournament, 'userInvitations': userInvitations, 'form': form, 'match': match,
               'teamBlue': teamBlue, 'teamRed': teamRed, 'blueUsers': blueUsers, 'redUsers': redUsers,
               'requestTeam': requestTeam}

    return render(request, 'tournaments/match_view.html', context)


def show_ranking_view(request):
    allProfiles = Profile.objects.all().order_by('-rating', '-gamesPlayed')
    rankingTable = []
    try:
        userInvitations = Invitation.objects.filter(email=request.user.email, status='Invited')
        if userInvitations:
            context = {'rankingTable': rankingTable, 'userInvitations': userInvitations}
            return render(request, 'index.html', context)
    except:
        pass

    def get_number_of_users_list():
        list = []
        for element in range(1, len(allProfiles) + 1):
            list.append(element)
        return list

    numbersList = get_number_of_users_list()

    def check_winrate():
        list = []
        for profile in allProfiles:
            if profile.gamesPlayed != 0:
                list.append(str("%.0f" % ((profile.gamesWon / profile.gamesPlayed) * 100) + '%'))
            else:
                list.append(str("%.0f" % 0 + '%'))
        return list

    winratePercentageList = check_winrate()

    for iterator, profile, winrate in zip(numbersList, allProfiles, winratePercentageList):
        innerList = []
        innerList.append(iterator)
        innerList.append(profile.user.username)
        innerList.append(winrate)
        innerList.append(profile.gamesPlayed)
        innerList.append(profile.gamesWon)
        innerList.append(profile.gamesLost)
        innerList.append(profile.rating)
        rankingTable.append(innerList)

    context = {'rankingTable': rankingTable}

    return render(request, 'ranking/ranking_view.html', context)
