# RDA-005: Categorias de engajamento institucional (Espaços, Projetos, Missões, Atividades, Eventos)

**Status:** Aceita
**Data:** 2026-05-15
**Decisor:** Equipe FNP

## Contexto

A modelagem inicial concentrava todo o engajamento institucional em dois conceitos: `Evento` (acontecimento pontual com pontuação) e `Pauta` (eixo temático). Esse recorte não cobre adequadamente a realidade da FNP, que monitora simultaneamente:

- **Espaços de Diálogo Federativo** (conselhos, comissões, fóruns) — estruturas permanentes onde a FNP tem representação;
- **Projetos** — iniciativas com prazo definido, escopo e responsáveis;
- **Missões** — deslocamentos institucionais (nacionais ou internacionais) com delegação;
- **Atividades** — reuniões e encontros de uma instância, com pauta, ata e lista de presença;
- **Eventos** — acontecimentos pontuais com participação pontuada.

A máscara de monitoramento (planilha "Máscara_Monitoramento_Representações - FNP.xlsx") já operava com esses cinco conceitos como abas distintas, com campos e regras próprios. Persistir tudo em um único model `Evento` impediria o registro fiel dessas distinções.

## Decisão

**Introduzir cinco apps independentes correspondendo às cinco categorias da máscara FNP, e reorganizar o menu Unfold em três grandes seções: Cadastro, Categorias e Gestão.**

### Estrutura de apps após a decisão

```
aplicacoes/
├── cadastro/         # Pessoa, Município, Pauta, VínculoMunicípio (mantido)
├── instancias/       # NOVO — Instância (Espaço de Diálogo Federativo) e Representação
├── projetos/         # NOVO — Projeto institucional
├── missoes/          # NOVO — Missão e MembroDelegacao
├── atividades/       # NOVO — Atividade (reuniões de Instâncias)
├── eventos/          # Mantido — Evento e Participação
├── adimplencia/      # Mantido
└── engajamento/      # Mantido
```

### Estrutura de menu (Unfold)

- **Cadastro:** Pessoas, Municípios, Vínculos
- **Categorias:** Espaços de Diálogo Federativo, Projetos, Missões, Atividades, Eventos
- **Gestão:** Adimplência, Engajamento
- **Participações e Representações:** atalhos diretos para os modelos de vínculo entre Pessoa e Categoria

## Justificativa

### Fidelidade ao domínio

A operação real da FNP distingue claramente esses cinco objetos. Forçar tudo em um schema único geraria campos vazios, choices misturados e regras de negócio confusas. Apps separados isolam validações e fluxos próprios de cada categoria.

### Reuso do que já está pronto

`Pessoa`, `Município`, `Pauta` e `ModeloBase` continuam centrais e são referenciados por FK a partir das novas categorias. Isso preserva integridade referencial e mantém o ponto único de verdade para identidades.

### Caminho para infraestrutura compartilhada (RDA futura)

Repositório de documentos, histórico de eventos e dicionário de termos serão implementados como apps transversais (`documentos`, `historico`, `dicionario`) consumidos por todas as cinco categorias via `GenericForeignKey`. Manter as categorias separadas torna esse acoplamento opcional e previsível.

## Alternativas consideradas

1. **Polimorfismo em `Evento` via `tipo`**: descartado porque cada categoria tem campos próprios (composição de instância, fonte de recurso de projeto, país de missão) que não cabem em colunas opcionais de um único model.
2. **Tabela única "Iniciativa" com JSONField para extras**: descartado por dificultar consultas tipadas e relatórios agregados.
3. **Manter tudo em `eventos` e usar tags**: descartado por confundir o cadastro de eventos pontuais com o monitoramento de espaços permanentes.

## Mapeamento Excel → Models

| Aba na planilha | App | Modelo principal |
|---|---|---|
| Instâncias | `instancias` | `Instancia` |
| Representantes | `instancias` | `Representacao` |
| Atividade | `atividades` | `Atividade` |
| Eventos | `eventos` | `Evento` (será estendido na Fase 2) |
| Dicionário | (Fase 5) | `dicionario.TermoDicionario` |

Projetos e Missões não constam diretamente da planilha mas foram inseridos como categorias independentes a pedido da equipe, com modelagem própria.

## Plano de implementação

| Fase | Entrega | Status |
|---|---|---|
| 1 | Apps + menu + esta RDA | concluída |
| 2 | Campos do Excel em `Pessoa` (autorização imagem, termo confidencialidade, doc. indicação) e `Evento` (acesso, objetivo, natureza, vínculo com instância) | a fazer |
| 3 | App `documentos` com `GenericForeignKey` — repositório universal anexável a qualquer categoria | a fazer |
| 4 | Linha do tempo / histórico universal por entidade | a fazer |
| 5 | App `dicionario` + botão no header com modal | a fazer |
| 6 | Refinamento da `Participacao` para presença universal | a fazer |
| 7 | App `comunicacao` — mala direta com templates por categoria | a fazer |

## Consequências

- Migrations exigirão atenção: `Representacao` e `Atividade` referenciam `Pessoa` e `Instancia`. Criar migrações em ordem garantida.
- `cadastro.EnvolvimentoPauta` permanece, mas tende a perder relevância conforme `Representacao` cobre o vínculo formal a instâncias.
- Será necessário documentar onde cada usuário deve registrar coisas (dúvida típica: "isso é uma atividade ou um evento?"). Resolveremos com o dicionário (Fase 5).
- O menu fica mais alto; eventualmente migrar para um menu colapsável por seção via configuração Unfold.
