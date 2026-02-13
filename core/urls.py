from django.urls import path
from . import views, views_diesel

urlpatterns = [
    # Página Inicial (Home)
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Dashboards específicos por perfil
    path('dashboard/demandante/', views.dashboard_demandante, name='dashboard_demandante'),
    path('dashboard/supervisor/', views.dashboard_supervisor, name='dashboard_supervisor'),
    path('dashboard/transportes/', views.dashboard_transportes, name='dashboard_transportes'),

    # TESTE
    path('teste-botao/', views.teste_botao, name='teste_botao'),
    path('diagnostico-perfil/', views.diagnostico_perfil, name='diagnostico_perfil'),

    # Pedidos
    path('pedidos/', views.listar_pedidos, name='listar_pedidos'),
    path('pedidos/criar/', views.criar_pedido, name='criar_pedido'),
    path('pedidos/<int:pedido_id>/', views.detalhes_pedido, name='detalhes_pedido'),
    path('pedidos/<int:pedido_id>/editar/', views.editar_pedido, name='editar_pedido'),
    path('pedidos/<int:pedido_id>/excluir/', views.excluir_pedido, name='excluir_pedido'),
    path('pedidos/<int:pedido_id>/atualizar-status/', views.atualizar_status_pedido, name='atualizar_status_pedido'),
    path('pedidos/reordenar/', views.reordenar_pedidos, name='reordenar_pedidos'),

    # API para gerenciamento de áreas
    path('api/areas/', views.api_areas, name='api_areas'),
    path('api/areas/<int:area_id>/', views.api_area_detail, name='api_area_detail'),
    path('api/areas/<int:area_id>/delete/', views.api_area_delete, name='api_area_delete'),

    # API para gerenciamento de setores
    path('api/setores/', views.api_setores, name='api_setores'),
    path('api/setores/<int:setor_id>/', views.api_setor_detail, name='api_setor_detail'),

    # API para gerenciamento de equipamentos
    path('api/equipamentos/', views.api_equipamentos, name='api_equipamentos'),
    path('api/equipamentos/<int:equipamento_id>/', views.api_equipamento_detail, name='api_equipamento_detail'),
    path('api/equipamentos-pedido/', views.api_equipamentos_pedido, name='api_equipamentos_pedido'),

    # API para gerenciamento de categorias de equipamentos
    path('api/categorias-equipamentos/', views.api_categorias_equipamentos, name='api_categorias_equipamentos'),
    path('api/categorias-equipamentos/<int:categoria_id>/', views.api_categoria_equipamento_detail, name='api_categoria_equipamento_detail'),

    # API para gerenciamento de clientes
    path('api/clientes/', views.api_clientes, name='api_clientes'),
    path('api/clientes/<int:cliente_id>/', views.api_cliente_detail, name='api_cliente_detail'),

    # API para gerenciamento de usuários
    path('api/usuarios/', views.api_usuarios, name='api_usuarios'),
    path('api/usuarios/<int:usuario_id>/', views.api_usuario_detalhes, name='api_usuario_detalhes'),
    path('api/usuarios/<int:usuario_id>/editar-perfil/', views.api_editar_perfil_usuario, name='api_editar_perfil_usuario'),

    # API para gerenciamento de empresas
    path('api/empresas/', views.api_empresas, name='api_empresas'),
    path('api/empresas/criar/', views.api_criar_empresa, name='api_criar_empresa'),
    path('api/empresas/<int:empresa_id>/', views.api_empresa_detalhes, name='api_empresa_detalhes'),
    path('api/empresas/<int:empresa_id>/editar/', views.api_editar_empresa, name='api_editar_empresa'),
    path('api/empresas/<int:empresa_id>/excluir/', views.api_excluir_empresa, name='api_excluir_empresa'),
    path('api/mecanicos-por-empresa/', views.api_mecanicos_por_empresa, name='api_mecanicos_por_empresa'),
    path('api/tecnicos-disponiveis/', views.api_tecnicos_disponiveis, name='api_tecnicos_disponiveis'),
    path('api/mecanicos-por-maquina/', views.api_mecanicos_por_maquina, name='api_mecanicos_por_maquina'),

    # API para gerenciamento de perfis
    path('api/perfis-disponiveis/', views.api_perfis_disponiveis, name='api_perfis_disponiveis'),
    path('api/perfis/criar/', views.api_criar_perfil, name='api_criar_perfil'),
    path('api/perfis/editar/', views.api_editar_perfil, name='api_editar_perfil'),
    path('api/perfis/remover/', views.api_remover_perfil, name='api_remover_perfil'),
    path('api/perfis/reativar/', views.api_reativar_perfil, name='api_reativar_perfil'),
    path('api/setores/', views.api_setores, name='api_setores'),

    # Gestão de usuários
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/<int:user_id>/resetar-senha/', views.resetar_senha_usuario, name='resetar_senha_usuario'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),

    # Localização em tempo real
    path('api/atualizar-localizacao/', views.atualizar_localizacao, name='atualizar_localizacao'),
    path('api/atualizar-posicao/', views.api_atualizar_posicao, name='api_atualizar_posicao'),
    path('api/marcar-offline/', views.marcar_offline, name='marcar_offline'),
    path('api/localizacoes-operadores/', views.api_localizacoes_operadores, name='api_localizacoes_operadores'),

    # APIs para CRUD de pedidos (admin/supervisor)
    path('api/pedido/<int:pedido_id>/', views.api_obter_pedido, name='api_obter_pedido'),
    path('api/pedido/<int:pedido_id>/editar-rapido/', views.api_editar_pedido_rapido, name='api_editar_pedido_rapido'),
    path('api/operadores/', views.api_listar_operadores, name='api_listar_operadores'),
    path('mapa-operadores/', views.mapa_operadores, name='mapa_operadores'),

    # Relatórios
    path('relatorios/', views.relatorios_pedidos, name='relatorios_pedidos'),

    # Debug de localização
    path('debug-localizacao/', views.debug_localizacao, name='debug_localizacao'),
    path('configurar-estaleiro/', views.configurar_estaleiro, name='configurar_estaleiro'),

    # Página de teste
    path('teste-modal/', views.teste_modal, name='teste_modal'),

    # ===== CONTROLE DE DIESEL =====
    path('diesel/', views_diesel.dashboard_diesel, name='dashboard_diesel'),
    path('diesel/abastecer/', views_diesel.abastecer_veiculo, name='abastecer_veiculo'),
    path('diesel/historico/', views_diesel.historico_abastecimentos, name='historico_abastecimentos'),
    path('diesel/veiculos/', views_diesel.gerenciar_veiculos, name='gerenciar_veiculos'),
    path('diesel/registrar-chegada/', views_diesel.registrar_chegada_diesel, name='registrar_chegada_diesel'),
    path('diesel/testar-alerta/', views_diesel.testar_alerta_email, name='testar_alerta_email'),
    path('diesel/relatorio-compras/', views_diesel.relatorio_compras_diesel, name='relatorio_compras_diesel'),

    # APIs para controle de diesel
    path('api/diesel/tanque/', views_diesel.api_dados_tanque, name='api_dados_tanque'),
    path('api/diesel/veiculos-mais-abastecidos/', views_diesel.api_veiculos_mais_abastecidos, name='api_veiculos_mais_abastecidos'),
    path('api/diesel/veiculo/<int:veiculo_id>/agenda/', views_diesel.api_alterar_agenda_veiculo, name='api_alterar_agenda_veiculo'),
    path('api/diesel/veiculo/<int:veiculo_id>/status/', views_diesel.api_alterar_status_veiculo, name='api_alterar_status_veiculo'),
    path('api/diesel/veiculo/<int:veiculo_id>/ativo/', views_diesel.api_alterar_ativo_veiculo, name='api_alterar_ativo_veiculo'),
]
