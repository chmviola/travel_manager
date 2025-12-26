from django import forms
from .models import Expense, Trip, TripItem

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['title', 'start_date', 'end_date', 'status']
        
        # Aqui injetamos o CSS do Bootstrap nos campos
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Férias em Paris'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define que o Django deve aceitar o formato com 'T' que o HTML5 envia
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']

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
    class Meta:
        model = Expense
        fields = ['item', 'description', 'amount', 'currency', 'category', 'date']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Jantar em Paris'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alimentação, Transporte...'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        trip_id = kwargs.pop('trip_id', None)
        super().__init__(*args, **kwargs)
        # Filtra os itens para mostrar apenas os daquela viagem específica no dropdown
        if trip_id:
            self.fields['item'].queryset = TripItem.objects.filter(trip_id=trip_id)
            self.fields['item'].empty_label = "Gasto Geral (Nenhum item específico)"