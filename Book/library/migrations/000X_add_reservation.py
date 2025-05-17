from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('library', '0004_livre_couverture'),
    ]
    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('reservation_id', models.AutoField(primary_key=True, serialize=False)),
                ('date_reservation', models.DateField(default=django.utils.timezone.now)),
                ('livre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='library.livre')),
                ('lecteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='library.lecteur')),
            ],
        ),
    ]
