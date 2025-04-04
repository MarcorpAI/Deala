# Generated by Django 5.1 on 2024-10-08 23:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("delapp", "0005_usersubscription_verification_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customuser",
            name="verification_token",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="is_active",
            field=models.BooleanField(default=False),
        ),
    ]
