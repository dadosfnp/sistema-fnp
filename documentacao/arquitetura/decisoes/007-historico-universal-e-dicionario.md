# RDA-007: Histórico universal via LogAlteracao + Dicionário institucional

**Status:** Aceita
**Data:** 2026-05-15
**Decisor:** Equipe FNP

## Contexto

Duas necessidades transversais surgiram juntas:

1. **Histórico de cada entidade** — quando foi criada, quem editou, o que mudou, quando anexou documento. A FNP precisa auditar tudo que acontece em Instâncias, Projetos, Missões, Atividades, Eventos e Documentos. Sem isso, perde-se contexto e não há rastreabilidade institucional.
2. **Dicionário institucional** — o sistema usa termos como "Instância", "Representação", "Co-realização", "Natureza Deliberativa" que não são óbvios para quem entra pela primeira vez. A máscara FNP já documenta 50+ termos numa aba "Dicionário" da planilha — precisamos trazer isso pro sistema.

## Decisão

### Histórico

**Reutilizar o `LogAlteracao` já existente em `aplicacoes/nucleo/models.py`** como fonte única do histórico de qualquer entidade. Adicionar uma função `historico_de(objeto)` no serviço de auditoria que filtra logs por classe e PK.

Cada página de detalhe de categoria inclui um *partial* `templates/nucleo/parciais/timeline_historico.html` que renderiza a timeline visual no rodapé.

### Dicionário

**Criar app novo `aplicacoes/dicionario/`** com model `TermoDicionario` agrupado por seção (Instâncias, Representantes, Atividades, Eventos, Projetos, Missões, Geral). Seed inicial via management command `popular_dicionario` mantendo os termos da máscara FNP em código (auto-suficiente, sem dependência da planilha em runtime).

Sidebar ganha uma seção **Ajuda** abaixo de **Análise** com o item **Dicionário**.

## Justificativa

### Histórico — não criar nova tabela

`LogAlteracao` já existia e era usado por `registrar_criacao`/`registrar_edicao`/`registrar_exclusao` nas views de eventos. Reusá-lo evita duplicação. O par `(modelo, objeto_id)` é genérico — funciona pra qualquer model.

A função `historico_de` encapsula a query e mantém a interface simples:

```python
contexto['historico'] = historico_de(instancia)
```

E o partial é reutilizado em todos os detalhes via `{% include "nucleo/parciais/timeline_historico.html" %}`.

### Histórico — abrange criação de documentos também

A view de upload (`documentos.views.adicionar_documento`) e remoção (`remover_documento`) agora chamam `registrar_criacao`/`registrar_exclusao` no próprio `Documento`. O histórico do **documento** mostra quem o anexou; o histórico da **entidade dona** mostra suas próprias edições. Decidimos *não* fazer o documento criar log na entidade dona — caso contrário a timeline da entidade fica poluída por upload de cada arquivo. Manter separado, com o link clicável no documento para chegar à sua própria timeline.

### Dicionário — model próprio

Hard-codar definições em template seria rígido e bloquearia a equipe da FNP de ajustar definições sem deploy. Model + admin Unfold permite editar a qualquer momento. O seed via management command garante que ambientes novos (Render, máquinas locais) já tenham os 53 termos da máscara FNP carregados.

### Dicionário — seções

A aba "Dicionário" da planilha original já agrupava termos em ~5 grupos. Mantemos essa estrutura via `TermoDicionario.Secao` (TextChoices), inclusive a ordem dentro de cada seção via campo `ordem`. Editores podem reordenar pelo admin com `list_editable`.

## Alternativas consideradas

1. **Histórico em tabela separada por entidade** (ex.: `HistoricoInstancia`) — descartado por duplicação. `LogAlteracao` resolve via filtros.
2. **GenericForeignKey em LogAlteracao** — não necessário; o par `(modelo:str, objeto_id:str)` já basta e mantém compatibilidade com os logs já existentes no banco.
3. **Dicionário em arquivo Markdown/JSON estático** — descartado por não permitir busca via banco e edição online. Modelo do Django + admin Unfold é mais flexível.
4. **Dicionário como modal/tooltip por campo** — fica para uma fase futura (Fase de UX). Por ora, página dedicada acessível pela sidebar.

## Como usar

### Em uma nova categoria

1. Na view de detalhe, importe e chame `historico_de`:
    ```python
    from aplicacoes.nucleo.servicos.auditoria import historico_de
    contexto['historico'] = historico_de(objeto)
    ```
2. No template, inclua o partial:
    ```html
    {% include "nucleo/parciais/timeline_historico.html" %}
    ```
3. Garanta que as views de criação/edição chamem `registrar_criacao` e `registrar_edicao`.

### Adicionar termos novos ao dicionário

- Edite via `/admin/dicionario/termodicionario/` (qualquer editor pode)
- Ou edite `TERMOS` em `aplicacoes/dicionario/management/commands/popular_dicionario.py` e rode `python manage.py popular_dicionario` (idempotente via `update_or_create`)

## Consequências

- Logs antigos (anteriores a esta RDA) podem não cobrir todas as ações (representação, delegação) — refinamento futuro adicionará hooks. Atual cobertura: criação/edição via views front-end + upload/remoção de documentos.
- O dicionário aparece tanto no front (sidebar "Ajuda > Dicionário") quanto no admin Unfold (seção "Ajuda"). Manter as duas entradas em paridade.
- `historico_de` lê das 50 últimas alterações por padrão. Caso uma entidade tenha mais (Projeto antigo com muito tráfego), o limite pode ser elevado pontualmente, ou paginado.
- Não há ainda permissões por entrada de dicionário — qualquer editor pode editar qualquer termo. Refinar quando a equipe ficar maior.
