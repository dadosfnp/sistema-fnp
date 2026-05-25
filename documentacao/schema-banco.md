# Schema do banco — Sistema FNP

> Gerado automaticamente por `python manage.py gerar_doc_banco`. Não edite à mão — rode o comando após alterar models.

**Total de apps:** 14


---

## App: `adimplencia`

_Adimplência_


### `Adimplencia` — tabela `adimplencia_adimplencia`

Registro anual de adimplência de um município (adimplente/inadimplente/parcial).

- **Verbose:** adimplência
- **Ordenação:** `-ano_referencia`
- **Únicos (composto):** `municipio, ano_referencia`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `municipio` | ForeignKey → `Municipio` (CASCADE) |  |  | município |
| `ano_referencia` | IntegerField |  |  | ano de referência |
| `status` | CharField(20) [choices: `adimplente`, `inadimplente`, `parcial`] |  | `Adimplencia.Status.INADIMPLENTE` |  |
| `valor_devido` | DecimalField |  | `0` | valor devido |
| `valor_pago` | DecimalField |  | `0` | valor pago |
| `data_pagamento` | DateField | ✓ |  | data do pagamento |
| `observacao` | TextField |  |  | observação |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `atividades`


### `Atividade` — tabela `atividades_atividade`

Reunião ou encontro de uma Instância, com pauta, ata e lista de presença.

- **Ordenação:** `-data_reuniao`
- **Índices:** `(-data_reuniao)` | `(instancia, -data_reuniao)` | `(status)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `instancia` | ForeignKey → `Instancia` (CASCADE) |  |  | instância |
| `titulo` | CharField(255) |  |  | Opcional. Se vazio, será composto a partir da instância e data. |
| `data_reuniao` | DateField |  |  | data da reunião |
| `horario` | TimeField | ✓ |  | horário |
| `formato` | CharField(15) [choices: `presencial`, `virtual`, `hibrida`] |  | `Atividade.Formato.PRESENCIAL` |  |
| `tipo_calendario` | CharField(15) [choices: `ordinaria`, `extraordinaria`] |  | `Atividade.TipoCalendario.ORDINARIA` | tipo de reunião |
| `status` | CharField(15) [choices: `agendada`, `realizada`, `cancelada`, `adiada`] |  | `Atividade.Status.AGENDADA` |  |
| `local` | CharField(500) |  |  | Endereço presencial ou URL da chamada virtual. |
| `pauta_resumo` | TextField |  |  | Síntese dos itens. O documento completo vai no repositório de documentos. |
| `ata_resumo` | TextField |  |  | Síntese das deliberações. O documento completo vai no repositório. |
| `possui_pauta` | BooleanField |  | `False` | possui pauta registrada? |
| `possui_ata` | BooleanField |  | `False` | possui ata registrada? |
| `possui_lista_presenca` | BooleanField |  | `False` | possui lista de presença registrada? |
| `documentos` | GenericRelation | ✓ |  |  |
| `presencas` | GenericRelation | ✓ |  |  |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `cadastro`


### `EnvolvimentoPauta` — tabela `cadastro_envolvimentopauta`

Relação N:N entre Pessoa e Pauta com nível de envolvimento (apoiador/engajado/líder).

- **Verbose:** envolvimento em pauta
- **Únicos (composto):** `pessoa, pauta`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `pessoa` | ForeignKey → `Pessoa` (CASCADE) |  |  |  |
| `pauta` | ForeignKey → `Pauta` (CASCADE) |  |  |  |
| `nivel` | CharField(20) [choices: `apoiador`, `engajado`, `lider`] |  | `EnvolvimentoPauta.NivelEnvolvimento.APO | nível de envolvimento |
| `observacao` | TextField |  |  | observação |

**Properties calculadas:** `arquivado`, `pk`

### `Municipio` — tabela `cadastro_municipio`

Município brasileiro com dados geográficos, demográficos e vínculo FNP.

- **Verbose:** município
- **Ordenação:** `nome`
- **Índices:** `(nome)` | `(uf)` | `(regiao)` | `(associado_fnp)` | `(codigo_ibge)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `nome` | CharField(255) |  |  |  |
| `uf` | CharField(2) [choices: `AC`, `AL`, `AP`, `AM`, `BA`, `CE`, ... +21] |  |  |  |
| `codigo_ibge` | IntegerField |  |  | código IBGE |
| `populacao` | IntegerField |  | `0` | população |
| `regiao` | CharField(20) [choices: `norte`, `nordeste`, `centro_oeste`, `sudeste`, `sul`] |  |  | região |
| `brasao` | ImageField(100) |  |  |  |
| `eh_capital` | BooleanField |  | `False` | é capital? |
| `associado_fnp` | BooleanField |  | `False` | associado FNP? |
| `regiao_metropolitana` | CharField(80) |  |  | Nome da Região Metropolitana se o município faz parte (ex: RM de São Paulo). |
| `latitude` | DecimalField | ✓ |  |  |
| `longitude` | DecimalField | ✓ |  |  |

**Properties calculadas:** `adimplencia_atual`, `arquivado`, `pk`

### `Pauta` — tabela `cadastro_pauta`

Eixo temático institucional da FNP (ex.: saúde, mobilidade, segurança).

- **Ordenação:** `nome`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `nome` | CharField(100) |  |  |  |
| `descricao` | TextField |  |  | descrição |
| `icone` | CharField(50) |  |  | Nome do ícone (ex: heart, book) |
| `ativa` | BooleanField |  | `True` | ativa? |

**Properties calculadas:** `arquivado`, `pk`

### `Pessoa` — tabela `cadastro_pessoa`

Pessoa física vinculada à FNP — prefeito, secretário, assessor ou equipe interna.

- **Ordenação:** `nome`
- **Índices:** `(nome)` | `(tipo)` | `(ativo)` | `(email)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `nome` | CharField(255) |  |  |  |
| `email` | EmailField(254) | ✓ |  | e-mail |
| `telefone` | CharField(20) |  |  |  |
| `foto` | ImageField(100) |  |  |  |
| `tipo` | CharField(20) [choices: `interno`, `prefeito`, `vice_prefeito`, `secretario`, `assessor`, `vereador`, ... +1] |  | `Pessoa.TipoPessoa.OUTRO` |  |
| `cargo` | CharField(150) |  |  |  |
| `partido` | CharField(50) |  |  |  |
| `genero` | CharField(20) [choices: `masculino`, `feminino`, `outro`, `nao_informado`] |  | `Pessoa.Genero.NAO_INFORMADO` | gênero |
| `redes_sociais` | JSONField |  | `dict()` | Ex: {"instagram": "@prefeito", "twitter": "@prefeito"} |
| `biografia_curta` | TextField |  |  | biografia curta |
| `mandato_inicio` | DateField | ✓ |  | início do mandato |
| `mandato_fim` | DateField | ✓ |  | fim do mandato |
| `observacoes` | TextField |  |  | observações |
| `ativo` | BooleanField |  | `True` |  |
| `autorizacao_uso_imagem` | BooleanField |  | `False` | Termo de autorização assinado para uso da imagem em comunicações da FNP. |
| `termo_confidencialidade` | BooleanField |  | `False` | Termo de confidencialidade assinado quando aplicável à função na FNP. |

**Properties calculadas:** `arquivado`, `mandato_vigente`, `pk`

### `VinculoMunicipio` — tabela `cadastro_vinculomunicipio`

Vínculo formal entre uma Pessoa e um Município — define papel e período de mandato.

- **Verbose:** vínculo com município
- **Ordenação:** `-vigente, -inicio_mandato`
- **Únicos (composto):** `pessoa, municipio, papel, inicio_mandato`
- **Índices:** `(vigente)` | `(pessoa, vigente)` | `(municipio, vigente)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `pessoa` | ForeignKey → `Pessoa` (CASCADE) |  |  |  |
| `municipio` | ForeignKey → `Municipio` (CASCADE) |  |  | município |
| `papel` | CharField(20) [choices: `prefeito`, `vice_prefeito`, `secretario`, `assessor`, `vereador`, `contato`] |  |  |  |
| `inicio_mandato` | DateField | ✓ |  | início do mandato |
| `fim_mandato` | DateField | ✓ |  | fim do mandato |
| `vigente` | BooleanField |  | `True` | vigente? |
| `observacao` | TextField |  |  | observação |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `comunicacao`

_Comunicação_


### `Envio` — tabela `comunicacao_envio`

Registro de um envio de e-mail em massa a partir de uma entidade.

- **Verbose:** envio de e-mail
- **Ordenação:** `-criado_em`
- **Índices:** `(content_type, object_id)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `content_type` | ForeignKey → `ContentType` (CASCADE) |  |  | tipo da entidade |
| `object_id` | UUIDField(32) |  |  | id do objeto |
| `template` | ForeignKey → `TemplateEmail` (SET_NULL) | ✓ |  | template usado |
| `assunto` | CharField(255) |  |  | Snapshot do assunto na hora do envio (sem placeholders). |
| `corpo` | TextField |  |  | Snapshot do corpo (sem placeholders) — para auditoria. |
| `destinatarios` | JSONField |  | `list()` | Lista de e-mails efetivamente disparados (snapshot). |
| `total_destinatarios` | PositiveIntegerField |  | `0` | total de destinatários |
| `status` | CharField(10) [choices: `enviado`, `falha`, `parcial`] |  | `Envio.StatusEnvio.ENVIADO` |  |
| `enviado_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | enviado por |
| `erro` | TextField |  |  | mensagem de erro |
| `anexo` | FileField(100) | ✓ |  | Arquivo opcional anexado ao envio (máx. 25 MB, executáveis bloqueados). |
| `canal` | CharField(10) [choices: `email`, `whatsapp`, `ambos`] |  | `Envio.Canal.EMAIL` | WhatsApp gera links wa.me (cliquei e envio manual); e-mail envia via SMTP. |
| `links_whatsapp` | JSONField |  | `list()` | Lista de URLs wa.me prontas para o usuário clicar e disparar a mensagem. |
| `entidade` | GenericForeignKey |  |  |  |

**Properties calculadas:** `arquivado`, `pk`

### `TemplateEmail` — tabela `comunicacao_templateemail`

Modelo de e-mail reutilizável, agrupado por categoria do sistema.

- **Verbose:** template de e-mail
- **Ordenação:** `categoria, nome`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `nome` | CharField(200) |  |  | nome do template |
| `categoria` | CharField(15) [choices: `instancias`, `projetos`, `missoes`, `atividades`, `eventos`, `geral`] |  | `TemplateEmail.Categoria.GERAL` | Em que categoria do sistema este template fica disponível. |
| `assunto` | CharField(255) |  |  | Aceita placeholders: {{ entidade }}, {{ pessoa }}, {{ municipio }} |
| `corpo` | TextField |  |  | Aceita placeholders: {{ entidade }}, {{ pessoa }}, {{ municipio }}. |
| `ativo` | BooleanField |  | `True` | ativo? |
| `descricao` | TextField |  |  | Quando usar este template, observações internas. |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `dicionario`

_Dicionário_


### `TermoDicionario` — tabela `dicionario_termodicionario`

Termo conceitual do sistema com definição e exemplos de tipo de dado.

- **Verbose:** termo do dicionário
- **Ordenação:** `secao, ordem, termo`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `termo` | CharField(200) |  |  |  |
| `secao` | CharField(20) [choices: `instancias`, `representantes`, `atividades`, `eventos`, `projetos`, `missoes`, ... +1] |  | `TermoDicionario.Secao.GERAL` | seção |
| `definicao` | TextField |  |  | definição |
| `tipo_de_dado` | CharField(500) |  |  | Exemplos de valores possíveis ou formato esperado. |
| `ordem` | PositiveIntegerField |  | `100` | Menor valor aparece primeiro na seção. |
| `ativo` | BooleanField |  | `True` | ativo? |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `documentos`


### `Documento` — tabela `documentos_documento`

Arquivo anexado a uma entidade qualquer do sistema.

- **Ordenação:** `-criado_em`
- **Índices:** `(content_type, object_id)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `content_type` | ForeignKey → `ContentType` (CASCADE) |  |  | tipo da entidade |
| `object_id` | UUIDField(32) |  |  | UUID do objeto referenciado (Instância, Projeto, Missão etc.). |
| `nome` | CharField(255) |  |  | Título descritivo do documento (ex.: "Ata reunião 12/03/2026"). |
| `tipo` | CharField(20) [choices: `pauta`, `ata`, `programacao`, `lista_presenca`, `apresentacao`, `relatorio`, ... +6] |  | `Documento.TipoDocumento.OUTRO` | tipo de documento |
| `arquivo` | FileField(100) | ✓ |  | Arquivo PDF, imagem ou documento de texto. |
| `link_externo` | URLField(200) |  |  | Alternativa ao upload — URL para o documento hospedado externamente. |
| `descricao` | TextField |  |  | descrição |
| `enviado_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | enviado por |
| `entidade` | GenericForeignKey |  |  |  |

**Properties calculadas:** `arquivado`, `pk`, `url`

---

## App: `engajamento`


### `ConfiguracaoEngajamento` — tabela `engajamento_configuracaoengajamento`

Singleton com parâmetros globais do cálculo de engajamento (meta, decaimento, penalidades).

- **Verbose:** configuração de engajamento

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `bienio_atual` | CharField(10) |  | `'2025-2026'` | Ex: 2025-2026 |
| `meta_bienio` | IntegerField |  | `200` | Pontuação bruta para atingir nota 100. |
| `fator_decaimento` | DecimalField |  | `0.7` | Pontos do ano anterior são multiplicados por este fator. Ex: 0.70 = mantém 70%. |
| `penalidade_inadimplente` | DecimalField |  | `0.3` | Percentual de perda para inadimplentes. Ex: 0.30 = perde 30%. |
| `penalidade_parcial` | DecimalField |  | `0.15` | Percentual de perda para adimplência parcial. Ex: 0.15 = perde 15%. |

**Properties calculadas:** `arquivado`, `pk`

### `Engajamento` — tabela `engajamento_engajamento`

Score de engajamento de um município em um biênio — calculado a partir de participações.

- **Ordenação:** `-pontuacao_normalizada`
- **Únicos (composto):** `municipio, bienio`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `municipio` | ForeignKey → `Municipio` (CASCADE) |  |  | município |
| `bienio` | CharField(10) |  |  | Ex: 2025-2026 |
| `pontuacao_bruta` | IntegerField |  | `0` | pontuação bruta |
| `pontuacao_ano_atual` | IntegerField |  | `0` | pontos ano atual |
| `pontuacao_ano_anterior` | IntegerField |  | `0` | pontos ano anterior |
| `penalidade_adimplencia` | IntegerField |  | `0` | penalidade adimplência |
| `pontuacao_normalizada` | IntegerField |  | `0` | Score final de 0 a 100. |
| `total_participacoes` | IntegerField |  | `0` | total de participações |
| `nivel` | CharField(10) [choices: `alto`, `medio`, `baixo`, `inativo`] |  | `Engajamento.Nivel.INATIVO` | nível |
| `ultima_atualizacao` | DateTimeField |  | `auto_now` | última atualização |

**Properties calculadas:** `arquivado`, `pk`

### `PesoEngajamento` — tabela `engajamento_pesoengajamento`

Peso aplicado a cada tipo de contribuição no cálculo do engajamento.

- **Verbose:** peso do engajamento
- **Ordenação:** `chave, -vigente_de`
- **Índices:** `(chave, ativo)` | `(vigente_de, vigente_ate)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `chave` | CharField(40) [choices: `evento_presencial`, `evento_online`, `evento_bonus_palestrante`, `evento_bonus_organizador`, `representacao_titular`, `representacao_suplente`, ... +4] |  |  |  |
| `peso` | IntegerField |  | `10` | Quantos pontos esta contribuição vale, antes do decaimento e penalidades. |
| `descricao` | TextField |  |  | Explicação institucional do peso — aparece na página de metodologia. |
| `ativo` | BooleanField |  | `True` | ativo? |
| `vigente_de` | DateField | ✓ |  | Data a partir da qual este peso passa a valer. Vazio = sempre vigente. |
| `vigente_ate` | DateField | ✓ |  | Data até a qual este peso vale. Vazio = sem fim. Mudanças preservam histórico. |

**Properties calculadas:** `arquivado`, `pk`

### `SnapshotEngajamento` — tabela `engajamento_snapshotengajamento`

Foto congelada do Engajamento ao final de um bienio.

- **Verbose:** snapshot de engajamento
- **Ordenação:** `-bienio, municipio`
- **Únicos (composto):** `municipio, bienio`
- **Índices:** `(bienio)` | `(municipio, bienio)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `municipio` | ForeignKey → `Municipio` (CASCADE) |  |  |  |
| `bienio` | CharField(10) |  |  | biênio |
| `pontuacao_bruta` | IntegerField |  |  | pontuação bruta |
| `pontuacao_normalizada` | IntegerField |  |  | pontuação normalizada (0-100) |
| `nivel` | CharField(10) |  |  | nível |
| `total_participacoes` | IntegerField |  |  | total de participações |
| `data_snapshot` | DateField |  |  | data do snapshot |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `eventos`


### `Evento` — tabela `eventos_evento`

Evento institucional da FNP com configuração de pontos por modalidade e papel.

- **Ordenação:** `-data_inicio`
- **Índices:** `(-data_inicio)` | `(tipo)` | `(modalidade)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `titulo` | CharField(255) |  |  | título |
| `tipo` | CharField(25) [choices: `assembleia_geral`, `audiencia`, `comissoes`, `conferencia`, `congresso`, `grupos_trabalho`, ... +12] |  |  |  |
| `acesso` | CharField(20) [choices: `publico`, `privado`, `restrito`, `gratuito`, `inscricao_paga`] |  | `Evento.AcessoEvento.PUBLICO` | acesso ao evento |
| `tipo_participacao_fnp` | CharField(25) [choices: `apoio_institucional`, `realizacao`, `co_realizacao`, `patrocinador`, `tecnico`, `politico_institucional`] |  |  | Papel da FNP no evento (apoio, realização, patrocínio etc.). |
| `objetivo` | CharField(30) [choices: `articulacao_politica`, `formacao`, `incidencia_institucional`, `tomada_decisao`] |  |  |  |
| `natureza` | CharField(15) [choices: `deliberativo`, `consultivo`, `formativo`] |  |  |  |
| `modalidade` | CharField(15) [choices: `presencial`, `online`, `hibrido`] |  | `Evento.Modalidade.PRESENCIAL` |  |
| `instancia_vinculada` | ForeignKey → `Instancia` (SET_NULL) | ✓ |  | Espaço de Diálogo Federativo ao qual o evento está relacionado, se houver. |
| `data_inicio` | DateField |  |  | data de início |
| `data_fim` | DateField | ✓ |  | data de término |
| `local` | CharField(255) |  |  | local (lugar) |
| `cidade` | CharField(150) |  |  |  |
| `uf` | CharField(2) [choices: `AC`, `AL`, `AP`, `AM`, `BA`, `CE`, ... +21] |  |  |  |
| `descricao` | TextField |  |  | descrição |
| `pontos_presencial` | IntegerField |  | `10` | Pontos para participação presencial. |
| `pontos_online` | IntegerField |  | `5` | Pontos para participação online. 0 se não aplicável. |
| `pontos_palestrante_bonus` | IntegerField |  | `5` | Pontos extras para quem palestrou. |
| `pontos_organizador_bonus` | IntegerField |  | `5` | Pontos extras para quem organizou. |
| `documentos` | GenericRelation | ✓ |  |  |
| `presencas` | GenericRelation | ✓ |  |  |

**Properties calculadas:** `arquivado`, `pk`

### `Participacao` — tabela `eventos_participacao`

Participação de uma pessoa em um evento — gera pontos para o município vinculado.

- **Verbose:** participação
- **Ordenação:** `-criado_em`
- **Únicos (composto):** `pessoa, evento`
- **Índices:** `(confirmado)` | `(municipio, confirmado)` | `(evento, confirmado)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `pessoa` | ForeignKey → `Pessoa` (CASCADE) |  |  |  |
| `evento` | ForeignKey → `Evento` (CASCADE) |  |  |  |
| `municipio` | ForeignKey → `Municipio` (CASCADE) |  |  | Município que será pontuado por esta participação. |
| `forma_participacao` | CharField(15) [choices: `presencial`, `online`] |  | `Participacao.FormaParticipacao.PRESENCI | forma de participação |
| `papel_no_evento` | CharField(15) [choices: `participante`, `palestrante`, `organizador`, `moderador`, `coordenacao`, `expositor`, ... +1] |  | `Participacao.PapelNoEvento.PARTICIPANTE | papel no evento |
| `confirmado` | BooleanField |  | `False` | confirmado? |
| `pontos_calculados` | IntegerField |  | `0` | Pontos atribuídos automaticamente ao salvar. |
| `data_confirmacao` | DateTimeField | ✓ |  | data de confirmação |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `instancias`

_Espaços de Diálogo Federativo_


### `Instancia` — tabela `instancias_instancia`

Espaço de Diálogo Federativo onde a FNP atua ou tem representação.

- **Verbose:** instância
- **Ordenação:** `nome`
- **Índices:** `(nome)` | `(origem)` | `(status)` | `(origem, status)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `nome` | CharField(255) |  |  | nome do espaço |
| `origem` | CharField(10) [choices: `interna`, `externa`, `evento`] |  |  | Interna (criada pela FNP) \| Externa (espaço de outro órgão) \| Evento. |
| `forma` | CharField(20) [choices: `comissao`, `forum`, `com_representacao`, `sem_representacao`, `reuniao_geral`] |  |  | forma do espaço |
| `categoria` | CharField(15) [choices: `principal`, `secundaria`] |  | `Instancia.Categoria.PRINCIPAL` | Principal (a instância em si) \| Secundária (GT, CT, subcomissão). |
| `instancia_principal` | ForeignKey → `Instancia` (SET_NULL) | ✓ |  | Preencher quando esta for um GT/CT/subcomissão vinculada a uma instância maior. |
| `tipo_arcabouco` | CharField(30) [choices: `lei_federal`, `lei_complementar`, `decreto`, `portaria_ministerial`, `portaria_interministerial`, `regimento`, ... +1] |  |  | tipo do arcabouço legal |
| `numero_arcabouco` | CharField(100) |  |  | Ex.: Lei 3434/2020, Decreto 7890/2021, Portaria 45/2024. |
| `link_arcabouco` | URLField(200) |  |  | link do arcabouço legal |
| `status` | CharField(20) [choices: `em_construcao`, `em_funcionamento`, `inativo`] |  | `Instancia.Status.EM_FUNCIONAMENTO` |  |
| `composicao` | JSONField |  | `dict()` | Número de representantes por esfera. Ex.: {"federal": 2, "estadual": 3, "municipal": 5, "sociedade_civil": 2}. |
| `tempo_mandato` | CharField(15) [choices: `1_ano`, `2_anos`, `3_anos`, `4_anos`, `sem_previsao`] |  |  | tempo do mandato |
| `periodicidade_reunioes` | CharField(15) [choices: `semanal`, `mensal`, `bimestral`, `trimestral`, `semestral`, `em_definicao`] |  |  | periodicidade das reuniões |
| `possui_gt_ct` | BooleanField |  | `False` | Possui Grupos de Trabalho e/ou Comitês Temáticos. |
| `link_site` | URLField(200) |  |  | link do site |
| `ponto_focal_fnp` | ForeignKey → `Pessoa` (SET_NULL) | ✓ |  | Profissional técnico da FNP responsável por apoiar e acompanhar esta instância. |
| `descricao` | TextField |  |  | descrição |
| `documentos` | GenericRelation | ✓ |  |  |

**Properties calculadas:** `arquivado`, `pk`

### `Representacao` — tabela `instancias_representacao`

Vínculo formal de uma Pessoa a uma Instância (titular, suplente, presidência etc.).

- **Verbose:** representação
- **Ordenação:** `-vigente, -inicio_mandato`
- **Únicos (composto):** `instancia, pessoa, funcao, inicio_mandato`
- **Índices:** `(vigente)` | `(instancia, vigente)` | `(pessoa, vigente)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `instancia` | ForeignKey → `Instancia` (CASCADE) |  |  | instância |
| `pessoa` | ForeignKey → `Pessoa` (CASCADE) |  |  | representante |
| `funcao` | CharField(25) [choices: `titular`, `suplente`, `presidente`, `vice_presidente`, `secretario_geral`, `secretario_executivo`, ... +5] |  |  | função |
| `tipo_mandato` | CharField(15) [choices: `primeiro`, `segundo`, `reconducao`] |  |  | tipo de mandato |
| `documento_indicacao` | CharField(15) [choices: `dou`, `oficio`, `portaria`, `email`, `ata`] |  |  | documento de indicação/nomeação |
| `inicio_mandato` | DateField | ✓ |  | início do mandato |
| `fim_mandato` | DateField | ✓ |  | fim do mandato |
| `autorizacao_uso_imagem` | BooleanField |  | `False` | autorização do uso de imagem? |
| `termo_confidencialidade` | BooleanField |  | `False` | termo de confidencialidade assinado? |
| `vigente` | BooleanField |  | `True` | vigente? |
| `observacao` | TextField |  |  | observação |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `missoes`

_Missões_


### `MembroDelegacao` — tabela `missoes_membrodelegacao`

Pessoa que integra a delegação de uma missão, com papel definido.

- **Verbose:** membro da delegação
- **Únicos (composto):** `missao, pessoa`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `missao` | ForeignKey → `Missao` (CASCADE) |  |  | missão |
| `pessoa` | ForeignKey → `Pessoa` (CASCADE) |  |  |  |
| `papel` | CharField(20) [choices: `chefe`, `representante`, `tecnico`, `observador`, `convidado`] |  | `MembroDelegacao.Papel.REPRESENTANTE` | papel na missão |
| `observacao` | TextField |  |  | observação |

**Properties calculadas:** `arquivado`, `pk`

### `Missao` — tabela `missoes_missao`

Deslocamento institucional da FNP, nacional ou internacional, com delegação e objetivos.

- **Verbose:** missão
- **Ordenação:** `-data_inicio`
- **Índices:** `(-data_inicio)` | `(tipo)` | `(status)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `titulo` | CharField(255) |  |  | título |
| `tipo` | CharField(15) [choices: `nacional`, `internacional`] |  |  |  |
| `status` | CharField(15) [choices: `planejada`, `em_andamento`, `realizada`, `cancelada`] |  | `Missao.Status.PLANEJADA` |  |
| `pais` | CharField(100) |  |  | País de destino. Em missões nacionais, deixar em branco ou preencher "Brasil". |
| `cidade` | CharField(150) |  |  |  |
| `objetivo` | TextField |  |  |  |
| `data_inicio` | DateField |  |  | data de início |
| `data_fim` | DateField | ✓ |  | data de término |
| `chefe_delegacao` | ForeignKey → `Pessoa` (SET_NULL) | ✓ |  | chefe da delegação |
| `instancia_vinculada` | ForeignKey → `Instancia` (SET_NULL) | ✓ |  | instância vinculada |
| `relatorio_resumo` | TextField |  |  | Resumo executivo dos resultados da missão (documentos completos vão no repositório). |
| `documentos` | GenericRelation | ✓ |  |  |
| `presencas` | GenericRelation | ✓ |  |  |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `nucleo`

_Núcleo_


### `AceiteTermo` — tabela `nucleo_aceitetermo`

Aceite do termo de uso + política de privacidade (LGPD Art. 8º).

- **Verbose:** aceite de termo
- **Ordenação:** `-aceito_em`
- **Únicos (composto):** `usuario, versao`
- **Índices:** `(usuario, -aceito_em)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `usuario` | ForeignKey → `User` (CASCADE) |  |  |  |
| `versao` | CharField(20) |  |  | versao do termo aceito |
| `ip` | GenericIPAddressField(39) | ✓ |  | IP no aceite |
| `user_agent` | CharField(255) |  |  | user agent |
| `aceito_em` | DateTimeField |  | `auto_now_add` | aceito em |

**Properties calculadas:** `pk`

### `FiltroSalvo` — tabela `nucleo_filtrosalvo`

Atalho de filtros que o usuário salvou para reusar em uma lista.

- **Verbose:** filtro salvo
- **Ordenação:** `escopo, nome`
- **Únicos (composto):** `usuario, escopo, nome`
- **Índices:** `(usuario, escopo)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `usuario` | ForeignKey → `User` (CASCADE) |  |  |  |
| `escopo` | CharField(100) |  |  | Nome da URL da lista, ex. cadastro:lista_municipios. |
| `nome` | CharField(80) |  |  |  |
| `parametros` | CharField(500) |  |  | Query string sem o "?" inicial. |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |

**Properties calculadas:** `pk`

### `LogAcessoSensivel` — tabela `nucleo_logacessosensivel`

Registra LEITURA de dados sensíveis para auditoria LGPD (Art. 37, 46).

- **Verbose:** log de acesso sensível (LGPD)
- **Ordenação:** `-data`
- **Índices:** `(usuario, -data)` | `(modelo, objeto_id)` | `(-data)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `usuario` | ForeignKey → `User` (SET_NULL) | ✓ |  | usuário |
| `modelo` | CharField(80) |  |  | modelo acessado |
| `objeto_id` | CharField(50) |  |  | id do objeto |
| `ip` | GenericIPAddressField(39) | ✓ |  |  |
| `user_agent` | CharField(255) |  |  | user agent |
| `contexto` | CharField(50) |  |  | Ex: "detalhe_pessoa", "exportacao_csv". |
| `data` | DateTimeField |  | `auto_now_add` |  |

**Properties calculadas:** `pk`

### `LogAlteracao` — tabela `nucleo_logalteracao`

Registro imutável de auditoria — grava criação, edição e exclusão de objetos.

- **Verbose:** log de alteracao
- **Ordenação:** `-data`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `usuario` | ForeignKey → `User` (SET_NULL) | ✓ |  |  |
| `acao` | CharField(10) [choices: `criacao`, `edicao`, `exclusao`] |  |  |  |
| `modelo` | CharField(100) |  |  |  |
| `objeto_id` | CharField(50) |  |  | ID do objeto |
| `objeto_repr` | CharField(255) |  |  | representacao |
| `campos_alterados` | JSONField |  | `dict()` | Dicionario com campo: {antes, depois} |
| `data` | DateTimeField |  | `auto_now_add` |  |

**Properties calculadas:** `pk`

### `Perfil` — tabela `nucleo_perfil`

Perfil de acesso vinculado 1:1 ao User Django.

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `usuario` | OneToOneField → `User` (CASCADE) |  |  |  |
| `tipo` | CharField(15) [choices: `visualizador`, `editor`, `admin`, `prefeito`, `externo`] |  | `Perfil.TipoPerfil.VISUALIZADOR` | tipo de perfil |
| `permissoes_extras` | JSONField |  | `list()` | Lista de slugs de permissão (ex: ["pode_importar_ibge", "pode_exportar"]). |
| `municipio_vinculado` | ForeignKey → `Municipio` (SET_NULL) | ✓ |  | Para perfis tipo "prefeito": qual município ele(a) pode visualizar. |
| `status_aprovacao` | CharField(15) [choices: `pendente`, `aprovado`, `bloqueado`, `expirado`] |  | `Perfil.StatusAprovacao.APROVADO` | Externos ficam PENDENTE até DPO/admin liberar. |
| `expira_em` | DateField | ✓ |  | Após esta data, o login é bloqueado automaticamente. |
| `aprovado_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | aprovado por |
| `aprovado_em` | DateTimeField | ✓ |  | aprovado em |
| `justificativa_acesso` | TextField |  |  | Por que este usuário externo precisa acessar? Registrado para auditoria LGPD. |
| `requer_2fa` | BooleanField |  | `False` | Externos e admins devem ter 2FA habilitado. |
| `municipios_visiveis` | M2M → `Municipio` |  |  | Para perfis externos: lista de municípios que pode acessar além do vinculado. |

**Properties calculadas:** `acesso_valido`, `eh_editor`, `pk`

### `PermissaoEntidade` — tabela `nucleo_permissaoentidade`

ACL por objeto — quem pode ver/editar uma entidade específica (LGPD nível 2).

- **Verbose:** permissão por entidade
- **Únicos (composto):** `perfil, content_type, object_id`
- **Índices:** `(content_type, object_id)` | `(perfil, content_type)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `perfil` | ForeignKey → `Perfil` (CASCADE) |  |  |  |
| `content_type` | ForeignKey → `ContentType` (CASCADE) |  |  | tipo da entidade |
| `object_id` | UUIDField(32) |  |  | id do objeto |
| `nivel` | CharField(12) [choices: `visualizar`, `editar`] |  | `PermissaoEntidade.Nivel.VISUALIZAR` | nível |
| `concedido_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | concedido por |
| `concedido_em` | DateTimeField |  | `auto_now_add` | concedido em |
| `expira_em` | DateField | ✓ |  | Acesso temporário a esta entidade. Vazio = sem expiração. |
| `justificativa` | TextField |  |  |  |
| `entidade` | GenericForeignKey |  |  |  |

**Properties calculadas:** `pk`

### `SolicitacaoExclusao` — tabela `nucleo_solicitacaoexclusao`

Pedido de exclusão de dados pelo titular (LGPD Art. 18, VI).

- **Verbose:** solicitacao de exclusao (LGPD)
- **Ordenação:** `-criado_em`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `usuario` | ForeignKey → `User` (SET_NULL) | ✓ |  | usuario solicitante |
| `email_contato` | EmailField(254) |  |  | e-mail de contato |
| `motivo` | TextField |  |  | motivo do pedido |
| `status` | CharField(15) [choices: `pendente`, `em_analise`, `atendida`, `negada`] |  | `SolicitacaoExclusao.Status.PENDENTE` |  |
| `resposta_dpo` | TextField |  |  | resposta do DPO |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atendido_em` | DateTimeField | ✓ |  | atendido em |

**Properties calculadas:** `pk`

### `WebhookSubscription` — tabela `nucleo_webhooksubscription`

Assinatura externa para receber notificacoes de eventos do sistema.

- **Verbose:** webhook

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | BigAutoField |  |  |  |
| `nome` | CharField(80) |  |  | Identificacao amigavel — ex: "PowerBI FNP". |
| `url` | URLField(200) |  |  | Endpoint HTTPS que recebera os POSTs. |
| `secret` | CharField(64) |  |  | Chave compartilhada — usada em X-FNP-Signature (HMAC-SHA256). |
| `eventos` | JSONField |  | `list()` | Lista de slugs. Vazio = nenhum (subscricao desativada). |
| `ativo` | BooleanField |  | `True` | ativo? |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `ultima_entrega` | DateTimeField | ✓ |  | ultima entrega |
| `ultima_falha` | DateTimeField | ✓ |  | ultima falha |
| `contador_falhas` | IntegerField |  | `0` | falhas consecutivas |

**Properties calculadas:** `pk`

---

## App: `presenca`

_Presença_


### `CredenciamentoPrevio` — tabela `presenca_credenciamentoprevio`

Pré-credenciamento enviado por link público — preenche dados e foto antes da visita.

- **Verbose:** pré-credenciamento
- **Ordenação:** `-criado_em`
- **Índices:** `(token)` | `(status, -criado_em)` | `(content_type, object_id)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `token` | CharField(64) |  |  | Slug aleatorio usado na URL publica. Expira em 30 dias. |
| `nome_visitante` | CharField(255) |  |  | nome do visitante |
| `telefone` | CharField(20) |  |  | telefone (WhatsApp) |
| `email` | EmailField(254) |  |  | e-mail |
| `cpf` | CharField(14) |  |  | Opcional. Apenas dígitos ou formato XXX.XXX.XXX-XX. |
| `rg` | CharField(20) |  |  | Opcional. Útil quando o visitante não tem CPF à mão. |
| `organizacao` | CharField(255) |  |  | organização/cargo |
| `motivo` | CharField(255) |  |  | motivo da visita |
| `data_visita_prevista` | DateField | ✓ |  | data prevista da visita |
| `foto` | ImageField(100) | ✓ |  | foto enviada pelo visitante |
| `documentos_aceitos` | BooleanField |  | `False` | Aceite do tratamento de imagem para credenciamento. |
| `face_embedding` | JSONField |  | `list()` | Vetor de 128 floats extraído da foto enviada pelo visitante. |
| `status` | CharField(12) [choices: `pendente`, `preenchido`, `utilizado`, `expirado`] |  | `CredenciamentoPrevio.Status.PENDENTE` |  |
| `expira_em` | DateTimeField |  |  | expira em |
| `criado_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | criado por |
| `visita_gerada` | ForeignKey → `Visita` (SET_NULL) | ✓ |  | visita gerada |
| `content_type` | ForeignKey → `ContentType` (SET_NULL) | ✓ |  | tipo da entidade de origem |
| `object_id` | UUIDField(32) | ✓ |  | Vincula o pré-credenciamento ao evento/atividade/missão que motivou o convite. |
| `entidade_origem` | GenericForeignKey |  |  | entidade origem |

**Properties calculadas:** `arquivado`, `pk`

### `Presenca` — tabela `presenca_presenca`

Registro de presença/ausência de uma pessoa em uma entidade qualquer.

- **Verbose:** presença
- **Ordenação:** `-criado_em`
- **Únicos (composto):** `pessoa, content_type, object_id`
- **Índices:** `(content_type, object_id)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `pessoa` | ForeignKey → `Pessoa` (CASCADE) |  |  |  |
| `content_type` | ForeignKey → `ContentType` (CASCADE) |  |  | tipo da entidade |
| `object_id` | UUIDField(32) |  |  | id do objeto |
| `status` | CharField(15) [choices: `presente`, `ausente`, `justificada`, `em_transito`] |  | `Presenca.Status.PRESENTE` |  |
| `forma` | CharField(12) [choices: `presencial`, `online`, `hibrido`] |  | `Presenca.Forma.PRESENCIAL` | forma de participação |
| `municipio` | ForeignKey → `Municipio` (SET_NULL) | ✓ |  | Município vinculado à pessoa no momento do registro. |
| `observacao` | TextField |  |  | observação |
| `registrado_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | registrado por |
| `entidade` | GenericForeignKey |  |  |  |

**Properties calculadas:** `arquivado`, `pk`

### `Visita` — tabela `presenca_visita`

Visita à sede da FNP registrada pela recepção/secretaria.

- **Verbose:** visita à FNP
- **Ordenação:** `-chegou_em`
- **Índices:** `(-chegou_em)` | `(pessoa)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `pessoa` | ForeignKey → `Pessoa` (SET_NULL) | ✓ |  | Vincular a uma pessoa cadastrada se já existir. |
| `nome_visitante` | CharField(255) |  |  | Preenchido manualmente quando o visitante não tem cadastro. |
| `email` | EmailField(254) |  |  | e-mail |
| `telefone` | CharField(20) |  |  |  |
| `organizacao` | CharField(255) |  |  | Empresa, prefeitura, secretaria etc. |
| `motivo` | CharField(20) [choices: `reuniao`, `evento`, `entrega`, `tecnico`, `institucional`, `outro`] |  | `Visita.Motivo.OUTRO` |  |
| `pessoa_recebida_por` | CharField(255) |  |  | Quem na FNP irá atender (livre — ex.: "Eq. Presidência"). |
| `observacao` | TextField |  |  | observação |
| `municipio` | ForeignKey → `Municipio` (SET_NULL) | ✓ |  | Município que o visitante representa (se aplicável). |
| `chegou_em` | DateTimeField |  | `auto_now_add` | chegou em |
| `saiu_em` | DateTimeField | ✓ |  | saiu em |
| `registrado_por` | ForeignKey → `User` (SET_NULL) | ✓ |  | registrado por |
| `foto` | ImageField(100) | ✓ |  | Foto da pessoa visitando (webcam local ou enviada via pré-credenciamento). |
| `pre_credenciado` | BooleanField |  | `False` | True se a foto/dados vieram de um link enviado antes da visita. |
| `face_embedding` | JSONField |  | `list()` | Vetor de 128 floats extraído da foto via face-api.js para reconhecimento. |

**Properties calculadas:** `ainda_presente`, `arquivado`, `pk`

---

## App: `projetos`


### `Projeto` — tabela `projetos_projeto`

Iniciativa institucional com escopo, prazo e responsáveis definidos.

- **Ordenação:** `-data_inicio, nome`
- **Índices:** `(status)` | `(-data_inicio)` | `(fonte_recurso)`

| Campo | Tipo | Null | Default | Descrição |
|---|---|---|---|---|
| `id` | UUIDField(32) |  | `uuid4()` |  |
| `criado_em` | DateTimeField |  | `auto_now_add` | criado em |
| `atualizado_em` | DateTimeField |  | `auto_now` | atualizado em |
| `arquivado_em` | DateTimeField | ✓ |  | Marca de soft delete. Use arquivar() para esconder sem perder histórico. |
| `nome` | CharField(255) |  |  | nome do projeto |
| `descricao` | TextField |  |  | descrição |
| `objetivo` | TextField |  |  | Resultado pretendido com a execução do projeto. |
| `status` | CharField(15) [choices: `planejamento`, `em_andamento`, `pausado`, `concluido`, `cancelado`] |  | `Projeto.Status.PLANEJAMENTO` |  |
| `fonte_recurso` | CharField(15) [choices: `proprio`, `parceria`, `convenio`, `emenda`, `internacional`, `outro`] |  |  | fonte de recurso |
| `valor_orcado` | DecimalField | ✓ |  | valor orçado (R$) |
| `data_inicio` | DateField | ✓ |  | data de início |
| `data_fim_previsto` | DateField | ✓ |  | previsão de término |
| `data_fim_real` | DateField | ✓ |  | término real |
| `responsavel` | ForeignKey → `Pessoa` (SET_NULL) | ✓ |  | responsável |
| `instancia_vinculada` | ForeignKey → `Instancia` (SET_NULL) | ✓ |  | Espaço de Diálogo Federativo ao qual o projeto está relacionado, se houver. |
| `pautas` | M2M → `Pauta` |  |  | pautas relacionadas |
| `documentos` | GenericRelation | ✓ |  |  |

**Properties calculadas:** `arquivado`, `pk`

---

## App: `relatorios`

_Relatórios_


---

## Diagrama de relacionamentos (texto)

```
FK   Adimplencia.municipio → Municipio
FK   Atividade.instancia → Instancia
FK   EnvolvimentoPauta.pessoa → Pessoa
FK   EnvolvimentoPauta.pauta → Pauta
FK   VinculoMunicipio.pessoa → Pessoa
FK   VinculoMunicipio.municipio → Municipio
FK   Envio.content_type → ContentType
FK   Envio.template → TemplateEmail
FK   Envio.enviado_por → User
FK   Documento.content_type → ContentType
FK   Documento.enviado_por → User
FK   Engajamento.municipio → Municipio
FK   SnapshotEngajamento.municipio → Municipio
FK   Evento.instancia_vinculada → Instancia
FK   Participacao.pessoa → Pessoa
FK   Participacao.evento → Evento
FK   Participacao.municipio → Municipio
FK   Instancia.instancia_principal → Instancia
FK   Instancia.ponto_focal_fnp → Pessoa
FK   Representacao.instancia → Instancia
FK   Representacao.pessoa → Pessoa
FK   MembroDelegacao.missao → Missao
FK   MembroDelegacao.pessoa → Pessoa
FK   Missao.chefe_delegacao → Pessoa
FK   Missao.instancia_vinculada → Instancia
FK   AceiteTermo.usuario → User
FK   FiltroSalvo.usuario → User
FK   LogAcessoSensivel.usuario → User
FK   LogAlteracao.usuario → User
FK   Perfil.usuario → User
FK   Perfil.municipio_vinculado → Municipio
FK   Perfil.aprovado_por → User
M2M  Perfil.municipios_visiveis → Municipio
FK   PermissaoEntidade.perfil → Perfil
FK   PermissaoEntidade.content_type → ContentType
FK   PermissaoEntidade.concedido_por → User
FK   SolicitacaoExclusao.usuario → User
FK   CredenciamentoPrevio.criado_por → User
FK   CredenciamentoPrevio.visita_gerada → Visita
FK   CredenciamentoPrevio.content_type → ContentType
FK   Presenca.pessoa → Pessoa
FK   Presenca.content_type → ContentType
FK   Presenca.municipio → Municipio
FK   Presenca.registrado_por → User
FK   Visita.pessoa → Pessoa
FK   Visita.municipio → Municipio
FK   Visita.registrado_por → User
FK   Projeto.responsavel → Pessoa
FK   Projeto.instancia_vinculada → Instancia
M2M  Projeto.pautas → Pauta
```


## Estatísticas

- **Models totais:** 33
- **Campos totais (inclui relações reversas):** 464
