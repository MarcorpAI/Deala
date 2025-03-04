# Generated by Django 5.1 on 2025-02-05 03:46

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="StoredProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product_id", models.CharField(max_length=255)),
                ("title", models.TextField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "original_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("url", models.TextField()),
                ("image_url", models.TextField()),
                ("retailer", models.CharField(max_length=50)),
                ("description", models.TextField(blank=True)),
                ("available", models.BooleanField(default=True)),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("metadata", models.JSONField(blank=True, null=True)),
            ],
            options={
                "unique_together": {("product_id", "retailer")},
            },
        ),
    ]
