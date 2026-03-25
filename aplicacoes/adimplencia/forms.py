"""Formulários de adimplência."""

from django import forms

from aplicacoes.adimplencia.models import Adimplencia


class AdimplenciaForm(forms.ModelForm):
    """Formulário de criação/edição de registro de adimplência."""

    class Meta:
        model = Adimplencia
        fields = ['municipio', 'ano_referencia', 'status', 'valor_devido', 'valor_pago', 'data_pagamento', 'observacao']
        widgets = {
            'municipio': forms.Select(attrs={'class': 'form-input'}),
            'ano_referencia': forms.NumberInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'valor_devido': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'data_pagamento': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
