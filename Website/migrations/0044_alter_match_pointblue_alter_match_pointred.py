# Generated by Django 4.1.5 on 2023-01-10 02:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0043_alter_match_pointblue_alter_match_pointred'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='pointBlue',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='match',
            name='pointRed',
            field=models.IntegerField(default=0),
        ),
    ]
