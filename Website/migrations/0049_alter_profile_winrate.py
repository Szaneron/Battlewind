# Generated by Django 4.1.5 on 2023-01-16 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0048_profile_rating_profile_winrate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='winRate',
            field=models.FloatField(),
        ),
    ]
