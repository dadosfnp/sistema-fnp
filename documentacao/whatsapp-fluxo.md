# WhatsApp no Sistema FNP — como funciona hoje e como pode evoluir

## TL;DR

Hoje o sistema usa **wa.me (click-to-chat)** — o jeito mais simples, gratuito
e sem burocracia de enviar WhatsApp. Quando a FNP quiser **automatizar 100%**
o envio (sem clique manual da secretária), o caminho é integrar a
**Cloud API do Meta** ou um provedor BR como **Z-API/UltraMSG**.

---

## 1. Como funciona hoje — `wa.me` (click-to-chat)

### Fluxo atual

1. Sistema gera link no formato:
   ```
   https://wa.me/5511999998888?text=Olá%2C%20Maria
   ```
2. Usuário clica → WhatsApp abre (Web ou App) **já na conversa** com
   aquela pessoa, com a mensagem pré-preenchida no campo de texto.
3. Usuário **confirma e envia** manualmente.

### Onde está implementado

- `aplicacoes/comunicacao/servicos.py` → `montar_link_whatsapp(telefone, mensagem)`
  - Aceita telefone em formato livre (`(11) 99999-8888` etc).
  - Remove caracteres não-dígito.
  - Adiciona `55` (BR) se não tiver código de país (≤ 11 dígitos).
  - URL-encode da mensagem.
- **Mala direta** (`/comunicacao/processar/`):
  - Modal de composição: botão **"WhatsApp"** ou **"Ambos"** ao lado do "E-mail".
  - Modal de sucesso: lista de links `wa.me` clicáveis + botão **"Abrir todos"** (dispara `window.open` em sequência).
- **Pré-credenciamento** (`/presenca/credenciamento/novo/`):
  - Após criar o pré-cred, sistema gera link wa.me + mensagem pronta convidando a pessoa.

### Vantagens

- ✅ **Custo zero** (links são endpoint público da Meta)
- ✅ **Sem aprovação** do WhatsApp Business
- ✅ **Sem rate limit oficial** (limite só do "operador" humano)
- ✅ **Funciona com qualquer número** (não precisa ser conta Business)
- ✅ **LGPD-friendly**: o consentimento implícito está em a pessoa já ter dado o telefone

### Limitações

- ❌ **Não é automático** — alguém tem que clicar
- ❌ **Não rastreia entrega/leitura** (não há webhook)
- ❌ **Não envia imagens/arquivos** no link (só texto)
- ❌ **Para 100+ contatos é cansativo**, mesmo com "abrir todos"
- ❌ **Usuário precisa estar logado no WhatsApp** (Web ou App) no dispositivo

### Quando wa.me é suficiente

- Volume ≤ 50 mensagens por campanha
- Conteúdo personalizado (cada um lê e adapta)
- Convite para eventos pontuais
- Pré-credenciamento de visitante
- Comunicações da equipe FNP que querem manter "toque pessoal"

---

## 2. Próximo nível — Cloud API do Meta (oficial, gratuito até 1k/mês)

A **WhatsApp Business Platform Cloud API** é o caminho oficial do Meta para
envio automatizado. Desde 2022 é gratuita para até **1.000 conversas/mês**
iniciadas pela empresa (modelo "marketing-to-user" tem custos por região).

### Como funciona

1. Cadastrar a FNP no **Meta Business Manager**
2. Verificar a conta Business (envia documentos da CNPJ)
3. Criar um **App** na Meta for Developers
4. Vincular um número de telefone exclusivo (a FNP precisa de uma linha dedicada)
5. **Templates aprovados** pelo Meta para mensagens iniciadas pela empresa
   (mensagens reativas — dentro de 24h após contato do cliente — são livres)
6. Receber token `WHATSAPP_TOKEN` e usar no header `Authorization: Bearer <token>`

### Endpoint de envio

```http
POST https://graph.facebook.com/v18.0/<PHONE_ID>/messages
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "5511999998888",
  "type": "template",
  "template": {
    "name": "convite_fnp",
    "language": { "code": "pt_BR" },
    "components": [
      { "type": "body", "parameters": [
        { "type": "text", "text": "Maria Silva" },
        { "type": "text", "text": "https://sistema-fnp.onrender.com/pre/abc123" }
      ]}
    ]
  }
}
```

### Implementação proposta

No Sistema FNP isso entra como **canal adicional** no `Envio`:

```python
class Canal(models.TextChoices):
    EMAIL = 'email', 'E-mail'
    WHATSAPP = 'whatsapp', 'WhatsApp (link wa.me)'      # atual
    WHATSAPP_AUTO = 'whatsapp_auto', 'WhatsApp (Cloud API)'  # futuro
    AMBOS = 'ambos', 'E-mail + WhatsApp'
```

Service:
```python
def enviar_whatsapp_cloud(telefone, template_nome, parametros):
    """Envia mensagem via Cloud API com template aprovado."""
    import requests
    resp = requests.post(
        f'https://graph.facebook.com/v18.0/{settings.WA_PHONE_ID}/messages',
        headers={'Authorization': f'Bearer {settings.WA_TOKEN}'},
        json={
            'messaging_product': 'whatsapp',
            'to': re.sub(r'\D', '', telefone),
            'type': 'template',
            'template': {
                'name': template_nome,
                'language': {'code': 'pt_BR'},
                'components': [{'type': 'body', 'parameters': parametros}],
            },
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()['messages'][0]['id']
```

### Vantagens

- ✅ **Envio 100% automatizado** (sem cliques)
- ✅ **Status de entrega/leitura** via webhook
- ✅ **Suporta imagem, vídeo, áudio, documento, botões, listas**
- ✅ **Gratuito até 1k conversas/mês** (FNP cabe nisso)
- ✅ **Oficial Meta** — sem risco de bloqueio

### Custos quando passar de 1k/mês

- Brasil (2026): ~R$ 0,30 por conversa iniciada pela FNP
- Conversas iniciadas pelo cliente (24h após mensagem): livres
- Para a FNP, com ~500 prefeitos, mesmo 2 campanhas/mês = 1k conversas → ainda gratuito

### Limitações

- ❌ **Aprovação Meta** leva 2–7 dias úteis
- ❌ **Número dedicado** — não pode usar o WhatsApp da secretária
- ❌ **Templates aprovados** — cada modelo de mensagem inicial precisa ser revisado
- ❌ **CNPJ obrigatório**
- ❌ **Documentação em inglês** principalmente

---

## 3. Atalho mais barato — Z-API / UltraMSG / Twilio (provedores)

Provedores intermediários que **simplificam** a integração com WhatsApp,
muitas vezes usando WhatsApp Web não-oficial (Z-API) ou Cloud API por trás
(Twilio).

| Provedor | Modelo | Preço | Burocracia |
|---|---|---|---|
| **Z-API** (BR) | WhatsApp Web | R$ 100/mês ilimitado | QR-code, sem aprovação |
| **UltraMSG** (BR) | WhatsApp Web | R$ 50/mês ilimitado | QR-code, sem aprovação |
| **Twilio** | Cloud API oficial | US$ 0.005 por msg + Meta | Setup mais técnico |
| **MessageBird** | Cloud API oficial | EUR 0.005 + Meta | Suporte BR ok |

### Vantagens dos provedores BR (Z-API / UltraMSG)

- ✅ **Setup em 5 minutos** (escaneia QR)
- ✅ **Sem aprovação Meta** (usa o WhatsApp Web do número conectado)
- ✅ **Preço fixo barato** (R$ 50–100/mês)
- ✅ **Suporta TUDO** (texto, imagem, áudio, doc, botões…)
- ✅ **Webhook nativo** de recebimento + entrega

### Riscos

- ❌ **Não-oficial**: WhatsApp pode bloquear o número se detectar bot
- ❌ **Limite de ~1000 mensagens/dia** por número (boa prática)
- ❌ **Se a Meta apertar regras**, pode parar de funcionar
- ❌ **LGPD**: dados passam pela infra do provedor (precisa contrato)

### Quando usar

Volume **médio** (100–1000 msgs/mês), urgência de implementar, sem CNPJ pronto.
**A FNP tem CNPJ e estrutura** — vai direto pra Cloud API oficial vale mais a pena.

---

## 4. Recomendação para a FNP

**Curto prazo (agora):** continuar com `wa.me`. Atende a maioria dos casos da
recepção (pré-credenciamento individual) e da mala direta (campanhas
selecionadas onde tom personalizado importa).

**Médio prazo (3–6 meses):** quando a FNP tiver volume regular de comunicação
> 200 mensagens/semana, **iniciar processo de aprovação na Cloud API do Meta**:
- Solicitar Business Manager
- Verificar conta com documentos da CNPJ
- Comprar/dedicar número de telefone exclusivo
- Criar 3–5 templates iniciais (convite, lembrete, comunicado, cobrança, certificado)

**Longo prazo:** com Cloud API rodando, implementar:
- Webhook que recebe respostas dos prefeitos (chatbot básico FAQ)
- Status de entrega/leitura visível no histórico de envios do sistema
- Mensagens de aniversário, lembrete de mandato, etc (automação)

---

## 5. Como o sistema está preparado

O design atual **já facilita** essa evolução:

- `Envio.canal` aceita string — basta adicionar `whatsapp_auto`
- `Envio.links_whatsapp` (JSONField) pode armazenar `{ msg_id, status, entregue_em }` no futuro
- `servicos.py` já abstrai geração do link — `enviar_whatsapp_cloud()` entra como nova função
- Cada Pessoa já tem `telefone` separado de `email`

Quando contratar Cloud API: ~3 dias de implementação para ligar o switch.
