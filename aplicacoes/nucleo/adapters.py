"""Adapters do django-allauth — auto-aprovar @fnp.org.br, externos pendentes.

Quando o usuário entra via Google OAuth:
- Se o e-mail estiver em ``settings.DOMINIOS_AUTOAPROVADOS`` (ex: @fnp.org.br),
  criamos/garantimos um Perfil tipo 'visualizador' com ``status_aprovacao='aprovado'``.
- Caso contrário, criamos Perfil tipo 'externo' com ``status_aprovacao='pendente'``
  e bloqueamos o login até DPO/admin aprovar no admin Django.
"""

from django.conf import settings
from django.utils import timezone
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


def _dominio_email(email):
    """Extrai o domínio (parte após @) ou string vazia."""
    if not email or '@' not in email:
        return ''
    return email.split('@', 1)[1].lower().strip()


class SocialAccountAdapterFNP(DefaultSocialAccountAdapter):
    """Adapter que decide automaticamente aprovação por domínio de e-mail.

    Por que: a equipe FNP já tem Google Workspace; forçá-la a esperar
    aprovação manual é fricção sem ganho. Externos, ao contrário, precisam
    ser avaliados pelo DPO antes de ver qualquer dado pessoal.
    """

    def save_user(self, request, sociallogin, form=None):
        """Hook chamado quando um usuário é criado via login social.

        Cria o User normalmente e em seguida configura o Perfil de acordo
        com o domínio. Não bloqueamos a criação aqui — bloqueamos o ACESSO
        via ``Perfil.acesso_valido`` no middleware.
        """
        user = super().save_user(request, sociallogin, form=form)
        self._configurar_perfil(user)
        return user

    def _configurar_perfil(self, user):
        from aplicacoes.nucleo.models import Perfil

        dominio = _dominio_email(user.email)
        autoaprovado = dominio in {
            d.lower() for d in getattr(settings, 'DOMINIOS_AUTOAPROVADOS', [])
        }

        defaults = {}
        if autoaprovado:
            defaults.update({
                'tipo': Perfil.TipoPerfil.VISUALIZADOR,
                'status_aprovacao': Perfil.StatusAprovacao.APROVADO,
                'aprovado_em': timezone.now(),
                'requer_2fa': False,
            })
        else:
            # Externos: pendente, expira em 90 dias por padrão, exige 2FA
            defaults.update({
                'tipo': Perfil.TipoPerfil.EXTERNO,
                'status_aprovacao': Perfil.StatusAprovacao.PENDENTE,
                'expira_em': (timezone.now() + timezone.timedelta(days=90)).date(),
                'requer_2fa': True,
            })
        Perfil.objects.update_or_create(usuario=user, defaults=defaults)
