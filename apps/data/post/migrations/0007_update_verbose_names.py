# Generated by Django 3.2.2 on 2021-06-03 10:12

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("post", "0006_tpost_streams"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="mpostkind",
            options={"verbose_name": "Post Kind", "verbose_name_plural": "Post Kinds"},
        ),
        migrations.AlterModelOptions(
            name="mpoststatus",
            options={"verbose_name": "Post Status", "verbose_name_plural": "Post Statuses"},
        ),
        migrations.AlterModelOptions(
            name="tpost",
            options={"verbose_name": "Post", "verbose_name_plural": "Posts"},
        ),
    ]
