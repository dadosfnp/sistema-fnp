"""Dispatcher de webhooks — envia POSTs assincronos para sistemas externos.

Disparo em background (Thread) para nao bloquear signals. Inclui HMAC-SHA256
em ``X-FNP-Signature`` para o destinatario validar autenticidade.

Uso:
    from aplicacoes.nucleo.servicos.webhooks import disparar
    disparar('municipio.adimplencia_mudou', {'municipio_id': str(m.pk), 'status': 'inadimplente'})

Falhas sao registradas em WebhookSubscription.contador_falhas; apos 5 falhas
consecutivas o webhook eh marcado inativo automaticamente.
"""

import hashlib
import hmac
import json
import threading
from datetime import datetime

from django.utils import timezone


def _enviar(subscription, payload_bytes, headers):
    """Faz POST sincrono — chamado em thread separada."""
    import urllib.request

    from aplicacoes.nucleo.models import WebhookSubscription

    try:
        req = urllib.request.Request(
            subscription.url, data=payload_bytes, headers=headers, method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = 200 <= resp.status < 300
    except Exception:
        ok = False

    # Atualiza estado da subscricao
    if ok:
        WebhookSubscription.objects.filter(pk=subscription.pk).update(
            ultima_entrega=timezone.now(), contador_falhas=0,
        )
    else:
        # Refresh + increment
        sub = WebhookSubscription.objects.filter(pk=subscription.pk).first()
        if sub:
            sub.ultima_falha = timezone.now()
            sub.contador_falhas += 1
            if sub.contador_falhas >= 5:
                sub.ativo = False  # desativa para nao spammar
            sub.save(update_fields=['ultima_falha', 'contador_falhas', 'ativo'])


def disparar(tipo_evento, dados):
    """Envia o evento para todas as subscricoes ativas que o assinam.

    Args:
        tipo_evento: slug do evento (ex: 'municipio.adimplencia_mudou').
        dados: dict serializavel com o payload especifico.
    """
    from aplicacoes.nucleo.models import WebhookSubscription

    payload = {
        'tipo': tipo_evento,
        'timestamp': datetime.now().isoformat(),
        'dados': dados,
    }
    payload_bytes = json.dumps(payload).encode('utf-8')

    subs = WebhookSubscription.objects.filter(ativo=True).filter(eventos__contains=[tipo_evento])
    for sub in subs:
        assinatura = hmac.new(
            sub.secret.encode('utf-8'), payload_bytes, hashlib.sha256,
        ).hexdigest()
        headers = {
            'Content-Type': 'application/json',
            'X-FNP-Event': tipo_evento,
            'X-FNP-Signature': f'sha256={assinatura}',
        }
        # Background — nao bloqueia o signal
        thread = threading.Thread(target=_enviar, args=(sub, payload_bytes, headers), daemon=True)
        thread.start()
