from django.urls import path

from aplicacoes.engajamento import views

app_name = 'engajamento'

urlpatterns = [
    path('', views.lista_engajamento, name='lista_engajamento'),
    path('indice-fnp/', views.indice_fnp_ranking, name='indice_fnp'),
    path('metodologia/', views.metodologia, name='metodologia'),
]
