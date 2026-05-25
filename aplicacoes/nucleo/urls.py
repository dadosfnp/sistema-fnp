from django.urls import path

from aplicacoes.nucleo import views, views_lgpd

app_name = 'nucleo'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('entrar/', views.entrar, name='entrar'),
    path('sair/', views.sair, name='sair'),
    path('api/busca/', views.busca_global, name='busca_global'),
    path('api/notificacoes/', views.notificacoes_dropdown, name='notificacoes_dropdown'),
    path('api/filtros-salvos/', views.filtros_salvos_listar, name='filtros_salvos_listar'),
    path('api/filtros-salvos/novo/', views.filtros_salvos_criar, name='filtros_salvos_criar'),
    path('api/filtros-salvos/<int:pk>/remover/', views.filtros_salvos_remover, name='filtros_salvos_remover'),

    # LGPD — direitos do titular (Art. 18) + transparência (Art. 9º)
    path('conta/termo-de-uso/', views_lgpd.termo_de_uso, name='termo_de_uso'),
    path('conta/politica-privacidade/', views_lgpd.politica_privacidade, name='politica_privacidade'),
    path('conta/exportar-meus-dados/', views_lgpd.exportar_meus_dados, name='exportar_meus_dados'),
    path('conta/solicitar-exclusao/', views_lgpd.solicitar_exclusao, name='solicitar_exclusao'),
]
