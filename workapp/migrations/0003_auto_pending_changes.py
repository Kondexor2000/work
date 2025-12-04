# Generated migration for pending model changes
# This migration handles schema updates since last applied migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workapp', '0002_opinion_transmition_comment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # No operations - all current models are already in applied migrations
        # This migration serves as a checkpoint for future changes
    ]
