# Generated by Django 4.1.4 on 2023-01-02 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0009_alter_team_teamname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='summonerName',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
