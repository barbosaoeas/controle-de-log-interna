from django.urls import path
from . import views

app_name = 'gases'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_gases, name='dashboard'),

    # Tipos de Gases
    path('tipos/', views.listar_tipos_gas, name='tipos'),
    path('tipos/criar/', views.criar_tipo_gas, name='criar_tipo'),
    path('tipos/<int:tipo_id>/editar/', views.editar_tipo_gas, name='editar_tipo'),
    path('tipos/<int:tipo_id>/deletar/', views.deletar_tipo_gas, name='deletar_tipo'),

    # Movimentações
    path('movimentacoes/', views.listar_movimentacoes, name='movimentacoes'),
    path('movimentacoes/criar/', views.criar_movimentacao, name='criar_movimentacao'),
    path('movimentacoes/entrada-lote/', views.entrada_lote, name='entrada_lote'),
    path('movimentacoes/<int:movimentacao_id>/editar/', views.editar_movimentacao, name='editar_movimentacao'),
    path('movimentacoes/<int:movimentacao_id>/deletar/', views.deletar_movimentacao, name='deletar_movimentacao'),

    # Importação
    path('movimentacoes/importar-excel/', views.importar_excel, name='importar_excel'),
]
