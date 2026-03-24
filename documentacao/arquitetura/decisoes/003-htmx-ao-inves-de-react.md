# RDA-003: HTMX + Tailwind ao invés de React SPA

**Status:** Aceita  
**Data:** 2026-03-24  
**Decisor:** Equipe de Tecnologia FNP

## Contexto

O sistema precisa ser intuitivo e bonito para que toda a equipe da FNP utilize. A pergunta é: precisa ser uma SPA (Aplicação de Página Única) com React/Vue, ou Django Templates com interatividade via HTMX são suficientes?

## Decisão

**Usar Django Templates + HTMX + Tailwind CSS + Alpine.js para o frontend. Não adotar React/SPA neste momento.**

## Justificativa

### HTMX resolve 90% das necessidades

- Busca dinâmica com atraso (digitar e ver resultados sem recarregar)
- Formulários que salvam sem recarregar a página
- Modais e painéis laterais para edição em linha
- Filtros dinâmicos em tabelas
- Paginação infinita
- Confirmações e notificações

### Vantagens sobre SPA

- **Zero etapa de compilação**: sem webpack, sem npm, sem compilação. HTMX é um script CDN.
- **SEO e desempenho**: HTML do servidor, sem JavaScript pesado no cliente.
- **Uma linguagem**: toda a lógica fica em Python. Sem troca de contexto para TypeScript.
- **Depuração simples**: inspecionar HTML no navegador, sem ferramentas React.
- **Tempo de entrega**: 2-3x mais rápido que montar SPA + API REST.

### Tailwind CSS

- Sistema de design pronto com classes utilitárias
- Componentes consistentes sem escrever CSS personalizado
- Integração com Django via `django-tailwind`
- Comunidade enorme, muitos modelos prontos

### Alpine.js para interações locais

- Alternâncias, menus suspensos, abas, contadores
- 15kb, sem etapa de compilação
- Sintaxe em linha no HTML (`x-show`, `x-on:click`)

## Alternativas consideradas

1. **React + Next.js SPA**: descartada por complexidade e falta de conhecimento.
2. **Vue.js + Nuxt**: descartada pelo mesmo motivo.
3. **Django Templates puro (sem HTMX)**: descartada por experiência de usuário inferior (recarregamentos constantes).

## Porta de saída

Se no futuro módulos específicos precisarem de mais interatividade:
1. Adicionar Django REST Framework ao backend
2. Criar componentes React/Vue isolados que consumam a API
3. Integrar via `django-vite` ou similar

Isso não exige reescrever nada — apenas adiciona uma camada opcional.

## Consequências

- Desenvolvedores que só sabem React terão curva de adaptação.
- Interações muito complexas (arrastar-e-soltar, colaboração em tempo real) exigirão avaliação caso a caso.
- A interface será rápida e funcional, mas não terá transições de SPA (sem roteamento no cliente).
