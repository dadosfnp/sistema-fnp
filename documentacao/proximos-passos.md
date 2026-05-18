# Próximos passos — sessão de segunda-feira (2026-05-18)

Pontos definidos na sexta 2026-05-15 para iniciar na próxima sessão de trabalho.

---

## 1. Escala: 5 mil municípios + 10 mil+ pessoas

**Contexto:** hoje a base tem ~50 pessoas e 36 municípios catalogados. A meta é suportar **5.570+ municípios** (universo brasileiro) e estimadas **10.000+ pessoas**, partindo de mais de 1.000 já catalogadas no acervo da FNP.

**Trabalho:**
- **Segurança de dados pessoais** (LGPD):
  - Auditar campos sensíveis em `Pessoa` (telefone, e-mail, CPF se aplicável)
  - Política de retenção / pseudo-anonimização para usuários inativos
  - Logs de acesso a dados de pessoas (`LogAlteracao` já registra edições; falta registrar *consultas* sensíveis)
  - Revisar permissões: `eh_editor` é coarse — talvez precise de granularidade por área
- **Desempenho:**
  - Adicionar índices nos campos mais filtrados (`Pessoa.tipo`, `Pessoa.ativo`, `Municipio.uf`, `Municipio.regiao`, `VinculoMunicipio.vigente`)
  - Paginação real nas listas grandes (hoje carrega tudo de uma vez em `lista_pessoas`, `lista_municipios`)
  - `select_related` / `prefetch_related` consistente nas views (alguns lugares já têm, outros não)
  - Cache de queries pesadas (top engajamento na home, contagens dos KPIs)
  - Avaliar `django-debug-toolbar` em dev para identificar N+1
- **Ingestão em massa:**
  - Comando de importação de municípios IBGE (CSV oficial)
  - Validação e deduplicação de pessoas no import
  - Considerar `bulk_create` / `bulk_update` nos seeds em vez de `get_or_create` em loop

**Discussão necessária:** decidir se é hora de migrar de SQLite local pra Postgres local também (em prod já é Postgres). Importar 5 mil municípios pode passar de um threshold onde SQLite começa a ficar chato.

---

## 2. Header informativo em cada página (não só tabelas)

**Contexto:** hoje, ao abrir `/pessoas/` ou `/municipios/`, o usuário vê uma tabela direta. UX pode ser mais rica.

**Trabalho:**
- Cada lista ganha um bloco no topo com:
  - 1 frase explicando a categoria (similar ao header do Dicionário)
  - 2–4 KPIs específicos da categoria (ex.: em `/pessoas/` mostrar quantos prefeitos, quantos secretários, quantos com e-mail cadastrado, % com termo assinado)
  - Quick filters visuais (ex.: cards clicáveis "Ativos / Inativos")
- Manter o componente reaproveitável (talvez um `nucleo/parciais/header_categoria.html`)

---

## 3. Melhorar tela de Relatórios

**Trabalho:**
- Levantar quais relatórios a equipe da FNP realmente precisa imprimir / exportar
- Filtros úteis (período, região, UF, pauta, tipo de pessoa)
- Exportação CSV / Excel / PDF (já temos `reportlab` e `openpyxl` no requirements)
- Gráficos com dados reais (não só ranking de engajamento)
- Templates de relatórios prontos (engajamento por UF, adimplência por região, atividades por instância…)

**Discussão necessária:** quais relatórios são prioridade #1? Pedir lista da equipe.

---

## 4. Renomear "Cadastro" → "Controle"

**Trabalho:**
- Sidebar do front (`templates/base.html`): trocar `CADASTRO` por `CONTROLE`
- Sidebar do admin Unfold (`configuracao/base.py`): mesmo
- Talvez `Pessoas` e `Municípios` ainda fazem sentido nessa seção, mas se "Controle" cobrir mais coisas (auditoria, logs), aproveitar e reorganizar

---

## 5. Acentuação correta nos rótulos da sidebar

**Termos atualmente sem acento que precisam ganhar:**
- `Dicionario` → **Dicionário**
- `Relatorios` → **Relatórios**
- `Adimplencia` → **Adimplência**
- `Missoes` → **Missões**
- `Dialogo` (em "Espacos de Dialogo") → **Diálogo** ("Espaços de Diálogo")

**Onde mexer:** [templates/base.html](templates/base.html) (sidebar do front) e talvez algumas labels em templates dos detalhes / listas. Cuidado para não quebrar comparações `{% if 'dicionario' in request.path %}` — o path da URL continua sem acento, apenas o texto visível muda.

---

## 6. Peso de cada categoria no engajamento

**Contexto:** o engajamento hoje é calculado só com base em `Participacao` em eventos. Precisa expandir para incluir contribuição de:
- Representações em instâncias (titularidade ativa)
- Membros de delegações em missões
- Presenças confirmadas em atividades
- Talvez: documentos contribuídos, participação em projetos

**Trabalho:**
- Definir o modelo de pesos: por categoria? Por tipo de participação dentro da categoria?
- Onde armazenar: pode ser um model `ConfiguracaoEngajamento` (já existe um — revisar) editável pelo admin
- Lógica de recálculo: via signal ou comando agendado?
- UI de edição dos pesos (form simples no admin)

**Discussão necessária:** sentar com a equipe para definir os pesos. Sugestão de baseline:
- Presença confirmada presencial: 10 pts
- Presença online: 5 pts
- Representação titular ativa: 20 pts (constante, não cumulativo por evento)
- Membro de delegação em missão internacional: 30 pts
- Bônus de palestrante: +5 pts

---

## 7. Página de Metodologia (abaixo de Dicionário)

**Contexto:** complementa o ponto 6. Equipe quer um lugar para explicar transparentemente como a nota de engajamento é calculada.

**Trabalho:**
- Nova entrada na sidebar **AJUDA > Metodologia** (logo abaixo de Dicionário)
- Página que combina:
  - Texto explicativo da lógica geral
  - Tabela dinâmica dos pesos atuais (lendo do model de configuração)
  - Exemplo prático (município X tem Y representação ativa + Z presenças = N pontos = nível "Médio")
  - Histórico de alterações nos pesos (quando mudou, por quem)
- Pode ser implementado como app `metodologia` ou como página estática dentro de `aplicacoes/engajamento/`

---

## 8. Lista de presença: adicionar pessoa nova "na hora"

**Contexto:** na tela de "Marcar presenças" só aparecem candidatos pré-cadastrados (representantes vigentes da instância). Se alguém novo entra na reunião, hoje precisa sair, criar Pessoa, voltar e marcar.

**Trabalho:**
- Botão "+ Adicionar pessoa" no form de presença
- Modal HTMX com campos mínimos: nome, e-mail, município (autocomplete), tipo
- Salva como Pessoa + cria Representacao automática (se for em Atividade) + marca presença
- Validação para evitar duplicatas (mesmo nome+e-mail)

---

## 9. Mala direta — bug + modal na mesma página

**Bug reportado:** mala direta veio com erro (print fornecido pelo usuário). **Investigar primeiro:**
- Reproduzir o cenário
- Provavelmente erro no envio síncrono (SMTP não configurado em dev resulta em backend console — ok) ou no `Template.render` com placeholders ausentes

**Refatoração do fluxo:**
- Substituir a página dedicada `/comunicacao/enviar/...` por um **modal HTMX na própria página de detalhe** da entidade
- Modal com:
  - Campo **Assunto**
  - Campo **Corpo** (textarea grande)
  - Campo **Anexo** (file input, opcional — pode reusar `Documento`?)
  - **Lista preview dos destinatários** já carregada (puxando da entidade — eventos/atividades/etc.)
  - Botão "Enviar agora"
- Acentuar que a lista vem **automaticamente** da entidade (participantes do evento, representantes da atividade, delegação da missão)
- Confirmação pré-envio (modal de "tem certeza?" se forem muitos destinatários)

**Considerar:**
- Anexar documento existente do repositório vs. fazer upload novo
- Em produção: configurar SMTP real (Mailgun? SES? Gmail SMTP com app-password?)

---

## 10. 5 sugestões de UX/UI para o sistema

**A entregar na segunda como abertura da sessão.** Pensar em:
- Densidade de informação nas listas
- Atalhos de teclado
- Estados vazios (empty states) mais informativos
- Onboarding pra usuários novos
- Mobile / responsivo
- Modo escuro?
- Feedback visual de ações (toasts, animações sutis)
- Acessibilidade (contraste, navegação por teclado, screen reader)

Vou preparar uma lista priorizada com mockup/descrição para cada uma.

---

## Ordem sugerida para segunda

Trabalho de maior dependência primeiro:

1. **Item 5** (acentos) — rápido, melhora percepção imediata
2. **Item 4** (renomear Controle) — junto com 5, mesma área
3. **Item 9** (mala direta — bug + modal) — destrava feature já entregue
4. **Item 8** (adicionar pessoa na hora) — relacionado a presença, complementa
5. **Item 2** (header informativo) — UX horizontal, melhora todas as páginas
6. **Item 6 + 7** (peso engajamento + metodologia) — tem decisão de negócio, melhor discutir junto
7. **Item 3** (melhorar relatórios) — precisa de input da equipe primeiro
8. **Item 1** (escala 5k municípios) — projeto maior, dividir em sub-tarefas
9. **Item 10** (sugestões UX/UI) — entregar como abertura, discussão livre

Itens 1, 3, 6, 7 precisam de **discussão com a equipe FNP antes da implementação**.
