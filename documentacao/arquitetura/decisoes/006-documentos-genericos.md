# RDA-006: Repositório de documentos universal via GenericForeignKey

**Status:** Aceita
**Data:** 2026-05-15
**Decisor:** Equipe FNP

## Contexto

As cinco categorias (Instâncias, Projetos, Missões, Atividades, Eventos), e potencialmente outras entidades (Pessoa, Município, Representação), precisam de um repositório de documentos: pauta, ata, lista de presença, apresentação, relatório, certificado, ofício, decreto.

Caminhos possíveis:
1. **Tabela `Documento` por categoria** — duplica colunas, dificulta busca cruzada.
2. **JSONField com lista de arquivos** — sem filtragem, sem auditoria, sem permissões.
3. **App único `documentos` com `GenericForeignKey`** — uma tabela serve a todas as entidades.

## Decisão

**Implementar a opção 3: app `aplicacoes/documentos/` com model único `Documento` usando `GenericForeignKey` (`content_type` + `object_id`).**

Cada model que precisa de documentos declara um `GenericRelation` apontando para `documentos.Documento`, expondo `obj.documentos.all()` para uso em templates e queries.

## Justificativa

### Reuso máximo

Uma única migration cria a estrutura para todas as categorias. Novas entidades que queiram suporte a documentos só precisam adicionar uma linha `documentos = GenericRelation(...)` em seu model.

### Centralização da auditoria

`enviado_por`, `criado_em` e `atualizado_em` ficam num único lugar. Buscas administrativas tipo "todos os documentos enviados na semana" são triviais.

### Tipo padronizado

`Documento.TipoDocumento` codifica os tipos canônicos da máscara FNP (Pauta, Ata, Lista de Presença, Apresentação, Relatório, Certificado). Relatórios agregados ficam consistentes.

### Inline genérico no admin

`DocumentoGenericInline` (subclasse de `GenericTabularInline`) é incluída em cada `ModelAdmin` (Instância, Projeto, Missão, Atividade, Evento) sem código duplicado.

### Upload ou link externo

O model aceita `arquivo` (upload local) **ou** `link_externo` (URL externa — Google Drive, OneDrive, sites públicos). A propriedade `Documento.url` resolve transparente para o template.

## Alternativas consideradas

1. **Tabela por categoria**: descartada por duplicação. Mudar o tipo "Ata" exigiria migration em 5 lugares.
2. **JSONField**: descartada por perda de tipagem, busca e permissões — perde-se Django Admin gratuito.
3. **App externo (django-attachments, django-filer)**: descartado para evitar dependência pesada num projeto que ainda é jovem; pode ser reavaliado quando precisarmos de gestão avançada (versionamento, thumbnails, OCR).

## Como usar (esqueleto)

```python
# models.py de qualquer app
from django.contrib.contenttypes.fields import GenericRelation

class MinhaEntidade(ModeloBase):
    nome = models.CharField(...)
    documentos = GenericRelation(
        'documentos.Documento',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='minha_entidade',
    )

# admin.py
from aplicacoes.documentos.admin import DocumentoGenericInline

class MinhaEntidadeAdmin(ModelAdmin):
    inlines = [..., DocumentoGenericInline]

# template
{% for doc in obj.documentos.all %}
  <a href="{{ doc.url }}">{{ doc.nome }}</a> — {{ doc.get_tipo_display }}
{% endfor %}

# URL para listar/anexar documentos de uma entidade
{% url 'documentos:listar' app_label='instancias' model_name='instancia' object_id=instancia.pk %}
```

## Consequências

- Como `object_id` é UUID, queries cruzadas precisam dos índices definidos em `Meta.indexes`. Já incluídos.
- Para FK reverso (`evento.documentos.all()`) funcionar, cada model dono precisa declarar `GenericRelation`. Documentar isso no checklist quando criar nova categoria.
- O storage padrão do Django (`FileField`) salva em `MEDIA_ROOT`. No Render usaremos disco efêmero por enquanto — quando isso for um problema, migrar para S3/Cloudflare R2 via `django-storages`.
- Não há permissões por documento (todos editores podem anexar/remover em qualquer entidade). Refinar quando perfis ficarem mais granulares.
