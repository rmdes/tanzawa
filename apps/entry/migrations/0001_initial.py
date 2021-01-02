# Generated by Django 3.1.4 on 2020-12-31 21:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("post", "0002_register_status_kinds"),
    ]

    operations = [
        migrations.CreateModel(
            name="TEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("p_name", models.CharField(blank=True, default="", max_length=255)),
                (
                    "p_summary",
                    models.CharField(blank=True, default="", max_length=1024),
                ),
                ("e_content", models.TextField(blank=True, default="")),
                (
                    "t_post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="post.tpost"
                    ),
                ),
            ],
            options={
                "db_table": "t_entry",
            },
        ),
    ]
