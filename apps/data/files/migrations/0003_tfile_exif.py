# Generated by Django 3.1.4 on 2021-01-13 21:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("files", "0002_add_t_formatted_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="tfile",
            name="exif",
            field=models.JSONField(default=dict),
        ),
    ]
