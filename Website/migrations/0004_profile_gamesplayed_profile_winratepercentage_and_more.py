# Generated by Django 4.1.4 on 2023-01-01 16:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Website', '0003_profile_profilepic'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='gamesPlayed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='winratePercentage',
            field=models.FloatField(default=100),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profilePic',
            field=models.ImageField(blank=True, default='default_image.png', null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
