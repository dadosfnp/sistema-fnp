"""Formulários de eventos e participações."""

from django import forms

from aplicacoes.eventos.models import Evento, Participacao


class EventoForm(forms.ModelForm):
    """Formulário de criação/edição de evento."""

    class Meta:
        model = Evento
        fields = [
            'titulo', 'tipo', 'modalidade', 'data_inicio', 'data_fim',
            'local', 'descricao', 'pontos_presencial', 'pontos_online',
            'pontos_palestrante_bonus', 'pontos_organizador_bonus',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'modalidade': forms.Select(attrs={'class': 'form-input'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'local': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'pontos_presencial': forms.NumberInput(attrs={'class': 'form-input'}),
            'pontos_online': forms.NumberInput(attrs={'class': 'form-input'}),
            'pontos_palestrante_bonus': forms.NumberInput(attrs={'class': 'form-input'}),
            'pontos_organizador_bonus': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class ParticipacaoForm(forms.ModelForm):
    """Formulário de registro de participação em evento."""

    class Meta:
        model = Participacao
        fields = ['pessoa', 'evento', 'municipio', 'forma_participacao', 'papel_no_evento', 'confirmado']
        widgets = {
            'pessoa': forms.Select(attrs={'class': 'form-input'}),
            'evento': forms.Select(attrs={'class': 'form-input'}),
            'municipio': forms.Select(attrs={'class': 'form-input'}),
            'forma_participacao': forms.Select(attrs={'class': 'form-input'}),
            'papel_no_evento': forms.Select(attrs={'class': 'form-input'}),
        }
