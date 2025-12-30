from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_tripattachment'),
    ]

    operations = [
        # --- MANTENHA ESTE BLOCO (Cria a tabela API) ---
        migrations.CreateModel(
            name='APIConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(choices=[('WEATHER_API', 'WeatherAPI (Clima)'), ('GOOGLE_MAPS', 'Google Maps API')], max_length=50, unique=True, verbose_name='Serviço/API')),
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

        # --- COMENTE ESTES BLOCOS ABAIXO (O Banco já tem, então ignoramos) ---
        migrations.AddField(
             model_name='item',
             name='weather_condition',
             field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
             model_name='item',
             name='weather_icon',
             field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
             model_name='item',
             name='weather_temp',
             field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]