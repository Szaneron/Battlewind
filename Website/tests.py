from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile, Team, Tournament, Organizer


# Create your tests here.
class authenticatedUserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user2 = User.objects.create_user(username="testuser2", password="testpass")
        self.user3 = User.objects.create_user(username="testuser3", password="testpass")
        self.user4 = User.objects.create_user(username="testuser4", password="testpass")
        self.user5 = User.objects.create_user(username="testuser5", password="testpass")
        self.profile = Profile.objects.create(user=self.user)
        self.profile2 = Profile.objects.create(user=self.user2)
        self.profile3 = Profile.objects.create(user=self.user3)
        self.profile4 = Profile.objects.create(user=self.user4)
        self.profile5 = Profile.objects.create(user=self.user5)
        self.client.login(username="testuser", password="testpass")

        self.testTeam = Team.objects.create(
            teamName='testTeam',
            createdBy=self.user
        )
        self.testTeam.members.add(self.user, self.user2, self.user3, self.user4, self.user5)

        self.organizer = Organizer.objects.create(
            name="Test organizer"
        )
        self.tournament = Tournament.objects.create(
            name='Test tournament',
            description='description',
            organizer=self.organizer,
            dateTime='2023-03-15 02:30:00',
            server='EUNE',
            maxTeams=8,
            status='in_progress'
        )
        self.tournament2 = Tournament.objects.create(
            name='Test tournament2',
            description='description2',
            organizer=self.organizer,
            dateTime='2023-03-16 02:30:00',
            server='EUNE',
            maxTeams=4,
            status='in_progress'
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
