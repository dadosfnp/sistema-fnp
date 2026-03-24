# RDA-002: PostgreSQL ao invés de Google Sheets como banco de dados

**Status:** Aceita  
**Data:** 2026-03-24  
**Decisor:** Equipe de Tecnologia FNP

## Contexto

Os dados da FNP estão atualmente em múltiplas planilhas Google Sheets. Isso funciona para consultas simples, mas apresenta problemas crescentes: limite de 60 requisições/minuto na API, sem consultas complexas (junções, agregações), sem transações ACID, sem controle de acesso granular, sem integridade referencial, e dificuldade de escalar além de 50-100 mil linhas.

## Decisão

**Usar PostgreSQL 16 como banco de dados principal. Google Sheets será utilizado apenas como fonte de dados para migração inicial.**

## Justificativa

- **Integridade referencial**: chaves estrangeiras garantem que vínculos pessoa↔município sejam consistentes.
- **Consultas complexas**: relatórios de adimplência, ranking de engajamento, cruzamentos — SQL nativo.
- **Busca textual**: busca de pessoas e municípios sem serviço externo.
- **Django ORM**: integração nativa perfeita, migrações automáticas.
- **Desempenho**: índices, planejador de consultas, pool de conexões.
- **Cópias de segurança**: pg_dump automatizado, recuperação pontual.
- **Escalabilidade**: suporta milhões de registros sem degradação.
- **Custo**: gratuito. Serviços gerenciados (Supabase, Railway) oferecem plano grátis generoso.

## Estratégia de migração

1. Mapear todas as planilhas existentes para models Django
2. Criar comandos de gerenciamento `python manage.py importar_planilhas` usando `gspread`
3. Validar dados durante importação (limpar duplicatas, normalizar)
4. Rodar migração em ambiente de homologação antes de produção
5. Manter planilhas somente-leitura por 30 dias como cópia de segurança, depois desativar

## Consequências

- Equipe não poderá mais editar dados diretamente nas planilhas — usará o sistema web.
- Django Admin supre a necessidade de edição rápida que as planilhas ofereciam.
- Relatórios serão mais poderosos com SQL, mas exigem desenvolvimento.
