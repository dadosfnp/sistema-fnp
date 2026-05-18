"""Formulário de criação/edição de Missão institucional."""

from django import forms

from aplicacoes.missoes.models import Missao


class MissaoForm(forms.ModelForm):
    """Formulário com todos os campos relevantes para cadastro de uma missão."""

    class Meta:
        model = Missao
        fields = [
            'titulo', 'tipo', 'status', 'pais', 'cidade', 'objetivo',
            'data_inicio', 'data_fim', 'chefe_delegacao',
            'instancia_vinculada', 'relatorio_resumo',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'pais': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex.: Brasil, França'}),
            'cidade': forms.TextInput(attrs={'class': 'form-input'}),
            'objetivo': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'chefe_delegacao': forms.Select(attrs={'class': 'form-input'}),
            'instancia_vinculada': forms.Select(attrs={'class': 'form-input'}),
            'relatorio_resumo': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }
