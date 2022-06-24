# Generated by Django 4.0.5 on 2022-06-24 09:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import phonenumber_field.modelfields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(default='+254712345678', max_length=25, region=None, verbose_name='Phone Number')),
                ('about_me', models.TextField(default='Say something about yourself', verbose_name='About Me')),
                ('license', models.CharField(blank=True, max_length=20, null=True, verbose_name='Real Estate License')),
                ('profile_photo', models.ImageField(default='/profile_default.png', upload_to='', verbose_name='Profile Photo')),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Other', max_length=20, verbose_name='Gender')),
                ('country', django_countries.fields.CountryField(default='Kenya', max_length=2, verbose_name='Country')),
                ('city', models.CharField(default='Nairobi', max_length=180, verbose_name='City')),
                ('is_buyer', models.BooleanField(default=False, help_text='Are you looking for a property', verbose_name='Buyer')),
                ('is_seller', models.BooleanField(default=False, help_text='Are you selling a property', verbose_name='Seller')),
                ('is_agent', models.BooleanField(default=False, help_text='Are you an Agent', verbose_name='Agent')),
                ('rating', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('num_reviews', models.IntegerField(blank=True, default=0, null=True, verbose_name='Reviews')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
