from django import forms
from .models import Expense, Trip, TripItem, TripAttachment
from django.contrib.auth.models import User, Group

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

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = TripAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Voucher do Hotel'}),
        }

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

class UserEditForm(forms.ModelForm):
    # Na edição, não mostramos o campo de senha para evitar erros de recriptografia
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-control'}), required=False, label="Grupos de Acesso")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'groups', 'is_active', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input ml-2'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input ml-2'}),
        }
