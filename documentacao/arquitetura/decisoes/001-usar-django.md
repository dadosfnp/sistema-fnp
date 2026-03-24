# RDA-001: Usar Django ao invés de Next.js/TypeScript

**Status:** Aceita  
**Data:** 2026-03-24  
**Decisor:** Equipe de Tecnologia FNP

## Contexto

A FNP precisa construir um sistema web unificado do zero. Os dados hoje estão em Google Sheets. A equipe de tecnologia tem experiência com Python/Django e nenhuma experiência com TypeScript/Next.js. O sistema é predominantemente centrado em dados (cadastros, relacionamentos, relatórios) e não centrado em interface (não é uma rede social, não precisa de interatividade em tempo real).

## Decisão

**Usar Django 5.x com Python 3.12 como framework principal.**

## Justificativa

### A favor do Django

- **Conhecimento existente**: a equipe já domina Python e Django. Produtividade imediata.
- **Batteries-included**: ORM, Admin, autenticação, migrações, segurança — tudo pronto.
- **Django Admin**: painel administrativo completo praticamente grátis, essencial para operação interna.
- **Maturidade**: framework estável desde 2005, usado por Instagram, Pinterest, Mozilla, NASA.
- **Ecossistema Python BR**: comunidade forte no Brasil, facilidade para contratar.
- **Modelo mental simples**: requisição → visão → resposta. Previsível em qualquer escala do projeto.

### Contra Next.js/TypeScript

- **Curva de aprendizado**: aprender TypeScript + React + Next.js + ecossistema Node durante a construção de um sistema crítico é arriscado.
- **Complexidade crescente**: múltiplos modelos de renderização (SSR, CSR, ISR) adicionam complexidade desnecessária para um sistema interno.
- **Backend limitado**: Next.js é primariamente frontend; para lógica de negócio complexa, precisaríamos de um backend separado de qualquer forma.
- **Overhead de ferramentas**: npm, webpack/turbopack, compilador TypeScript — mais pontos de falha.

## Alternativas consideradas

1. **Next.js + TypeScript**: descartada por falta de conhecimento na equipe e complexidade desnecessária.
2. **Flask**: descartada por ser mais minimalista; Django oferece mais funcionalidade pronta.
3. **Laravel (PHP)**: descartada por falta de conhecimento na equipe.

## Consequências

- Frontend usará Django Templates (não SPA). Interatividade via HTMX.
- Se no futuro precisar de SPA em módulos específicos, pode-se adicionar React consumindo API Django REST Framework.
- Contratação de devs Python/Django é viável no mercado brasileiro.
