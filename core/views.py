from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import csv
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.http import HttpResponse
from .models import Pedido, Setor, Area, Cliente, Equipamento, PerfilUsuario, HistoricoPedido


@login_required
def home(request):
    """Página inicial com cards de módulos - controlados por permissão"""
    try:
        perfil = request.user.perfil

        # Estatísticas de Transporte
        if perfil.codigo_perfil == 'DEMANDANTE':
            pedidos_base = Pedido.objects.filter(criado_por=request.user)
        else:
            pedidos_base = Pedido.objects.all()

        stats_transporte = {
            'pendentes': pedidos_base.filter(status='PENDENTE').count(),
            'em_andamento': pedidos_base.filter(status='EM_ANDAMENTO').count(),
            'total': pedidos_base.count(),
        }

        # Estatísticas de Combustível (apenas para admin/supervisor)
        stats_combustivel = {'nivel': 0, 'abastecimentos_hoje': 0}
        if perfil.is_admin_ou_supervisor:
            from .models import ConfiguracaoTanque, AbastecimentoVeiculo
            try:
                tanque = ConfiguracaoTanque.objects.first()
                if tanque:
                    stats_combustivel['nivel'] = tanque.nivel_percentual
                stats_combustivel['abastecimentos_hoje'] = AbastecimentoVeiculo.objects.filter(
                    data_abastecimento__date=timezone.now().date()
                ).count()
            except:
                pass

        # Estatísticas de Frotas (para perfis com acesso)
        stats_frotas = {'chamados_abertos': 0, 'veiculos_manutencao': 0}
        if perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR', 'MANUTENCAO_CONT_PTA', 'CONTROLE_MAN_PTA', 'CONTROLE_PROD_PTA'] or perfil.is_terceiro:
            try:
                from frota_locada.models import ChamadoManutencao, VeiculoLocado
                stats_frotas['chamados_abertos'] = ChamadoManutencao.objects.filter(
                    status__in=['ABERTO', 'EM_ATENDIMENTO']
                ).count()
                stats_frotas['veiculos_manutencao'] = VeiculoLocado.objects.filter(
                    status='MANUTENCAO'
                ).count()
            except:
                pass

        # Estatísticas de Gases (apenas admin)
        stats_gases = {'total_cilindros': 0, 'baixo_estoque': 0}
        if perfil.codigo_perfil == 'ADMIN':
            try:
                from gases.models import TipoGas
                gases = TipoGas.objects.all()
                stats_gases['total_cilindros'] = sum(g.quantidade_atual for g in gases)
                stats_gases['baixo_estoque'] = gases.filter(quantidade_atual__lt=5).count()
            except:
                pass

        # Estatísticas de Admin
        stats_admin = {'total_usuarios': 0, 'usuarios_ativos': 0}
        if perfil.is_admin_ou_supervisor:
            stats_admin['total_usuarios'] = User.objects.count()
            stats_admin['usuarios_ativos'] = User.objects.filter(is_active=True).count()

        context = {
            'stats_transporte': stats_transporte,
            'stats_combustivel': stats_combustivel,
            'stats_frotas': stats_frotas,
            'stats_gases': stats_gases,
            'stats_admin': stats_admin,
        }

        return render(request, 'core/home.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado. Entre em contato com o administrador.')
        return redirect('login')


@login_required
def dashboard(request):
    """Dashboard principal - agora redireciona para home"""
    return redirect('home')


@login_required
def dashboard_demandante(request):
    """Dashboard para setores demandantes"""
    try:
        perfil = request.user.perfil
        setor = perfil.setor

        # Estatísticas dos pedidos do usuário
        pedidos_usuario = Pedido.objects.filter(criado_por=request.user)
        stats = {
            'total_pedidos': pedidos_usuario.count(),
            'pendentes': pedidos_usuario.filter(status='PENDENTE').count(),
            'em_andamento': pedidos_usuario.filter(status='EM_ANDAMENTO').count(),
            'concluidos': pedidos_usuario.filter(status='CONCLUIDO').count(),
        }

        # Pedidos recentes do usuário
        pedidos_recentes = pedidos_usuario.order_by('-data_solicitacao')[:10]

        context = {
            'perfil': perfil,
            'setor': setor,
            'stats': stats,
            'pedidos_recentes': pedidos_recentes,
        }

        return render(request, 'core/dashboard_demandante.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def dashboard_supervisor(request):
    """Dashboard para administradores e supervisores"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            messages.error(request, 'Acesso negado. Área restrita a administradores e supervisores.')
            return redirect('dashboard_demandante')

        # Estatísticas gerais do sistema
        stats = {
            'total_pedidos': Pedido.objects.count(),
            'pendentes': Pedido.objects.filter(status='PENDENTE').count(),
            'em_andamento': Pedido.objects.filter(status='EM_ANDAMENTO').count(),
            'concluidos_hoje': Pedido.objects.filter(
                status='CONCLUIDO',
                data_conclusao__date=timezone.now().date()
            ).count(),
        }

        # Pedidos pendentes mais antigos
        pedidos_pendentes = Pedido.objects.filter(status='PENDENTE').order_by('data_solicitacao')[:5]

        # Pedidos em andamento
        pedidos_andamento = Pedido.objects.filter(status='EM_ANDAMENTO').order_by('data_inicio')[:5]

        # Estatísticas por setor
        setores_stats = []
        for setor in Setor.objects.filter(ativo=True):
            setor_pedidos = Pedido.objects.filter(setor_solicitante=setor)
            setores_stats.append({
                'setor': setor,
                'total': setor_pedidos.count(),
                'pendentes': setor_pedidos.filter(status='PENDENTE').count(),
                'em_andamento': setor_pedidos.filter(status='EM_ANDAMENTO').count(),
            })

        # Operadores online (para admins/supervisores)
        operadores_online = PerfilUsuario.objects.filter(
            tipo_perfil__codigo='TRANSPORTES',
            status_online=True
        ).count()

        total_operadores = PerfilUsuario.objects.filter(tipo_perfil__codigo='TRANSPORTES').count()

        context = {
            'perfil': perfil,
            'stats': stats,
            'pedidos_pendentes': pedidos_pendentes,
            'pedidos_andamento': pedidos_andamento,
            'setores_stats': setores_stats,
            'operadores_online': operadores_online,
            'total_operadores': total_operadores,
        }

        return render(request, 'core/dashboard_supervisor.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def dashboard_transportes(request):
    """Dashboard para setor de transportes"""
    try:
        perfil = request.user.perfil
        if not perfil.is_transportes:
            messages.error(request, 'Acesso negado. Área restrita ao setor de transportes.')
            return redirect('dashboard_demandante')

        # Estatísticas gerais
        stats = {
            'total_pedidos': Pedido.objects.count(),
            'pendentes': Pedido.objects.filter(status='PENDENTE').count(),
            'em_andamento': Pedido.objects.filter(status='EM_ANDAMENTO').count(),
            'concluidos_hoje': Pedido.objects.filter(
                status='CONCLUIDO',
                data_conclusao__date=timezone.now().date()
            ).count(),
        }

        # Pedidos por prioridade
        pedidos_urgentes = Pedido.objects.filter(
            status__in=['PENDENTE', 'EM_ANDAMENTO'],
            prioridade='URGENTE'
        ).count()

        # Pedidos pendentes ordenados por prioridade e data
        pedidos_pendentes = Pedido.objects.filter(
            status='PENDENTE'
        ).order_by('-prioridade', 'ordem_manual', 'data_solicitacao')[:15]

        # Pedidos em andamento
        pedidos_andamento = Pedido.objects.filter(
            status='EM_ANDAMENTO'
        ).order_by('data_inicio')[:10]

        context = {
            'perfil': perfil,
            'stats': stats,
            'pedidos_urgentes': pedidos_urgentes,
            'pedidos_pendentes': pedidos_pendentes,
            'pedidos_andamento': pedidos_andamento,
        }

        return render(request, 'core/dashboard_transportes.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def listar_pedidos(request):
    """Lista pedidos baseado no perfil do usuário"""
    try:
        perfil = request.user.perfil
        hoje = timezone.now().date()

        # Filtros base por perfil
        if perfil.is_admin_ou_supervisor:
            # Admins e Supervisores veem TODOS os pedidos (qualquer data)
            pedidos = Pedido.objects.all()
        elif perfil.is_transportes:
            # Operadores de Transporte veem apenas pedidos do DIA ATUAL
            # (agendados para hoje ou anteriores que ainda estão pendentes)
            pedidos = Pedido.objects.filter(
                Q(data_agendamento=hoje) |  # Agendados para hoje
                Q(data_agendamento__lt=hoje, status__in=['PENDENTE', 'EM_ANDAMENTO'])  # Atrasados
            )
        else:
            # Demandantes veem apenas seus próprios pedidos (qualquer data)
            pedidos = Pedido.objects.filter(criado_por=request.user)

        # Filtros de busca
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        setor_filter = request.GET.get('setor', '')
        prioridade_filter = request.GET.get('prioridade', '')
        data_filter = request.GET.get('data', '')  # Novo filtro de data

        if search:
            pedidos = pedidos.filter(
                Q(descricao__icontains=search) |
                Q(setor_solicitante__nome__icontains=search) |
                Q(equipamento__nome__icontains=search)
            )

        # Filtro de status - por padrão mostra apenas PENDENTES e EM_ANDAMENTO
        if status_filter:
            if status_filter == 'TODOS':
                # Não aplica filtro de status - mostra todos
                pass
            else:
                pedidos = pedidos.filter(status=status_filter)
        else:
            # Filtro padrão: apenas pedidos ativos (PENDENTE e EM_ANDAMENTO)
            pedidos = pedidos.filter(status__in=['PENDENTE', 'EM_ANDAMENTO'])

        if setor_filter and (perfil.is_transportes or perfil.is_admin_ou_supervisor):
            pedidos = pedidos.filter(setor_solicitante_id=setor_filter)

        if prioridade_filter:
            pedidos = pedidos.filter(prioridade=prioridade_filter)

        # Filtro de data (apenas para admin/supervisor)
        if data_filter and perfil.is_admin_ou_supervisor:
            from datetime import datetime
            try:
                data_filtro = datetime.strptime(data_filter, '%Y-%m-%d').date()
                pedidos = pedidos.filter(data_agendamento=data_filtro)
            except ValueError:
                pass

        # Ordenação:
        # 1. Pedidos ATRASADOS primeiro (data anterior a hoje e não concluídos)
        # 2. Pedidos do DIA ATUAL
        # 3. Pedidos FUTUROS (agendados para depois de hoje)
        # 4. Dentro de cada grupo: ordenar por PRIORIDADE (URGENTE → ALTA → MÉDIA → BAIXA)
        from django.db.models import Case, When, IntegerField, Value

        pedidos = pedidos.annotate(
            # Pedidos atrasados têm prioridade 0, hoje têm prioridade 1, futuros têm prioridade 2
            dia_order=Case(
                # Atrasados: data anterior a hoje E status não concluído/cancelado
                When(data_agendamento__lt=hoje, status__in=['PENDENTE', 'EM_ANDAMENTO'], then=Value(0)),
                # Hoje
                When(data_agendamento=hoje, then=Value(1)),
                # Futuros
                default=Value(2),
                output_field=IntegerField()
            ),
            # Prioridade: URGENTE=1, ALTA=2, MEDIA=3, BAIXA=4
            prioridade_order=Case(
                When(prioridade='URGENTE', then=1),
                When(prioridade='ALTA', then=2),
                When(prioridade='MEDIA', then=3),
                When(prioridade='BAIXA', then=4),
                default=5,
                output_field=IntegerField()
            ),
            # Status: PENDENTE primeiro, depois EM_ANDAMENTO
            status_priority=Case(
                When(status='PENDENTE', then=1),
                When(status='EM_ANDAMENTO', then=2),
                When(status='CANCELADO', then=3),
                When(status='CONCLUIDO', then=4),
                default=5,
                output_field=IntegerField()
            )
        ).order_by(
            'dia_order',           # 1º: ATRASADOS primeiro, depois HOJE, depois FUTUROS
            'data_agendamento',    # 2º: Ordenar por data (mais antiga primeiro para atrasados)
            'prioridade_order',    # 3º: Dentro do grupo, URGENTE primeiro
            'status_priority',     # 4º: PENDENTE antes de EM_ANDAMENTO
            'ordem_manual',        # 5º: Ordem manual (se houver)
            'data_solicitacao'     # 6º: Mais antigo primeiro
        )

        # Paginação
        paginator = Paginator(pedidos, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Dados para filtros
        setores = Setor.objects.filter(ativo=True) if (perfil.is_transportes or perfil.is_admin_ou_supervisor) else None

        # Contar pedidos agendados para o futuro (apenas para admin/supervisor)
        pedidos_agendados = 0
        if perfil.is_admin_ou_supervisor:
            pedidos_agendados = Pedido.objects.filter(
                data_agendamento__gt=hoje,
                status__in=['PENDENTE', 'EM_ANDAMENTO']
            ).count()

        context = {
            'perfil': perfil,
            'page_obj': page_obj,
            'setores': setores,
            'search': search,
            'status_filter': status_filter,
            'setor_filter': setor_filter,
            'prioridade_filter': prioridade_filter,
            'data_filter': data_filter,
            'status_choices': Pedido.STATUS_CHOICES,
            'prioridade_choices': Pedido.PRIORIDADE_CHOICES,
            'data_hoje': hoje.strftime('%Y-%m-%d'),
            'pedidos_agendados': pedidos_agendados,
        }

        return render(request, 'core/listar_pedidos.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def criar_pedido(request):
    """Criar novo pedido"""
    try:
        perfil = request.user.perfil

        # Todos os perfis podem criar pedidos (demandantes, supervisores e transportes)
        # Demandantes só podem criar para si mesmos
        # Supervisores e Transportes podem criar para qualquer um

        if request.method == 'POST':
            # Processar dados do formulário
            tipo_pedido = request.POST.get('tipo_pedido')
            descricao = request.POST.get('descricao')
            quantidade = 1  # Valor padrão fixo
            unidade_medida = 'UN'  # Valor padrão fixo
            prioridade = request.POST.get('prioridade', 'MEDIA')

            # Campos opcionais
            cliente_id = request.POST.get('cliente') or None
            area_origem_id = request.POST.get('area_origem') or None
            area_destino_id = request.POST.get('area_destino') or None
            equipamento_id = request.POST.get('equipamento') or None
            observacoes = request.POST.get('observacoes', '')

            # 📅 Data de agendamento (padrão: hoje)
            data_agendamento_str = request.POST.get('data_agendamento')
            if data_agendamento_str:
                from datetime import datetime, time
                data_agendamento = datetime.strptime(data_agendamento_str, '%Y-%m-%d').date()
            else:
                data_agendamento = timezone.now().date()

            # ⏰ Hora desejada (opcional)
            hora_agendamento_str = request.POST.get('hora_agendamento')
            hora_agendamento = None
            if hora_agendamento_str:
                from datetime import datetime, time
                try:
                    hora_agendamento = datetime.strptime(hora_agendamento_str, '%H:%M').time()
                except ValueError:
                    pass

            # 📸 Foto do material (opcional)
            foto_material = request.FILES.get('foto_material')

            # Obter nome do requisitante (usuário logado)
            nome_requisitante = request.user.get_full_name() or request.user.username

            # Validar IDs antes de criar (evitar FOREIGN KEY constraint failed)
            if cliente_id:
                if not Cliente.objects.filter(id=cliente_id).exists():
                    messages.error(request, f'Cliente com ID {cliente_id} não encontrado.')
                    return redirect('criar_pedido')

            if area_origem_id:
                if not Area.objects.filter(id=area_origem_id).exists():
                    messages.error(request, f'Área de origem com ID {area_origem_id} não encontrada.')
                    return redirect('criar_pedido')

            if area_destino_id:
                if not Area.objects.filter(id=area_destino_id).exists():
                    messages.error(request, f'Área de destino com ID {area_destino_id} não encontrada.')
                    return redirect('criar_pedido')

            if equipamento_id:
                if not Equipamento.objects.filter(id=equipamento_id).exists():
                    messages.error(request, f'Equipamento com ID {equipamento_id} não encontrado.')
                    return redirect('criar_pedido')

            # Criar pedido
            pedido = Pedido.objects.create(
                setor_solicitante=perfil.setor,
                tipo_pedido=tipo_pedido,
                descricao=descricao,
                quantidade=quantidade,
                unidade_medida=unidade_medida,
                prioridade=prioridade,
                cliente_id=cliente_id,
                area_origem_id=area_origem_id,
                area_destino_id=area_destino_id,
                equipamento_id=equipamento_id,
                observacoes=observacoes,
                criado_por=request.user,
                nome_requisitante=nome_requisitante,
                data_agendamento=data_agendamento,
                hora_agendamento=hora_agendamento,
                foto_material=foto_material
            )

            # Criar histórico
            obs_historico = 'Pedido criado'
            if data_agendamento > timezone.now().date():
                hora_str = f' às {hora_agendamento.strftime("%H:%M")}' if hora_agendamento else ''
                obs_historico = f'Pedido criado - Agendado para {data_agendamento.strftime("%d/%m/%Y")}{hora_str}'

            HistoricoPedido.objects.create(
                pedido=pedido,
                status_novo='PENDENTE',
                observacao=obs_historico,
                usuario=request.user
            )

            # Mensagem de sucesso
            if data_agendamento > timezone.now().date():
                hora_str = f' às {hora_agendamento.strftime("%H:%M")}' if hora_agendamento else ''
                messages.success(request, f'Pedido #{pedido.id} agendado para {data_agendamento.strftime("%d/%m/%Y")}{hora_str}!')
            else:
                hora_str = f' para às {hora_agendamento.strftime("%H:%M")}' if hora_agendamento else ''
                messages.success(request, f'Pedido #{pedido.id} criado com sucesso{hora_str}!')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'pedido_id': pedido.id})

            return redirect('listar_pedidos')

        # GET - mostrar formulário
        # Filtrar equipamentos que aparecem no select: OPERACIONAL ou MANUTENCAO
        # FORA_SERVICO e INATIVO não aparecem
        equipamentos_visiveis = Equipamento.objects.filter(
            ativo=True,
            status_operacional__in=['OPERACIONAL', 'MANUTENCAO']
        ).order_by('nome')

        context = {
            'perfil': perfil,
            'clientes': Cliente.objects.filter(ativo=True),
            'areas': Area.objects.filter(ativa=True),
            'equipamentos': equipamentos_visiveis,
            'tipo_choices': Pedido.TIPO_CHOICES,
            'prioridade_choices': Pedido.PRIORIDADE_CHOICES,
            'unidade_choices': Pedido.UNIDADE_CHOICES,
            'data_hoje': timezone.now().date().strftime('%Y-%m-%d'),
        }

        return render(request, 'core/criar_pedido.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def atualizar_status_pedido(request, pedido_id):
    """Atualizar status do pedido (transportes, admin e supervisor)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})

    try:
        perfil = request.user.perfil
        if not perfil.pode_iniciar_finalizar:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        pedido = get_object_or_404(Pedido, id=pedido_id)
        novo_status = request.POST.get('status')
        observacao = request.POST.get('observacao', '')
        foto_comprovacao = request.FILES.get('foto_comprovacao')

        if novo_status not in dict(Pedido.STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Status inválido'})

        # Validar foto obrigatória para conclusão
        if novo_status == 'CONCLUIDO' and not foto_comprovacao:
            return JsonResponse({'success': False, 'error': 'Foto de comprovação é obrigatória para concluir o serviço'})

        status_anterior = pedido.status
        pedido.status = novo_status
        pedido.atualizado_por = request.user

        # Salvar foto de comprovação se fornecida
        if foto_comprovacao:
            pedido.foto_comprovacao = foto_comprovacao

        pedido.save()

        # Criar histórico
        HistoricoPedido.objects.create(
            pedido=pedido,
            status_anterior=status_anterior,
            status_novo=novo_status,
            observacao=observacao,
            usuario=request.user
        )

        message = f'Status do pedido #{pedido.id} atualizado para {pedido.get_status_display()}'
        if foto_comprovacao:
            message += ' com foto de comprovação'

        return JsonResponse({
            'success': True,
            'message': message
        })

    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def detalhes_pedido(request, pedido_id):
    """Visualizar detalhes do pedido"""
    try:
        perfil = request.user.perfil

        if perfil.is_transportes:
            # Transportes pode ver qualquer pedido
            pedido = get_object_or_404(Pedido, id=pedido_id)
        else:
            # Requisitantes só veem seus próprios pedidos
            pedido = get_object_or_404(Pedido, id=pedido_id, criado_por=request.user)

        # Histórico do pedido
        historico = pedido.historico.all().order_by('-data_alteracao')

        context = {
            'perfil': perfil,
            'pedido': pedido,
            'historico': historico,
            'status_choices': Pedido.STATUS_CHOICES if perfil.is_transportes else None,
        }

        return render(request, 'core/detalhes_pedido.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def reordenar_pedidos(request):
    """Reordenar pedidos manualmente (apenas transportes)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})

    try:
        perfil = request.user.perfil
        if not perfil.pode_iniciar_finalizar:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        pedidos_ordem = request.POST.getlist('pedidos[]')

        for index, pedido_id in enumerate(pedidos_ordem):
            Pedido.objects.filter(id=pedido_id).update(ordem_manual=index)

        return JsonResponse({'success': True, 'message': 'Ordem dos pedidos atualizada'})

    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# API VIEWS PARA GERENCIAMENTO DE ÁREAS
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def api_areas(request):
    """API para listar e criar áreas"""
    try:
        if request.method == 'GET':
            # Listar áreas - todos podem ver
            areas = Area.objects.filter(ativa=True).order_by('nome')
            areas_data = []
            for area in areas:
                areas_data.append({
                    'id': area.id,
                    'nome': area.nome,
                    'localizacao': area.localizacao,
                    'descricao': area.descricao,
                })
            return JsonResponse(areas_data, safe=False)

        elif request.method == 'POST':
            # Criar nova área - apenas admin/supervisor
            try:
                perfil = request.user.perfil
                if not perfil.is_admin_ou_supervisor:
                    return JsonResponse({'success': False, 'error': 'Acesso negado. Apenas administradores e supervisores podem criar áreas.'})
            except PerfilUsuario.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Perfil de usuário não encontrado.'})

            nome = request.POST.get('nome', '').strip()
            localizacao = request.POST.get('localizacao', '').strip()
            descricao = request.POST.get('descricao', '').strip()

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome da área é obrigatório'})

            # Verificar se já existe uma área com o mesmo nome
            if Area.objects.filter(nome__iexact=nome, ativa=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe uma área com este nome'})

            # Criar a área
            area = Area.objects.create(
                nome=nome,
                localizacao=localizacao,
                descricao=descricao,
                ativa=True
            )

            return JsonResponse({
                'success': True,
                'area': {
                    'id': area.id,
                    'nome': area.nome,
                    'localizacao': area.localizacao,
                    'descricao': area.descricao,
                }
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["DELETE"])
def api_area_delete(request, area_id):
    """API para remover área"""
    try:
        area = get_object_or_404(Area, id=area_id)

        # Verificar se a área está sendo usada em algum pedido
        pedidos_origem = area.pedidos_origem.exists()
        pedidos_destino = area.pedidos_destino.exists()

        if pedidos_origem or pedidos_destino:
            # Não remover, apenas desativar
            area.ativa = False
            area.save()
            return JsonResponse({
                'success': True,
                'message': 'Área desativada pois está sendo usada em pedidos existentes'
            })
        else:
            # Pode remover completamente
            area.delete()
            return JsonResponse({'success': True, 'message': 'Área removida com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["GET", "PUT"])
def api_area_detail(request, area_id):
    """API para buscar e atualizar área específica"""
    try:
        # Verificar permissões
        try:
            perfil = request.user.perfil
            if not perfil.is_admin_ou_supervisor:
                return JsonResponse({'success': False, 'error': 'Acesso negado. Apenas administradores e supervisores podem gerenciar áreas.'})
        except PerfilUsuario.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Perfil de usuário não encontrado.'})

        area = get_object_or_404(Area, id=area_id)

        if request.method == 'GET':
            # Retornar dados da área
            return JsonResponse({
                'id': area.id,
                'nome': area.nome,
                'localizacao': area.localizacao,
                'descricao': area.descricao,
                'ativa': area.ativa,
            })

        elif request.method == 'PUT':
            # Atualizar área
            import urllib.parse

            # Para requisições PUT, precisamos ler os dados do body
            put_data = urllib.parse.parse_qs(request.body.decode('utf-8'))

            # Extrair valores (parse_qs retorna listas)
            nome = put_data.get('nome', [''])[0].strip()
            localizacao = put_data.get('localizacao', [''])[0].strip()
            descricao = put_data.get('descricao', [''])[0].strip()
            ativa = put_data.get('ativa', ['false'])[0] == 'true'

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome da área é obrigatório'})

            # Verificar se já existe outra área com o mesmo nome
            if Area.objects.filter(nome__iexact=nome, ativa=True).exclude(id=area.id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outra área com este nome'})

            # Atualizar a área
            area.nome = nome
            area.localizacao = localizacao
            area.descricao = descricao
            area.ativa = ativa
            area.save()

            return JsonResponse({
                'success': True,
                'area': {
                    'id': area.id,
                    'nome': area.nome,
                    'localizacao': area.localizacao,
                    'descricao': area.descricao,
                    'ativa': area.ativa,
                }
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# API VIEWS PARA GERENCIAMENTO DE SETORES
# =============================================================================

@login_required
@require_http_methods(["GET", "POST", "PUT"])
def api_setores(request):
    """API para listar e criar setores"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        if request.method == 'GET':
            # Listar setores
            setores = Setor.objects.filter(ativo=True).order_by('nome')
            setores_data = []
            for setor in setores:
                setores_data.append({
                    'id': setor.id,
                    'nome': setor.nome,
                    'responsavel': setor.responsavel,
                    'descricao': setor.descricao,
                    'ativo': setor.ativo,
                })
            return JsonResponse({
                'success': True,
                'setores': setores_data
            })

        elif request.method == 'POST':
            # Criar novo setor
            nome = request.POST.get('nome', '').strip()
            responsavel = request.POST.get('responsavel', '').strip()
            descricao = request.POST.get('descricao', '').strip()

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome do setor é obrigatório'})

            # Verificar se já existe um setor com o mesmo nome
            if Setor.objects.filter(nome__iexact=nome, ativo=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um setor com este nome'})

            # Criar o setor
            setor = Setor.objects.create(
                nome=nome,
                responsavel=responsavel,
                descricao=descricao,
                ativo=True
            )

            return JsonResponse({
                'success': True,
                'setor': {
                    'id': setor.id,
                    'nome': setor.nome,
                    'responsavel': setor.responsavel,
                    'descricao': setor.descricao,
                }
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def api_setor_detail(request, setor_id):
    """API para obter, editar ou remover setor específico"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        setor = get_object_or_404(Setor, id=setor_id)

        if request.method == 'GET':
            # Retornar dados do setor
            return JsonResponse({
                'success': True,
                'setor': {
                    'id': setor.id,
                    'nome': setor.nome,
                    'responsavel': setor.responsavel,
                    'descricao': setor.descricao,
                }
            })

        elif request.method == 'PUT':
            # Editar setor
            import urllib.parse

            # Para requisições PUT, precisamos ler os dados do body
            put_data = urllib.parse.parse_qs(request.body.decode('utf-8'))

            # Extrair valores (parse_qs retorna listas)
            nome = put_data.get('nome', [''])[0].strip()
            responsavel = put_data.get('responsavel', [''])[0].strip()
            descricao = put_data.get('descricao', [''])[0].strip()

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome do setor é obrigatório'})

            # Verificar se já existe outro setor com o mesmo nome
            if Setor.objects.filter(nome__iexact=nome, ativo=True).exclude(id=setor_id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro setor com este nome'})

            # Atualizar o setor
            setor.nome = nome
            setor.responsavel = responsavel
            setor.descricao = descricao
            setor.save()

            return JsonResponse({
                'success': True,
                'setor': {
                    'id': setor.id,
                    'nome': setor.nome,
                    'responsavel': setor.responsavel,
                    'descricao': setor.descricao,
                },
                'message': 'Setor atualizado com sucesso'
            })

        elif request.method == 'DELETE':
            # Remover setor
            usuarios_setor = PerfilUsuario.objects.filter(setor=setor).exists()
            pedidos_setor = Pedido.objects.filter(setor_solicitante=setor).exists()

            if usuarios_setor or pedidos_setor:
                # Não remover, apenas desativar
                setor.ativo = False
                setor.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Setor desativado pois está sendo usado por usuários ou pedidos existentes'
                })
            else:
                # Pode remover completamente
                setor.delete()
                return JsonResponse({'success': True, 'message': 'Setor removido com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# API VIEWS PARA GERENCIAMENTO DE EQUIPAMENTOS
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def api_equipamentos(request):
    """API para listar e criar equipamentos"""
    try:
        # Debug: log do usuário
        print(f"DEBUG: Usuário {request.user.username} acessando API equipamentos")

        # Verificar se é supervisor
        perfil = request.user.perfil
        print(f"DEBUG: Perfil do usuário: {perfil.codigo_perfil}, is_admin_ou_supervisor: {perfil.is_admin_ou_supervisor}")

        if not perfil.is_admin_ou_supervisor:
            print("DEBUG: Acesso negado - usuário não é admin/supervisor")
            return JsonResponse({'success': False, 'error': 'Acesso negado. Apenas administradores e supervisores podem acessar esta funcionalidade.'})

        if request.method == 'GET':
            # Listar equipamentos
            equipamentos = Equipamento.objects.all().order_by('nome')
            print(f"DEBUG: Encontrados {equipamentos.count()} equipamentos")
            equipamentos_data = []

            for equipamento in equipamentos:
                try:
                    equipamento_dict = {
                        'id': equipamento.id,
                        'nome': equipamento.nome,
                        'codigo': equipamento.codigo or '',
                        'categoria': equipamento.categoria,
                        'status_operacional': equipamento.status_operacional,
                        'ativo': equipamento.ativo,
                        'descricao': equipamento.descricao or '',
                        'status_display': equipamento.get_status_operacional_display(),
                        'status_css_class': equipamento.status_badge_class,
                        'is_operacional': equipamento.status_operacional == 'OPERACIONAL',
                        'is_em_manutencao': equipamento.status_operacional == 'MANUTENCAO',
                        'is_fora_servico': equipamento.status_operacional == 'FORA_SERVICO',
                        'aparece_no_select': equipamento.aparece_no_select,
                        'disponivel_para_pedido': equipamento.disponivel_para_pedido,
                    }

                    equipamentos_data.append(equipamento_dict)
                    print(f"DEBUG: Equipamento {equipamento.nome} adicionado com sucesso")
                except Exception as e:
                    print(f"DEBUG: Erro ao processar equipamento {equipamento.id}: {e}")
                    continue

            print(f"DEBUG: Retornando {len(equipamentos_data)} equipamentos")
            return JsonResponse(equipamentos_data, safe=False)

        elif request.method == 'POST':
            # Criar novo equipamento
            import json

            # Tentar obter dados do JSON primeiro, depois do POST
            try:
                data = json.loads(request.body)
            except:
                data = request.POST

            nome = data.get('nome', '').strip()
            codigo = data.get('codigo', '').strip()
            categoria = data.get('categoria', 'MATERIAL')
            status_operacional = data.get('status_operacional', 'OPERACIONAL')
            ativo = str(data.get('ativo', 'true')).lower() == 'true'
            descricao = data.get('descricao', '').strip()
            quantidade_litros = data.get('quantidade_litros')

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome do equipamento é obrigatório'})

            # Validar status_operacional
            status_validos = ['OPERACIONAL', 'MANUTENCAO', 'FORA_SERVICO', 'INATIVO']
            if status_operacional not in status_validos:
                status_operacional = 'OPERACIONAL'

            # Verificar se já existe um equipamento com o mesmo nome
            if Equipamento.objects.filter(nome__iexact=nome, ativo=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um equipamento com este nome'})

            # Verificar código se fornecido
            if codigo and Equipamento.objects.filter(codigo__iexact=codigo, ativo=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um equipamento com este código'})

            # Criar o equipamento (SEM em_servico - NOVA LÓGICA)
            equipamento = Equipamento.objects.create(
                nome=nome,
                codigo=codigo,
                categoria=categoria,
                status_operacional=status_operacional,
                descricao=descricao,
                ativo=ativo,
                quantidade_litros=quantidade_litros
            )

            return JsonResponse({
                'success': True,
                'equipamento': {
                    'id': equipamento.id,
                    'nome': equipamento.nome,
                    'codigo': equipamento.codigo,
                    'categoria': equipamento.categoria,
                    'status_operacional': equipamento.status_operacional,
                    'status_display': equipamento.status_display,
                    'status_css_class': equipamento.status_css_class,
                    'is_operacional': equipamento.is_operacional,
                    'is_em_manutencao': equipamento.is_em_manutencao,
                    'ativo': equipamento.ativo,
                    'em_servico': equipamento.em_servico,
                    'descricao': equipamento.descricao,
                    'quantidade_litros': equipamento.quantidade_litros,
                }
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_equipamento_detail(request, equipamento_id):
    """API para obter, editar ou remover equipamento específico"""
    try:
        # Verificar se é supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        equipamento = get_object_or_404(Equipamento, id=equipamento_id)

        if request.method == 'GET':
            # Retornar dados do equipamento (SEM em_servico - NOVA LÓGICA)
            return JsonResponse({
                'success': True,
                'equipamento': {
                    'id': equipamento.id,
                    'nome': equipamento.nome,
                    'codigo': equipamento.codigo,
                    'categoria': equipamento.categoria,
                    'status_operacional': equipamento.status_operacional,
                    'ativo': equipamento.ativo,
                    'descricao': equipamento.descricao,
                    'quantidade_litros': getattr(equipamento, 'quantidade_litros', None),
                    'aparece_no_select': equipamento.aparece_no_select,
                    'disponivel_para_pedido': equipamento.disponivel_para_pedido,
                }
            })

        elif request.method == 'PUT':
            # Editar equipamento
            import json
            data = json.loads(request.body)

            nome = data.get('nome', '').strip()
            codigo = data.get('codigo', '').strip()
            categoria = data.get('categoria', 'MATERIAL')
            status_operacional = data.get('status_operacional', 'OPERACIONAL')
            ativo = data.get('ativo', True)
            descricao = data.get('descricao', '').strip()
            quantidade_litros = data.get('quantidade_litros')

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome do equipamento é obrigatório'})

            # Validar status_operacional
            status_validos = ['OPERACIONAL', 'MANUTENCAO', 'FORA_SERVICO', 'INATIVO']
            if status_operacional not in status_validos:
                status_operacional = 'OPERACIONAL'

            # Verificar se já existe outro equipamento com o mesmo nome
            if Equipamento.objects.filter(nome__iexact=nome, ativo=True).exclude(id=equipamento_id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro equipamento com este nome'})

            # Verificar código se fornecido
            if codigo and Equipamento.objects.filter(codigo__iexact=codigo, ativo=True).exclude(id=equipamento_id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro equipamento com este código'})

            # Atualizar o equipamento (SEM em_servico - NOVA LÓGICA)
            equipamento.nome = nome
            equipamento.codigo = codigo
            equipamento.categoria = categoria
            equipamento.status_operacional = status_operacional
            equipamento.ativo = ativo
            equipamento.descricao = descricao
            equipamento.quantidade_litros = quantidade_litros
            equipamento.save()

            return JsonResponse({
                'success': True,
                'equipamento': {
                    'id': equipamento.id,
                    'nome': equipamento.nome,
                    'codigo': equipamento.codigo,
                    'categoria': equipamento.categoria,
                    'status_operacional': equipamento.status_operacional,
                    'status_display': equipamento.status_display,
                    'status_css_class': equipamento.status_css_class,
                    'is_operacional': equipamento.is_operacional,
                    'is_em_manutencao': equipamento.is_em_manutencao,
                    'is_fora_servico': equipamento.is_fora_servico,
                    'ativo': equipamento.ativo,
                    'aparece_no_select': equipamento.aparece_no_select,
                    'disponivel_para_pedido': equipamento.disponivel_para_pedido,
                    'descricao': equipamento.descricao,
                },
                'message': 'Equipamento atualizado com sucesso'
            })

        elif request.method == 'DELETE':
            # Remover equipamento
            pedidos_equipamento = Pedido.objects.filter(equipamento=equipamento).exists()

            if pedidos_equipamento:
                # Não remover, apenas desativar
                equipamento.ativo = False
                equipamento.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Equipamento desativado pois está sendo usado em pedidos existentes'
                })
            else:
                # Pode remover completamente
                equipamento.delete()
                return JsonResponse({'success': True, 'message': 'Equipamento removido com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# API VIEWS PARA GERENCIAMENTO DE CATEGORIAS DE EQUIPAMENTOS
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def api_categorias_equipamentos(request):
    """API para listar e criar categorias de equipamentos"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        if request.method == 'GET':
            # Listar categorias
            from .models import CategoriaEquipamento
            categorias = CategoriaEquipamento.objects.filter(ativo=True).order_by('nome')
            categorias_data = []
            for categoria in categorias:
                categorias_data.append({
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'descricao': categoria.descricao,
                    'cor': categoria.cor,
                    'ativo': categoria.ativo,
                })
            return JsonResponse(categorias_data, safe=False)

        elif request.method == 'POST':
            # Criar nova categoria
            import json

            # Tentar obter dados do JSON primeiro, depois do POST
            try:
                data = json.loads(request.body)
            except:
                data = request.POST

            nome = data.get('nome', '').strip()
            descricao = data.get('descricao', '').strip()
            cor = data.get('cor', 'primary')

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome da categoria é obrigatório'})

            # Verificar se já existe uma categoria com o mesmo nome
            from .models import CategoriaEquipamento
            if CategoriaEquipamento.objects.filter(nome__iexact=nome, ativo=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe uma categoria com este nome'})

            # Criar a categoria
            categoria = CategoriaEquipamento.objects.create(
                nome=nome.upper(),  # Salvar em maiúsculo
                descricao=descricao,
                cor=cor,
                ativo=True
            )

            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'descricao': categoria.descricao,
                    'cor': categoria.cor,
                    'ativo': categoria.ativo,
                }
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_categoria_equipamento_detail(request, categoria_id):
    """API para obter, editar ou remover categoria específica"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        from .models import CategoriaEquipamento
        categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)

        if request.method == 'GET':
            # Retornar dados da categoria
            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'descricao': categoria.descricao,
                    'cor': categoria.cor,
                    'ativo': categoria.ativo,
                }
            })

        elif request.method == 'PUT':
            # Editar categoria
            import json
            data = json.loads(request.body)

            nome = data.get('nome', '').strip()
            descricao = data.get('descricao', '').strip()
            cor = data.get('cor', categoria.cor)

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome da categoria é obrigatório'})

            # Verificar se já existe outra categoria com o mesmo nome
            if CategoriaEquipamento.objects.filter(nome__iexact=nome, ativo=True).exclude(id=categoria_id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe uma categoria com este nome'})

            # Atualizar categoria
            categoria.nome = nome.upper()
            categoria.descricao = descricao
            categoria.cor = cor
            categoria.save()

            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'descricao': categoria.descricao,
                    'cor': categoria.cor,
                    'ativo': categoria.ativo,
                }
            })

        elif request.method == 'DELETE':
            # Verificar se a categoria está sendo usada
            equipamentos_usando = Equipamento.objects.filter(categoria=categoria.nome, ativo=True).count()

            if equipamentos_usando > 0:
                # Não pode remover, apenas desativar
                categoria.ativo = False
                categoria.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Categoria desativada pois está sendo usada por {equipamentos_usando} equipamento(s)'
                })
            else:
                # Pode remover completamente
                categoria.delete()
                return JsonResponse({'success': True, 'message': 'Categoria removida com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# API VIEWS PARA GERENCIAMENTO DE CLIENTES
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def api_clientes(request):
    """API para listar e criar clientes"""
    try:
        # Verificar permissões
        perfil = request.user.perfil

        if request.method == 'GET':
            # DEMANDANTE pode listar clientes para criar pedidos
            # Outros perfis precisam ser admin ou supervisor
            if not (perfil.is_admin_ou_supervisor or perfil.codigo_perfil == 'DEMANDANTE'):
                return JsonResponse({'success': False, 'error': 'Acesso negado'})

        else:
            # Para POST (criar), apenas admin ou supervisor
            if not perfil.is_admin_ou_supervisor:
                return JsonResponse({'success': False, 'error': 'Acesso negado'})

        if request.method == 'GET':
            # Para DEMANDANTE: apenas clientes ativos
            # Para ADMIN/SUPERVISOR: todos os clientes (para gerenciamento)
            if perfil.codigo_perfil == 'DEMANDANTE':
                clientes = Cliente.objects.filter(ativo=True).order_by('nome')
            else:
                clientes = Cliente.objects.all().order_by('nome')

            clientes_data = []
            for cliente in clientes:
                clientes_data.append({
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'endereco': cliente.endereco,
                    'ativo': cliente.ativo,
                })
            return JsonResponse(clientes_data, safe=False)

        elif request.method == 'POST':
            # Criar novo cliente
            nome = request.POST.get('nome', '').strip()
            email = request.POST.get('email', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            endereco = request.POST.get('endereco', '').strip()
            ativo = request.POST.get('ativo', 'true').lower() == 'true'

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome do cliente é obrigatório'})

            # Verificar se já existe um cliente com o mesmo nome
            if Cliente.objects.filter(nome__iexact=nome, ativo=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um cliente com este nome'})

            # Verificar email se fornecido
            if email and Cliente.objects.filter(email__iexact=email, ativo=True).exists():
                return JsonResponse({'success': False, 'error': 'Já existe um cliente com este email'})

            # Criar o cliente
            cliente = Cliente.objects.create(
                nome=nome,
                email=email,
                telefone=telefone,
                endereco=endereco,
                ativo=ativo
            )

            return JsonResponse({
                'success': True,
                'cliente': {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'endereco': cliente.endereco,
                    'ativo': cliente.ativo,
                }
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_cliente_detail(request, cliente_id):
    """API para obter, editar ou remover cliente específico"""
    try:
        # Verificar se é supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        cliente = get_object_or_404(Cliente, id=cliente_id)

        if request.method == 'GET':
            # Retornar dados do cliente
            return JsonResponse({
                'success': True,
                'cliente': {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'endereco': cliente.endereco,
                    'ativo': cliente.ativo,
                }
            })

        elif request.method == 'PUT':
            # Editar cliente
            import json
            data = json.loads(request.body)

            nome = data.get('nome', '').strip()
            email = data.get('email', '').strip()
            telefone = data.get('telefone', '').strip()
            endereco = data.get('endereco', '').strip()
            ativo = data.get('ativo', True)

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome do cliente é obrigatório'})

            # Verificar se já existe outro cliente com o mesmo nome (apenas entre os ativos)
            if Cliente.objects.filter(nome__iexact=nome, ativo=True).exclude(id=cliente_id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro cliente ativo com este nome'})

            # Verificar email se fornecido
            if email and Cliente.objects.filter(email__iexact=email, ativo=True).exclude(id=cliente_id).exists():
                return JsonResponse({'success': False, 'error': 'Já existe outro cliente com este email'})

            # Atualizar o cliente
            cliente.nome = nome
            cliente.email = email
            cliente.telefone = telefone
            cliente.endereco = endereco
            cliente.ativo = ativo
            cliente.save()

            return JsonResponse({
                'success': True,
                'cliente': {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'endereco': cliente.endereco,
                    'ativo': cliente.ativo,
                },
                'message': 'Cliente atualizado com sucesso'
            })

        elif request.method == 'DELETE':
            # Remover cliente
            pedidos_cliente = Pedido.objects.filter(cliente=cliente).exists()

            if pedidos_cliente:
                # Não remover, apenas desativar
                cliente.ativo = False
                cliente.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Cliente desativado pois está sendo usado em pedidos existentes'
                })
            else:
                # Pode remover completamente
                cliente.delete()
                return JsonResponse({'success': True, 'message': 'Cliente removido com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# API VIEWS PARA GERENCIAMENTO DE USUÁRIOS
# =============================================================================

@login_required
@require_http_methods(["GET", "POST"])
def api_usuarios(request):
    """API para listar e criar usuários"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        if request.method == 'GET':
            # Listar usuários
            from django.contrib.auth.models import User
            usuarios = User.objects.select_related('perfil', 'perfil__setor').all().order_by('username')
            usuarios_data = []

            for usuario in usuarios:
                usuario_data = {
                    'id': usuario.id,
                    'username': usuario.username,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'email': usuario.email,
                    'is_active': usuario.is_active,
                    'date_joined': usuario.date_joined.strftime('%d/%m/%Y %H:%M') if usuario.date_joined else None,
                }

                if hasattr(usuario, 'perfil') and usuario.perfil:
                    usuario_data.update({
                        'perfil': usuario.perfil.codigo_perfil,
                        'perfil_display': usuario.perfil.nome_perfil,
                        'setor_id': usuario.perfil.setor.id if usuario.perfil.setor else None,
                        'setor_nome': usuario.perfil.setor.nome if usuario.perfil.setor else None,
                        'empresa_id': usuario.perfil.empresa.id if usuario.perfil.empresa else None,
                        'empresa_nome': usuario.perfil.empresa.nome if usuario.perfil.empresa else None,
                        'disponivel': usuario.perfil.disponivel,
                        'telefone': usuario.perfil.telefone,
                        'precisa_alterar_senha': usuario.perfil.precisa_alterar_senha,
                        'senha_alterada_em': usuario.perfil.senha_alterada_em.strftime('%d/%m/%Y %H:%M') if usuario.perfil.senha_alterada_em else None,
                    })
                else:
                    usuario_data.update({
                        'perfil': None,
                        'perfil_display': 'Sem perfil',
                        'setor_id': None,
                        'setor_nome': 'Sem setor',
                        'telefone': None,
                        'precisa_alterar_senha': False,
                        'senha_alterada_em': None,
                    })

                usuarios_data.append(usuario_data)

            return JsonResponse(usuarios_data, safe=False)

        elif request.method == 'POST':
            # Criar usuário
            # Suportar tanto FormData quanto JSON
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
                username = data.get('username', '').strip()
                first_name = data.get('first_name', '').strip()
                last_name = data.get('last_name', '').strip()
                email = data.get('email', '').strip()
                telefone = data.get('telefone', '').strip()
                setor_id = data.get('setor_id')
                perfil_tipo = data.get('perfil')
                empresa_id = data.get('empresa_id')
                disponivel = data.get('disponivel', True)
            else:
                username = request.POST.get('username', '').strip()
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                telefone = request.POST.get('telefone', '').strip()
                setor_id = request.POST.get('setor_id')
                perfil_tipo = request.POST.get('perfil')
                empresa_id = request.POST.get('empresa_id')
                disponivel = request.POST.get('disponivel', 'true').lower() == 'true'

            if not username:
                return JsonResponse({'success': False, 'error': 'Nome de usuário é obrigatório'})

            if not setor_id:
                return JsonResponse({'success': False, 'error': 'Setor é obrigatório'})

            if not perfil_tipo:
                return JsonResponse({'success': False, 'error': 'Perfil de acesso é obrigatório'})

            # Validar empresa para terceiros
            if perfil_tipo.startswith('TERCEIRO_') and not empresa_id:
                return JsonResponse({'success': False, 'error': 'Empresa é obrigatória para usuários terceirizados'})

            # Verificar se já existe usuário com mesmo username
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': f'Usuário "{username}" já existe'})

            # Verificar se email já existe (se fornecido)
            if email and User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': f'Email "{email}" já está em uso'})

            # Verificar se setor existe
            try:
                setor = Setor.objects.get(id=setor_id, ativo=True)
            except Setor.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Setor não encontrado'})

            # Verificar se empresa existe (se fornecida)
            empresa = None
            if empresa_id:
                try:
                    from .models import Empresa
                    empresa = Empresa.objects.get(id=empresa_id, ativo=True)
                except Empresa.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Empresa não encontrada'})

            # Buscar TipoPerfil
            try:
                from .models import TipoPerfil
                tipo_perfil = TipoPerfil.objects.get(codigo=perfil_tipo)
            except TipoPerfil.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Tipo de perfil "{perfil_tipo}" não encontrado'})

            try:
                # Criar usuário
                user = User.objects.create_user(
                    username=username,
                    password='123456',  # Senha padrão
                    first_name=first_name,
                    last_name=last_name,
                    email=email if email else ''
                )

                # Verificar se já existe perfil (criado pelo signal) e atualizar, ou criar novo
                try:
                    perfil_usuario = PerfilUsuario.objects.get(user=user)
                    # Atualizar perfil existente
                    perfil_usuario.setor = setor
                    perfil_usuario.tipo_perfil = tipo_perfil
                    perfil_usuario.empresa = empresa
                    perfil_usuario.telefone = telefone
                    perfil_usuario.disponivel = disponivel
                    perfil_usuario.precisa_alterar_senha = True
                    perfil_usuario.save()
                except PerfilUsuario.DoesNotExist:
                    # Criar novo perfil se não existir
                    perfil_usuario = PerfilUsuario.objects.create(
                        user=user,
                        setor=setor,
                        tipo_perfil=tipo_perfil,
                        empresa=empresa,
                        telefone=telefone,
                        disponivel=disponivel,
                        precisa_alterar_senha=True
                    )

                return JsonResponse({
                    'success': True,
                    'usuario': {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'is_active': user.is_active,
                        'perfil': perfil_usuario.codigo_perfil,
                        'perfil_display': perfil_usuario.nome_perfil,
                        'setor_nome': setor.nome,
                        'telefone': perfil_usuario.telefone,
                    }
                })

            except Exception as e:
                # Se houve erro, deletar o usuário se foi criado
                try:
                    if 'user' in locals():
                        user.delete()
                except:
                    pass
                return JsonResponse({'success': False, 'error': f'Erro ao criar usuário: {str(e)}'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def api_usuario_detalhes(request, usuario_id):
    """API para obter, editar ou remover usuário específico"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        from django.contrib.auth.models import User
        usuario = get_object_or_404(User, id=usuario_id)

        if request.method == 'GET':
            # Retornar dados do usuário
            usuario_data = {
                'id': usuario.id,
                'username': usuario.username,
                'first_name': usuario.first_name,
                'last_name': usuario.last_name,
                'email': usuario.email,
                'is_active': usuario.is_active,
            }

            if hasattr(usuario, 'perfil') and usuario.perfil:
                usuario_data.update({
                    'perfil': usuario.perfil.codigo_perfil,
                    'setor_id': usuario.perfil.setor.id if usuario.perfil.setor else None,
                    'empresa_id': usuario.perfil.empresa.id if usuario.perfil.empresa else None,
                    'disponivel': usuario.perfil.disponivel,
                    'telefone': usuario.perfil.telefone,
                })

            return JsonResponse({
                'success': True,
                'usuario': usuario_data
            })

        elif request.method == 'PUT':
            # Editar usuário
            import json
            data = json.loads(request.body)

            username = data.get('username', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            email = data.get('email', '').strip()
            telefone = data.get('telefone', '').strip()
            setor_id = data.get('setor_id')
            perfil_tipo = data.get('perfil')
            empresa_id = data.get('empresa_id')
            disponivel = data.get('disponivel', True)
            is_active = data.get('is_active', True)

            if not username:
                return JsonResponse({'success': False, 'error': 'Nome de usuário é obrigatório'})

            if not setor_id:
                return JsonResponse({'success': False, 'error': 'Setor é obrigatório'})

            if not perfil_tipo:
                return JsonResponse({'success': False, 'error': 'Perfil de acesso é obrigatório'})

            # Validar empresa para terceiros
            if perfil_tipo.startswith('TERCEIRO_') and not empresa_id:
                return JsonResponse({'success': False, 'error': 'Empresa é obrigatória para usuários terceirizados'})

            # Verificar se já existe outro usuário com mesmo username
            if User.objects.filter(username=username).exclude(id=usuario_id).exists():
                return JsonResponse({'success': False, 'error': f'Já existe outro usuário com o nome "{username}"'})

            # Verificar se email já existe (se fornecido)
            if email and User.objects.filter(email=email).exclude(id=usuario_id).exists():
                return JsonResponse({'success': False, 'error': f'Já existe outro usuário com o email "{email}"'})

            # Verificar se setor existe
            try:
                setor = Setor.objects.get(id=setor_id, ativo=True)
            except Setor.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Setor não encontrado'})

            # Verificar se empresa existe (se fornecida)
            empresa = None
            if empresa_id:
                try:
                    from .models import Empresa
                    empresa = Empresa.objects.get(id=empresa_id, ativo=True)
                except Empresa.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Empresa não encontrada'})

            # Buscar TipoPerfil
            try:
                from .models import TipoPerfil
                tipo_perfil = TipoPerfil.objects.get(codigo=perfil_tipo)
            except TipoPerfil.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Tipo de perfil "{perfil_tipo}" não encontrado'})

            try:
                # Atualizar usuário
                usuario.username = username
                usuario.first_name = first_name
                usuario.last_name = last_name
                usuario.email = email if email else ''
                usuario.is_active = is_active == 'true' if isinstance(is_active, str) else bool(is_active)
                usuario.save()

                # Atualizar ou criar perfil
                if hasattr(usuario, 'perfil') and usuario.perfil:
                    perfil_usuario = usuario.perfil
                    perfil_usuario.setor = setor
                    perfil_usuario.tipo_perfil = tipo_perfil
                    perfil_usuario.empresa = empresa
                    perfil_usuario.telefone = telefone
                    perfil_usuario.disponivel = disponivel
                    perfil_usuario.save()
                else:
                    perfil_usuario = PerfilUsuario.objects.create(
                        user=usuario,
                        setor=setor,
                        tipo_perfil=tipo_perfil,
                        empresa=empresa,
                        telefone=telefone,
                        disponivel=disponivel,
                        precisa_alterar_senha=True
                    )

                return JsonResponse({
                    'success': True,
                    'usuario': {
                        'id': usuario.id,
                        'username': usuario.username,
                        'first_name': usuario.first_name,
                        'last_name': usuario.last_name,
                        'email': usuario.email,
                        'is_active': usuario.is_active,
                        'perfil': perfil_usuario.codigo_perfil,
                        'perfil_display': perfil_usuario.nome_perfil,
                        'setor_nome': setor.nome,
                        'telefone': perfil_usuario.telefone,
                    },
                    'message': 'Usuário atualizado com sucesso'
                })

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Erro ao atualizar usuário: {str(e)}'})

        elif request.method == 'DELETE':
            # Remover usuário
            # Verificar se o usuário tem pedidos associados
            pedidos_criados = Pedido.objects.filter(criado_por=usuario).exists()
            pedidos_atualizados = Pedido.objects.filter(atualizado_por=usuario).exists()

            if pedidos_criados or pedidos_atualizados:
                # Não remover, apenas desativar
                usuario.is_active = False
                usuario.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Usuário desativado pois possui pedidos associados'
                })
            else:
                # Pode remover completamente
                usuario.delete()
                return JsonResponse({'success': True, 'message': 'Usuário removido com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# VIEWS PARA EDITAR E EXCLUIR PEDIDOS
# =============================================================================

@login_required
def editar_pedido(request, pedido_id):
    """View para editar pedido (demandantes próprios pedidos pendentes, supervisores todos os pedidos)"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Verificar permissões
        if perfil.is_transportes:
            messages.error(request, 'Setor de transportes não pode editar pedidos.')
            return redirect('listar_pedidos')

        # Supervisores podem editar qualquer pedido, demandantes apenas os próprios
        if not perfil.pode_editar_pedidos and pedido.criado_por != request.user:
            messages.error(request, 'Você só pode editar seus próprios pedidos.')
            return redirect('listar_pedidos')

        if pedido.status != 'PENDENTE':
            messages.error(request, 'Apenas pedidos pendentes podem ser editados.')
            return redirect('listar_pedidos')

        if request.method == 'POST':
            # Processar edição
            tipo_pedido = request.POST.get('tipo_pedido')
            descricao = request.POST.get('descricao', '').strip()
            prioridade = request.POST.get('prioridade')
            area_origem_id = request.POST.get('area_origem')
            area_destino_id = request.POST.get('area_destino')
            cliente_id = request.POST.get('cliente')
            equipamento_id = request.POST.get('equipamento')
            observacoes = request.POST.get('observacoes', '').strip()

            # 📅 Data e hora de agendamento
            data_agendamento_str = request.POST.get('data_agendamento')
            hora_agendamento_str = request.POST.get('hora_agendamento')

            # 📸 Foto do material
            foto_material = request.FILES.get('foto_material')

            # Validações
            if not tipo_pedido or tipo_pedido not in dict(Pedido.TIPO_CHOICES):
                messages.error(request, 'Tipo de pedido inválido.')
                return redirect('editar_pedido', pedido_id=pedido_id)

            if not descricao:
                messages.error(request, 'Descrição é obrigatória.')
                return redirect('editar_pedido', pedido_id=pedido_id)

            if not prioridade or prioridade not in dict(Pedido.PRIORIDADE_CHOICES):
                messages.error(request, 'Prioridade inválida.')
                return redirect('editar_pedido', pedido_id=pedido_id)

            # Atualizar pedido
            pedido.tipo_pedido = tipo_pedido
            pedido.descricao = descricao
            pedido.prioridade = prioridade
            pedido.observacoes = observacoes

            # Campos opcionais
            pedido.area_origem = Area.objects.get(id=area_origem_id) if area_origem_id else None
            pedido.area_destino = Area.objects.get(id=area_destino_id) if area_destino_id else None
            pedido.cliente = Cliente.objects.get(id=cliente_id) if cliente_id else None
            pedido.equipamento = Equipamento.objects.get(id=equipamento_id) if equipamento_id else None

            # 📅 Data de agendamento
            if data_agendamento_str:
                from datetime import datetime
                pedido.data_agendamento = datetime.strptime(data_agendamento_str, '%Y-%m-%d').date()

            # ⏰ Hora de agendamento
            if hora_agendamento_str:
                from datetime import datetime
                try:
                    pedido.hora_agendamento = datetime.strptime(hora_agendamento_str, '%H:%M').time()
                except ValueError:
                    pedido.hora_agendamento = None
            else:
                pedido.hora_agendamento = None

            # 📸 Foto do material (só atualiza se enviou nova)
            if foto_material:
                pedido.foto_material = foto_material

            # Manter o nome do requisitante original (não alterar)
            if not pedido.nome_requisitante:
                pedido.nome_requisitante = request.user.get_full_name() or request.user.username

            pedido.save()

            # Registrar no histórico
            HistoricoPedido.objects.create(
                pedido=pedido,
                status_anterior=pedido.status,
                status_novo=pedido.status,
                observacao=f'Pedido editado por {request.user.get_full_name() or request.user.username}',
                usuario=request.user
            )

            messages.success(request, 'Pedido atualizado com sucesso!')
            return redirect('detalhes_pedido', pedido_id=pedido.id)

        # GET - mostrar formulário de edição
        context = {
            'perfil': perfil,
            'pedido': pedido,
            'clientes': Cliente.objects.filter(ativo=True),
            'areas': Area.objects.filter(ativa=True),
            'equipamentos': Equipamento.objects.filter(ativo=True),
            'tipo_choices': Pedido.TIPO_CHOICES,
            'prioridade_choices': Pedido.PRIORIDADE_CHOICES,
            'data_hoje': timezone.now().strftime('%Y-%m-%d'),
        }
        return render(request, 'core/editar_pedido.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Erro ao editar pedido: {str(e)}')
        return redirect('listar_pedidos')


@login_required
@require_http_methods(["DELETE"])
def excluir_pedido(request, pedido_id):
    """API para excluir pedido (demandantes próprios pedidos pendentes, supervisores todos os pedidos)"""
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Verificar permissões
        if perfil.is_transportes:
            return JsonResponse({'success': False, 'error': 'Setor de transportes não pode excluir pedidos.'})

        # Supervisores podem excluir qualquer pedido, demandantes apenas os próprios
        if not perfil.pode_editar_pedidos and pedido.criado_por != request.user:
            return JsonResponse({'success': False, 'error': 'Você só pode excluir seus próprios pedidos.'})

        if pedido.status != 'PENDENTE':
            return JsonResponse({'success': False, 'error': 'Apenas pedidos pendentes podem ser excluídos.'})

        # Salvar informações para o log
        pedido_info = f"#{pedido.id} - {pedido.descricao[:50]}"

        # Excluir pedido (isso também excluirá o histórico devido ao CASCADE)
        pedido.delete()

        return JsonResponse({
            'success': True,
            'message': f'Pedido {pedido_info} foi excluído com sucesso.'
        })

    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil de usuário não encontrado.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# GESTÃO DE USUÁRIOS
# =============================================================================

@login_required
def listar_usuarios(request):
    """Lista todos os usuários do sistema (apenas para supervisores)"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            messages.error(request, 'Acesso negado. Apenas administradores e supervisores podem gerenciar usuários.')
            return redirect('dashboard')

        from django.contrib.auth.models import User
        usuarios = User.objects.select_related('perfil', 'perfil__setor').all().order_by('username')

        context = {
            'usuarios': usuarios,
            'perfil': perfil,
        }

        return render(request, 'core/listar_usuarios.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')

@login_required
def teste_botao(request):
    """Página de teste para verificar botões"""
    return render(request, 'core/teste_botao.html')

@login_required
def diagnostico_perfil(request):
    """Página de diagnóstico completo do perfil do usuário"""
    return render(request, 'core/diagnostico_perfil.html')

@login_required
def cadastrar_usuario(request):
    """Cadastra novo usuário com senha padrão 123456"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            messages.error(request, 'Acesso negado. Apenas administradores e supervisores podem cadastrar usuários.')
            return redirect('dashboard')

        if request.method == 'POST':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            setor_id = request.POST.get('setor')
            perfil_tipo = request.POST.get('perfil')
            telefone = request.POST.get('telefone', '')

            # Validações
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Usuário "{username}" já existe.')
                return redirect('cadastrar_usuario')

            if email and User.objects.filter(email=email).exists():
                messages.error(request, f'Email "{email}" já está em uso.')
                return redirect('cadastrar_usuario')

            if not setor_id:
                messages.error(request, 'Setor é obrigatório.')
                return redirect('cadastrar_usuario')

            try:
                setor = Setor.objects.get(id=setor_id)
            except Setor.DoesNotExist:
                messages.error(request, 'Setor não encontrado.')
                return redirect('cadastrar_usuario')

            try:
                # Criar usuário
                user = User.objects.create_user(
                    username=username,
                    password='123456',  # Senha padrão
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )

                # Criar perfil
                PerfilUsuario.objects.create(
                    user=user,
                    setor=setor,
                    perfil=perfil_tipo,
                    telefone=telefone,
                    precisa_alterar_senha=True
                )

                messages.success(request, f'Usuário "{username}" cadastrado com sucesso! Senha padrão: 123456')
                return redirect('listar_usuarios')

            except Exception as e:
                # Se houve erro, deletar o usuário se foi criado
                try:
                    if 'user' in locals():
                        user.delete()
                except:
                    pass
                messages.error(request, f'Erro ao cadastrar usuário: {str(e)}')
                return redirect('cadastrar_usuario')

        # GET - mostrar formulário
        setores = Setor.objects.filter(ativo=True).order_by('nome')

        context = {
            'setores': setores,
            'perfil': perfil,
        }

        return render(request, 'core/cadastrar_usuario.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
@require_http_methods(["POST"])
def resetar_senha_usuario(request, user_id):
    """Reseta a senha do usuário para 123456 (apenas supervisores)"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado.'})

        from django.contrib.auth.models import User
        user = get_object_or_404(User, id=user_id)

        # Resetar senha
        user.perfil.resetar_senha_padrao()

        return JsonResponse({
            'success': True,
            'message': f'Senha do usuário "{user.username}" foi resetada para 123456'
        })

    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def alterar_senha(request):
    """Permite ao usuário alterar sua própria senha"""
    try:
        perfil = request.user.perfil

        if request.method == 'POST':
            senha_atual = request.POST.get('senha_atual')
            nova_senha = request.POST.get('nova_senha')
            confirmar_senha = request.POST.get('confirmar_senha')

            # Validações
            if not request.user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta.')
                return redirect('alterar_senha')

            if nova_senha != confirmar_senha:
                messages.error(request, 'Nova senha e confirmação não coincidem.')
                return redirect('alterar_senha')

            if len(nova_senha) < 6:
                messages.error(request, 'Nova senha deve ter pelo menos 6 caracteres.')
                return redirect('alterar_senha')

            if nova_senha == '123456':
                messages.error(request, 'A nova senha não pode ser a senha padrão (123456).')
                return redirect('alterar_senha')

            # Alterar senha
            request.user.set_password(nova_senha)
            request.user.save()

            # Marcar que a senha foi alterada
            perfil.marcar_senha_alterada()

            # Fazer login novamente com a nova senha
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)

            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('dashboard')

        # GET - mostrar formulário
        context = {
            'perfil': perfil,
            'precisa_alterar': perfil.precisa_alterar_senha,
        }

        return render(request, 'core/alterar_senha.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


# === VIEWS DE LOCALIZAÇÃO EM TEMPO REAL ===

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def atualizar_localizacao(request):
    """Atualiza a localização do usuário em tempo real"""
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        precisao = data.get('accuracy')

        if not latitude or not longitude:
            return JsonResponse({'success': False, 'error': 'Coordenadas inválidas'})

        # Atualizar localização do usuário
        perfil = request.user.perfil
        perfil.atualizar_localizacao(latitude, longitude, precisao)

        return JsonResponse({
            'success': True,
            'message': 'Localização atualizada com sucesso',
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def marcar_offline(request):
    """Marca o usuário como offline"""
    try:
        perfil = request.user.perfil
        perfil.status_online = False
        perfil.save(update_fields=['status_online'])

        return JsonResponse({'success': True, 'message': 'Status atualizado para offline'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_localizacoes_operadores(request):
    """API para obter localizações de todos os operadores (apenas supervisores)"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        # Buscar todos os operadores (transportes) com localização
        operadores = PerfilUsuario.objects.filter(
            tipo_perfil__codigo='TRANSPORTES',
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('user', 'setor')

        localizacoes = []
        for operador in operadores:
            # Calcular tempo desde última atualização
            tempo_offline = None
            if operador.ultima_localizacao:
                tempo_offline = (timezone.now() - operador.ultima_localizacao).total_seconds() / 60  # em minutos

            localizacoes.append({
                'id': operador.user.id,
                'nome': operador.user.get_full_name() or operador.user.username,
                'setor': operador.setor.nome,
                'latitude': float(operador.latitude),
                'longitude': float(operador.longitude),
                'precisao': operador.precisao_gps,
                'status': operador.status_localizacao,
                'online': operador.status_online,
                'ultima_atualizacao': operador.ultima_localizacao.isoformat() if operador.ultima_localizacao else None,
                'tempo_offline_minutos': tempo_offline,
                'telefone': operador.telefone
            })

        return JsonResponse({
            'success': True,
            'operadores': localizacoes,
            'total': len(localizacoes),
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mapa_operadores(request):
    """Página do mapa com localização dos operadores (apenas supervisores)"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            messages.error(request, 'Acesso negado. Apenas administradores e supervisores podem ver o mapa.')
            return redirect('dashboard')

        # Estatísticas dos operadores
        total_operadores = PerfilUsuario.objects.filter(tipo_perfil__codigo='TRANSPORTES').count()
        operadores_online = PerfilUsuario.objects.filter(
            tipo_perfil__codigo='TRANSPORTES',
            status_online=True
        ).count()

        operadores_com_localizacao = PerfilUsuario.objects.filter(
            tipo_perfil__codigo='TRANSPORTES',
            latitude__isnull=False,
            longitude__isnull=False
        ).count()

        context = {
            'perfil': perfil,
            'total_operadores': total_operadores,
            'operadores_online': operadores_online,
            'operadores_com_localizacao': operadores_com_localizacao,
            'operadores_offline': total_operadores - operadores_online,
        }

        return render(request, 'core/mapa_operadores.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def debug_localizacao(request):
    """Página de debug para verificar localização dos operadores"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            messages.error(request, 'Acesso negado.')
            return redirect('dashboard')

        # Buscar todos os operadores
        operadores = PerfilUsuario.objects.filter(tipo_perfil__codigo='TRANSPORTES').select_related('user', 'setor')

        # Coordenadas do Estaleiro Atlântico Sul
        # Ajuste estas coordenadas para a localização exata do estaleiro
        estaleiro_lat = -8.0476  # Latitude do estaleiro
        estaleiro_lng = -34.8770  # Longitude do estaleiro

        # IMPORTANTE: Para obter coordenadas corretas:
        # 1. Abra Google Maps
        # 2. Pesquise "Estaleiro Atlântico Sul"
        # 3. Clique no local exato
        # 4. Copie as coordenadas e substitua acima

        debug_info = []
        for operador in operadores:
            # Calcular distância do estaleiro se tiver localização
            distancia_estaleiro = None
            if operador.tem_localizacao:
                distancia_estaleiro = operador.calcular_distancia(estaleiro_lat, estaleiro_lng)

            info = {
                'usuario': operador.user.get_full_name() or operador.user.username,
                'username': operador.user.username,
                'tipo_perfil': operador.tipo_perfil.nome if operador.tipo_perfil else 'N/A',
                'setor': operador.setor.nome if operador.setor else 'N/A',
                'telefone': operador.telefone,
                'tem_localizacao': operador.tem_localizacao,
                'latitude': operador.latitude,
                'longitude': operador.longitude,
                'ultima_localizacao': operador.ultima_localizacao,
                'status_online': operador.status_online,
                'precisao_gps': operador.precisao_gps,
                'status_localizacao': operador.status_localizacao,
                'localizacao_atualizada': operador.localizacao_atualizada,
                'distancia_estaleiro': distancia_estaleiro,
                'dentro_do_raio': distancia_estaleiro is not None and distancia_estaleiro <= 50,
            }
            debug_info.append(info)

        context = {
            'perfil': perfil,
            'operadores': debug_info,
            'total_operadores': len(debug_info),
        }

        return render(request, 'core/debug_localizacao.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def configurar_estaleiro(request):
    """Página para configurar coordenadas do estaleiro"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            messages.error(request, 'Acesso negado.')
            return redirect('dashboard')

        if request.method == 'POST':
            # Processar coordenadas enviadas
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')

            if latitude and longitude:
                try:
                    lat_float = float(latitude)
                    lng_float = float(longitude)

                    # Aqui você pode salvar em um modelo de configuração
                    # Por enquanto, vamos apenas mostrar uma mensagem
                    messages.success(request, f'Coordenadas atualizadas: {lat_float}, {lng_float}')
                    messages.info(request, 'Para aplicar permanentemente, atualize o código em views.py')

                except ValueError:
                    messages.error(request, 'Coordenadas inválidas. Use formato decimal.')
            else:
                messages.error(request, 'Informe latitude e longitude.')

        # Coordenadas atuais (as mesmas do debug)
        estaleiro_lat = -8.0476
        estaleiro_lng = -34.8770

        context = {
            'perfil': perfil,
            'estaleiro_lat': estaleiro_lat,
            'estaleiro_lng': estaleiro_lng,
        }

        return render(request, 'core/configurar_estaleiro.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('admin:index')


@login_required
def api_obter_pedido(request, pedido_id):
    """API para obter dados de um pedido específico"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        pedido = get_object_or_404(Pedido, id=pedido_id)

        pedido_data = {
            'id': pedido.id,
            'descricao': pedido.descricao,
            'prioridade': pedido.prioridade,
            'status': pedido.status,
            'observacoes': pedido.observacoes,
            'tipo_pedido': pedido.tipo_pedido,
            'quantidade': pedido.quantidade,
            'unidade_medida': pedido.unidade_medida,
            'nome_requisitante': pedido.nome_requisitante,
            'data_solicitacao': pedido.data_solicitacao.isoformat(),
            'criado_por': pedido.criado_por.get_full_name() or pedido.criado_por.username,
        }

        return JsonResponse({'success': True, 'pedido': pedido_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_editar_pedido_rapido(request, pedido_id):
    """API para edição rápida de pedidos (admin/supervisor)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})

    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Parse JSON data
        import json
        data = json.loads(request.body)

        # Atualizar campos
        pedido.prioridade = data.get('prioridade', pedido.prioridade)
        pedido.status = data.get('status', pedido.status)
        pedido.descricao = data.get('descricao', pedido.descricao)
        pedido.observacoes = data.get('observacoes', pedido.observacoes)
        pedido.atualizado_por = request.user

        # Se status mudou para EM_ANDAMENTO, definir data_inicio
        if pedido.status == 'EM_ANDAMENTO' and not pedido.data_inicio:
            pedido.data_inicio = timezone.now()

        # Se status mudou para CONCLUIDO, definir data_conclusao
        if pedido.status == 'CONCLUIDO' and not pedido.data_conclusao:
            pedido.data_conclusao = timezone.now()

        pedido.save()

        # Registrar no histórico
        from .models import HistoricoPedido
        HistoricoPedido.objects.create(
            pedido=pedido,
            usuario=request.user,
            acao='EDITADO_RAPIDO',
            observacao=f'Edição rápida: Status={pedido.status}, Prioridade={pedido.prioridade}'
        )

        return JsonResponse({'success': True, 'message': 'Pedido atualizado com sucesso'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_listar_operadores(request):
    """API para listar operadores disponíveis"""
    try:
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        # Buscar operadores (perfil TRANSPORTES)
        operadores = PerfilUsuario.objects.filter(
            perfil='TRANSPORTES',
            user__is_active=True
        ).select_related('user', 'setor')

        operadores_data = []
        for operador in operadores:
            operadores_data.append({
                'id': operador.user.id,
                'nome': operador.user.get_full_name() or operador.user.username,
                'setor': operador.setor.nome,
                'telefone': operador.telefone,
                'online': operador.status_online,
            })

        return JsonResponse({'success': True, 'operadores': operadores_data})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def teste_modal(request):
    """Página de teste para o modal de equipamentos"""
    return render(request, 'teste_modal.html')


@login_required
def relatorios_pedidos(request):
    """View para relatórios de pedidos com filtros"""
    try:
        perfil = request.user.perfil

        # Filtros do request
        cliente_id = request.GET.get('cliente')
        mes = request.GET.get('mes')
        ano = request.GET.get('ano')
        status = request.GET.get('status')
        demandante_id = request.GET.get('demandante')

        # Query base - demandantes veem apenas seus pedidos
        if perfil.is_admin_ou_supervisor:
            pedidos = Pedido.objects.all()
        else:
            pedidos = Pedido.objects.filter(criado_por=request.user)

        # Aplicar filtros
        if cliente_id:
            pedidos = pedidos.filter(cliente_id=cliente_id)

        if mes and ano:
            pedidos = pedidos.filter(
                data_solicitacao__month=mes,
                data_solicitacao__year=ano
            )
        elif ano:
            pedidos = pedidos.filter(data_solicitacao__year=ano)

        # Filtro de status nos relatórios
        if status:
            if status == 'TODOS':
                # Não aplica filtro de status - mostra todos
                pass
            else:
                pedidos = pedidos.filter(status=status)
        # Nos relatórios, por padrão mostra todos (diferente da listagem)

        if demandante_id and perfil.is_admin_ou_supervisor:
            pedidos = pedidos.filter(criado_por_id=demandante_id)

        # Ordenar por data mais recente
        pedidos = pedidos.order_by('-data_solicitacao')

        # Estatísticas
        total_pedidos = pedidos.count()
        pedidos_pendentes = pedidos.filter(status='PENDENTE').count()
        pedidos_aprovados = pedidos.filter(status='APROVADO').count()
        pedidos_rejeitados = pedidos.filter(status='REJEITADO').count()

        # Dados para os filtros
        clientes = Cliente.objects.filter(ativo=True).order_by('nome')
        anos_disponiveis = Pedido.objects.dates('data_solicitacao', 'year', order='DESC')

        # Lista de demandantes (apenas para admin/supervisor)
        demandantes = []
        if perfil.is_admin_ou_supervisor:
            demandantes = PerfilUsuario.objects.filter(
                perfil__in=['ADMIN', 'SUPERVISOR', 'REQUISITANTE', 'DEMANDANTE']
            ).select_related('user').order_by('user__first_name', 'user__username')

        # Verificar se é exportação CSV
        if request.GET.get('export') == 'csv':
            return exportar_pedidos_csv(pedidos, request)

        # Paginação
        paginator = Paginator(pedidos, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'pedidos': page_obj,
            'total_pedidos': total_pedidos,
            'pedidos_pendentes': pedidos_pendentes,
            'pedidos_aprovados': pedidos_aprovados,
            'pedidos_rejeitados': pedidos_rejeitados,
            'clientes': clientes,
            'anos_disponiveis': anos_disponiveis,
            'demandantes': demandantes,
            'filtros': {
                'cliente_id': cliente_id,
                'mes': mes,
                'ano': ano,
                'status': status,
                'demandante_id': demandante_id,
            },
            'meses': [
                (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
                (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
                (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
                (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
            ],
            'status_choices': Pedido.STATUS_CHOICES,
        }

        return render(request, 'core/relatorios_pedidos.html', context)

    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')


def exportar_pedidos_csv(pedidos, request):
    """Exporta pedidos para CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="relatorio_pedidos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    # Adicionar BOM para UTF-8 (para Excel reconhecer acentos)
    response.write('\ufeff')

    writer = csv.writer(response)

    # Cabeçalho
    headers = [
        'ID', 'Data Solicitação', 'Cliente', 'Descrição', 'Status',
        'Prioridade', 'Setor', 'Área', 'Data Necessidade'
    ]

    # Adicionar coluna demandante se for admin/supervisor
    if hasattr(request.user, 'perfil') and request.user.perfil.is_admin_ou_supervisor:
        headers.append('Demandante')
        headers.append('Setor Demandante')

    writer.writerow(headers)

    # Dados
    for pedido in pedidos:
        row = [
            pedido.id,
            pedido.data_solicitacao.strftime('%d/%m/%Y %H:%M'),
            pedido.cliente.nome,
            pedido.descricao,
            pedido.get_status_display(),
            pedido.get_prioridade_display(),
            pedido.setor.nome if pedido.setor else '',
            pedido.area.nome if pedido.area else '',
            pedido.data_necessidade.strftime('%d/%m/%Y') if pedido.data_necessidade else '',
        ]

        # Adicionar dados do demandante se for admin/supervisor
        if hasattr(request.user, 'perfil') and request.user.perfil.is_admin_ou_supervisor:
            row.append(pedido.criado_por.get_full_name() or pedido.criado_por.username)
            row.append(pedido.criado_por.perfil.setor.nome if hasattr(pedido.criado_por, 'perfil') and pedido.criado_por.perfil.setor else '')

        writer.writerow(row)

    return response


@login_required
@require_http_methods(["POST"])
def api_atualizar_posicao(request):
    """API para atualizar a posição GPS do usuário"""
    try:
        import json
        from django.utils import timezone
        from decimal import Decimal

        # Verificar se o usuário tem perfil
        perfil = request.user.perfil

        # Parse do JSON
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        precisao = data.get('precisao', 0)

        if latitude is None or longitude is None:
            return JsonResponse({'success': False, 'error': 'Latitude e longitude são obrigatórias'})

        # Atualizar posição do usuário
        perfil.latitude = Decimal(str(latitude))
        perfil.longitude = Decimal(str(longitude))
        perfil.precisao_gps = float(precisao) if precisao else None
        perfil.ultima_localizacao = timezone.now()
        perfil.status_online = True
        perfil.save()

        return JsonResponse({
            'success': True,
            'message': 'Posição atualizada com sucesso',
            'latitude': float(perfil.latitude),
            'longitude': float(perfil.longitude),
            'precisao': perfil.precisao_gps,
            'ultima_atualizacao': perfil.ultima_localizacao.isoformat()
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_equipamentos_pedido(request):
    """API específica para listar equipamentos no select de pedidos

    Lógica SIMPLIFICADA:
    - APARECEM: ativo=True E status_operacional IN (OPERACIONAL, MANUTENCAO)
    - DISPONÍVEIS: status_operacional='OPERACIONAL' (selecionável)
    - BLOQUEADOS: status_operacional='MANUTENCAO' (aparece mas disabled)
    - NÃO APARECEM: ativo=False OU status_operacional IN (FORA_SERVICO, INATIVO)
    """
    try:
        # Filtrar equipamentos que devem aparecer no select
        equipamentos_queryset = Equipamento.objects.filter(
            ativo=True,
            status_operacional__in=['OPERACIONAL', 'MANUTENCAO']
        ).order_by('nome')

        equipamentos_data = []
        for equipamento in equipamentos_queryset:
            # OPERACIONAL = disponível, MANUTENCAO = bloqueado
            disponivel = equipamento.status_operacional == 'OPERACIONAL'

            equipamentos_data.append({
                'id': equipamento.id,
                'nome': equipamento.nome,
                'codigo': equipamento.codigo or '',
                'categoria': equipamento.categoria,
                'status_operacional': equipamento.status_operacional,
                'disponivel': disponivel,
                'texto_completo': f"{equipamento.nome}{' (' + equipamento.codigo + ')' if equipamento.codigo else ''}",
                'texto_disabled': f"{equipamento.nome}{' (' + equipamento.codigo + ')' if equipamento.codigo else ''} - Em Manutenção" if not disponivel else None
            })
        return JsonResponse(equipamentos_data, safe=False)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# =============================================================================
# VIEW CUSTOMIZADA DE LOGOUT
# =============================================================================

def custom_logout(request):
    """View customizada de logout que funciona com GET e POST"""
    try:
        # Marcar usuário como offline se tiver perfil
        if hasattr(request.user, 'perfil'):
            perfil = request.user.perfil
            perfil.status_online = False
            perfil.save(update_fields=['status_online'])
    except:
        pass  # Ignorar erros de perfil

    # Fazer logout
    logout(request)

    # Adicionar mensagem de sucesso
    messages.success(request, 'Logout realizado com sucesso!')

    # Redirecionar para login
    return redirect('login')


# ===== GERENCIAMENTO DE EMPRESAS =====

@login_required
@require_http_methods(["GET", "POST"])
def api_empresas(request):
    """API para listar e criar empresas"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        if request.method == 'GET':
            # Listar empresas
            from .models import Empresa
            empresas = Empresa.objects.filter(ativo=True).order_by('nome')

            empresas_data = []
            for empresa in empresas:
                empresas_data.append({
                    'id': empresa.id,
                    'nome': empresa.nome,
                    'cnpj': empresa.cnpj,
                    'tipo': empresa.tipo,
                    'tipo_display': empresa.get_tipo_display(),
                    'contrato': empresa.contrato,
                    'contato': empresa.contato,
                    'telefone': empresa.telefone,
                    'email': empresa.email,
                })

            return JsonResponse({'success': True, 'empresas': empresas_data})

        elif request.method == 'POST':
            # Criar empresa
            import json
            data = json.loads(request.body)

            nome = data.get('nome', '').strip()
            cnpj = data.get('cnpj', '').strip()
            tipo = data.get('tipo', 'TERCEIRIZADA')
            contrato = data.get('contrato', '').strip()
            contato = data.get('contato', '').strip()
            telefone = data.get('telefone', '').strip()
            email = data.get('email', '').strip()
            observacoes = data.get('observacoes', '').strip()

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome da empresa é obrigatório'})

            # Verificar se já existe empresa com mesmo nome
            from .models import Empresa
            if Empresa.objects.filter(nome=nome).exists():
                return JsonResponse({'success': False, 'error': f'Já existe uma empresa com o nome "{nome}"'})

            try:
                # Criar empresa
                empresa = Empresa.objects.create(
                    nome=nome,
                    cnpj=cnpj,
                    tipo=tipo,
                    contrato=contrato,
                    contato=contato,
                    telefone=telefone,
                    email=email,
                    observacoes=observacoes,
                    ativo=True
                )

                return JsonResponse({
                    'success': True,
                    'empresa': {
                        'id': empresa.id,
                        'nome': empresa.nome,
                        'cnpj': empresa.cnpj,
                        'tipo': empresa.tipo,
                        'tipo_display': empresa.get_tipo_display(),
                        'contrato': empresa.contrato,
                        'contato': empresa.contato,
                        'telefone': empresa.telefone,
                        'email': empresa.email,
                    }
                })

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Erro ao criar empresa: {str(e)}'})

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro na API de empresas: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def api_empresa_detalhes(request, empresa_id):
    """API para obter, editar ou remover empresa específica"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        from .models import Empresa
        empresa = get_object_or_404(Empresa, id=empresa_id)

        if request.method == 'GET':
            # Retornar dados da empresa
            return JsonResponse({
                'success': True,
                'empresa': {
                    'id': empresa.id,
                    'nome': empresa.nome,
                    'cnpj': empresa.cnpj,
                    'tipo': empresa.tipo,
                    'tipo_display': empresa.get_tipo_display(),
                    'contrato': empresa.contrato,
                    'contato': empresa.contato,
                    'telefone': empresa.telefone,
                    'email': empresa.email,
                    'observacoes': empresa.observacoes,
                    'ativo': empresa.ativo,
                }
            })

        elif request.method == 'PUT':
            # Editar empresa
            import json
            data = json.loads(request.body)

            nome = data.get('nome', '').strip()
            cnpj = data.get('cnpj', '').strip()
            tipo = data.get('tipo', 'TERCEIRIZADA')
            contrato = data.get('contrato', '').strip()
            contato = data.get('contato', '').strip()
            telefone = data.get('telefone', '').strip()
            email = data.get('email', '').strip()
            observacoes = data.get('observacoes', '').strip()

            if not nome:
                return JsonResponse({'success': False, 'error': 'Nome da empresa é obrigatório'})

            # Verificar se já existe outra empresa com mesmo nome
            if Empresa.objects.filter(nome=nome).exclude(id=empresa_id).exists():
                return JsonResponse({'success': False, 'error': f'Já existe outra empresa com o nome "{nome}"'})

            try:
                # Atualizar empresa
                empresa.nome = nome
                empresa.cnpj = cnpj
                empresa.tipo = tipo
                empresa.contrato = contrato
                empresa.contato = contato
                empresa.telefone = telefone
                empresa.email = email
                empresa.observacoes = observacoes
                empresa.save()

                return JsonResponse({
                    'success': True,
                    'empresa': {
                        'id': empresa.id,
                        'nome': empresa.nome,
                        'cnpj': empresa.cnpj,
                        'tipo': empresa.tipo,
                        'tipo_display': empresa.get_tipo_display(),
                        'contrato': empresa.contrato,
                        'contato': empresa.contato,
                        'telefone': empresa.telefone,
                        'email': empresa.email,
                    }
                })

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Erro ao atualizar empresa: {str(e)}'})

        elif request.method == 'DELETE':
            # Remover empresa (soft delete)
            try:
                # Verificar se há usuários vinculados
                usuarios_vinculados = PerfilUsuario.objects.filter(empresa=empresa).count()
                if usuarios_vinculados > 0:
                    return JsonResponse({
                        'success': False,
                        'error': f'Não é possível remover esta empresa pois há {usuarios_vinculados} usuário(s) vinculado(s) a ela.'
                    })

                # Soft delete
                empresa.ativo = False
                empresa.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Empresa "{empresa.nome}" removida com sucesso'
                })

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Erro ao remover empresa: {str(e)}'})

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro na API de detalhes da empresa: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_mecanicos_por_empresa(request):
    """
    API para buscar mecânicos vinculados a uma empresa
    """
    try:
        empresa_id = request.GET.get('empresa_id')

        if not empresa_id:
            return JsonResponse({'success': False, 'error': 'ID da empresa é obrigatório'})

        from django.contrib.auth.models import User
        from .models import Empresa

        # Buscar empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        if not empresa:
            return JsonResponse({'success': False, 'error': 'Empresa não encontrada'})

        # Buscar mecânicos vinculados à empresa
        mecanicos = User.objects.filter(
            perfil__empresa=empresa,
            is_active=True
        ).select_related('perfil', 'perfil__setor').order_by('first_name', 'last_name', 'username')

        mecanicos_data = []
        for mecanico in mecanicos:
            perfil = mecanico.perfil

            # Contar chamados abertos (se houver)
            chamados_abertos = 0
            try:
                from frota_locada.models import ChamadoManutencao
                chamados_abertos = ChamadoManutencao.objects.filter(
                    atribuido_para=mecanico,
                    status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
                ).count()
            except:
                pass

            mecanicos_data.append({
                'id': mecanico.id,
                'nome': mecanico.get_full_name() or mecanico.username,
                'username': mecanico.username,
                'email': mecanico.email,
                'perfil': perfil.codigo_perfil,
                'perfil_display': perfil.nome_perfil,
                'setor': perfil.setor.nome,
                'telefone': perfil.telefone,
                'disponivel': perfil.disponivel,
                'chamados_abertos': chamados_abertos,
            })

        return JsonResponse({
            'success': True,
            'empresa': {
                'id': empresa.id,
                'nome': empresa.nome,
            },
            'mecanicos': mecanicos_data,
            'total': len(mecanicos_data)
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro na API de mecânicos por empresa: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_mecanicos_por_maquina(request):
    """
    API para buscar mecânicos disponíveis baseado na máquina/empresa
    Retorna apenas mecânicos vinculados à empresa da máquina
    """
    try:
        maquina_id = request.GET.get('maquina_id')

        if not maquina_id:
            return JsonResponse({'success': False, 'error': 'ID da máquina é obrigatório'})

        from frota_locada.models import Maquina

        # Buscar máquina
        maquina = Maquina.objects.select_related('empresa').filter(id=maquina_id).first()
        if not maquina:
            return JsonResponse({'success': False, 'error': 'Máquina não encontrada'})

        # Buscar empresa da máquina
        empresa = maquina.empresa
        if not empresa:
            return JsonResponse({'success': False, 'error': 'Máquina não tem empresa vinculada'})

        # Buscar mecânicos vinculados à empresa (via PerfilUsuario)
        from django.contrib.auth.models import User
        mecanicos = User.objects.filter(
            perfil__empresa=empresa,
            perfil__disponivel=True,
            is_active=True
        ).select_related('perfil')

        mecanicos_data = []
        for mecanico in mecanicos:
            perfil = mecanico.perfil

            # Contar chamados abertos
            from frota_locada.models import ChamadoManutencao
            chamados_abertos = ChamadoManutencao.objects.filter(
                atribuido_para=mecanico,
                status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
            ).count()

            mecanicos_data.append({
                'id': mecanico.id,
                'nome': mecanico.get_full_name() or mecanico.username,
                'username': mecanico.username,
                'perfil': perfil.codigo_perfil,
                'perfil_display': perfil.nome_perfil,
                'empresa': empresa.nome,
                'empresa_id': empresa.id,
                'disponivel': perfil.disponivel,
                'chamados_abertos': chamados_abertos,
                'telefone': perfil.telefone,
            })

        return JsonResponse({
            'success': True,
            'maquina': {
                'id': maquina.id,
                'nome': maquina.nome,
                'codigo': maquina.codigo,
            },
            'empresa': {
                'id': empresa.id,
                'nome': empresa.nome,
                'tipo': empresa.get_tipo_display(),
            },
            'mecanicos': mecanicos_data,
            'total': len(mecanicos_data)
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro na API de mecânicos por máquina: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def api_tecnicos_disponiveis(request):
    """API para buscar técnicos disponíveis filtrados por empresa e/ou setor"""
    try:
        empresa_id = request.GET.get('empresa_id')
        setor_id = request.GET.get('setor_id')
        perfil_tipo = request.GET.get('perfil_tipo')  # 'MANUTENCAO', 'TERCEIRO', etc.

        # Filtro base: usuários ativos e disponíveis
        tecnicos = PerfilUsuario.objects.filter(
            user__is_active=True,
            disponivel=True
        ).select_related('user', 'setor', 'empresa')

        # Filtrar por empresa se fornecido
        if empresa_id:
            tecnicos = tecnicos.filter(empresa_id=empresa_id)

        # Filtrar por setor se fornecido
        if setor_id:
            tecnicos = tecnicos.filter(setor_id=setor_id)

        # Filtrar por tipo de perfil se fornecido
        if perfil_tipo:
            if perfil_tipo == 'MANUTENCAO':
                tecnicos = tecnicos.filter(perfil__startswith='MANUTENCAO')
            elif perfil_tipo == 'TERCEIRO':
                tecnicos = tecnicos.filter(perfil__startswith='TERCEIRO_')

        tecnicos_data = []
        for tecnico in tecnicos:
            # Contar chamados de MANUTENÇÃO (frota_locada) abertos
            # NÃO misturar com chamados de TRANSPORTE (gases)
            chamados_abertos = tecnico.get_chamados_manutencao_abertos_count()

            tecnicos_data.append({
                'id': tecnico.user.id,
                'nome': tecnico.user.get_full_name() or tecnico.user.username,
                'username': tecnico.user.username,
                'perfil': tecnico.codigo_perfil,
                'perfil_display': tecnico.nome_perfil,
                'setor': tecnico.setor.nome,
                'setor_id': tecnico.setor.id,
                'empresa': tecnico.nome_empresa,
                'empresa_id': tecnico.empresa.id if tecnico.empresa else None,
                'is_terceiro': tecnico.is_terceiro,
                'disponivel': tecnico.disponivel,
                'chamados_abertos': chamados_abertos,
                'telefone': tecnico.telefone,
            })

        return JsonResponse({'success': True, 'tecnicos': tecnicos_data})

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao buscar técnicos disponíveis: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


# ===== GERENCIAMENTO DE PERFIS =====

@login_required
@require_http_methods(["GET"])
def api_perfis_disponiveis(request):
    """API para listar perfis disponíveis"""
    try:
        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not (perfil.is_admin or perfil.is_supervisor):
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        # Obter todos os perfis disponíveis da tabela TipoPerfil
        from .models import TipoPerfil

        perfis = TipoPerfil.objects.all().order_by('nome')
        perfis_data = []

        for tipo_perfil in perfis:
            # Contar quantos usuários têm este perfil
            usuarios_count = PerfilUsuario.objects.filter(tipo_perfil=tipo_perfil).count()

            perfis_data.append({
                'codigo': tipo_perfil.codigo,
                'nome': tipo_perfil.nome,  # Nome original
                'nome_exibicao': tipo_perfil.nome,  # Nome personalizado ou original
                'descricao': tipo_perfil.descricao,
                'usuarios_count': usuarios_count,
                'tem_personalizacao': True,  # Todos agora têm registro
                'ativo': tipo_perfil.ativo,
                'is_admin': tipo_perfil.is_admin,
                'is_supervisor': tipo_perfil.is_supervisor,
                'is_terceiro': tipo_perfil.is_terceiro,
                'is_sistema': tipo_perfil.is_sistema
            })

        return JsonResponse({
            'success': True,
            'perfis': perfis_data
        })

    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
@require_http_methods(["POST"])
def api_criar_perfil(request):
    """API para criar novo perfil - ADMIN e SUPERVISOR têm acesso total"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🆕 API criar perfil chamada por: {request.user.username}")

        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        logger.info(f"👤 Perfil do usuário: {perfil.codigo_perfil}, is_admin_ou_supervisor: {perfil.is_admin_ou_supervisor}")

        if not perfil.is_admin_ou_supervisor:
            logger.warning(f"❌ Acesso negado para {request.user.username} ({perfil.codigo_perfil})")
            return JsonResponse({'success': False, 'error': 'Apenas administradores e supervisores podem gerenciar perfis'})

        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip().upper()
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()

        logger.info(f"📋 Dados recebidos: codigo={codigo}, nome={nome}, descricao={descricao}")

        if not codigo or not nome:
            logger.warning(f"❌ Dados incompletos: codigo={codigo}, nome={nome}")
            return JsonResponse({'success': False, 'error': 'Código e nome são obrigatórios'})

        # Validar formato do código
        import re
        if not re.match(r'^[A-Z0-9_]+$', codigo):
            return JsonResponse({'success': False, 'error': 'Código deve conter apenas letras maiúsculas, números e underscore'})

        # FUNCIONALIDADE REAL PARA ADMIN E SUPERVISOR
        # Criar novo tipo de perfil na tabela TipoPerfil

        from .models import TipoPerfil

        # Verificar se já existe um perfil com este código
        if TipoPerfil.objects.filter(codigo=codigo).exists():
            return JsonResponse({
                'success': False,
                'error': f'Já existe um perfil com o código {codigo}.\n\n' +
                        f'Use o botão de EDITAR (✏️) para modificar este perfil.'
            })

        # Criar novo tipo de perfil
        tipo_perfil = TipoPerfil.objects.create(
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            is_admin=False,  # Por padrão não é admin
            is_supervisor=False,  # Por padrão não é supervisor
            is_terceiro=False,  # Por padrão não é terceiro
            ativo=True,
            is_sistema=False  # Perfis criados pelo usuário não são do sistema
        )

        logger.info(f"✅ ADMIN/SUPERVISOR {request.user.username} criou novo tipo de perfil: {codigo} - {nome}")

        mensagem_sucesso = f'✅ NOVO TIPO DE PERFIL CRIADO COM SUCESSO!\n\n' + \
                          f'👤 Criado por: {request.user.username} ({perfil.codigo_perfil})\n' + \
                          f'📋 Código: {codigo}\n' + \
                          f'📝 Nome: {nome}\n' + \
                          f'📄 Descrição: {descricao}\n\n' + \
                          f'💾 SALVO NO BANCO DE DADOS!\n' + \
                          f'🆔 ID: {tipo_perfil.id}\n\n' + \
                          f'⚙️ Configure as permissões (is_admin, is_supervisor, is_terceiro) no Django Admin se necessário.'

        return JsonResponse({
            'success': True,
            'message': mensagem_sucesso,
            'perfil': {
                'id': tipo_perfil.id,
                'codigo': codigo,
                'nome': nome,
                'descricao': descricao,
                'criado_por': request.user.username,
                'criado_em': tipo_perfil.created_at.isoformat()
            }
        })

    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil do usuário não encontrado'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao criar perfil: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})


@require_http_methods(["PUT", "POST"])
def api_editar_perfil(request):
    """API para editar perfil existente - ADMIN e SUPERVISOR têm acesso total"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"✏️ API editar perfil chamada por: {request.user.username}")

        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        logger.info(f"👤 Perfil do usuário: {perfil.codigo_perfil}, is_admin_ou_supervisor: {perfil.is_admin_ou_supervisor}")

        if not perfil.is_admin_ou_supervisor:
            logger.warning(f"❌ Acesso negado para {request.user.username} ({perfil.codigo_perfil})")
            return JsonResponse({'success': False, 'error': 'Apenas administradores e supervisores podem editar perfis'})

        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip().upper()
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()

        logger.info(f"📋 Dados recebidos para edição: codigo={codigo}, nome={nome}, descricao={descricao}")

        if not codigo or not nome:
            logger.warning(f"❌ Dados incompletos: codigo={codigo}, nome={nome}")
            return JsonResponse({'success': False, 'error': 'Código e nome são obrigatórios'})

        # FUNCIONALIDADE REAL PARA ADMIN E SUPERVISOR
        # Atualizar tipo de perfil na tabela TipoPerfil

        from .models import TipoPerfil
        from django.utils import timezone

        # Buscar o tipo de perfil
        try:
            tipo_perfil = TipoPerfil.objects.get(codigo=codigo)
        except TipoPerfil.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Perfil {codigo} não encontrado'})

        # Atualizar dados
        tipo_perfil.nome = nome
        tipo_perfil.descricao = descricao
        tipo_perfil.ativo = True  # Reativar se estava inativo
        tipo_perfil.save()

        # Log da ação para auditoria
        logger.info(f"✅ ADMIN/SUPERVISOR {request.user.username} editou o perfil: {codigo} - {nome}")

        return JsonResponse({
            'success': True,
            'message': f'✅ PERFIL EDITADO COM SUCESSO!\n\n' +
                      f'👤 Editado por: {request.user.username} ({perfil.codigo_perfil})\n' +
                      f'📋 Código: {codigo}\n' +
                      f'📝 Nome: {nome}\n' +
                      f'📄 Descrição: {descricao}\n\n' +
                      f'💾 As alterações foram SALVAS NO BANCO DE DADOS!',
            'perfil': {
                'codigo': codigo,
                'nome': nome,
                'descricao': descricao,
                'editado_por': request.user.username,
                'editado_em': timezone.now().isoformat()
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao editar perfil: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})


@login_required
@require_http_methods(["DELETE", "POST"])
def api_remover_perfil(request):
    """API para remover/excluir perfil de acesso - ADMIN e SUPERVISOR"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🗑️ API remover perfil chamada por: {request.user.username}")

        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        logger.info(f"👤 Perfil do usuário: {perfil.codigo_perfil}, is_admin_ou_supervisor: {perfil.is_admin_ou_supervisor}")

        if not perfil.is_admin_ou_supervisor:
            logger.warning(f"❌ Acesso negado para {request.user.username} ({perfil.codigo_perfil})")
            return JsonResponse({'success': False, 'error': 'Apenas administradores e supervisores podem remover perfis'})

        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip().upper()
        excluir_completamente = data.get('excluir_completamente', False)

        logger.info(f"📋 Código recebido para remoção: {codigo}, Excluir completamente: {excluir_completamente}")

        if not codigo:
            logger.warning(f"❌ Código não fornecido")
            return JsonResponse({'success': False, 'error': 'Código do perfil é obrigatório'})

        from .models import TipoPerfil
        from django.utils import timezone

        # Buscar o tipo de perfil
        try:
            tipo_perfil = TipoPerfil.objects.get(codigo=codigo)
        except TipoPerfil.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Perfil {codigo} não encontrado'
            })

        # Verificar se pode excluir
        if excluir_completamente:
            pode_excluir, mensagem = tipo_perfil.pode_ser_excluido()
            if not pode_excluir:
                logger.warning(f"❌ {mensagem}")
                return JsonResponse({
                    'success': False,
                    'error': f'❌ NÃO É POSSÍVEL EXCLUIR!\n\n{mensagem}'
                })

        nome = tipo_perfil.nome
        descricao = tipo_perfil.descricao

        # Agora executar a ação (desativar ou excluir)
        if excluir_completamente:
            # EXCLUIR COMPLETAMENTE do banco de dados
            tipo_perfil.delete()

            logger.info(f"✅ ADMIN/SUPERVISOR {request.user.username} EXCLUIU COMPLETAMENTE o perfil: {codigo}")

            return JsonResponse({
                'success': True,
                'message': f'✅ PERFIL EXCLUÍDO COM SUCESSO!\n\n' +
                          f'👤 Excluído por: {request.user.username} ({perfil.codigo_perfil})\n' +
                          f'📋 Código: {codigo}\n' +
                          f'📝 Nome: {nome}\n' +
                          f'📄 Descrição: {descricao}\n\n' +
                          f'🗑️ O perfil foi REMOVIDO PERMANENTEMENTE do banco de dados!\n' +
                          f'⚠️ Esta ação não pode ser desfeita.',
                'perfil': {
                    'codigo': codigo,
                    'nome': nome,
                    'excluido_por': request.user.username,
                    'excluido_em': timezone.now().isoformat()
                }
            })
        else:
            # DESATIVAR apenas (manter no banco mas inativo)
            tipo_perfil.ativo = False
            tipo_perfil.save()

            logger.info(f"✅ ADMIN/SUPERVISOR {request.user.username} DESATIVOU o perfil: {codigo}")

            return JsonResponse({
                'success': True,
                'message': f'✅ PERFIL DESATIVADO COM SUCESSO!\n\n' +
                          f'👤 Desativado por: {request.user.username} ({perfil.codigo_perfil})\n' +
                          f'📋 Código: {codigo}\n' +
                          f'📝 Nome: {nome}\n\n' +
                          f'💾 O perfil foi DESATIVADO mas permanece no banco de dados.\n' +
                          f'✅ Você pode reativá-lo a qualquer momento.',
                'perfil': {
                    'codigo': codigo,
                    'nome': nome,
                    'desativado_por': request.user.username,
                    'desativado_em': timezone.now().isoformat()
                }
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Erro ao remover perfil: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def api_reativar_perfil(request):
    """API para reativar perfil desativado - ADMIN e SUPERVISOR"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🔄 API reativar perfil chamada por: {request.user.username}")

        # Verificar se é admin ou supervisor
        perfil = request.user.perfil
        if not perfil.is_admin_ou_supervisor:
            logger.warning(f"❌ Acesso negado para {request.user.username} ({perfil.codigo_perfil})")
            return JsonResponse({'success': False, 'error': 'Apenas administradores e supervisores podem reativar perfis'})

        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip().upper()

        logger.info(f"📋 Código recebido para reativação: {codigo}")

        if not codigo:
            logger.warning(f"❌ Código não fornecido")
            return JsonResponse({'success': False, 'error': 'Código do perfil é obrigatório'})

        from .models import TipoPerfil
        from django.utils import timezone

        # Buscar tipo de perfil
        try:
            tipo_perfil = TipoPerfil.objects.get(codigo=codigo)

            if tipo_perfil.ativo:
                return JsonResponse({
                    'success': False,
                    'error': f'O perfil {codigo} já está ativo!'
                })

            # Reativar
            tipo_perfil.ativo = True
            tipo_perfil.save()

            logger.info(f"✅ ADMIN/SUPERVISOR {request.user.username} REATIVOU o perfil: {codigo}")

            return JsonResponse({
                'success': True,
                'message': f'✅ PERFIL REATIVADO COM SUCESSO!\n\n' +
                          f'👤 Reativado por: {request.user.username} ({perfil.codigo_perfil})\n' +
                          f'📋 Código: {codigo}\n' +
                          f'📝 Nome: {tipo_perfil.nome}\n\n' +
                          f'✅ O perfil está ativo novamente!',
                'perfil': {
                    'codigo': codigo,
                    'nome': tipo_perfil.nome,
                    'reativado_por': request.user.username,
                    'reativado_em': timezone.now().isoformat()
                }
            })

        except TipoPerfil.DoesNotExist:
            logger.warning(f"⚠️ Tentativa de reativar perfil inexistente: {codigo}")
            return JsonResponse({
                'success': False,
                'error': f'Perfil {codigo} não encontrado no banco de dados.'
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Erro ao reativar perfil: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def api_editar_perfil_usuario(request, usuario_id):
    """API para editar perfil de um usuário"""
    try:
        # Verificar se é admin ou supervisor
        perfil_solicitante = request.user.perfil
        if not (perfil_solicitante.is_admin or perfil_solicitante.is_supervisor):
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        # Buscar usuário
        try:
            usuario = User.objects.get(id=usuario_id)
            perfil_usuario = usuario.perfil
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Usuário não encontrado'})
        except PerfilUsuario.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Perfil do usuário não encontrado'})

        data = json.loads(request.body)
        novo_perfil = data.get('perfil', '').strip()
        novo_setor_id = data.get('setor_id')

        if not novo_perfil or not novo_setor_id:
            return JsonResponse({'success': False, 'error': 'Perfil e setor são obrigatórios'})

        # Verificar se o perfil existe
        perfis_validos = [choice[0] for choice in PerfilUsuario.PERFIL_CHOICES]
        if novo_perfil not in perfis_validos:
            return JsonResponse({'success': False, 'error': 'Perfil inválido'})

        # Verificar se o setor existe
        try:
            novo_setor = Setor.objects.get(id=novo_setor_id)
        except Setor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Setor não encontrado'})

        # Atualizar perfil
        perfil_usuario.perfil = novo_perfil
        perfil_usuario.setor = novo_setor
        perfil_usuario.save()

        return JsonResponse({
            'success': True,
            'message': f'Perfil do usuário {usuario.username} atualizado com sucesso'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def api_criar_empresa(request):
    """API para criar nova empresa via AJAX"""
    from .models import Empresa

    try:
        # Verificar permissões
        if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        # Obter dados do formulário
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', 'TERCEIRIZADA')
        cnpj = request.POST.get('cnpj', '').strip()
        contrato = request.POST.get('contrato', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        email = request.POST.get('email', '').strip()
        observacoes = request.POST.get('observacoes', '').strip()

        # Validação
        if not nome:
            return JsonResponse({'success': False, 'error': 'Nome da empresa é obrigatório'})

        # Verificar se já existe empresa com mesmo nome
        if Empresa.objects.filter(nome=nome).exists():
            return JsonResponse({'success': False, 'error': 'Já existe uma empresa com este nome'})

        # Criar empresa
        empresa = Empresa.objects.create(
            nome=nome,
            tipo=tipo,
            cnpj=cnpj,
            contrato=contrato,
            telefone=telefone,
            email=email,
            observacoes=observacoes,
            ativo=True
        )

        return JsonResponse({
            'success': True,
            'empresa': {
                'id': empresa.id,
                'nome': empresa.nome,
                'tipo': empresa.get_tipo_display(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["PUT", "POST"])
def api_editar_empresa(request, empresa_id):
    """API para editar empresa via AJAX"""
    from .models import Empresa

    try:
        # Verificar permissões
        if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        empresa = get_object_or_404(Empresa, id=empresa_id)

        # Obter dados do formulário
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', empresa.tipo)
        cnpj = request.POST.get('cnpj', '').strip()
        contrato = request.POST.get('contrato', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        email = request.POST.get('email', '').strip()
        observacoes = request.POST.get('observacoes', '').strip()

        # Validação
        if not nome:
            return JsonResponse({'success': False, 'error': 'Nome da empresa é obrigatório'})

        # Verificar se já existe outra empresa com mesmo nome
        if Empresa.objects.filter(nome=nome).exclude(id=empresa_id).exists():
            return JsonResponse({'success': False, 'error': 'Já existe outra empresa com este nome'})

        # Atualizar empresa
        empresa.nome = nome
        empresa.tipo = tipo
        empresa.cnpj = cnpj
        empresa.contrato = contrato
        empresa.telefone = telefone
        empresa.email = email
        empresa.observacoes = observacoes
        empresa.save()

        return JsonResponse({
            'success': True,
            'empresa': {
                'id': empresa.id,
                'nome': empresa.nome,
                'tipo': empresa.get_tipo_display(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["DELETE", "POST"])
def api_excluir_empresa(request, empresa_id):
    """API para excluir empresa via AJAX"""
    from .models import Empresa

    try:
        # Verificar permissões
        if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
            return JsonResponse({'success': False, 'error': 'Acesso negado'})

        empresa = get_object_or_404(Empresa, id=empresa_id)

        # Verificar se há usuários vinculados
        if empresa.perfilusuario_set.exists():
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir esta empresa pois existem usuários vinculados a ela'
            })

        # Verificar se há fornecedores vinculados
        if hasattr(empresa, 'fornecedores_atendidos') and empresa.fornecedores_atendidos.exists():
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir esta empresa pois existem fornecedores vinculados a ela'
            })

        nome = empresa.nome
        empresa.delete()

        return JsonResponse({
            'success': True,
            'message': f'Empresa "{nome}" excluída com sucesso'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
