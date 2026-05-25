# DPIA + Registro de Operações de Tratamento — Sistema FNP

**Versão:** 2026-05 • **Última atualização:** 2026-05-25
**Controlador:** Frente Nacional de Prefeitos (FNP)
**Encarregado (DPO):** dpo@fnp.org.br

Este documento atende ao Art. 37 da LGPD (Registro das Operações de Tratamento) e funciona como Relatório de Impacto à Proteção de Dados (DPIA) simplificado para fins de fiscalização pela ANPD.

---

## 1. Finalidade do tratamento

Gestão institucional da Frente Nacional de Prefeitos: cadastro de pessoas (prefeitos, secretários, equipe interna), municípios associados, controle de adimplência, engajamento, eventos, missões, comunicação e prestação de contas.

## 2. Hipóteses legais (Art. 7º LGPD)

| Hipótese | Aplicação |
|---|---|
| Execução de contrato | Dados de municípios associados e seus representantes |
| Legítimo interesse | Dados de contato institucional de prefeitos e secretários |
| Consentimento | Uso de imagem (foto institucional, foto de credenciamento) |
| Obrigação legal | Auditoria, prestação de contas, retenção fiscal |
| Tutela da saúde (não se aplica) | — |
| Política pública (não se aplica) | — |

## 3. Categorias de dados tratados

### 3.1 Dados pessoais comuns
- Nome completo, cargo, partido político, organização
- E-mail institucional, telefone
- Município de vínculo, data de início/fim de mandato
- Foto institucional (mediante autorização — `Pessoa.autorizacao_uso_imagem`)
- Biografia curta, redes sociais públicas

### 3.2 Dados pessoais sensíveis tratados
- **Foto + embedding facial** (face-api.js) — visitantes pré-credenciados
- **CPF, RG** — visitantes (opcional, em `CredenciamentoPrevio`)

> Embeddings faciais são considerados dados biométricos sensíveis pelo Art. 5º, II LGPD. Tratados apenas para identificação na recepção, sob consentimento expresso (`documentos_aceitos=True`), com retenção máxima conforme política de purga.

### 3.3 Dados técnicos / de auditoria
- IP, user-agent, timestamps
- Logs de criação, edição, exclusão (`LogAlteracao`)
- Logs de leitura de dados sensíveis (`LogAcessoSensivel`)
- Aceites de termo (`AceiteTermo`)

## 4. Operações de tratamento

| Operação | Onde acontece | Quem executa |
|---|---|---|
| Coleta | Forms web, importação IBGE, pré-credenciamento WhatsApp/web | Equipe FNP, próprio visitante |
| Armazenamento | PostgreSQL (Digital Ocean) | Hospedagem gerida (com SLA LGPD) |
| Consulta | Sistema FNP, admin Django | Usuários autenticados conforme perfil |
| Compartilhamento interno | Equipe FNP autorizada | Conforme escopo do `Perfil` |
| Eliminação | Comando `purgar_dados_antigos` | DPO (manual ou cron) |
| Anonimização | Comando `purgar_dados_antigos` (Visitas >5 anos) | DPO |

## 5. Compartilhamento com terceiros

- **Não há venda nem cessão comercial de dados.**
- Hospedagem: Digital Ocean (PostgreSQL gerenciado), Render.com (app + media). Ambos com cláusulas LGPD/GDPR e residência fora do Brasil — risco mitigado por criptografia em trânsito e at-rest no provedor.
- Google (OAuth login + Workspace e-mail FNP): contratualmente obrigado por GDPR/LGPD.
- Autoridades públicas: apenas mediante ordem judicial.

## 6. Período de retenção

| Dado | Retenção | Ação ao final |
|---|---|---|
| Pessoas e Municípios (cadastro ativo) | Indeterminado enquanto vínculo institucional | Anonimização sob pedido |
| Visitas à FNP | 5 anos | Anonimização (preserva estatística) |
| LogAlteracao | 2 anos | Eliminação |
| LogAcessoSensivel | 2 anos | Eliminação |
| Envios de mala direta | 5 anos | Eliminação |
| Pré-credenciamento expirado/usado | 1 ano | Eliminação |
| Solicitação de exclusão atendida | 5 anos (auditoria ANPD) | Eliminação |

## 7. Medidas técnicas e organizacionais (Art. 46)

### Técnicas
- TLS 1.2+ em todas as conexões (HTTPS forçado em produção)
- Senhas com hash PBKDF2-SHA256 (Django padrão)
- Validação rigorosa de uploads (magic bytes + Pillow.verify)
- CSRF + XSS protection (Django middleware)
- HSTS habilitado (30 dias) com X-Frame-Options DENY
- Rate limit em mala direta (10 envios/h por usuário)
- Mascaramento automático de PII (CPF/e-mail/telefone) em logs persistentes
- 2FA TOTP obrigatório para perfis externos e administradores
- Bloqueio de brute-force (django-axes: 5 tentativas → cooloff 1h)

### Organizacionais
- Modelo de perfis com escopo definido (visualizador, editor, admin, prefeito, externo)
- ACL por entidade (`PermissaoEntidade`) para acesso granular a objetos específicos
- Aprovação manual obrigatória para usuários de domínio externo
- Auditoria de leitura de dados sensíveis (`LogAcessoSensivel`)
- Termo de uso versionado com aceite expresso bloqueante
- Política de privacidade pública e acessível em `/conta/politica-privacidade/`
- DPO designado e e-mail público no rodapé de todas as páginas

## 8. Direitos dos titulares (Art. 18) — como exercer

| Direito | Como o titular exerce |
|---|---|
| Confirmação de tratamento | E-mail ao DPO |
| Acesso aos dados | Botão "Exportar meus dados" no rodapé → JSON |
| Correção | Contatar gestor da FNP |
| Anonimização/eliminação | "Solicitar exclusão" no rodapé → DPO analisa em 15 dias |
| Portabilidade | Mesma exportação JSON serve |
| Informação sobre compartilhamentos | Este documento |
| Revogação de consentimento | E-mail ao DPO (implica suspensão de acesso) |

## 9. Avaliação de risco (matriz simplificada)

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Vazamento de credenciais | Média | Alto | 2FA obrigatório p/ externos; axes; mascaramento PII em logs |
| Acesso indevido por usuário interno | Baixa | Alto | LogAcessoSensivel + escopo por perfil + alertas de volume anormal (futuro) |
| SQL injection / XSS | Baixa | Alto | Django ORM + auto-escape; testes; CSP (futuro) |
| Upload malicioso | Baixa | Médio | Magic bytes + Pillow.verify + bloqueio de extensões executáveis |
| Exposição de embedding facial | Baixa | Alto | Não exportado em API; armazenamento em JSONField protegido por perfil |
| Provedor cloud comprometido | Muito baixa | Crítico | SLA + criptografia at-rest do provedor; backup criptografado |
| Retenção excessiva | Média | Médio | Purga automática agendada; anonimização de Visitas >5 anos |

## 10. Plano de resposta a incidente (resumo)

1. **Detecção:** DPO/admin nota acesso anômalo via `LogAcessoSensivel` ou notificação de provedor.
2. **Contenção:** Bloquear conta envolvida (`status_aprovacao=bloqueado`), revogar tokens API.
3. **Análise:** Identificar escopo via logs de acesso e auditoria.
4. **Notificação ANPD:** Se houver risco aos titulares — em até 48h via `comunicado@anpd.gov.br`.
5. **Notificação dos titulares:** E-mail individual com orientações.
6. **Documentação:** Adicionar incidente neste documento, seção 11.

## 11. Histórico de incidentes

_Nenhum incidente registrado até a data desta versão._

## 12. Revisão

Este documento deve ser revisado:
- A cada nova categoria de dado tratada
- A cada alteração de provedor cloud
- A cada incidente de segurança
- Anualmente, no mínimo (próxima revisão: 2027-05-25)
