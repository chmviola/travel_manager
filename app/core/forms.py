from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm
from .models import Expense, Trip, TripItem, TripAttachment, APIConfiguration
import re  # <--- Importante para validação regex

#--- FORMULÁRIOS PERSONALIZADOS COM BOOTSTRAP E VALIDAÇÕES ESPECÍFICAS ---
class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['title', 'start_date', 'end_date', 'status']
        
        # Aqui injetamos o CSS do Bootstrap nos campos
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Férias em Paris'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

#--- Formulário para Itens da Viagem ---
class TripItemForm(forms.ModelForm):
    # Sobrescrevemos o campo details para ser um texto simples na visão do usuário
    details = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Voo G3 1234, Assento 12C...'}),
        required=False,
        label="Detalhes / Notas"
    )

    class Meta:
        model = TripItem
        fields = ['item_type', 'name', 'start_datetime', 'end_datetime', 'location_address', 'details']
        
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location_address': forms.TextInput(attrs={'class': 'form-control'}),
            
            # O type='datetime-local' cria o calendário com hora
            # DateTimeInput precisa do formato exato com 'T'
            'start_datetime': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M', 
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'end_datetime': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M', 
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se estiver editando (instance existe) e tiver detalhes
        if self.instance and self.instance.pk and self.instance.details:
            # Pega apenas o valor de 'notes' para mostrar no campo
            self.initial['details'] = self.instance.details.get('notes', '')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Ao salvar, reempacota o texto dentro da estrutura JSON {'notes': ...}
        instance.details = {'notes': self.cleaned_data['details']}
        if commit:
            instance.save()
        return instance

    def clean_details(self):
        """
        Pega o texto que o usuário digitou e transforma em um dicionário JSON
        para o banco de dados aceitar.
        """
        data = self.cleaned_data['details']
        if data:
            # Salva como {"notes": "texto do usuário"}
            return {'notes': data} 
        return {}

#-- Formulário para Gastos da Viagem ---
class ExpenseForm(forms.ModelForm):
    # Sobrescrevemos o campo amount para aceitar vírgula (localize=True)
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        localize=True, # <--- ESSENCIAL: Diz ao Django que a entrada virá com vírgula (pt-br)
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '0,00',
            # Javascript simples para mascarar e ajudar na digitação (opcional, mas ajuda)
            'onkeyup': "this.value = this.value.replace(/[^0-9,.]/g, '')"
        }),
        label="Valor"
    )

    class Meta:
        model = Expense
        fields = ['item', 'description', 'amount', 'currency', 'category', 'date']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Jantar em Paris'}),
            # Removemos o 'amount' daqui pois definimos ele manualmente acima
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alimentação, Transporte...'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        trip_id = kwargs.pop('trip_id', None)
        super().__init__(*args, **kwargs)
        # Filtra os itens para mostrar apenas os daquela viagem específica no dropdown
        if trip_id:
            self.fields['item'].queryset = TripItem.objects.filter(trip_id=trip_id)
            self.fields['item'].empty_label = "Gasto Geral (Nenhum item específico)"

#-- Formulário para Anexos da Viagem ---
class AttachmentForm(forms.ModelForm):
    class Meta:
        model = TripAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Voucher do Hotel'}),
        }

#--- FORMULÁRIOS DE USUÁRIO COM VALIDAÇÃO DE SENHA E BOOTSTRAP ---
class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Senha")
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-control'}), required=False, label="Grupos de Acesso")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'groups', 'is_active', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Criptografa a senha
        if commit:
            user.save()
            self.save_m2m() # Salva os grupos
        return user

#-- Formulário de Edição de Usuário com Validação de Senha ---
class UserEditForm(forms.ModelForm):
    # Na edição, não mostramos o campo de senha para evitar erros de recriptografia
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Grupos de Acesso"
    )

    # --- NOVOS CAMPOS DE SENHA ---
    # required=False permite editar outros dados sem obrigar a mudar a senha
    password = forms.CharField(
        label='Nova Senha', 
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Deixe vazio para manter a atual'})
    )
    confirm_password = forms.CharField(
        label='Confirmar Senha', 
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a nova senha'})
    )
    # -----------------------------

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'groups', 'is_active', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # Checkboxes com estilo customizado
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'margin-left: 10px;'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'margin-left: 10px;'}),
        }

    # --- VALIDAÇÃO DA SENHA ---
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password:
            # 1. Verificar se conferem
            if password != confirm_password:
                self.add_error('confirm_password', "As senhas não conferem.")

            # 2. Complexidade (Regex)
            if len(password) < 8:
                self.add_error('password', "A senha deve ter no mínimo 8 caracteres.")
            
            if not re.search(r'\d', password):
                self.add_error('password', "A senha deve conter pelo menos um número.")

            if not re.search(r'[A-Z]', password):
                self.add_error('password', "A senha deve conter pelo menos uma letra maiúscula.")

            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                self.add_error('password', "A senha deve conter pelo menos um caractere especial.")

        return cleaned_data

    # --- SALVAMENTO ---
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        # Se o campo senha foi preenchido, fazemos o hash
        if password:
            user.set_password(password)
            
        if commit:
            user.save()
            self.save_m2m() # Importante para salvar os Grupos!
            
        return user
    # -----------------------

#-- Formulário para Edição do Perfil do Usuário ---
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seuemail@exemplo.com'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}), # Opcional: Bloquear troca de username
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'username': 'Usuário (Login)',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # CORREÇÃO: .exclude(pk=self.instance.pk) garante que não valida contra si mesmo
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este e-mail já está em uso por outro usuário.")
        return email

#-- Formulário para Troca de Senha com Bootstrap ---
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplica a classe form-control do Bootstrap em todos os campos
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

#-- Formulário para Configuração de Chaves de API ---
class APIConfigurationForm(forms.ModelForm):
    class Meta:
        model = APIConfiguration
        fields = ['key', 'value', 'description', 'is_active']
        widgets = {
            'key': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cole a chave API aqui'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input ml-2'}),
        }

#-- Formulário para Configuração de Chaves de API (Versão Livre) ---
class APIConfigurationForm(forms.ModelForm):
    class Meta:
        model = APIConfiguration
        fields = ['key', 'value', 'is_active']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: GOOGLE_MAPS_API (Maiúsculo, sem espaços)'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cole a chave aqui'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input ml-2'}),
        }
        labels = {
            'key': 'Nome da Chave (ID Interno)',
            'value': 'Valor da API Key',
            'is_active': 'Chave Ativa?',
        }

    def clean_key(self):
        # Força a chave a ser maiúscula e sem espaços para evitar erros no código
        key = self.cleaned_data['key']
        return key.upper().strip().replace(' ', '_')