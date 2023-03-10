from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    summonerName = models.CharField(max_length=30, null=True, blank=True, unique=True)
    profilePic = models.ImageField(default='default_image.png', null=True, blank=True, upload_to='profiles_images')
    gamesPlayed = models.IntegerField(default=0, null=False)
    gamesWon = models.IntegerField(default=0, null=False)
    gamesLost = models.IntegerField(default=0, null=False)
    rating = models.IntegerField(default=0, null=False)

    def __str__(self):
        return str(self.user)


class Team(models.Model):
    teamName = models.CharField(max_length=100, null=False, blank=False, unique=True)
    createdBy = models.ForeignKey(User, related_name='created_teams', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='teams')

    class Meta:
        ordering = ['teamName']

    def __str__(self):
        return str(self.teamName)


class Invitation(models.Model):
    # Status
    INVITED = 'invited'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    CANCELLED = 'cancelled'

    CHOICES_STATUS = (
        (INVITED, 'Invited'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
        (CANCELLED, 'Cancelled')
    )

    team = models.ForeignKey(Team, related_name='invitations', on_delete=models.CASCADE)
    email = models.EmailField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=CHOICES_STATUS, default=INVITED)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Organizer(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(default='default_image_organizer.png', null=True, blank=True,
                              upload_to='organizers_images')

    def __str__(self):
        return self.name


class Tournament(models.Model):
    # Status
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

    CHOICES_STATUS = (
        (IN_PROGRESS, 'In_progress'),
        (COMPLETED, 'Completed')
    )
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, null=True)
    image = models.ImageField(default='default_image_tournament.png', null=True, blank=True,
                              upload_to='tournaments_images')
    dateTime = models.DateTimeField(null=True, blank=True)
    server = models.CharField(max_length=10)
    registeredTeams = models.ManyToManyField(Team, related_name='registeredTeams', blank=True)
    maxTeams = models.IntegerField()
    status = models.CharField(max_length=25, choices=CHOICES_STATUS, default=IN_PROGRESS)

    def __str__(self):
        return self.name


class Match(models.Model):
    ACTIVE = 'active'
    COMPLETED = 'completed'

    CHOICES_STATUS = (
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed')
    )
    tournamentName = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    matchName = models.IntegerField()
    teamsInMatch = models.ManyToManyField(Team, related_name='teamsInMatch', blank=True)
    winner = models.CharField(max_length=100, null=True, blank=True)
    losser = models.CharField(max_length=100, null=True, blank=True)
    pointBlue = models.IntegerField(default=0)
    pointRed = models.IntegerField(default=0)
    status = models.CharField(max_length=25, choices=CHOICES_STATUS, default=ACTIVE)
    afterGameImage = models.ImageField(null=True, blank=True, upload_to='matchEnds_images')

    def __str__(self):
        return self.tournamentName.name
