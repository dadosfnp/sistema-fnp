# RDA-008: Presença universal e Mala direta por entidade

**Status:** Aceita
**Data:** 2026-05-15
**Decisor:** Equipe FNP

## Contexto

Duas necessidades complementares para fechar o monitoramento institucional:

1. **Presença universal** — controle de quem efetivamente esteve em Atividades, Eventos, Missões. Eventos já tinham `Participacao` (focado em pontuação de engajamento) e Missões tinham `MembroDelegacao` (focado em papéis). Atividades não tinham registro nenhum, e a equipe queria uma maneira **uniforme** de marcar presença/ausência em qualquer contexto, sem disturbar os modelos especializados.
2. **Mala direta** — enviar e-mails em massa para participantes de uma instância, projeto, missão, atividade ou evento, com templates reutilizáveis por categoria.

## Decisão

### Presença universal

**Criar app `aplicacoes/presenca/` com model `Presenca` via `GenericForeignKey`**, no mesmo padrão arquitetural de `aplicacoes/documentos/` (RDA-006).

Cada model que precisa de controle de presença declara `GenericRelation`:

```python
presencas = GenericRelation('presenca.Presenca', ...)
```

`Presenca` armazena status (Presente / Ausente / Justificada / Em trânsito), forma (Presencial / Online / Híbrido), `pessoa` (FK), `municipio` (snapshot do vínculo vigente), e o usuário que registrou.

Convive — não substitui — `Participacao` (eventos, com pontuação) e `MembroDelegacao` (missões, com papel formal). Refatorar para um único modelo no futuro fica como caminho aberto.

### Mala direta

**Criar app `aplicacoes/comunicacao/` com `TemplateEmail` + `Envio`**:

- `TemplateEmail`: assunto + corpo padrão por categoria (Instâncias / Projetos / Missões / Atividades / Eventos / Geral). Aceita placeholders Django (`{{ pessoa }}`, `{{ municipio }}`, `{{ entidade }}`) renderizados na hora do envio.
- `Envio`: snapshot do disparo (assunto + corpo renderizados, lista de destinatários, status, quem enviou). É a auditoria do que efetivamente saiu.

Destinatários são coletados pelo serviço `comunicacao.servicos.coletar_destinatarios(entidade)`, que tem regra diferente por categoria:
- **Instância** → representantes vigentes
- **Atividade** → representantes vigentes da instância associada
- **Evento** → participações confirmadas
- **Missão** → delegação
- **Projeto** → responsável

## Justificativa

### Presença separada via GFK em vez de unificar Participacao

Refatorar `Participacao` e `MembroDelegacao` em um único model agora exigiria:
- Migrar dados existentes (Render já tem)
- Adaptar a lógica de pontuação de engajamento (FK direto em `Evento`, com bônus por papel)
- Quebrar admin/inlines de eventos/missões já em uso

Custo alto pra benefício difuso. Manter os dois conceitos especializados + adicionar `Presenca` genérico cobre o caso de Atividade (que era o real lacuna) sem mexer no que está funcionando.

### Snapshot de município no Presenca

Pessoas trocam de cargo/município ao longo do tempo. Gravar `municipio` no momento do registro preserva a verdade histórica: "em março/2026, fulano representou São Paulo". Se a pessoa depois assumir cargo em outra cidade, o registro permanece correto.

### Mala direta — templates editáveis

Hardcodar e-mails em código seria rígido. Equipe precisa ajustar tom e conteúdo sem deploy. `TemplateEmail` no banco + Unfold admin permite edição livre. Seed via `popular_templates_email` garante baseline em qualquer ambiente novo.

### Mala direta — Envio como auditoria

Não basta saber que "foi enviado" — em comunicação institucional, importa exatamente *o quê* foi enviado, *para quem* e *quando*. `Envio` guarda essa fotografia em JSON, intocada por edições posteriores do template.

### Mala direta — placeholders Django

Reutilizar o motor de template do próprio Django evita reinventar parsing. Os placeholders são apenas variáveis de contexto Django renderizadas via `Template(texto).render(Context(ctx))`.

## Alternativas consideradas

1. **Unificar Participacao/MembroDelegacao/Presenca em um único model** — descartada pelo custo de migração no momento. Pode acontecer numa fase de consolidação futura.
2. **Mala direta via Celery + filas** — descartado por excesso de complexidade. O envio é síncrono (poucos destinatários, eventualmente lentos). Quando o volume crescer, escalar com Celery vira justificativa real.
3. **Integração direta com Mailgun/SendGrid/SES** — descartada por agora. `EmailMessage` do Django funciona com qualquer SMTP via env vars. Em dev local usa console backend; em produção configura SMTP de provider.

## Como usar

### Marcar presença (front-end)

1. Em qualquer página de detalhe (Atividade, Evento), botão "Marcar presenças"
2. Lista candidatos relevantes (representantes vigentes pra Atividades; pessoas ativas como fallback)
3. Status/Forma/Observação por linha; submete em massa

### Adicionar suporte a presença em nova entidade

```python
# models.py
from django.contrib.contenttypes.fields import GenericRelation

class MinhaEntidade(ModeloBase):
    presencas = GenericRelation('presenca.Presenca', ...)
```

### Disparar mala direta

1. Página de detalhe → botão "Mala direta"
2. Escolhe template (filtrado por categoria) ou escreve do zero
3. Pré-visualiza destinatários
4. Disparar — em dev, sai no console; em prod, vai via SMTP

### Adicionar templates novos

Via admin (`/admin/comunicacao/templateemail/`) ou via seed:

```python
# popular_templates_email.py
TEMPLATES = [
    ('Nome do template', 'categoria', 'Assunto', 'Corpo'),
    ...
]
```

## Consequências

- **Envio sincrôno**: se houver 100+ destinatários e o SMTP estiver lento, a view pode demorar. Aceitável no escopo atual; refatorar com Celery quando for caso real.
- **Sem rastreamento de bounces**: erro de SMTP no momento do disparo é registrado, mas rejeições posteriores (bounce, spam) não voltam. Para tracking real seria necessário webhook do provider.
- **Privacidade dos e-mails**: por enquanto, o admin Unfold mostra os e-mails dos destinatários em `Envio.destinatarios`. Caso vire problema de LGPD, restringir acesso ou mascarar.
- **Compatibilidade com `Participacao`**: dados de presença em Eventos podem ficar em dois lugares (Participacao + Presenca). Os admins enxergam ambos. Documentar isso pra equipe e, num próximo ciclo, decidir convergência.
- **Storage**: `Envio.corpo` pode ficar grande (e-mails extensos). Para reduzir custo de banco, mover para arquivo no futuro se virar problema.
