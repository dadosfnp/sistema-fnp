"""Gera ``documentacao/schema-banco.md`` a partir dos models registrados.

Varre todos os apps em ``aplicacoes/`` extraindo:
- Nome do model + docstring
- Tabela física no Postgres
- Campos (nome, tipo, null, default, help_text, choices)
- Relacionamentos (FK, M2M, OneToOne, GenericForeignKey)
- Meta (verbose_name, ordering, indexes, unique_together)
- Properties que valem como "colunas calculadas"

Idempotente — pode rodar quantas vezes precisar. Sempre regrava o arquivo.

Uso:
    python manage.py gerar_doc_banco
"""

from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import (
    DateField, DateTimeField, ForeignKey, ManyToManyField, OneToOneField,
)


class Command(BaseCommand):
    help = 'Gera documentacao/schema-banco.md a partir dos models.'

    def handle(self, *args, **opts):
        linhas = []
        linhas.append('# Schema do banco — Sistema FNP\n')
        linhas.append('> Gerado automaticamente por `python manage.py gerar_doc_banco`. '
                      'Não edite à mão — rode o comando após alterar models.\n')
        linhas.append(f'**Total de apps:** {len([a for a in apps.get_app_configs() if a.label in self._apps_nossos()])}\n')

        for app_config in sorted(apps.get_app_configs(), key=lambda a: a.label):
            if app_config.label not in self._apps_nossos():
                continue
            models = app_config.get_models()
            if not models:
                continue

            linhas.append(f'\n---\n\n## App: `{app_config.label}`\n')
            verbose = (app_config.verbose_name or '').strip()
            if verbose and verbose.lower() != app_config.label:
                linhas.append(f'_{verbose}_\n')

            for model in sorted(models, key=lambda m: m.__name__):
                linhas.extend(self._documentar_model(model))

        # Resumo final
        linhas.append('\n---\n\n## Diagrama de relacionamentos (texto)\n')
        linhas.append('```')
        linhas.extend(self._diagrama_textual())
        linhas.append('```\n')

        # Estatísticas
        total_models = sum(
            1 for a in apps.get_app_configs()
            if a.label in self._apps_nossos()
            for _ in a.get_models()
        )
        total_campos = sum(
            len(m._meta.get_fields()) for a in apps.get_app_configs()
            if a.label in self._apps_nossos()
            for m in a.get_models()
        )
        linhas.append(f'\n## Estatísticas\n')
        linhas.append(f'- **Models totais:** {total_models}')
        linhas.append(f'- **Campos totais (inclui relações reversas):** {total_campos}\n')

        destino = Path(__file__).resolve().parents[4] / 'documentacao' / 'schema-banco.md'
        destino.write_text('\n'.join(linhas), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(
            f'Doc gerada em {destino} ({total_models} models, {total_campos} campos)'
        ))

    def _apps_nossos(self):
        return {
            'nucleo', 'cadastro', 'adimplencia', 'engajamento', 'eventos',
            'instancias', 'projetos', 'missoes', 'atividades', 'documentos',
            'presenca', 'comunicacao', 'dicionario', 'relatorios',
        }

    def _documentar_model(self, model):
        meta = model._meta
        linhas = [f'\n### `{model.__name__}` — tabela `{meta.db_table}`\n']

        # Docstring
        doc = (model.__doc__ or '').strip()
        if doc:
            # Pega só a primeira linha significativa
            primeira_linha = next((l.strip() for l in doc.split('\n') if l.strip()), '')
            linhas.append(f'{primeira_linha}\n')

        # Meta info
        meta_info = []
        if meta.verbose_name and str(meta.verbose_name).lower() != model.__name__.lower():
            meta_info.append(f'**Verbose:** {meta.verbose_name}')
        if meta.ordering:
            meta_info.append(f'**Ordenação:** `{", ".join(meta.ordering)}`')
        if meta.unique_together:
            constraints = [list(u) if isinstance(u, (list, tuple)) else [u] for u in meta.unique_together]
            constraints_str = ' | '.join(', '.join(c) for c in constraints)
            meta_info.append(f'**Únicos (composto):** `{constraints_str}`')
        if meta.indexes:
            idx_str = ' | '.join(f'`({", ".join(i.fields)})`' for i in meta.indexes)
            meta_info.append(f'**Índices:** {idx_str}')
        if meta_info:
            linhas.append('\n'.join('- ' + m for m in meta_info) + '\n')

        # Tabela de campos
        linhas.append('| Campo | Tipo | Null | Default | Descrição |')
        linhas.append('|---|---|---|---|---|')
        for campo in meta.get_fields():
            linha = self._formatar_campo(campo)
            if linha:
                linhas.append(linha)

        # Properties úteis (não campos)
        props = [
            n for n in dir(model)
            if isinstance(getattr(model, n, None), property)
            and not n.startswith('_')
        ]
        if props:
            linhas.append('\n**Properties calculadas:** ' + ', '.join(f'`{p}`' for p in props))

        return linhas

    def _formatar_campo(self, campo):
        nome = campo.name
        tipo = type(campo).__name__

        # Relacionamentos reversos: ignorar para nao poluir
        if campo.is_relation and campo.auto_created and not campo.concrete:
            return ''

        # Detalhes específicos por tipo
        if isinstance(campo, (ForeignKey, OneToOneField)):
            target = campo.related_model.__name__ if campo.related_model else '?'
            tipo = f'{tipo} → `{target}`'
            on_delete_name = getattr(campo.remote_field, 'on_delete', None)
            if on_delete_name:
                nome_acao = getattr(on_delete_name, '__name__', str(on_delete_name))
                tipo += f' ({nome_acao})'
        elif isinstance(campo, ManyToManyField):
            target = campo.related_model.__name__ if campo.related_model else '?'
            tipo = f'M2M → `{target}`'
        elif hasattr(campo, 'max_length') and campo.max_length:
            tipo = f'{tipo}({campo.max_length})'

        # Choices
        choices = getattr(campo, 'choices', None)
        if choices:
            valores = ', '.join(f'`{c[0]}`' for c in choices[:6])
            if len(choices) > 6:
                valores += f', ... +{len(choices) - 6}'
            tipo += f' [choices: {valores}]'

        null = '✓' if getattr(campo, 'null', False) else ''
        default = self._formatar_default(campo)
        descricao = (getattr(campo, 'help_text', '') or '').strip().replace('|', '\\|').replace('\n', ' ')
        if not descricao and getattr(campo, 'verbose_name', None):
            verbose = str(campo.verbose_name).strip()
            if verbose and verbose.lower() != nome.lower():
                descricao = verbose

        return f'| `{nome}` | {tipo} | {null} | {default} | {descricao} |'

    def _formatar_default(self, campo):
        if isinstance(campo, (DateField, DateTimeField)):
            if getattr(campo, 'auto_now', False):
                return '`auto_now`'
            if getattr(campo, 'auto_now_add', False):
                return '`auto_now_add`'
        from django.db.models import NOT_PROVIDED
        default = getattr(campo, 'default', NOT_PROVIDED)
        if default is NOT_PROVIDED:
            return ''
        if callable(default):
            return f'`{default.__name__}()`'
        return f'`{default!r}`'[:40]

    def _diagrama_textual(self):
        """Lista simples de FKs/M2M no formato `Origem.campo → Destino`."""
        linhas = []
        for app_config in sorted(apps.get_app_configs(), key=lambda a: a.label):
            if app_config.label not in self._apps_nossos():
                continue
            for model in sorted(app_config.get_models(), key=lambda m: m.__name__):
                for campo in model._meta.get_fields():
                    if isinstance(campo, (ForeignKey, OneToOneField, ManyToManyField)):
                        if campo.related_model:
                            tipo_rel = 'M2M' if isinstance(campo, ManyToManyField) else 'FK '
                            linhas.append(
                                f'{tipo_rel}  {model.__name__}.{campo.name} '
                                f'→ {campo.related_model.__name__}'
                            )
        return linhas
