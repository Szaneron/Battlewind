# Generated by Django 4.1.5 on 2023-01-05 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Website', '0020_alter_invitation_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='status',
            field=models.CharField(choices=[('invited', 'Invited'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('cancelled', 'Cancelled')], default='invited', max_length=20),
        ),
    ]
