"""Formulário de upload de Documento."""

from django import forms

from aplicacoes.documentos.models import Documento


class DocumentoForm(forms.ModelForm):
    """Formulário para anexar um documento a uma entidade qualquer.

    ``content_type``, ``object_id`` e ``enviado_por`` são preenchidos
    automaticamente pela view com base na URL e no usuário autenticado.
    """

    class Meta:
        model = Documento
        fields = ['nome', 'tipo', 'arquivo', 'link_externo', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'link_externo': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def clean(self):
        """Exige que pelo menos um entre arquivo e link_externo seja fornecido."""
        cleaned = super().clean()
        arquivo = cleaned.get('arquivo')
        link = cleaned.get('link_externo')
        if not arquivo and not link:
            raise forms.ValidationError(
                'Informe um arquivo para upload ou um link externo.'
            )
        return cleaned
