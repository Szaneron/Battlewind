# Generated by Django 4.1.4 on 2023-01-02 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0010_alter_profile_summonername'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='summonerName',
            field=models.CharField(max_length=30, null=True, unique=True),
        ),
    ]