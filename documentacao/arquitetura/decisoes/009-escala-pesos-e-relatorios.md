# RDA-009: Escala, pesos do engajamento, metodologia e relatórios consolidados

**Status:** Aceita
**Data:** 2026-05-18
**Decisor:** Equipe FNP

## Contexto

Após a entrega das 7 fases iniciais (RDA-005 a 008), surgiram demandas
acumuladas no backlog (`documentacao/proximos-passos.md`) que tocam três
frentes complementares:

1. **Escala** — base vai chegar a 5.570 municípios e 10k+ pessoas; precisa
   de índices, paginação e ingestão em massa.
2. **Engajamento expandido** — a nota deixa de depender só de eventos e
   passa a refletir todas as categorias institucionais (instâncias,
   missões, atividades), com pesos editáveis.
3. **Relatórios** — visão consolidada com KPIs, filtros geográficos e
   exportações cobrindo as novas categorias.

## Decisão

### Escala

**Adicionar `Meta.indexes` aos models com filtros frequentes** (Pessoa,
Município, VinculoMunicipio, Instancia, Representacao, Evento, Participacao,
Atividade, Missao, Projeto). 31 índices criados no total — cobrem busca
por nome, tipo, status, datas e relacionamentos vigentes.

**Implementar paginação server-side (`django.core.paginator`)** em Pessoas e
Municípios (50 itens/página). Categorias maiores podem ganhar paginação
conforme volume real exigir. Partial reutilizável
`templates/nucleo/parciais/paginador.html` preserva filtros e busca via GET.

**Comando `importar_municipios_ibge`** consome a API pública
`servicodados.ibge.gov.br` (sem autenticação) e usa `bulk_create` em lotes
de 500 para inserir todos os ~5.570 municípios em poucos segundos. Suporta
flag `--uf` para imports incrementais e `--limpar` para refresh seguro
(preserva associados).

**Hardening LGPD em `producao.py`**: HSTS 30 dias, cookies HttpOnly + SameSite,
sessão de 8h, X-Frame-Options DENY, referrer policy estrita, upload limit
de 10MB, logging estruturado.

### Pesos do engajamento

**Model `PesoEngajamento`** com chaves enumeradas (10 chaves: evento
presencial/online/bônus, representação titular/suplente/diretiva, presença
em atividade, missão nacional/internacional). Cada peso é editável no admin
Unfold sem deploy. Seed inicial via `popular_pesos_engajamento`.

`Engajamento.recalcular` foi reescrito para somar contribuições de **todas
as fontes** (não só eventos), ponderadas pelos pesos. Decaimento anual e
penalidade de adimplência continuam aplicados no final.

### Metodologia

Página dedicada `/engajamento/metodologia/` mostra:
- Fórmula geral em pseudo-código
- Configuração vigente do biênio (meta, decaimento, penalidades)
- Tabela completa de pesos com descrições
- Faixas de nível (alto/médio/baixo/inativo)

Acessível pela sidebar **AJUDA > Metodologia** (logo abaixo de Dicionário)
e pelo admin Unfold em **Ajuda > Pesos do Engajamento**.

### Relatórios

Painel reescrito com:
- 4 KPIs principais (pessoas, municípios, representações, participações)
- 5 KPIs por categoria
- 7 gráficos Chart.js (adimplência, engajamento, regiões, instâncias por
  origem, projetos por status, missões nacional/internacional, atividades
  por status)
- Top 10 municípios mais engajados — clicável, leva para detalhe
- Filtros geográficos região/UF que recalculam os dados
- Export Excel com 6 abas (engajamento, adimplência, pessoas, instâncias,
  projetos, missões)

## Justificativa

### Índices: por que esses campos

Os índices selecionados refletem as queries reais do sistema:
- `nome` em Pessoa/Município/Instância: usado em buscas textuais
- `tipo`, `status`, `vigente`: filtros principais dos selects de cada lista
- `(pessoa, vigente)`, `(municipio, vigente)`: queries de vínculos ativos
- `-data_inicio`, `-data_reuniao`: orderings padrão das listas

Custo: escrita marginalmente mais lenta. Benefício: filtros sobre 10k+
pessoas e 5k+ municípios continuam em milissegundos.

### Paginação server-side em vez de infinite scroll

Mais previsível, indexável (URL muda a cada página), compatível com export
direto e HTMX. Infinite scroll fica para uma fase futura se virar
demanda real de UX.

### Pesos como model em vez de constantes

Constantes em código exigiriam deploy para cada ajuste. Equipe FNP
precisa autonomia para calibrar. Singleton seria muito rígido — model com
chave única por tipo permite ligar/desligar individualmente.

### Recálculo síncrono

Por enquanto, `Engajamento.recalcular` roda sob demanda. Quando a base
crescer e a fórmula ficar mais cara, mover para Celery ou agendado.
Atualmente: ~50 municípios × tempo médio de recálculo = sub-segundo.

### Exportação completa em Excel

Excel ainda é o formato preferido pela equipe FNP para análises. Manter
multi-aba mesmo que pareça redundante — o usuário típico filtra na aba que
precisa.

## Alternativas consideradas

1. **PostgreSQL FTS** em vez de `icontains`: descartado por ora. `icontains`
   com índice em `nome` é suficiente em 10k registros. Revisar se passar
   de 100k.
2. **Celery para recálculo de engajamento**: descartado por excesso de
   complexidade no momento. Cron com management command resolve. Refatorar
   quando o tempo de cálculo virar > 5s.
3. **Pandas/duckdb para relatórios**: descartado. Querys agregadas do ORM
   atendem; gráficos Chart.js renderizam no cliente.
4. **`django-import-export`**: descartado para `importar_municipios_ibge`
   porque queremos controle fino do mapeamento UF→região e do flag
   `eh_capital`. Library seria over-engineering pra um único comando.

## Como usar

### Importar municípios IBGE

```bash
# Importação completa (recomendado na 1ª vez)
python manage.py importar_municipios_ibge

# Apenas uma UF
python manage.py importar_municipios_ibge --uf SP

# Refresh completo (preserva associados FNP)
python manage.py importar_municipios_ibge --limpar
```

### Atualizar pesos do engajamento

Via admin: `/admin/engajamento/pesoengajamento/`. Após alterar, recalcular
todos os engajamentos:

```python
python manage.py shell -c "from aplicacoes.engajamento.models import Engajamento; [e.recalcular() for e in Engajamento.objects.all()]"
```

### Recriar engajamentos dos municípios

```python
python manage.py shell -c "
from aplicacoes.cadastro.models import Municipio
from aplicacoes.engajamento.models import Engajamento
for m in Municipio.objects.all():
    e, _ = Engajamento.objects.get_or_create(municipio=m, bienio='2025-2026')
    e.recalcular()
"
```

## Consequências

- Migrations dos índices são `CREATE INDEX` em colunas existentes — rápido
  em SQLite local; em Postgres do Render leva alguns segundos por índice.
- Paginação muda URLs — link direto pra "pessoa X" pode mudar de página se
  novas pessoas forem cadastradas. Aceitável; o detalhe da pessoa tem URL
  estável por UUID.
- Comando IBGE depende da API pública estar disponível. Quando offline,
  falha gracefully (`try/except` com retry). Para ambientes air-gapped,
  futuramente exportar um dump JSON estático.
- HSTS 30 dias é conservador — após validar HTTPS estável em produção,
  subir para 1 ano + preload.
