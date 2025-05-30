# Generated by Django 5.1 on 2025-04-21 17:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('delapp', '0012_conversationstate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(blank=True, help_text='For anonymous users', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='SavedItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(blank=True, max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('price', models.FloatField(blank=True, null=True)),
                ('original_price', models.FloatField(blank=True, null=True)),
                ('currency', models.CharField(default='USD', max_length=5)),
                ('image_url', models.URLField(blank=True, max_length=1000)),
                ('product_url', models.URLField(blank=True, max_length=1000)),
                ('retailer', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(blank=True, help_text='Optional category or tag', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional product data')),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='delapp.cart')),
                ('conversation', models.ForeignKey(blank=True, help_text='Conversation where this item was saved from', null=True, on_delete=django.db.models.deletion.SET_NULL, to='delapp.conversation')),
            ],
            options={
                'verbose_name': 'Saved Item',
                'verbose_name_plural': 'Saved Items',
                'ordering': ['-created_at'],
            },
        ),
    ]
