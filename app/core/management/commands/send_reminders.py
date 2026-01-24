from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import timedelta
from core.models import TripItem, EmailConfiguration
from core.utils import get_db_mail_connection

class Command(BaseCommand):
    help = 'Verifica itens com lembrete configurado e envia e-mails HTML'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        self.stdout.write(f"--- Verificando lembretes em {now} ---")

        # Busca itens pendentes de aviso
        items = TripItem.objects.filter(reminder_hours__gt=0, reminder_sent=False)
        
        count_sent = 0

        for item in items:
            # Calcula gatilho
            reminder_trigger = item.start_datetime - timedelta(hours=item.reminder_hours)
            
            # Se já passou da hora de avisar
            if now >= reminder_trigger:
                try:
                    self.send_reminder_email(item)
                    
                    # Marca como enviado
                    item.reminder_sent = True
                    item.save()
                    count_sent += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ E-mail enviado: {item.name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Erro ao enviar {item.name}: {e}"))

        self.stdout.write(f"--- Fim. Total enviados: {count_sent} ---")

    def send_reminder_email(self, item):
        subject = f"🔔 Lembrete: {item.name} (em {item.trip.title})"
        user = item.trip.user
        
        # URL do sistema
        base_url = getattr(settings, 'BASE_URL', 'https://travel-dev.chmviola.com.br')
        # Link direto para detalhes da viagem na data do evento
        trip_url = f"{base_url}/viagens/{item.trip.id}/timeline/?date={item.start_datetime.strftime('%Y-%m-%d')}"

        # Contexto para o template HTML
        context = {
            'user': user,
            'item': item,
            'trip': item.trip,
            'system_url': trip_url,
        }

        # 1. Renderiza o HTML
        html_content = render_to_string('emails/reminder_email.html', context)
        # 2. Cria versão texto puro (fallback) removendo tags HTML
        text_content = strip_tags(html_content)

        # Configura Remetente (Banco ou Default)
        from_email = settings.DEFAULT_FROM_EMAIL
        try:
            email_config = EmailConfiguration.objects.first()
            if email_config and email_config.default_from_email:
                from_email = email_config.default_from_email
        except: pass

        # Obtém conexão SMTP customizada
        connection = get_db_mail_connection()
        
        # Cria o objeto de e-mail Multi-Part
        msg = EmailMultiAlternatives(
            subject,
            text_content, # Versão texto
            from_email,
            [user.email],
            connection=connection
        )
        # Anexa a versão HTML
        msg.attach_alternative(html_content, "text/html")
        
        # Envia
        msg.send()