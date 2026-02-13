from django.urls import path
from . import views

app_name = 'frota_locada'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard-manutencao/', views.dashboard_manutencao, name='dashboard_manutencao'),
    
    # Veículos
    path('veiculos/', views.listar_veiculos, name='listar_veiculos'),
    path('veiculos/cadastrar/', views.cadastrar_veiculo, name='cadastrar_veiculo'),
    path('veiculos/<int:veiculo_id>/', views.detalhes_veiculo, name='detalhes_veiculo'),
    path('veiculos/<int:veiculo_id>/editar/', views.editar_veiculo, name='editar_veiculo'),
    path('veiculos/<int:veiculo_id>/excluir/', views.excluir_veiculo, name='excluir_veiculo'),
    
    # Fornecedores
    path('fornecedores/', views.listar_fornecedores, name='listar_fornecedores'),
    path('fornecedores/cadastrar/', views.cadastrar_fornecedor, name='cadastrar_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/editar/', views.editar_fornecedor, name='editar_fornecedor'),
    
    # Tipos de Veículo
    path('tipos-veiculo/', views.listar_tipos_veiculo, name='listar_tipos_veiculo'),
    path('tipos-veiculo/cadastrar/', views.cadastrar_tipo_veiculo, name='cadastrar_tipo_veiculo'),

    # Marcas de Veículo
    path('marcas/', views.listar_marcas, name='listar_marcas'),
    path('marcas/cadastrar/', views.cadastrar_marca, name='cadastrar_marca'),
    path('marcas/<int:marca_id>/editar/', views.editar_marca, name='editar_marca'),
    path('marcas/<int:marca_id>/excluir/', views.excluir_marca, name='excluir_marca'),
    
    # Manutenções
    path('manutencoes/', views.listar_manutencoes, name='listar_manutencoes'),
    path('manutencoes/agendar/', views.agendar_manutencao, name='agendar_manutencao'),
    path('manutencoes/<int:manutencao_id>/', views.detalhes_manutencao, name='detalhes_manutencao'),
    path('manutencoes/<int:manutencao_id>/editar/', views.editar_manutencao, name='editar_manutencao'),
    
    # Histórico Horímetro
    path('historico-horimetro/', views.listar_historico_horimetro, name='listar_historico_horimetro'),
    path('historico-km/registrar/', views.registrar_km, name='registrar_km'),
    
    # Relatórios
    path('relatorios/custos/', views.relatorio_custos, name='relatorio_custos'),
    path('relatorios/km/', views.relatorio_km, name='relatorio_km'),
    
    # Máquinas
    path('maquinas/', views.listar_maquinas, name='listar_maquinas'),
    path('maquinas/cadastrar/', views.cadastrar_maquina, name='cadastrar_maquina'),
    path('maquinas/<int:maquina_id>/editar/', views.editar_maquina, name='editar_maquina'),

    # Chamados de Manutenção
    path('chamados/', views.listar_chamados, name='listar_chamados'),
    path('chamados/abrir/', views.abrir_chamado, name='abrir_chamado'),
    path('chamados/<int:chamado_id>/', views.detalhes_chamado, name='detalhes_chamado'),
    path('chamados/<int:chamado_id>/iniciar/', views.iniciar_atendimento, name='iniciar_atendimento'),
    path('chamados/<int:chamado_id>/finalizar/', views.finalizar_chamado, name='finalizar_chamado'),

    # Área do Mecânico - Atendimentos
    path('meus-chamados/', views.meus_chamados, name='meus_chamados'),
    path('atendimentos/<int:atendimento_id>/', views.detalhes_atendimento, name='detalhes_atendimento'),
    path('atendimentos/<int:atendimento_id>/finalizar/', views.finalizar_atendimento, name='finalizar_atendimento'),
    path('atendimentos/<int:atendimento_id>/pausar/', views.pausar_atendimento, name='pausar_atendimento'),
    path('atendimentos/<int:atendimento_id>/retomar/', views.retomar_atendimento, name='retomar_atendimento'),

    # AJAX
    path('ajax/atualizar-status-manutencao/', views.atualizar_status_manutencao, name='atualizar_status_manutencao'),
    path('ajax/obter-horimetro-veiculo/', views.obter_horimetro_veiculo, name='obter_horimetro_veiculo'),
    path('ajax/cadastrar-marca/', views.cadastrar_marca_ajax, name='cadastrar_marca_ajax'),
    path('ajax/editar-marca/<int:marca_id>/', views.editar_marca_ajax, name='editar_marca_ajax'),
    path('ajax/atualizar-tempos-chamado/<int:chamado_id>/', views.atualizar_tempos_chamado, name='atualizar_tempos_chamado'),

    # API endpoints
    path('api/maquina/<int:maquina_id>/fornecedor/', views.api_maquina_fornecedor, name='api_maquina_fornecedor'),
    path('api/veiculo-locado/<int:veiculo_id>/fornecedor/', views.api_veiculo_locado_fornecedor, name='api_veiculo_locado_fornecedor'),
]
