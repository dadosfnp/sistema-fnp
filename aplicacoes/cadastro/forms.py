from django import forms

from aplicacoes.cadastro.models import Municipio, Pessoa, VinculoMunicipio


class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = [
            'nome', 'email', 'telefone', 'tipo', 'cargo', 'partido',
            'genero', 'biografia_curta', 'mandato_inicio', 'mandato_fim',
            'ativo', 'observacoes',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'telefone': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'cargo': forms.TextInput(attrs={'class': 'form-input'}),
            'partido': forms.TextInput(attrs={'class': 'form-input'}),
            'genero': forms.Select(attrs={'class': 'form-input'}),
            'biografia_curta': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'mandato_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'mandato_fim': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class MunicipioForm(forms.ModelForm):
    class Meta:
        model = Municipio
        fields = [
            'nome', 'uf', 'codigo_ibge', 'populacao', 'regiao',
            'eh_capital', 'associado_fnp', 'latitude', 'longitude',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'uf': forms.Select(attrs={'class': 'form-input'}),
            'codigo_ibge': forms.NumberInput(attrs={'class': 'form-input'}),
            'populacao': forms.NumberInput(attrs={'class': 'form-input'}),
            'regiao': forms.Select(attrs={'class': 'form-input'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.0000001'}),
        }
