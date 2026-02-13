from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncYear
from .models import TipoGas, MovimentacaoGas
from core.models import Cliente
import json
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal, InvalidOperation


@login_required
def dashboard_gases(request):
    """Dashboard avançado do módulo de gases com filtros"""
    # Verificar se é ADMIN
    if request.user.perfil.perfil != 'ADMIN':
        messages.error(request, 'Acesso negado. Apenas administradores podem acessar este módulo.')
        return redirect('dashboard')

    # Obter filtros da requisição
    periodo = request.GET.get('periodo', 'mes_atual')  # mes_atual, ano_atual, personalizado
    categoria_filter = request.GET.get('categoria_gas', '')
    cliente_id = request.GET.get('cliente', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    # Definir período base
    hoje = timezone.now().date()
    if periodo == 'mes_atual':
        inicio_periodo = hoje.replace(day=1)
        fim_periodo = hoje
        # Preencher campos de data para exibição
        if not data_inicio:
            data_inicio = inicio_periodo.strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = fim_periodo.strftime('%Y-%m-%d')
    elif periodo == 'ano_atual':
        inicio_periodo = hoje.replace(month=1, day=1)
        fim_periodo = hoje
        # Preencher campos de data para exibição
        if not data_inicio:
            data_inicio = inicio_periodo.strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = fim_periodo.strftime('%Y-%m-%d')
    elif periodo == 'personalizado' and data_inicio and data_fim:
        inicio_periodo = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        fim_periodo = datetime.strptime(data_fim, '%Y-%m-%d').date()
    else:
        # Padrão: últimos 30 dias
        inicio_periodo = hoje - timedelta(days=30)
        fim_periodo = hoje
        if not data_inicio:
            data_inicio = inicio_periodo.strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = fim_periodo.strftime('%Y-%m-%d')

    # Query base para movimentações no período
    movimentacoes_query = MovimentacaoGas.objects.filter(
        data_entrega__gte=inicio_periodo,
        data_entrega__lte=fim_periodo
    )

    # Aplicar filtros
    if categoria_filter:
        movimentacoes_query = movimentacoes_query.filter(categoria_gas=categoria_filter)
    if cliente_id:
        movimentacoes_query = movimentacoes_query.filter(cliente_id=cliente_id)

    # Estatísticas principais
    stats = movimentacoes_query.aggregate(
        total_valor=Sum('valor_total'),
        total_quantidade=Sum('quantidade'),
        total_movimentacoes=Count('id'),
        valor_medio=Avg('valor_total')
    )

    # Estatísticas gerais (sem filtro de período)
    total_tipos = TipoGas.objects.filter(ativo=True).count()
    total_clientes = Cliente.objects.filter(ativo=True).count()
    total_movimentacoes_geral = MovimentacaoGas.objects.count()

    # Top 5 gases por valor no período (agrupado por categoria)
    top_gases = movimentacoes_query.values('categoria_gas').annotate(
        total_valor=Sum('valor_total'),
        total_quantidade=Sum('quantidade'),
        total_movimentacoes=Count('id')
    ).order_by('-total_valor')[:5]

    # Converter códigos de categoria para nomes amigáveis
    top_gases_formatado = []
    for item in top_gases:
        categoria_nome = dict(MovimentacaoGas.CATEGORIA_GAS_CHOICES).get(item['categoria_gas'], item['categoria_gas'])
        top_gases_formatado.append({
            'categoria_gas': item['categoria_gas'],
            'categoria_nome': categoria_nome,
            'total_valor': item['total_valor'],
            'total_quantidade': item['total_quantidade'],
            'total_movimentacoes': item['total_movimentacoes']
        })

    # Top 5 clientes por valor no período
    top_clientes = movimentacoes_query.filter(cliente__isnull=False).values('cliente__nome').annotate(
        total_valor=Sum('valor_total'),
        total_quantidade=Sum('quantidade')
    ).order_by('-total_valor')[:5]

    # Movimentações por mês (últimos 12 meses para gráfico)
    doze_meses_atras = hoje - timedelta(days=365)
    movimentacoes_mensais = MovimentacaoGas.objects.filter(
        data_entrega__gte=doze_meses_atras
    ).annotate(
        mes=TruncMonth('data_entrega')
    ).values('mes').annotate(
        total_valor=Sum('valor_total'),
        total_quantidade=Sum('quantidade'),
        total_movimentacoes=Count('id')
    ).order_by('mes')

    # Evolução mensal por categoria (últimos 12 meses)
    evolucao_mensal_categoria = MovimentacaoGas.objects.filter(
        data_entrega__gte=doze_meses_atras
    ).annotate(
        mes=TruncMonth('data_entrega')
    ).values('mes', 'categoria_gas').annotate(
        quantidade=Sum('quantidade')
    ).order_by('mes', 'categoria_gas')

    # Últimas movimentações
    ultimas_movimentacoes = MovimentacaoGas.objects.select_related(
        'tipo_gas', 'cliente', 'criado_por'
    ).order_by('-criado_em')[:10]

    # Dados para os selects
    tipos_gas = TipoGas.objects.filter(ativo=True).order_by('nome_gas')
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')

    context = {
        # Estatísticas principais
        'total_tipos': total_tipos,
        'total_clientes': total_clientes,
        'total_movimentacoes_geral': total_movimentacoes_geral,
        'stats': stats,

        # Filtros aplicados
        'periodo': periodo,
        'categoria_filter': categoria_filter,
        'cliente_id': cliente_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'inicio_periodo': inicio_periodo,
        'fim_periodo': fim_periodo,

        # Rankings
        'top_gases': top_gases_formatado,
        'top_clientes': top_clientes,

        # Dados para gráficos (serializar datas corretamente)
        'movimentacoes_mensais': json.dumps([
            {
                'mes': item['mes'].isoformat() if item['mes'] else None,
                'total_valor': float(item['total_valor']) if item['total_valor'] else 0,
                'total_quantidade': float(item['total_quantidade']) if item['total_quantidade'] else 0,
                'total_movimentacoes': item['total_movimentacoes'] or 0
            }
            for item in movimentacoes_mensais
        ]),

        # Dados para gráfico de evolução mensal por categoria
        'evolucao_mensal_categoria': json.dumps([
            {
                'mes': item['mes'].isoformat() if item['mes'] else None,
                'categoria': dict(MovimentacaoGas.CATEGORIA_GAS_CHOICES).get(item['categoria_gas'], item['categoria_gas']),
                'quantidade': float(item['quantidade']) if item['quantidade'] else 0
            }
            for item in evolucao_mensal_categoria
        ]),

        # Listagens
        'ultimas_movimentacoes': ultimas_movimentacoes,

        # Dados para selects
        'categoria_choices': MovimentacaoGas.CATEGORIA_GAS_CHOICES,
        'clientes': clientes,
    }

    return render(request, 'gases/dashboard.html', context)


@login_required
def entrada_lote(request):
    """Entrada em lote de movimentações por NF"""
    # Verificar se é ADMIN
    if request.user.perfil.perfil != 'ADMIN':
        messages.error(request, 'Acesso negado. Apenas administradores podem acessar este módulo.')
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            # Dados comuns da NF
            data_entrega = request.POST.get('data_entrega')
            nf = request.POST.get('nf')
            fornecedor = request.POST.get('fornecedor')
            cliente_id = request.POST.get('cliente')

            # Validar dados obrigatórios
            if not all([data_entrega, nf, fornecedor, cliente_id]):
                messages.error(request, 'Todos os campos da NF são obrigatórios.')
                return redirect('gases:entrada_lote')

            # Buscar cliente
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente não encontrado.')
                return redirect('gases:entrada_lote')

            # Processar produtos
            produtos_salvos = 0
            produtos_com_erro = 0
            erros_detalhados = []

            # Extrair produtos do POST
            produtos = {}
            for key, value in request.POST.items():
                if key.startswith('produtos[') and '][' in key:
                    # Extrair índice e campo: produtos[1][tipo_gas_id] -> index=1, field=tipo_gas_id
                    parts = key.replace('produtos[', '').replace(']', '').split('[')
                    if len(parts) == 2:
                        index, field = parts
                        if index not in produtos:
                            produtos[index] = {}
                        produtos[index][field] = value

            # Salvar cada produto
            for index, produto_data in produtos.items():
                try:
                    # Validar dados do produto
                    tipo_gas_id = produto_data.get('tipo_gas_id')
                    quantidade = produto_data.get('quantidade')
                    unidade = produto_data.get('unidade')
                    categoria_gas = produto_data.get('categoria_gas')
                    valor_unitario = produto_data.get('valor_unitario')

                    if not all([tipo_gas_id, quantidade, unidade, categoria_gas, valor_unitario]):
                        erros_detalhados.append(f'Produto {index}: Campos obrigatórios não preenchidos')
                        produtos_com_erro += 1
                        continue

                    # Buscar tipo de gás
                    try:
                        tipo_gas = TipoGas.objects.get(id=tipo_gas_id)
                    except TipoGas.DoesNotExist:
                        erros_detalhados.append(f'Produto {index}: Tipo de gás não encontrado')
                        produtos_com_erro += 1
                        continue

                    # Converter valores
                    try:
                        quantidade = Decimal(quantidade)
                        valor_unitario = Decimal(valor_unitario)
                        valor_total = quantidade * valor_unitario
                    except (ValueError, InvalidOperation):
                        erros_detalhados.append(f'Produto {index}: Valores numéricos inválidos')
                        produtos_com_erro += 1
                        continue

                    # Verificar duplicata (NF + tipo_gas)
                    if MovimentacaoGas.objects.filter(nf=nf, tipo_gas=tipo_gas).exists():
                        erros_detalhados.append(f'Produto {index}: Já existe movimentação para NF {nf} + {tipo_gas.nome_gas}')
                        produtos_com_erro += 1
                        continue

                    # Criar movimentação
                    MovimentacaoGas.objects.create(
                        data_entrega=data_entrega,
                        nf=nf,
                        tipo_gas=tipo_gas,
                        quantidade=quantidade,
                        unidade=unidade,
                        categoria_gas=categoria_gas,
                        fornecedor=fornecedor,
                        cliente=cliente,
                        valor_unitario=valor_unitario,
                        valor_total=valor_total,
                        criado_por=request.user
                    )
                    produtos_salvos += 1

                except Exception as e:
                    erros_detalhados.append(f'Produto {index}: Erro inesperado - {str(e)}')
                    produtos_com_erro += 1

            # Mensagem de resultado
            if produtos_salvos > 0:
                messages.success(request, f'✅ Entrada em lote concluída! {produtos_salvos} produtos salvos.')
                if produtos_com_erro > 0:
                    messages.warning(request, f'⚠️ {produtos_com_erro} produtos com erro. Detalhes: {"; ".join(erros_detalhados[:5])}')
                return redirect('gases:movimentacoes')
            else:
                messages.error(request, f'❌ Nenhum produto foi salvo. Erros: {"; ".join(erros_detalhados[:5])}')

        except Exception as e:
            messages.error(request, f'Erro inesperado: {str(e)}')

    # GET - Exibir formulário
    tipos_gas = TipoGas.objects.filter(ativo=True).order_by('nome_gas')
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')

    context = {
        'tipos_gas': tipos_gas,
        'clientes': clientes,
        'fornecedor_choices': MovimentacaoGas.FORNECEDOR_CHOICES,
        'unidade_choices': MovimentacaoGas.UNIDADE_CHOICES,
        'categoria_choices': MovimentacaoGas.CATEGORIA_GAS_CHOICES,
    }

    return render(request, 'gases/entrada_lote.html', context)


@login_required
def listar_tipos_gas(request):
    """Listar tipos de gases com CRUD"""
    # Verificar se é ADMIN
    if request.user.perfil.perfil != 'ADMIN':
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Busca
    search = request.GET.get('search', '')
    tipos = TipoGas.objects.all()

    if search:
        tipos = tipos.filter(nome_gas__icontains=search)

    tipos = tipos.order_by('nome_gas')

    # Paginação
    paginator = Paginator(tipos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
    }

    return render(request, 'gases/tipos_gas.html', context)


@login_required
@require_http_methods(["POST"])
def criar_tipo_gas(request):
    """Criar novo tipo de gás via AJAX"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Acesso negado'})

    try:
        data = json.loads(request.body)
        nome_gas = data.get('nome_gas', '').strip()

        if not nome_gas:
            return JsonResponse({'success': False, 'error': 'Nome do gás é obrigatório'})

        # Verificar se já existe
        if TipoGas.objects.filter(nome_gas__iexact=nome_gas).exists():
            return JsonResponse({'success': False, 'error': 'Este tipo de gás já existe'})

        # Criar
        tipo_gas = TipoGas.objects.create(nome_gas=nome_gas)

        return JsonResponse({
            'success': True,
            'message': 'Tipo de gás criado com sucesso',
            'tipo_gas': {
                'id': tipo_gas.id,
                'nome_gas': tipo_gas.nome_gas,
                'ativo': tipo_gas.ativo
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def editar_tipo_gas(request, tipo_id):
    """Editar tipo de gás via AJAX"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Acesso negado'})

    try:
        tipo_gas = get_object_or_404(TipoGas, id=tipo_id)
        data = json.loads(request.body)
        nome_gas = data.get('nome_gas', '').strip()
        ativo = data.get('ativo', True)

        if not nome_gas:
            return JsonResponse({'success': False, 'error': 'Nome do gás é obrigatório'})

        # Verificar se já existe (exceto o atual)
        if TipoGas.objects.filter(nome_gas__iexact=nome_gas).exclude(id=tipo_id).exists():
            return JsonResponse({'success': False, 'error': 'Este tipo de gás já existe'})

        # Atualizar
        tipo_gas.nome_gas = nome_gas
        tipo_gas.ativo = ativo
        tipo_gas.save()

        return JsonResponse({
            'success': True,
            'message': 'Tipo de gás atualizado com sucesso',
            'tipo_gas': {
                'id': tipo_gas.id,
                'nome_gas': tipo_gas.nome_gas,
                'ativo': tipo_gas.ativo
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def deletar_tipo_gas(request, tipo_id):
    """Deletar tipo de gás via AJAX"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Acesso negado'})

    try:
        tipo_gas = get_object_or_404(TipoGas, id=tipo_id)

        # Verificar se tem movimentações
        if MovimentacaoGas.objects.filter(tipo_gas=tipo_gas).exists():
            return JsonResponse({
                'success': False,
                'error': 'Não é possível excluir. Este tipo de gás possui movimentações registradas.'
            })

        tipo_gas.delete()

        return JsonResponse({
            'success': True,
            'message': 'Tipo de gás excluído com sucesso'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== MOVIMENTAÇÕES DE GASES ====================

@login_required
def listar_movimentacoes(request):
    """Lista movimentações de gases com paginação e busca"""
    if request.user.perfil.perfil != 'ADMIN':
        return render(request, 'core/acesso_negado.html')

    search = request.GET.get('search', '')
    categoria_filter = request.GET.get('categoria_filter', '')
    movimentacoes = MovimentacaoGas.objects.select_related('tipo_gas', 'cliente', 'criado_por').all()

    if search:
        movimentacoes = movimentacoes.filter(
            Q(tipo_gas__nome_gas__icontains=search) |
            Q(nf__icontains=search) |
            Q(fornecedor__icontains=search)
        )

    if categoria_filter:
        movimentacoes = movimentacoes.filter(categoria_gas=categoria_filter)

    movimentacoes = movimentacoes.order_by('-criado_em')

    # Paginação
    paginator = Paginator(movimentacoes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Buscar dados para os formulários (não para filtros)
    tipos_gas = TipoGas.objects.filter(ativo=True).order_by('nome_gas')
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')

    # Choices de categoria para filtro
    categoria_choices = MovimentacaoGas.CATEGORIA_GAS_CHOICES

    # Dados para gráfico de quantidade por tipo (últimos 12 meses)
    from datetime import datetime, timedelta
    hoje = datetime.now().date()
    doze_meses_atras = hoje - timedelta(days=365)

    # Dados mensais para gráfico de linha (mantido para referência futura)
    dados_quantidade_por_tipo_mensal = MovimentacaoGas.objects.filter(
        data_entrega__gte=doze_meses_atras
    ).annotate(
        mes=TruncMonth('data_entrega')
    ).values('mes', 'categoria_gas').annotate(
        quantidade=Sum('quantidade')
    ).order_by('mes', 'categoria_gas')

    # Dados totais por categoria para gráfico de barras
    dados_total_por_categoria = MovimentacaoGas.objects.filter(
        data_entrega__gte=doze_meses_atras
    ).values('categoria_gas').annotate(
        quantidade_total=Sum('quantidade')
    ).order_by('-quantidade_total')

    # Dados para gráfico por unidade de medida (M³ e KG)
    dados_quantidade_por_unidade = MovimentacaoGas.objects.filter(
        data_entrega__gte=doze_meses_atras
    ).annotate(
        mes=TruncMonth('data_entrega')
    ).values('mes', 'unidade').annotate(
        quantidade=Sum('quantidade')
    ).order_by('mes', 'unidade')

    # Serializar dados para JavaScript - Totais por categoria (para gráfico de barras)
    dados_grafico_barras = []
    for item in dados_total_por_categoria:
        # Converter código da categoria para nome amigável
        nome_categoria = dict(MovimentacaoGas.CATEGORIA_GAS_CHOICES).get(item['categoria_gas'], item['categoria_gas'])
        dados_grafico_barras.append({
            'categoria': nome_categoria,
            'quantidade_total': float(item['quantidade_total']) if item['quantidade_total'] else 0
        })

    # Serializar dados para JavaScript - Evolução mensal por categoria (para gráfico de linhas)
    dados_grafico_mensal = []
    for item in dados_quantidade_por_tipo_mensal:
        # Converter código da categoria para nome amigável
        nome_categoria = dict(MovimentacaoGas.CATEGORIA_GAS_CHOICES).get(item['categoria_gas'], item['categoria_gas'])
        dados_grafico_mensal.append({
            'mes': item['mes'].isoformat() if item['mes'] else None,
            'categoria': nome_categoria,
            'quantidade': float(item['quantidade']) if item['quantidade'] else 0
        })

    # Serializar dados para JavaScript - Por unidade
    dados_grafico_unidade = []
    for item in dados_quantidade_por_unidade:
        # Converter código da unidade para nome amigável
        nome_unidade = dict(MovimentacaoGas.UNIDADE_CHOICES).get(item['unidade'], item['unidade'])
        dados_grafico_unidade.append({
            'mes': item['mes'].isoformat() if item['mes'] else None,
            'unidade': nome_unidade,
            'quantidade': float(item['quantidade']) if item['quantidade'] else 0
        })

    context = {
        'page_obj': page_obj,
        'search': search,
        'categoria_filter': categoria_filter,
        'tipos_gas': tipos_gas,  # Para formulários apenas
        'categoria_choices': categoria_choices,
        'clientes': clientes,
        'total_movimentacoes': movimentacoes.count(),
        'dados_total_por_categoria': json.dumps(dados_grafico_barras),
        'dados_quantidade_por_unidade': json.dumps(dados_grafico_unidade)
    }

    return render(request, 'gases/movimentacoes.html', context)


@login_required
@require_http_methods(["POST"])
def criar_movimentacao(request):
    """Criar nova movimentação de gás"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Acesso negado'})

    try:
        data = json.loads(request.body)

        # Validações
        if not data.get('data_entrega'):
            return JsonResponse({'success': False, 'error': 'Data de entrega é obrigatória'})

        if not data.get('nf'):
            return JsonResponse({'success': False, 'error': 'Nota fiscal é obrigatória'})

        if not data.get('tipo_gas_id'):
            return JsonResponse({'success': False, 'error': 'Tipo de gás é obrigatório'})

        if not data.get('quantidade'):
            return JsonResponse({'success': False, 'error': 'Quantidade é obrigatória'})

        # Buscar tipo de gás
        try:
            tipo_gas = TipoGas.objects.get(id=data['tipo_gas_id'], ativo=True)
        except TipoGas.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tipo de gás não encontrado'})

        # Buscar cliente se fornecido
        cliente = None
        if data.get('cliente_id'):
            try:
                cliente = Cliente.objects.get(id=data['cliente_id'], ativo=True)
            except Cliente.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})

        # Converter data
        try:
            data_entrega = datetime.strptime(data['data_entrega'], '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Data inválida'})

        # Criar movimentação
        movimentacao = MovimentacaoGas.objects.create(
            data_entrega=data_entrega,
            nf=data['nf'],
            tipo_gas=tipo_gas,
            quantidade=float(data['quantidade']),
            unidade=data.get('unidade', 'KG'),
            categoria_gas=data.get('categoria_gas', ''),
            fornecedor=data.get('fornecedor', 'WHITE_MARTINS'),
            cliente=cliente,
            valor_unitario=float(data.get('valor_unitario', 0)),
            criado_por=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Movimentação criada com sucesso!',
            'movimentacao': {
                'id': movimentacao.id,
                'data_entrega': movimentacao.data_entrega.strftime('%d/%m/%Y'),
                'nf': movimentacao.nf,
                'tipo_gas': movimentacao.tipo_gas.nome_gas,
                'quantidade': str(movimentacao.quantidade),
                'unidade': movimentacao.get_unidade_display(),
                'embalagem': movimentacao.get_embalagem_display(),
                'fornecedor': movimentacao.get_fornecedor_display(),
                'cliente': movimentacao.cliente.nome if movimentacao.cliente else '',
                'valor_unitario': str(movimentacao.valor_unitario),
                'valor_total': str(movimentacao.valor_total)
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def editar_movimentacao(request, movimentacao_id):
    """Editar movimentação existente"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Acesso negado'})

    try:
        movimentacao = get_object_or_404(MovimentacaoGas, id=movimentacao_id)
        data = json.loads(request.body)

        # Validações
        if not data.get('data_entrega'):
            return JsonResponse({'success': False, 'error': 'Data de entrega é obrigatória'})

        if not data.get('nf'):
            return JsonResponse({'success': False, 'error': 'Nota fiscal é obrigatória'})

        if not data.get('tipo_gas_id'):
            return JsonResponse({'success': False, 'error': 'Tipo de gás é obrigatório'})

        if not data.get('quantidade'):
            return JsonResponse({'success': False, 'error': 'Quantidade é obrigatória'})

        # Buscar tipo de gás
        try:
            tipo_gas = TipoGas.objects.get(id=data['tipo_gas_id'], ativo=True)
        except TipoGas.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tipo de gás não encontrado'})

        # Buscar cliente se fornecido
        cliente = None
        if data.get('cliente_id'):
            try:
                cliente = Cliente.objects.get(id=data['cliente_id'], ativo=True)
            except Cliente.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})

        # Converter data
        try:
            data_entrega = datetime.strptime(data['data_entrega'], '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Data inválida'})

        # Atualizar movimentação
        movimentacao.data_entrega = data_entrega
        movimentacao.nf = data['nf']
        movimentacao.tipo_gas = tipo_gas
        movimentacao.quantidade = float(data['quantidade'])
        movimentacao.unidade = data.get('unidade', movimentacao.unidade)
        movimentacao.categoria_gas = data.get('categoria_gas', movimentacao.categoria_gas)
        movimentacao.fornecedor = data.get('fornecedor', movimentacao.fornecedor)
        movimentacao.cliente = cliente
        movimentacao.valor_unitario = float(data.get('valor_unitario', 0))
        movimentacao.save()

        return JsonResponse({
            'success': True,
            'message': 'Movimentação atualizada com sucesso!',
            'movimentacao': {
                'id': movimentacao.id,
                'data_entrega': movimentacao.data_entrega.strftime('%d/%m/%Y'),
                'nf': movimentacao.nf,
                'tipo_gas': movimentacao.tipo_gas.nome_gas,
                'quantidade': str(movimentacao.quantidade),
                'unidade': movimentacao.get_unidade_display(),
                'embalagem': movimentacao.get_embalagem_display(),
                'fornecedor': movimentacao.get_fornecedor_display(),
                'cliente': movimentacao.cliente.nome if movimentacao.cliente else '',
                'valor_unitario': str(movimentacao.valor_unitario),
                'valor_total': str(movimentacao.valor_total)
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def deletar_movimentacao(request, movimentacao_id):
    """Deletar movimentação"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Acesso negado'})

    try:
        movimentacao = get_object_or_404(MovimentacaoGas, id=movimentacao_id)
        nf = movimentacao.nf
        movimentacao.delete()

        return JsonResponse({
            'success': True,
            'message': f'Movimentação NF {nf} excluída com sucesso!'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ==================== IMPORTAÇÃO DO EXCEL ====================

@login_required
@require_http_methods(["POST"])
def importar_excel(request):
    """Importar movimentações de gases a partir de arquivo Excel"""
    if request.user.perfil.perfil != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Acesso negado'})

    try:
        import pandas as pd
        from decimal import Decimal
        import io

        # Verificar se arquivo foi enviado
        if 'arquivo_excel' not in request.FILES:
            return JsonResponse({'success': False, 'message': 'Nenhum arquivo foi enviado'})

        arquivo = request.FILES['arquivo_excel']

        # Validar extensão
        if not arquivo.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({'success': False, 'message': 'Formato de arquivo inválido. Use .xlsx ou .xls'})

        # Validar tamanho (10MB)
        if arquivo.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'message': 'Arquivo muito grande. Máximo 10MB'})

        # Opções de importação
        sobrescrever_duplicatas = request.POST.get('sobrescrever_duplicatas') == 'on'
        validar_apenas = request.POST.get('validar_apenas') == 'on'

        # Ler arquivo Excel
        try:
            df = pd.read_excel(arquivo)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao ler arquivo Excel: {str(e)}'})

        # Validar colunas obrigatórias (ordem: Data, NF, Tipo de Gás, Cliente, Quantidade, Unidade, Embalagem, Valor Unitário, Valor Total, Fornecedor)
        colunas_obrigatorias = ['Data', 'NF', 'Tipo de Gás', 'Quantidade', 'Unidade', 'Embalagem', 'Valor Unitário', 'Fornecedor']
        colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]

        if colunas_faltando:
            return JsonResponse({
                'success': False,
                'message': f'Colunas obrigatórias faltando: {", ".join(colunas_faltando)}'
            })

        # Verificar colunas opcionais
        tem_cliente = 'Cliente' in df.columns
        tem_valor_total = 'Valor Total' in df.columns

        # Contadores
        importados = 0
        erros = 0
        detalhes_erros = []

        print(f"📊 Iniciando processamento de {len(df)} linhas")
        print(f"🔧 Colunas encontradas: {list(df.columns)}")
        print(f"⚙️ Validar apenas: {validar_apenas}")
        print(f"🔄 Sobrescrever duplicatas: {sobrescrever_duplicatas}")

        # Processar cada linha
        for index, row in df.iterrows():
            try:
                linha_num = index + 2  # +2 porque pandas começa em 0 e Excel tem cabeçalho
                print(f"🔍 Processando linha {linha_num}: {dict(row)}")

                # Validar dados obrigatórios
                if pd.isna(row['Data']) or pd.isna(row['NF']) or pd.isna(row['Tipo de Gás']):
                    detalhes_erros.append(f'Linha {linha_num}: Dados obrigatórios faltando (Data: {row["Data"]}, NF: {row["NF"]}, Tipo: {row["Tipo de Gás"]})')
                    erros += 1
                    continue

                # Converter data
                try:
                    if isinstance(row['Data'], str):
                        data_entrega = datetime.strptime(row['Data'], '%d/%m/%Y').date()
                    else:
                        data_entrega = row['Data'].date() if hasattr(row['Data'], 'date') else row['Data']
                except:
                    detalhes_erros.append(f'Linha {linha_num}: Data inválida')
                    erros += 1
                    continue

                # Buscar tipo de gás (removendo espaços extras)
                tipo_gas_nome = str(row['Tipo de Gás']).strip()
                try:
                    tipo_gas = TipoGas.objects.get(nome_gas__iexact=tipo_gas_nome)
                except TipoGas.DoesNotExist:
                    # Tentar busca flexível sem espaços extras
                    try:
                        tipo_gas = TipoGas.objects.get(nome_gas__icontains=tipo_gas_nome.rstrip())
                    except TipoGas.DoesNotExist:
                        detalhes_erros.append(f'Linha {linha_num}: Tipo de gás não encontrado: "{tipo_gas_nome}"')
                        erros += 1
                        continue

                # Buscar cliente (opcional)
                cliente = None
                if tem_cliente and not pd.isna(row.get('Cliente', '')):
                    try:
                        cliente = Cliente.objects.get(nome__icontains=row['Cliente'])
                    except Cliente.DoesNotExist:
                        detalhes_erros.append(f'Linha {linha_num}: Cliente não encontrado: {row["Cliente"]}')
                        # Não é erro crítico, continua sem cliente

                # Validar valores numéricos
                try:
                    def limpar_valor_monetario(valor_str):
                        """Limpa valores monetários brasileiros para formato decimal"""
                        valor_str = str(valor_str).replace('R$', '').replace(' ', '').strip()
                        # Se tem ponto e vírgula, é formato brasileiro (ex: 14.353,23)
                        if '.' in valor_str and ',' in valor_str:
                            valor_str = valor_str.replace('.', '').replace(',', '.')
                        # Se tem apenas vírgula, trocar por ponto (ex: 2,28)
                        elif ',' in valor_str and '.' not in valor_str:
                            valor_str = valor_str.replace(',', '.')
                        return valor_str

                    # Limpar e converter quantidade
                    quantidade_str = limpar_valor_monetario(row['Quantidade'])
                    quantidade = Decimal(quantidade_str)

                    # Limpar e converter valor unitário
                    valor_unitario_str = limpar_valor_monetario(row['Valor Unitário'])
                    valor_unitario = Decimal(valor_unitario_str)

                    # Processar valor total
                    valor_total_raw = row.get('Valor Total', '')
                    if tem_valor_total and not pd.isna(valor_total_raw) and str(valor_total_raw).strip() != '':
                        # Se valor total foi informado, limpar e usar ele
                        valor_total_str = limpar_valor_monetario(valor_total_raw)
                        if valor_total_str.strip() != '':
                            valor_total = Decimal(valor_total_str)
                        else:
                            # Se valor total está vazio, calcular automaticamente
                            valor_total = quantidade * valor_unitario
                    else:
                        # Se não foi informado, calcular automaticamente
                        valor_total = quantidade * valor_unitario

                except Exception as e:
                    detalhes_erros.append(f'Linha {linha_num}: Valores numéricos inválidos: {str(e)}')
                    erros += 1
                    continue

                # Validar choices
                unidade_choices = dict(MovimentacaoGas.UNIDADE_CHOICES)
                categoria_choices = dict(MovimentacaoGas.CATEGORIA_GAS_CHOICES)
                fornecedor_choices = dict(MovimentacaoGas.FORNECEDOR_CHOICES)

                # Mapear unidade com flexibilidade para M³
                unidade_excel = str(row['Unidade']).upper().strip()
                unidade_mapeada = None

                # Mapeamento flexível de unidades
                if unidade_excel in ['M³', 'M3', 'METRO CÚBICO', 'METRO CUBICO']:
                    unidade_mapeada = 'M3'
                elif unidade_excel in ['KG', 'QUILOGRAMA', 'QUILO']:
                    unidade_mapeada = 'KG'

                if not unidade_mapeada:
                    valores_aceitos = [v for k, v in unidade_choices.items()]
                    detalhes_erros.append(f'Linha {linha_num}: Unidade inválida: {unidade_excel}. Valores aceitos: {", ".join(valores_aceitos)} ou "M³", "KG"')
                    erros += 1
                    continue

                unidade = unidade_mapeada

                # Mapear categoria de gás com flexibilidade
                categoria_excel = str(row['Embalagem']).strip()
                categoria_mapeada = None

                # Mapeamento flexível de categorias
                categoria_upper = categoria_excel.upper()
                if categoria_upper in ['ACETILENO']:
                    categoria_mapeada = 'ACETILENO'
                elif categoria_upper in ['ARGONIO', 'ARGÔNIO']:
                    categoria_mapeada = 'ARGONIO'
                elif categoria_upper in ['DIOXIDO CARBONO', 'DIÓXIDO CARBONO', 'DIOXIDO_CARBONO']:
                    categoria_mapeada = 'DIOXIDO_CARBONO'
                elif categoria_upper in ['GLP']:
                    categoria_mapeada = 'GLP'
                elif categoria_upper in ['NITROGENIO', 'NITROGÊNIO']:
                    categoria_mapeada = 'NITROGENIO'
                elif categoria_upper in ['OXIGENIO MEDICINAL', 'OXIGÊNIO MEDICINAL']:
                    categoria_mapeada = 'OXIGENIO_MEDICINAL'
                elif categoria_upper in ['OXIGENIO', 'OXIGÊNIO']:
                    categoria_mapeada = 'OXIGENIO'
                else:
                    # Buscar por valor exato (chave ou valor)
                    for chave, valor in categoria_choices.items():
                        if categoria_excel == valor or categoria_upper == chave.upper():
                            categoria_mapeada = chave
                            break

                if not categoria_mapeada:
                    valores_aceitos = [v for k, v in categoria_choices.items()]
                    detalhes_erros.append(f'Linha {linha_num}: Categoria inválida: {categoria_excel}. Valores aceitos: {", ".join(valores_aceitos)}')
                    erros += 1
                    continue

                categoria_gas = categoria_mapeada

                # Mapear fornecedor
                fornecedor_excel = str(row['Fornecedor']).strip()
                fornecedor_mapeado = None

                # Mapeamento flexível de fornecedores
                if fornecedor_excel.upper() in ['WHITE MARTINS', 'WHITE_MARTINS']:
                    fornecedor_mapeado = 'WHITE_MARTINS'
                elif fornecedor_excel.upper() in ['ULTRA GAS', 'ULTRA_GAS']:
                    fornecedor_mapeado = 'ULTRA_GAS'
                elif fornecedor_excel.upper() in ['ULTRAGAZ/BAHIANA', 'ULTRAGAZ BAHIANA', 'ULTRAGAZ']:
                    fornecedor_mapeado = 'ULTRAGAZ_BAHIANA'
                else:
                    # Buscar por valor exato
                    for chave, valor in fornecedor_choices.items():
                        if fornecedor_excel == valor or fornecedor_excel.upper() == chave.upper():
                            fornecedor_mapeado = chave
                            break

                if not fornecedor_mapeado:
                    valores_aceitos = [v for k, v in fornecedor_choices.items()]
                    detalhes_erros.append(f'Linha {linha_num}: Fornecedor inválido: {fornecedor_excel}. Valores aceitos: {", ".join(valores_aceitos)} ou "White Martins", "Ultra Gas", "Ultragaz/Bahiana"')
                    erros += 1
                    continue

                fornecedor = fornecedor_mapeado

                # Se é apenas validação, não salvar
                if validar_apenas:
                    importados += 1
                    continue

                # Verificar duplicatas (NF + Tipo de Gás)
                nf = str(row['NF']).strip()
                print(f"🔍 Linha {linha_num}: Verificando NF {nf} + {tipo_gas.nome_gas}")

                movimentacao_existente = MovimentacaoGas.objects.filter(
                    nf=nf,
                    tipo_gas=tipo_gas
                ).first()

                if movimentacao_existente:
                    print(f"⚠️ Linha {linha_num}: Encontrada duplicata - NF {nf} + {tipo_gas.nome_gas}")
                    if sobrescrever_duplicatas:
                        # Atualizar existente
                        movimentacao_existente.data_entrega = data_entrega
                        movimentacao_existente.quantidade = quantidade
                        movimentacao_existente.unidade = unidade
                        movimentacao_existente.categoria_gas = categoria_gas
                        movimentacao_existente.fornecedor = fornecedor
                        movimentacao_existente.cliente = cliente
                        movimentacao_existente.valor_unitario = valor_unitario
                        movimentacao_existente.valor_total = valor_total
                        movimentacao_existente.save()
                        importados += 1
                        print(f"✅ Atualizado: NF {nf} - {tipo_gas.nome_gas}")
                    else:
                        # Pular duplicata sem contar como erro
                        print(f"⏭️ Pulado: NF {nf} - {tipo_gas.nome_gas} (duplicata)")
                        continue
                else:
                    # Criar nova movimentação
                    MovimentacaoGas.objects.create(
                        data_entrega=data_entrega,
                        nf=nf,
                        tipo_gas=tipo_gas,
                        quantidade=quantidade,
                        unidade=unidade,
                        categoria_gas=categoria_gas,
                        fornecedor=fornecedor,
                        cliente=cliente,
                        valor_unitario=valor_unitario,
                        valor_total=valor_total,
                        criado_por=request.user
                    )
                    importados += 1
                    print(f"✅ Criado: NF {nf} - {tipo_gas.nome_gas}")

            except Exception as e:
                detalhes_erros.append(f'Linha {linha_num}: Erro inesperado: {str(e)}')
                erros += 1
                continue

        # Resultado
        if validar_apenas:
            detalhes_validacao = f'Registros válidos: {importados}, Erros: {erros}'
            if detalhes_erros:
                detalhes_validacao += f'\n\nPrimeiros erros encontrados:\n' + '\n'.join(detalhes_erros[:5])
            return JsonResponse({
                'success': True,
                'message': 'Validação concluída',
                'importados': importados,
                'erros': erros,
                'detalhes': detalhes_validacao
            })
        else:
            detalhes_importacao = f'✅ Registros importados: {importados}\n❌ Registros com erro: {erros}'
            if detalhes_erros:
                detalhes_importacao += f'\n\n📋 Detalhes dos erros:\n' + '\n'.join(detalhes_erros[:10])
                if len(detalhes_erros) > 10:
                    detalhes_importacao += f'\n... e mais {len(detalhes_erros) - 10} erros'
            else:
                detalhes_importacao += '\n\n🎉 Nenhum erro encontrado!'

            return JsonResponse({
                'success': True,
                'message': 'Importação concluída',
                'importados': importados,
                'erros': erros,
                'detalhes': detalhes_importacao
            })

    except ImportError:
        return JsonResponse({
            'success': False,
            'message': 'Biblioteca pandas não instalada. Execute: pip install pandas openpyxl'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro inesperado: {str(e)}'})
