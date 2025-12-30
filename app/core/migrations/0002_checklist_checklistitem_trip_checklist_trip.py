import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Checklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(default='Geral', max_length=50)),
                ('item', models.CharField(max_length=200)),
                ('is_checked', models.BooleanField(default=False)),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.checklist')),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Nome da Viagem')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Início')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Fim')),
                ('status', models.CharField(choices=[('PLANNING', 'Planejamento'), ('CONFIRMED', 'Confirmada'), ('COMPLETED', 'Concluída'), ('CANCELED', 'Cancelada')], default='PLANNING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trips', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Viagem',
                'verbose_name_plural': 'Viagens',
                'ordering': ['-start_date'],
            },
        ),
        migrations.AddField(
            model_name='checklist',
            name='trip',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='checklist', to='core.trip'),
        ),
    ]