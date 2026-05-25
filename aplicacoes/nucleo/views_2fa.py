"""Views de 2FA TOTP — setup (QR code) + verificação no login.

Fluxo:
1. Usuário com ``perfil.requer_2fa=True`` cai em ``/conta/2fa/login/`` toda sessão
2. Se não tem device confirmado, é mandado para ``/conta/2fa/setup/`` (uma vez)
3. Setup mostra QR para escanear no Google Authenticator + 8 códigos de backup
4. Verificação aceita TOTP (6 dígitos) ou um código de backup
"""

import base64
import io
from urllib.parse import quote

import qrcode
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django_otp import login as otp_login
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice


def _device_confirmado(user):
    """Retorna o TOTPDevice confirmado do usuário, se houver."""
    return TOTPDevice.objects.filter(user=user, confirmed=True).first()


@login_required
def setup_2fa(request):
    """Gera ou exibe o TOTPDevice + QR code + códigos de backup.

    Idempotente: se já existe device confirmado, redireciona para login_2fa.
    """
    if _device_confirmado(request.user):
        return HttpResponseRedirect('/conta/2fa/login/')

    # Cria device não-confirmado (ou reusa o existente)
    device, _ = TOTPDevice.objects.get_or_create(
        user=request.user, name='default', defaults={'confirmed': False},
    )

    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            # Cria 8 códigos de backup estáticos
            static_device, _ = StaticDevice.objects.get_or_create(
                user=request.user, name='backup',
            )
            static_device.token_set.all().delete()
            codigos = [get_random_string(8) for _ in range(8)]
            for c in codigos:
                StaticToken.objects.create(device=static_device, token=c)
            otp_login(request, device)
            return render(request, 'nucleo/2fa_setup_ok.html', {'codigos_backup': codigos})
        erro = 'Código inválido. Tente novamente — o código TOTP muda a cada 30 segundos.'
    else:
        erro = None

    # Gera QR code (formato otpauth://) — secret no proprio device
    issuer = 'Sistema FNP'
    label = quote(f'{issuer}:{request.user.email or request.user.username}')
    otpauth_url = (
        f'otpauth://totp/{label}?secret={device.bin_key.hex().upper()}'
        f'&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30'
    )
    img = qrcode.make(otpauth_url)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('ascii')

    return render(request, 'nucleo/2fa_setup.html', {
        'qr_b64': qr_b64,
        'secret': device.bin_key.hex().upper(),
        'erro': erro,
    })


@login_required
def login_2fa(request):
    """Verifica o TOTP da sessão atual (ou redireciona para setup)."""
    device = _device_confirmado(request.user)
    if not device:
        return HttpResponseRedirect('/conta/2fa/setup/')

    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        # Tenta TOTP primeiro, depois código de backup
        if device.verify_token(token):
            otp_login(request, device)
            return HttpResponseRedirect(request.GET.get('next', '/'))
        # Backup estático
        for sd in StaticDevice.objects.filter(user=request.user):
            if sd.verify_token(token):
                otp_login(request, sd)
                return HttpResponseRedirect(request.GET.get('next', '/'))
        erro = 'Código inválido. Use seu app autenticador ou um código de backup.'
    else:
        erro = None

    return render(request, 'nucleo/2fa_login.html', {'erro': erro})
