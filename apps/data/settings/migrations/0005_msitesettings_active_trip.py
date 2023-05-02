# Generated by Django 3.2.13 on 2022-05-08 02:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trips", "0002_auto_20220404_0621"),
        ("settings", "0004_icon_footer_snippet"),
    ]

    operations = [
        migrations.AddField(
            model_name="msitesettings",
            name="active_trip",
            field=models.ForeignKey(
                blank=True,
                help_text="Prefills the selected trip when creating a new post.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="trips.ttrip",
            ),
        ),
    ]
