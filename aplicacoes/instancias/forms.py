"""Formulário de criação/edição de Instância (Espaço de Diálogo Federativo)."""

from django import forms

from aplicacoes.instancias.models import Instancia


class InstanciaForm(forms.ModelForm):
    """Formulário com todos os campos relevantes para cadastro de uma instância."""

    class Meta:
        model = Instancia
        fields = [
            'nome', 'origem', 'forma', 'categoria', 'instancia_principal',
            'tipo_arcabouco', 'numero_arcabouco', 'link_arcabouco',
            'status', 'tempo_mandato', 'periodicidade_reunioes',
            'possui_gt_ct', 'link_site', 'ponto_focal_fnp', 'descricao',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'origem': forms.Select(attrs={'class': 'form-input'}),
            'forma': forms.Select(attrs={'class': 'form-input'}),
            'categoria': forms.Select(attrs={'class': 'form-input'}),
            'instancia_principal': forms.Select(attrs={'class': 'form-input'}),
            'tipo_arcabouco': forms.Select(attrs={'class': 'form-input'}),
            'numero_arcabouco': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex.: Lei 3434/2020'}),
            'link_arcabouco': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'tempo_mandato': forms.Select(attrs={'class': 'form-input'}),
            'periodicidade_reunioes': forms.Select(attrs={'class': 'form-input'}),
            'link_site': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'ponto_focal_fnp': forms.Select(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
