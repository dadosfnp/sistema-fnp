"""Formulário de criação/edição de Projeto institucional."""

from django import forms

from aplicacoes.projetos.models import Projeto


class ProjetoForm(forms.ModelForm):
    """Formulário com todos os campos relevantes para cadastro de um projeto."""

    class Meta:
        model = Projeto
        fields = [
            'nome', 'descricao', 'objetivo', 'status', 'fonte_recurso',
            'valor_orcado', 'data_inicio', 'data_fim_previsto', 'data_fim_real',
            'responsavel', 'pautas', 'instancia_vinculada',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'objetivo': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'fonte_recurso': forms.Select(attrs={'class': 'form-input'}),
            'valor_orcado': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_fim_previsto': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_fim_real': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'responsavel': forms.Select(attrs={'class': 'form-input'}),
            'pautas': forms.SelectMultiple(attrs={'class': 'form-input', 'size': '5'}),
            'instancia_vinculada': forms.Select(attrs={'class': 'form-input'}),
        }
