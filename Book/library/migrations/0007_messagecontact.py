# Generated by Django 4.1 on 2025-05-01 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0006_merge_0005_commentaire_000X_add_reservation'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('sujet', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('traité', models.BooleanField(default=False)),
            ],
        ),
    ]
