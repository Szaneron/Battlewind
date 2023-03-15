from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile, Team, Tournament, Organizer, Match


# Create your tests here.
class authenticatedUserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass")
        self.user3 = User.objects.create_user(username="testuser3", password="testpass")
        self.user4 = User.objects.create_user(username="testuser4", password="testpass")
        self.user5 = User.objects.create_user(username="testuser5", password="testpass")
        self.user6 = User.objects.create_user(username="testuser6", password="testpass")
        self.user7 = User.objects.create_user(username="testuser7", password="testpass")
        self.user8 = User.objects.create_user(username="testuser8", password="testpass")
        self.user9 = User.objects.create_user(username="testuser9", password="testpass")
        self.user10 = User.objects.create_user(username="testuser10", password="testpass")
        self.profile = Profile.objects.create(user=self.user, summonerName='Xeventri')
        self.profile2 = Profile.objects.create(user=self.user2, summonerName='Usual Girl')
        self.profile3 = Profile.objects.create(user=self.user3, summonerName='MokryBambusChan')
        self.profile4 = Profile.objects.create(user=self.user4, summonerName='MagicznyBambus')
        self.profile5 = Profile.objects.create(user=self.user5, summonerName='fryc')
        self.profile6 = Profile.objects.create(user=self.user6, summonerName='MagicznySzpinak')
        self.profile7 = Profile.objects.create(user=self.user7, summonerName='life in society')
        self.profile8 = Profile.objects.create(user=self.user8, summonerName='Ivyw')
        self.profile9 = Profile.objects.create(user=self.user9, summonerName='GasioR777')
        self.profile10 = Profile.objects.create(user=self.user10, summonerName='kubaxi')
        self.client.login(username="testuser", password="testpass")

        self.testTeam = Team.objects.create(
            teamName='testTeam',
            createdBy=self.user
        )
        self.testTeam.members.add(self.user, self.user2, self.user3, self.user4, self.user5)

        self.testTeam2 = Team.objects.create(
            teamName='testTeam2',
            createdBy=self.user6
        )
        self.testTeam2.members.add(self.user6, self.user7, self.user8, self.user9, self.user10)

        self.organizer = Organizer.objects.create(
            name="Test organizer"
        )
        self.tournament = Tournament.objects.create(
            name='Test tournament',
            description='description',
            organizer=self.organizer,
            dateTime=datetime.now() + timedelta(hours=2),
            server='EUNE',
            maxTeams=8,
            status='in_progress'
        )
        self.tournament2 = Tournament.objects.create(
            name='Test tournament2',
            description='description2',
            organizer=self.organizer,
            dateTime=datetime.now() + timedelta(hours=4),
            server='EUNE',
            maxTeams=4,
            status='in_progress'
        )
        self.tournamentUploadImage = Tournament.objects.create(
            name='Test tournamentUploadImage',
            description='tournamentUploadImage',
            organizer=self.organizer,
            dateTime=datetime.now() - timedelta(hours=2),
            server='EUNE',
            maxTeams=4,
            status='in_progress'
        )
        self.match = Match.objects.create(
            tournamentName=self.tournamentUploadImage,
            matchName=1,
            status='active'
        )
        self.match.teamsInMatch.add(self.testTeam, self.testTeam2)

        self.match3 = Match.objects.create(
            tournamentName=self.tournamentUploadImage,
            matchName=3,
            status='active'
        )
        self.match4 = Match.objects.create(
            tournamentName=self.tournamentUploadImage,
            matchName=4,
            status='active'
        )

    # User team creation test
    def test_team_creation(self):
        #  Simulate the user filling out the team creation form and submitting it by sending a POST request
        url = reverse('profile')
        data = {
            'teamName': 'New Team',
            'createdBy': self.user.id,
            'members': self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # check that the team was created with the correct data
        team = Team.objects.get(createdBy=self.user, teamName=data['teamName'])
        self.assertEqual(team.teamName, data['teamName'])
        self.assertEqual(team.createdBy, self.user)
        self.assertEqual(team.members.count(), 1)

    # User team update test
    def test_team_update(self):
        #  Simulate the user filling out the team update form and submitting it by sending a POST request
        url = reverse('view_team', args=[self.testTeam.id])
        data = {
            'update': 'Update',
            'teamName': 'editedTeamName'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # check that the team was updated with the correct data
        team = Team.objects.get(teamName=data['teamName'])
        self.assertEqual(team.teamName, data['teamName'])

    # User team delete test
    def test_team_delete(self):
        #  Simulate the user filling out the team update form and submitting it by sending a POST request
        url = reverse('view_team', args=[self.testTeam.id])
        data = {
            'delete_team': 'Delete_team'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # check that the team was deleted
        self.assertFalse(Team.objects.filter(id=self.testTeam.id).exists())

    # Test that retrieves the list of upcoming tournaments
    def test_get_incoming_tournaments(self):
        # create a tournament with a past date
        self.tournament3 = Tournament.objects.create(
            name='Test tournament3',
            description='description3',
            organizer=self.organizer,
            dateTime='2023-03-10 02:30:00',
            server='EUNE',
            maxTeams=4,
            status='completed'
        )
        url = reverse('open_tournament')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # check that the response contains the future tournaments and not the past one
        self.assertContains(response, self.tournament.name)
        self.assertContains(response, self.tournament2.name)
        self.assertNotContains(response, self.tournament3.name)

    # Team registration for the tournament test
    def test_team_registration_for_the_tournament(self):
        url = reverse('details_tournament', args=[self.tournament.id])
        data = {
            'join': 'Join',
            'teamName': self.testTeam
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        # check that the team is now registered for the tournament
        self.assertIn(self.testTeam, self.tournament.registeredTeams.all())

    # Team leave from the tournament test
    def test_team_leave_from_the_tournament(self):
        self.tournament.registeredTeams.add(self.testTeam)
        url = reverse('teams_in_tournament', args=[self.tournament.id])
        data = {
            'leave': 'Leave',
            'teamName': self.testTeam
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        # check that the team left from the tournament
        self.assertNotIn(self.testTeam, self.tournament.registeredTeams.all())

    # Test of uploading and verifying the image sent by the user
    def test_upload_image(self):
        # simulate the user submitting a POST request to upload an image
        url = reverse('show_match_in_tournament', args=[self.tournamentUploadImage.id, self.match.id])
        with open('Website/static/mecz1win.png', 'rb') as f:
            response = self.client.post(url, {'afterGameImage': f, 'user': self.user})

        # check that the response status code is 302 Found (redirect)
        self.assertEqual(response.status_code, 302)

        # check that the image was saved to the database
        testedMatch = Match.objects.get(tournamentName=self.tournamentUploadImage, matchName=self.match.matchName)
        self.assertIsNotNone(testedMatch.afterGameImage.url)

        # check that the match instances were updated correctly
        self.assertEqual(testedMatch.winner, self.testTeam.teamName)
        self.assertEqual(testedMatch.losser, self.testTeam2.teamName)
        self.assertEqual(testedMatch.pointBlue, 1)
        self.assertEqual(testedMatch.pointRed, 0)
        self.assertEqual(testedMatch.status, 'completed')
        self.assertEqual(self.match3.teamsInMatch.count(), 1)
        self.assertEqual(self.match4.teamsInMatch.count(), 1)
