# Generated by Django 5.1 on 2024-09-06 08:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("delapp", "0002_waitlist"),
    ]

    operations = [
        migrations.AlterField(
            model_name="waitlist",
            name="name",
            field=models.CharField(max_length=100),
        ),
    ]
