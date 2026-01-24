from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
# Adicionamos EmailConfiguration aqui para ler o remetente
from core.models import TripItem, EmailConfiguration 
from core.utils import get_db_mail_connection

class Command(BaseCommand):
    help = 'Verifica itens com lembrete configurado e envia e-mails'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        self.stdout.write(f"--- Verificando lembretes em {now} ---")

        # 1. Busca itens que TEM lembrete, AINDA NÃO foram enviados e NÃO são 'Sem lembrete' (0)
        items = TripItem.objects.filter(reminder_hours__gt=0, reminder_sent=False)
        
        count_sent = 0

        for item in items:
            # Calcula quando o lembrete deveria ser enviado
            reminder_trigger = item.start_datetime - timedelta(hours=item.reminder_hours)
            
            # Se AGORA já passou do horário do gatilho
            if now >= reminder_trigger:
                try:
                    self.send_reminder_email(item)
                    
                    # Marca como enviado para não mandar de novo
                    item.reminder_sent = True
                    item.save()
                    count_sent += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ E-mail enviado: {item.name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Erro ao enviar {item.name}: {e}"))

        self.stdout.write(f"--- Fim. Total enviados: {count_sent} ---")

    def send_reminder_email(self, item):
        subject = f"Lembrete de Viagem: {item.name}"
        user = item.trip.user
        
        # Define base_url de forma segura
        base_url = getattr(settings, 'BASE_URL', 'https://travel-dev.chmviola.com.br')

        # Corpo do e-mail
        message = f"""
        Olá, {user.first_name or user.username}!
        
        Este é um lembrete para o item da sua viagem "{item.trip.title}".
        
        O QUE: {item.name}
        QUANDO: {item.start_datetime.strftime('%d/%m/%Y às %H:%M')}
        ONDE: {item.location_address or 'Não informado'}
        
        Acesse o sistema para mais detalhes: {base_url}
        """
        
        # --- CORREÇÃO: Busca o remetente no banco ---
        from_email = settings.DEFAULT_FROM_EMAIL # Fallback padrão
        try:
            email_config = EmailConfiguration.objects.first()
            if email_config and email_config.default_from_email:
                from_email = email_config.default_from_email
        except Exception:
            pass # Se der erro na busca, mantém o padrão
            
        # Tenta usar a conexão configurada no banco
        connection = get_db_mail_connection()
        
        send_mail(
            subject,
            message,
            from_email, # <--- Agora usa o e-mail do seu domínio
            [user.email],
            connection=connection,
            fail_silently=False,
        )