# Generated by Django 4.1.4 on 2022-12-31 00:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0002_alter_profile_summonername'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='profilePic',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
