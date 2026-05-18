"""Formulário de criação/edição de Atividade (reunião de instância)."""

from django import forms

from aplicacoes.atividades.models import Atividade


class AtividadeForm(forms.ModelForm):
    """Formulário com todos os campos relevantes para cadastro de uma atividade."""

    class Meta:
        model = Atividade
        fields = [
            'instancia', 'titulo', 'data_reuniao', 'horario',
            'formato', 'tipo_calendario', 'status', 'local',
            'pauta_resumo', 'ata_resumo',
            'possui_pauta', 'possui_ata', 'possui_lista_presenca',
        ]
        widgets = {
            'instancia': forms.Select(attrs={'class': 'form-input'}),
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Opcional'}),
            'data_reuniao': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'horario': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'formato': forms.Select(attrs={'class': 'form-input'}),
            'tipo_calendario': forms.Select(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'local': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Endereço presencial ou URL'}),
            'pauta_resumo': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'ata_resumo': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
