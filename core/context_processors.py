"""
Context processors para dados globais do navbar
NOVO ARQUIVO - não afeta código existente
"""

from django.db.models import Q
from .models import Pedido, ConfiguracaoTanque, AbastecimentoTanque

def navbar_context(request):
    """
    Context processor para fornecer dados para o novo navbar
    """
    context = {
        'pedidos_pendentes': 0,
        'nivel_combustivel': 0,
        'combustivel_critico': False,
    }
    
    # Só processar se usuário estiver logado
    if request.user.is_authenticated and hasattr(request.user, 'perfil'):
        try:
            # Contar pedidos pendentes baseado no perfil
            if request.user.perfil.codigo_perfil == 'DEMANDANTE':
                # Demandante vê apenas seus pedidos pendentes
                context['pedidos_pendentes'] = Pedido.objects.filter(
                    criado_por=request.user,
                    status__in=['PENDENTE', 'APROVADO']
                ).count()

            elif request.user.perfil.codigo_perfil in ['SUPERVISOR', 'ADMIN']:
                # Supervisor/Admin vê todos os pedidos pendentes de aprovação
                context['pedidos_pendentes'] = Pedido.objects.filter(
                    status='PENDENTE'
                ).count()

            elif request.user.perfil.codigo_perfil == 'TRANSPORTES':
                # Transportes vê pedidos aprovados aguardando execução
                context['pedidos_pendentes'] = Pedido.objects.filter(
                    status='APROVADO'
                ).count()
            
            # Calcular nível de combustível
            try:
                config_tanque = ConfiguracaoTanque.objects.first()
                if config_tanque:
                    # Pegar último abastecimento
                    ultimo_abastecimento = AbastecimentoTanque.objects.order_by('-data_registro').first()
                    
                    if ultimo_abastecimento:
                        nivel_atual = ultimo_abastecimento.nivel_apos_abastecimento
                    else:
                        # Se não há abastecimentos, usar nível inicial
                        nivel_atual = getattr(config_tanque, 'nivel_inicial', 5200)
                    
                    # Calcular percentual
                    percentual = (nivel_atual / config_tanque.capacidade_total) * 100
                    context['nivel_combustivel'] = round(percentual, 1)
                    context['combustivel_critico'] = percentual < 25
                    
            except Exception as e:
                # Em caso de erro, usar valores padrão
                context['nivel_combustivel'] = 0
                context['combustivel_critico'] = True
                
        except Exception as e:
            # Em caso de erro geral, manter valores padrão
            pass
    
    return context

def user_permissions_context(request):
    """
    Context processor para permissões do usuário
    """
    context = {
        'user_can_manage_users': False,
        'user_can_manage_areas': False,
        'user_can_view_fuel': False,
        'user_can_approve_requests': False,
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'perfil'):
        perfil = request.user.perfil.codigo_perfil

        # Definir permissões baseadas no perfil
        if perfil in ['ADMIN', 'SUPERVISOR']:
            context.update({
                'user_can_manage_users': True,
                'user_can_manage_areas': True,
                'user_can_view_fuel': True,
                'user_can_approve_requests': True,
            })

        elif perfil == 'TRANSPORTES':
            context.update({
                'user_can_manage_areas': False,  # TRANSPORTES não gerencia áreas
                'user_can_view_fuel': False,     # TRANSPORTES não vê combustível
            })

        elif perfil == 'MANUTENCAO':
            context.update({
                'user_can_manage_areas': True,
            })
    
    return context
