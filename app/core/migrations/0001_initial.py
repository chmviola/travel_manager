import django.db.models.deletion
import django.db.models.functions.datetime
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='APIConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(choices=[('WEATHER_API', 'WeatherAPI (Clima)'), ('GOOGLE_MAPS', 'Google Maps API'), ('OPENAI_API', 'OpenAI API')], max_length=50, unique=True, verbose_name='Serviço/API')),
                ('value', models.CharField(max_length=255, verbose_name='Chave de Acesso (Key)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descrição/Notas')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuração de API',
                'verbose_name_plural': 'Configurações de API',
            },
        ),
        # migrations.CreateModel(
        #     name='Checklist',
        #     fields=[
        #         ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        #         ('created_at', models.DateTimeField(auto_now_add=True)),
        #     ],
        # ),
        # migrations.CreateModel(
        #     name='ChecklistItem',
        #     fields=[
        #         ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        #         ('category', models.CharField(default='Geral', max_length=50)),
        #         ('item', models.CharField(max_length=200)),
        #         ('is_checked', models.BooleanField(default=False)),
        #         ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.checklist')),
        #     ],
        # ),
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
        # migrations.AddField(
        #     model_name='checklist',
        #     name='trip',
        #     field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='checklist', to='core.trip'),
        # ),
        migrations.CreateModel(
            name='TripItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(choices=[('FLIGHT', 'Voo'), ('HOTEL', 'Hospedagem'), ('ACTIVITY', 'Atração/Passeio'), ('RENTAL', 'Aluguel de Carro'), ('RESTAURANT', 'Restaurante'), ('NOTE', 'Anotação')], max_length=20)),
                ('name', models.CharField(max_length=200, verbose_name='Nome do Item')),
                ('start_datetime', models.DateTimeField(verbose_name='Início/Check-in')),
                ('end_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Fim/Check-out')),
                ('location_lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('location_lng', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('location_address', models.CharField(blank=True, max_length=255, null=True, verbose_name='Endereço')),
                ('weather_temp', models.CharField(blank=True, max_length=10, null=True)),
                ('weather_condition', models.CharField(blank=True, max_length=100, null=True)),
                ('weather_icon', models.CharField(blank=True, max_length=255, null=True)),
                ('details', models.JSONField(blank=True, default=dict, verbose_name='Detalhes Específicos')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.trip')),
            ],
            options={
                'verbose_name': 'Item da Viagem',
                'verbose_name_plural': 'Itens da Viagem',
                'ordering': ['start_datetime'],
            },
        ),
        migrations.CreateModel(
            name='TripAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='trip_files/', verbose_name='Arquivo (PDF/Img)')),
                ('description', models.CharField(blank=True, max_length=100, verbose_name='Descrição (Opcional)')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='core.tripitem')),
            ],
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200, verbose_name='Descrição')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor')),
                ('currency', models.CharField(choices=[('BRL', 'Real (BRL)'), ('USD', 'Dólar Americano (USD)'), ('EUR', 'Euro (EUR)'), ('CLP', 'Peso Chileno (CLP)'), ('ARS', 'Peso Argentino (ARS)'), ('UYU', 'Peso Uruguaio (UYU)'), ('COP', 'Peso Colombiano (COP)'), ('PEN', 'Sol Peruano (PEN)'), ('CAD', 'Dólar Canadense (CAD)'), ('GBP', 'Libra Esterlina (GBP)'), ('CHF', 'Franco Suíço (CHF)'), ('AUD', 'Dólar Australiano (AUD)'), ('JPY', 'Iene Japonês (JPY)')], default='BRL', max_length=3)),
                ('category', models.CharField(max_length=50, verbose_name='Categoria')),
                ('date', models.DateField(default=django.db.models.functions.datetime.Now)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='core.trip')),
                ('item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_expenses', to='core.tripitem')),
            ],
            options={
                'verbose_name': 'Gasto',
                'verbose_name_plural': 'Gastos',
                'ordering': ['date'],
            },
        ),
    ]