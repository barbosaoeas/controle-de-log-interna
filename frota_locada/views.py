from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    VeiculoLocado, Fornecedor, TipoVeiculo, MarcaVeiculo, ManutencaoVeiculo,
    TipoManutencao, HistoricoHorimetro, Maquina, ChamadoManutencao, AtendimentoChamado
)
from core.models import Empresa
from .forms import (
    VeiculoLocadoForm, FornecedorForm, TipoVeiculoForm, MarcaVeiculoForm,
    ManutencaoVeiculoForm, HistoricoHorimetroForm, MaquinaForm, ChamadoManutencaoForm,
    FinalizarChamadoForm
)


@login_required
def dashboard_manutencao(request):
    """Dashboard de Chamados de Manutenção de PTAs"""
    from datetime import timedelta, datetime
    from django.db.models import Avg, Sum, F, ExpressionWrapper, DurationField, Q

    # Verificar permissões
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')

    perfil = request.user.perfil

    # ========================================================================
    # FILTRO POR EMPRESA DO USUÁRIO
    # ========================================================================
    # Usuários terceirizados só veem dados da sua empresa
    # Admins/Supervisores veem todas as empresas
    perfis_terceiros = [
        'TERCEIRO_MANUTENCAO_PTA',
        'TERCEIRO_MANUTENCAO_EMPILHADEIRA',
        'TERCEIRO_MANUTENCAO_GUINDASTE',
        'TERCEIRO_MANUTENCAO_SOLDA',
        'TERCEIRO_MANUTENCAO_GERAL'
    ]

    if perfil.codigo_perfil in perfis_terceiros:
        empresa_filtro = perfil.empresa
    else:
        # Admin pode ver todas as empresas, mas vamos filtrar por empresa se houver parâmetro
        empresa_id = request.GET.get('empresa')
        if empresa_id:
            try:
                empresa_filtro = Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                empresa_filtro = None
        else:
            empresa_filtro = None

    # ========================================================================
    # FILTRO POR MÊS/ANO E STATUS
    # ========================================================================
    hoje = timezone.now()
    mes_selecionado = request.GET.get('mes', hoje.month)
    ano_selecionado = request.GET.get('ano', hoje.year)
    status_filtro = request.GET.get('status', 'ABERTOS')  # Padrão: mostrar apenas abertos

    try:
        mes_selecionado = int(mes_selecionado)
        ano_selecionado = int(ano_selecionado)
    except (ValueError, TypeError):
        mes_selecionado = hoje.month
        ano_selecionado = hoje.year

    # Calcular primeiro e último dia do mês
    from calendar import monthrange
    primeiro_dia = datetime(ano_selecionado, mes_selecionado, 1)
    ultimo_dia_numero = monthrange(ano_selecionado, mes_selecionado)[1]
    ultimo_dia = datetime(ano_selecionado, mes_selecionado, ultimo_dia_numero, 23, 59, 59)

    # Tornar timezone-aware
    primeiro_dia = timezone.make_aware(primeiro_dia)
    ultimo_dia = timezone.make_aware(ultimo_dia)

    # Filtro base para o mês selecionado
    filtro_mes = Q(data_abertura__gte=primeiro_dia, data_abertura__lte=ultimo_dia)

    # Filtro base para empresa (se aplicável)
    filtro_empresa = Q()
    if empresa_filtro:
        filtro_empresa = Q(maquina__empresa=empresa_filtro)

    # Estatísticas de Chamados (FILTRADAS POR MÊS E EMPRESA)
    total_chamados = ChamadoManutencao.objects.filter(filtro_mes, filtro_empresa).count()
    chamados_aguardando = ChamadoManutencao.objects.filter(filtro_mes, filtro_empresa, status='AGUARDANDO').count()
    chamados_em_atendimento = ChamadoManutencao.objects.filter(filtro_mes, filtro_empresa, status='EM_ATENDIMENTO').count()
    chamados_concluidos = ChamadoManutencao.objects.filter(filtro_mes, filtro_empresa, status='CONCLUIDO').count()
    chamados_criticos = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa,
        prioridade='CRITICA',
        status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
    ).count()

    # ========================================================================
    # CÁLCULO DE MÉTRICAS DE MANUTENÇÃO (FILTRADAS POR MÊS)
    # ========================================================================

    # Total de horas de atendimento (atendimentos finalizados no mês e da empresa)
    atendimentos_finalizados = AtendimentoChamado.objects.filter(
        status='FINALIZADO',
        data_finalizacao__isnull=False,
        data_finalizacao__gte=primeiro_dia,
        data_finalizacao__lte=ultimo_dia
    )
    if empresa_filtro:
        atendimentos_finalizados = atendimentos_finalizados.filter(chamado__maquina__empresa=empresa_filtro)

    total_horas_atendimento = timedelta(0)
    for atendimento in atendimentos_finalizados:
        if atendimento.tempo_atendimento:
            total_horas_atendimento += atendimento.tempo_atendimento

    # Converter para horas decimais
    total_horas_decimal = total_horas_atendimento.total_seconds() / 3600 if total_horas_atendimento else 0

    # Chamados concluídos com datas válidas (NO MÊS E DA EMPRESA)
    chamados_concluidos_validos = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa,
        status='CONCLUIDO',
        data_inicio_atendimento__isnull=False,
        data_fim_atendimento__isnull=False
    )

    # MTTR - Mean Time To Repair (Tempo Médio de Reparo)
    # Tempo médio entre início e fim do atendimento
    mttr_seconds = 0
    mttr_count = 0
    for chamado in chamados_concluidos_validos:
        tempo_reparo = chamado.data_fim_atendimento - chamado.data_inicio_atendimento
        mttr_seconds += tempo_reparo.total_seconds()
        mttr_count += 1

    mttr_horas = (mttr_seconds / 3600 / mttr_count) if mttr_count > 0 else 0

    # MTBF - Mean Time Between Failures (Tempo Médio Entre Falhas)
    # Para cada máquina, calcular tempo entre chamados
    # Filtrar máquinas por empresa
    if empresa_filtro:
        maquinas_ativas = Maquina.objects.filter(ativo=True, empresa=empresa_filtro)
    else:
        maquinas_ativas = Maquina.objects.filter(ativo=True)

    mtbf_total_seconds = 0
    mtbf_count = 0

    for maquina in maquinas_ativas:
        chamados_maquina = ChamadoManutencao.objects.filter(
            maquina=maquina,
            status='CONCLUIDO'
        ).order_by('data_abertura')

        if chamados_maquina.count() >= 2:
            # Calcular tempo entre chamados consecutivos
            chamados_list = list(chamados_maquina)
            for i in range(1, len(chamados_list)):
                tempo_entre_falhas = chamados_list[i].data_abertura - chamados_list[i-1].data_fim_atendimento
                if tempo_entre_falhas.total_seconds() > 0:  # Ignorar valores negativos
                    mtbf_total_seconds += tempo_entre_falhas.total_seconds()
                    mtbf_count += 1

    mtbf_horas = (mtbf_total_seconds / 3600 / mtbf_count) if mtbf_count > 0 else 0

    # DISPONIBILIDADE MÉDIA
    # Disponibilidade = (MTBF / (MTBF + MTTR)) * 100
    if mtbf_horas > 0 and mttr_horas > 0:
        disponibilidade_media = (mtbf_horas / (mtbf_horas + mttr_horas)) * 100
    else:
        disponibilidade_media = 0

    # ========================================================================
    # MÉTRICAS POR EQUIPAMENTO (FILTRADAS POR MÊS)
    # ========================================================================
    metricas_por_equipamento = []

    for maquina in maquinas_ativas:
        chamados_maquina = ChamadoManutencao.objects.filter(
            filtro_mes,
            maquina=maquina,
            status='CONCLUIDO',
            data_inicio_atendimento__isnull=False,
            data_fim_atendimento__isnull=False
        ).order_by('data_abertura')

        total_chamados_maquina = chamados_maquina.count()

        if total_chamados_maquina > 0:
            # MTTR da máquina
            mttr_maquina_seconds = 0
            for chamado in chamados_maquina:
                tempo_reparo = chamado.data_fim_atendimento - chamado.data_inicio_atendimento
                mttr_maquina_seconds += tempo_reparo.total_seconds()
            mttr_maquina = (mttr_maquina_seconds / 3600 / total_chamados_maquina)

            # MTBF da máquina
            mtbf_maquina_seconds = 0
            mtbf_maquina_count = 0
            chamados_list = list(chamados_maquina)

            if len(chamados_list) >= 2:
                for i in range(1, len(chamados_list)):
                    tempo_entre_falhas = chamados_list[i].data_abertura - chamados_list[i-1].data_fim_atendimento
                    if tempo_entre_falhas.total_seconds() > 0:
                        mtbf_maquina_seconds += tempo_entre_falhas.total_seconds()
                        mtbf_maquina_count += 1

            mtbf_maquina = (mtbf_maquina_seconds / 3600 / mtbf_maquina_count) if mtbf_maquina_count > 0 else 0

            # Disponibilidade da máquina
            if mtbf_maquina > 0 and mttr_maquina > 0:
                disponibilidade_maquina = (mtbf_maquina / (mtbf_maquina + mttr_maquina)) * 100
            else:
                disponibilidade_maquina = 0

            # Total de horas de manutenção
            total_horas_manutencao = mttr_maquina_seconds / 3600

            metricas_por_equipamento.append({
                'maquina': maquina,
                'total_chamados': total_chamados_maquina,
                'mttr': mttr_maquina,
                'mtbf': mtbf_maquina,
                'disponibilidade': disponibilidade_maquina,
                'total_horas_manutencao': total_horas_manutencao,
            })

    # Ordenar por disponibilidade (menor primeiro - equipamentos mais problemáticos)
    metricas_por_equipamento.sort(key=lambda x: x['disponibilidade'])

    # ========================================================================
    # RELATÓRIO DE MÁQUINAS PARADAS (PARA RECLAMAÇÃO COM FORNECEDOR)
    # ========================================================================
    relatorio_maquinas_paradas = []

    for maquina in maquinas_ativas:
        chamados_maquina_mes = ChamadoManutencao.objects.filter(
            filtro_mes,
            maquina=maquina,
            status='CONCLUIDO',
            data_inicio_atendimento__isnull=False,
            data_fim_atendimento__isnull=False
        )

        total_chamados_mes = chamados_maquina_mes.count()

        if total_chamados_mes > 0:
            # Calcular total de horas paradas e verificar mau uso
            total_horas_paradas = timedelta(0)
            chamados_mau_uso = 0

            for chamado in chamados_maquina_mes:
                tempo_parado = chamado.data_fim_atendimento - chamado.data_inicio_atendimento
                total_horas_paradas += tempo_parado

                # Verificar se algum atendimento deste chamado foi marcado como mau uso
                tem_mau_uso = chamado.atendimentos.filter(mau_uso=True).exists()
                if tem_mau_uso:
                    chamados_mau_uso += 1

            # Converter para horas decimais
            horas_paradas_decimal = total_horas_paradas.total_seconds() / 3600

            # Calcular percentual de indisponibilidade no mês
            # Total de horas no mês
            total_horas_mes = (ultimo_dia - primeiro_dia).total_seconds() / 3600
            percentual_indisponibilidade = (horas_paradas_decimal / total_horas_mes) * 100

            relatorio_maquinas_paradas.append({
                'maquina': maquina,
                'total_chamados': total_chamados_mes,
                'chamados_mau_uso': chamados_mau_uso,
                'total_horas_paradas': horas_paradas_decimal,
                'percentual_indisponibilidade': percentual_indisponibilidade,
                'chamados': chamados_maquina_mes,
            })

    # Ordenar por horas paradas (maior primeiro)
    relatorio_maquinas_paradas.sort(key=lambda x: x['total_horas_paradas'], reverse=True)

    # Calcular total de horas paradas
    total_horas_paradas_geral = sum(item['total_horas_paradas'] for item in relatorio_maquinas_paradas)

    # Chamados recentes (últimos 10 do mês e da empresa) - COM FILTRO DE STATUS
    chamados_recentes_query = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa
    )

    # Aplicar filtro de status
    if status_filtro == 'ABERTOS':
        # Mostrar apenas AGUARDANDO e EM_ATENDIMENTO
        chamados_recentes_query = chamados_recentes_query.filter(status__in=['AGUARDANDO', 'EM_ATENDIMENTO'])
    elif status_filtro == 'CONCLUIDOS':
        # Mostrar apenas CONCLUIDOS
        chamados_recentes_query = chamados_recentes_query.filter(status='CONCLUIDO')
    # Se status_filtro == 'TODOS', não aplica filtro adicional

    chamados_recentes = chamados_recentes_query.select_related(
        'maquina', 'solicitante', 'mecanico'
    ).order_by('-data_abertura')[:10]

    # Chamados por prioridade (DO MÊS E DA EMPRESA)
    chamados_por_prioridade = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa,
        status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
    ).values('prioridade').annotate(total=Count('id')).order_by('-total')

    # Chamados por tipo de problema (DO MÊS E DA EMPRESA) - CORRIGIDO
    chamados_por_tipo = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa
    ).values('tipo_problema').annotate(total=Count('id')).order_by('-total')[:5]

    # Máquinas com mais chamados (DO MÊS E DA EMPRESA)
    maquinas_com_mais_chamados = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa
    ).values(
        'maquina__nome', 'maquina__codigo'
    ).annotate(total=Count('id')).order_by('-total')[:5]

    # Atendimentos em andamento (DA EMPRESA)
    atendimentos_andamento_query = AtendimentoChamado.objects.filter(
        status='EM_ANDAMENTO'
    )
    if empresa_filtro:
        atendimentos_andamento_query = atendimentos_andamento_query.filter(chamado__maquina__empresa=empresa_filtro)

    atendimentos_andamento = atendimentos_andamento_query.select_related(
        'chamado', 'chamado__maquina', 'mecanico'
    ).order_by('-data_inicio')[:10]

    # Lista de meses e anos para o filtro
    anos_disponiveis = range(2024, hoje.year + 2)
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    # Lista de empresas (apenas para admins/supervisores)
    empresas_disponiveis = []
    mostrar_filtro_empresa = False
    if perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR']:
        empresas_disponiveis = Empresa.objects.filter(ativo=True).order_by('nome')
        mostrar_filtro_empresa = True

    # ========================================================================
    # NOVAS MÉTRICAS: TEMPO DE ESPERA E INDISPONIBILIDADE
    # ========================================================================

    # Tempo Médio de Espera (chamados concluídos no mês)
    tempo_espera_total_seconds = 0
    tempo_espera_count = 0

    for chamado in chamados_concluidos_validos:
        if chamado.tempo_aguardando:
            tempo_espera_total_seconds += (chamado.tempo_aguardando * 3600)  # converter horas para segundos
            tempo_espera_count += 1

    tempo_medio_espera_horas = (tempo_espera_total_seconds / 3600 / tempo_espera_count) if tempo_espera_count > 0 else 0

    # Tempo Médio de Indisponibilidade Total (Espera + Reparo)
    tempo_indisponibilidade_total_seconds = 0
    tempo_indisponibilidade_count = 0

    for chamado in chamados_concluidos_validos:
        if chamado.tempo_total_indisponibilidade:
            tempo_indisponibilidade_total_seconds += (chamado.tempo_total_indisponibilidade * 3600)
            tempo_indisponibilidade_count += 1

    tempo_medio_indisponibilidade_horas = (tempo_indisponibilidade_total_seconds / 3600 / tempo_indisponibilidade_count) if tempo_indisponibilidade_count > 0 else 0

    # Tempo Médio de Espera por Prioridade
    tempo_espera_por_prioridade = []
    prioridades = ['BAIXA', 'MEDIA', 'ALTA', 'CRITICA']

    for prioridade in prioridades:
        chamados_prioridade = ChamadoManutencao.objects.filter(
            filtro_mes,
            filtro_empresa,
            status='CONCLUIDO',
            prioridade=prioridade,
            data_inicio_atendimento__isnull=False
        )

        tempo_espera_prioridade_seconds = 0
        count_prioridade = 0

        for chamado in chamados_prioridade:
            if chamado.tempo_aguardando:
                tempo_espera_prioridade_seconds += (chamado.tempo_aguardando * 3600)
                count_prioridade += 1

        tempo_medio_prioridade = (tempo_espera_prioridade_seconds / 3600 / count_prioridade) if count_prioridade > 0 else 0

        tempo_espera_por_prioridade.append({
            'prioridade': prioridade,
            'prioridade_display': dict(ChamadoManutencao.PRIORIDADE_CHOICES).get(prioridade, prioridade),
            'tempo_medio': tempo_medio_prioridade,
            'total_chamados': count_prioridade
        })

    # MTTR por Tipo de Problema
    mttr_por_tipo_problema = []
    tipos_problema_unicos = ChamadoManutencao.objects.filter(
        filtro_mes,
        filtro_empresa,
        status='CONCLUIDO'
    ).values_list('tipo_problema', flat=True).distinct()

    for tipo_problema in tipos_problema_unicos:
        if not tipo_problema:
            continue

        chamados_tipo = ChamadoManutencao.objects.filter(
            filtro_mes,
            filtro_empresa,
            status='CONCLUIDO',
            tipo_problema=tipo_problema,
            data_inicio_atendimento__isnull=False,
            data_fim_atendimento__isnull=False
        )

        mttr_tipo_seconds = 0
        count_tipo = 0

        for chamado in chamados_tipo:
            tempo_reparo = chamado.data_fim_atendimento - chamado.data_inicio_atendimento
            mttr_tipo_seconds += tempo_reparo.total_seconds()
            count_tipo += 1

        mttr_tipo_horas = (mttr_tipo_seconds / 3600 / count_tipo) if count_tipo > 0 else 0

        mttr_por_tipo_problema.append({
            'tipo_problema': tipo_problema,
            'mttr': mttr_tipo_horas,
            'total_chamados': count_tipo
        })

    # Ordenar por MTTR (maior primeiro - problemas mais demorados)
    mttr_por_tipo_problema.sort(key=lambda x: x['mttr'], reverse=True)

    context = {
        'total_chamados': total_chamados,
        'chamados_aguardando': chamados_aguardando,
        'chamados_em_atendimento': chamados_em_atendimento,
        'chamados_concluidos': chamados_concluidos,
        'chamados_criticos': chamados_criticos,
        'total_horas_atendimento': total_horas_decimal,
        'mttr': mttr_horas,
        'mtbf': mtbf_horas,
        'disponibilidade_media': disponibilidade_media,
        'metricas_por_equipamento': metricas_por_equipamento,
        'relatorio_maquinas_paradas': relatorio_maquinas_paradas,
        'total_horas_paradas_geral': total_horas_paradas_geral,
        'chamados_recentes': chamados_recentes,
        'chamados_por_prioridade': chamados_por_prioridade,
        'chamados_por_tipo': chamados_por_tipo,
        'maquinas_com_mais_chamados': maquinas_com_mais_chamados,
        'atendimentos_andamento': atendimentos_andamento,
        'mes_selecionado': mes_selecionado,
        'ano_selecionado': ano_selecionado,
        'status_filtro': status_filtro,  # Novo filtro de status
        'meses': meses,
        'anos_disponiveis': anos_disponiveis,
        'empresa_filtro': empresa_filtro,
        'empresas_disponiveis': empresas_disponiveis,
        'mostrar_filtro_empresa': mostrar_filtro_empresa,
        'titulo': 'Dashboard - Manutenção de PTAs',
        # Novas métricas
        'tempo_medio_espera': tempo_medio_espera_horas,
        'tempo_medio_indisponibilidade': tempo_medio_indisponibilidade_horas,
        'tempo_espera_por_prioridade': tempo_espera_por_prioridade,
        'mttr_por_tipo_problema': mttr_por_tipo_problema,
    }

    return render(request, 'frota_locada/dashboard_manutencao.html', context)


@login_required
def dashboard(request):
    """Dashboard principal da frota locada (Veículos)"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado. Apenas administradores e supervisores podem acessar esta área.')
        return redirect('dashboard')

    # Estatísticas gerais
    total_veiculos = VeiculoLocado.objects.count()
    veiculos_ativos = VeiculoLocado.objects.filter(status='ATIVO').count()
    veiculos_manutencao = VeiculoLocado.objects.filter(status='MANUTENCAO').count()

    # Custos mensais
    hoje = timezone.now().date()
    primeiro_dia_mes = hoje.replace(day=1)
    custo_mensal = VeiculoLocado.objects.filter(
        status__in=['ATIVO', 'MANUTENCAO'],
        data_inicio_locacao__lte=hoje
    ).aggregate(total=Sum('valor_mensal'))['total'] or 0

    # Manutenções pendentes
    manutencoes_agendadas = ManutencaoVeiculo.objects.filter(status='AGENDADA').count()
    manutencoes_andamento = ManutencaoVeiculo.objects.filter(status='EM_ANDAMENTO').count()

    # Veículos por fornecedor
    veiculos_por_fornecedor = VeiculoLocado.objects.values(
        'fornecedor__nome'
    ).annotate(
        total=Count('id'),
        ativos=Count('id', filter=Q(status='ATIVO'))
    ).order_by('-total')[:5]

    # Próximas manutenções (próximos 7 dias)
    proxima_semana = hoje + timedelta(days=7)
    proximas_manutencoes = ManutencaoVeiculo.objects.filter(
        status='AGENDADA',
        data_agendamento__date__range=[hoje, proxima_semana]
    ).select_related('veiculo', 'tipo_manutencao').order_by('data_agendamento')[:5]

    context = {
        'total_veiculos': total_veiculos,
        'veiculos_ativos': veiculos_ativos,
        'veiculos_manutencao': veiculos_manutencao,
        'custo_mensal': custo_mensal,
        'manutencoes_agendadas': manutencoes_agendadas,
        'manutencoes_andamento': manutencoes_andamento,
        'veiculos_por_fornecedor': veiculos_por_fornecedor,
        'proximas_manutencoes': proximas_manutencoes,
    }

    return render(request, 'frota_locada/dashboard.html', context)


@login_required
def listar_veiculos(request):
    """Lista todos os veículos locados"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    fornecedor_filter = request.GET.get('fornecedor', '')
    tipo_filter = request.GET.get('tipo', '')

    # Query base
    veiculos = VeiculoLocado.objects.select_related(
        'fornecedor', 'tipo_veiculo', 'cadastrado_por'
    ).all()

    # Aplicar filtros
    if search:
        veiculos = veiculos.filter(
            Q(placa__icontains=search) |
            Q(modelo__icontains=search) |
            Q(marca__icontains=search) |
            Q(fornecedor__nome__icontains=search)
        )

    if status_filter:
        veiculos = veiculos.filter(status=status_filter)

    if fornecedor_filter:
        veiculos = veiculos.filter(fornecedor_id=fornecedor_filter)

    if tipo_filter:
        veiculos = veiculos.filter(tipo_veiculo_id=tipo_filter)

    # Paginação
    paginator = Paginator(veiculos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para filtros
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('nome')
    tipos_veiculo = TipoVeiculo.objects.filter(ativo=True).order_by('nome')
    status_choices = VeiculoLocado.STATUS_CHOICES

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'fornecedor_filter': fornecedor_filter,
        'tipo_filter': tipo_filter,
        'fornecedores': fornecedores,
        'tipos_veiculo': tipos_veiculo,
        'status_choices': status_choices,
    }

    return render(request, 'frota_locada/listar_veiculos.html', context)


@login_required
def cadastrar_veiculo(request):
    """Cadastra um novo veículo locado"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = VeiculoLocadoForm(request.POST)
        if form.is_valid():
            veiculo = form.save(commit=False)
            veiculo.cadastrado_por = request.user
            veiculo.save()

            # Criar histórico inicial de horímetro
            HistoricoHorimetro.objects.create(
                veiculo=veiculo,
                horimetro_anterior=0,
                horimetro_atual=veiculo.horimetro_inicial,
                observacoes=f'Horímetro inicial do veículo {veiculo.placa}',
                registrado_por=request.user
            )

            messages.success(request, f'Veículo {veiculo.placa} cadastrado com sucesso!')
            return redirect('frota_locada:listar_veiculos')
    else:
        form = VeiculoLocadoForm()

    context = {
        'form': form,
        'titulo': 'Cadastrar Veículo',
        'botao_texto': 'Cadastrar',
    }
    return render(request, 'frota_locada/form_veiculo.html', context)


@login_required
def editar_veiculo(request, veiculo_id):
    """Edita um veículo locado"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    veiculo = get_object_or_404(VeiculoLocado, id=veiculo_id)
    horimetro_anterior = veiculo.horimetro_atual

    if request.method == 'POST':
        form = VeiculoLocadoForm(request.POST, instance=veiculo)
        if form.is_valid():
            veiculo_atualizado = form.save()

            # Se o horímetro foi alterado, criar histórico
            if veiculo_atualizado.horimetro_atual != horimetro_anterior:
                HistoricoHorimetro.objects.create(
                    veiculo=veiculo_atualizado,
                    horimetro_anterior=horimetro_anterior,
                    horimetro_atual=veiculo_atualizado.horimetro_atual,
                    observacoes=f'Horímetro atualizado via edição do veículo',
                    registrado_por=request.user
                )

            messages.success(request, f'Veículo {veiculo.placa} atualizado com sucesso!')
            return redirect('frota_locada:detalhes_veiculo', veiculo_id=veiculo.id)
    else:
        form = VeiculoLocadoForm(instance=veiculo)

    context = {
        'form': form,
        'veiculo': veiculo,
        'titulo': f'Editar Veículo - {veiculo.placa}',
        'botao_texto': 'Atualizar',
    }
    return render(request, 'frota_locada/form_veiculo.html', context)


@login_required
def detalhes_veiculo(request, veiculo_id):
    """Exibe detalhes de um veículo"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    veiculo = get_object_or_404(VeiculoLocado, id=veiculo_id)

    # Histórico de Horímetro (últimos 10 registros)
    historico_horimetro = veiculo.historico_horimetro.all()[:10]

    # Manutenções (últimas 5)
    manutencoes = veiculo.manutencoes.all()[:5]

    context = {
        'veiculo': veiculo,
        'historico_horimetro': historico_horimetro,
        'manutencoes': manutencoes,
    }
    return render(request, 'frota_locada/detalhes_veiculo.html', context)


@login_required
def excluir_veiculo(request, veiculo_id):
    """Exclui um veículo locado"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    veiculo = get_object_or_404(VeiculoLocado, id=veiculo_id)

    if request.method == 'POST':
        placa = veiculo.placa
        veiculo.delete()
        messages.success(request, f'Veículo {placa} excluído com sucesso!')
        return redirect('frota_locada:listar_veiculos')

    context = {
        'veiculo': veiculo,
    }
    return render(request, 'frota_locada/confirmar_exclusao.html', context)


# Views de Manutenção
@login_required
def listar_manutencoes(request):
    """Lista todas as manutenções"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    veiculo_filter = request.GET.get('veiculo', '')

    # Query base
    manutencoes = ManutencaoVeiculo.objects.select_related(
        'veiculo', 'tipo_manutencao', 'cadastrado_por'
    ).all()

    # Aplicar filtros
    if search:
        manutencoes = manutencoes.filter(
            Q(veiculo__placa__icontains=search) |
            Q(tipo_manutencao__nome__icontains=search) |
            Q(oficina__icontains=search)
        )

    if status_filter:
        manutencoes = manutencoes.filter(status=status_filter)

    if veiculo_filter:
        manutencoes = manutencoes.filter(veiculo_id=veiculo_filter)

    # Paginação
    paginator = Paginator(manutencoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para filtros
    veiculos = VeiculoLocado.objects.filter(status__in=['ATIVO', 'MANUTENCAO']).order_by('placa')
    status_choices = ManutencaoVeiculo.STATUS_CHOICES

    context = {
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'veiculo_filter': veiculo_filter,
        'veiculos': veiculos,
        'status_choices': status_choices,
    }

    return render(request, 'frota_locada/listar_manutencoes.html', context)


@login_required
def agendar_manutencao(request):
    """Agenda uma nova manutenção"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ManutencaoVeiculoForm(request.POST)
        if form.is_valid():
            manutencao = form.save(commit=False)
            manutencao.cadastrado_por = request.user
            manutencao.save()

            messages.success(request, f'Manutenção agendada para o veículo {manutencao.veiculo.placa}!')
            return redirect('frota_locada:listar_manutencoes')
    else:
        form = ManutencaoVeiculoForm()

    context = {
        'form': form,
        'titulo': 'Agendar Manutenção',
        'botao_texto': 'Agendar',
    }
    return render(request, 'frota_locada/form_manutencao.html', context)


# Views de Relatórios
@login_required
def relatorio_custos(request):
    """Relatório de custos da frota"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Filtros de data
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    hoje = timezone.now().date()
    if not data_inicio:
        data_inicio = hoje.replace(day=1)  # Primeiro dia do mês
    else:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()

    if not data_fim:
        data_fim = hoje
    else:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

    # Veículos ativos no período
    veiculos = VeiculoLocado.objects.filter(
        data_inicio_locacao__lte=data_fim
    ).filter(
        Q(data_fim_locacao__isnull=True) | Q(data_fim_locacao__gte=data_inicio)
    )

    # Calcular custos
    custo_total_mensal = 0
    custo_total_km = 0

    for veiculo in veiculos:
        # Calcular dias no período
        inicio_periodo = max(veiculo.data_inicio_locacao, data_inicio)
        fim_periodo = min(veiculo.data_fim_locacao or data_fim, data_fim)
        dias_periodo = (fim_periodo - inicio_periodo).days + 1

        # Custo mensal proporcional
        custo_mensal_proporcional = (veiculo.valor_mensal * dias_periodo) / 30
        custo_total_mensal += custo_mensal_proporcional

        # Custo por KM (se aplicável)
        if veiculo.valor_km:
            custo_total_km += veiculo.valor_total_km

    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'veiculos': veiculos,
        'custo_total_mensal': custo_total_mensal,
        'custo_total_km': custo_total_km,
        'custo_total_geral': custo_total_mensal + custo_total_km,
    }

    return render(request, 'frota_locada/relatorio_custos.html', context)


@login_required
def relatorio_km(request):
    """Relatório de quilometragem"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Filtros
    veiculo_filter = request.GET.get('veiculo', '')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Query base
    historico = HistoricoHorimetro.objects.select_related('veiculo', 'registrado_por').all()

    if veiculo_filter:
        historico = historico.filter(veiculo_id=veiculo_filter)

    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        historico = historico.filter(data_registro__date__gte=data_inicio_obj)

    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        historico = historico.filter(data_registro__date__lte=data_fim_obj)

    # Paginação
    paginator = Paginator(historico, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para filtros
    veiculos = VeiculoLocado.objects.all().order_by('placa')

    context = {
        'page_obj': page_obj,
        'veiculo_filter': veiculo_filter,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'veiculos': veiculos,
    }

    return render(request, 'frota_locada/relatorio_km.html', context)


# Views de Fornecedores
@login_required
def listar_fornecedores(request):
    """Lista todos os fornecedores"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Filtros
    search = request.GET.get('search', '')
    ativo_filter = request.GET.get('ativo', '')

    # Query base
    fornecedores = Fornecedor.objects.all()

    # Aplicar filtros
    if search:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search) |
            Q(cnpj__icontains=search) |
            Q(email__icontains=search)
        )

    if ativo_filter:
        fornecedores = fornecedores.filter(ativo=ativo_filter == 'true')

    # Paginação
    paginator = Paginator(fornecedores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'fornecedores': page_obj,  # Template usa 'fornecedores'
        'page_obj': page_obj,
        'search': search,
        'ativo_filter': ativo_filter,
    }

    return render(request, 'frota_locada/listar_fornecedores.html', context)


@login_required
def cadastrar_fornecedor(request):
    """Cadastra um novo fornecedor"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, f'Fornecedor {fornecedor.nome} cadastrado com sucesso!')
            return redirect('frota_locada:listar_fornecedores')
    else:
        form = FornecedorForm()

    context = {
        'form': form,
        'titulo': 'Cadastrar Fornecedor',
        'botao_texto': 'Cadastrar',
    }
    return render(request, 'frota_locada/form_fornecedor.html', context)


@login_required
def editar_fornecedor(request, fornecedor_id):
    """Edita um fornecedor"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)

    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            fornecedor_atualizado = form.save()
            messages.success(request, f'Fornecedor {fornecedor_atualizado.nome} atualizado com sucesso!')
            return redirect('frota_locada:listar_fornecedores')
    else:
        form = FornecedorForm(instance=fornecedor)

    context = {
        'form': form,
        'fornecedor': fornecedor,
        'titulo': f'Editar Fornecedor - {fornecedor.nome}',
        'botao_texto': 'Atualizar',
    }
    return render(request, 'frota_locada/form_fornecedor.html', context)


# Views de Tipos de Veículo
@login_required
def listar_tipos_veiculo(request):
    """Lista todos os tipos de veículo"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    tipos_veiculo = TipoVeiculo.objects.all().order_by('nome')

    context = {
        'tipos_veiculo': tipos_veiculo,
    }

    return render(request, 'frota_locada/listar_tipos_veiculo.html', context)


@login_required
def cadastrar_tipo_veiculo(request):
    """Cadastra um novo tipo de veículo"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = TipoVeiculoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f'Tipo de veículo {tipo.nome} cadastrado com sucesso!')
            return redirect('frota_locada:listar_tipos_veiculo')
    else:
        form = TipoVeiculoForm()

    context = {
        'form': form,
        'titulo': 'Cadastrar Tipo de Veículo',
        'botao_texto': 'Cadastrar',
    }
    return render(request, 'frota_locada/form_tipo_veiculo.html', context)


# Views de Histórico Horímetro
@login_required
def listar_historico_horimetro(request):
    """Lista histórico de Horímetro"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Filtros
    veiculo_filter = request.GET.get('veiculo', '')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Query base
    historico = HistoricoHorimetro.objects.select_related('veiculo', 'registrado_por').all()

    if veiculo_filter:
        historico = historico.filter(veiculo_id=veiculo_filter)

    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        historico = historico.filter(data_registro__date__gte=data_inicio_obj)

    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        historico = historico.filter(data_registro__date__lte=data_fim_obj)

    # Paginação
    paginator = Paginator(historico, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para filtros
    veiculos = VeiculoLocado.objects.all().order_by('placa')

    context = {
        'page_obj': page_obj,
        'veiculo_filter': veiculo_filter,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'veiculos': veiculos,
    }

    return render(request, 'frota_locada/listar_historico_horimetro.html', context)


@login_required
def registrar_km(request):
    """Registra nova quilometragem"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    # Pré-selecionar veículo se vier da URL
    veiculo_id = request.GET.get('veiculo')
    initial_data = {}
    if veiculo_id:
        try:
            veiculo = VeiculoLocado.objects.get(id=veiculo_id)
            initial_data['veiculo'] = veiculo
        except VeiculoLocado.DoesNotExist:
            pass

    if request.method == 'POST':
        form = HistoricoHorimetroForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.registrado_por = request.user

            # Atualizar horímetro atual do veículo
            veiculo = historico.veiculo
            historico.horimetro_anterior = veiculo.horimetro_atual
            veiculo.horimetro_atual = historico.horimetro_atual
            veiculo.save()

            historico.save()

            messages.success(request, f'Horímetro registrado para o veículo {veiculo.placa}!')
            return redirect('frota_locada:listar_historico_horimetro')
    else:
        form = HistoricoHorimetroForm(initial=initial_data)

    context = {
        'form': form,
        'titulo': 'Registrar Horímetro',
        'botao_texto': 'Registrar',
    }
    return render(request, 'frota_locada/form_historico_horimetro.html', context)


# Views AJAX
@login_required
def atualizar_status_manutencao(request, manutencao_id):
    """Atualiza status de manutenção via AJAX"""
    if request.method == 'POST':
        # Verificar permissões
        if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
            return JsonResponse({'success': False, 'message': 'Acesso negado.'})

        try:
            manutencao = ManutencaoVeiculo.objects.get(id=manutencao_id)
            novo_status = request.POST.get('status')

            if novo_status in dict(ManutencaoVeiculo.STATUS_CHOICES):
                manutencao.status = novo_status

                # Atualizar datas conforme o status
                if novo_status == 'EM_ANDAMENTO' and not manutencao.data_inicio:
                    manutencao.data_inicio = timezone.now()
                elif novo_status == 'CONCLUIDA' and not manutencao.data_conclusao:
                    manutencao.data_conclusao = timezone.now()

                manutencao.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Status atualizado para {manutencao.get_status_display()}',
                    'novo_status': manutencao.get_status_display()
                })
            else:
                return JsonResponse({'success': False, 'message': 'Status inválido.'})

        except ManutencaoVeiculo.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Manutenção não encontrada.'})

    return JsonResponse({'success': False, 'message': 'Método não permitido.'})


@login_required
def obter_horimetro_veiculo(request, veiculo_id):
    """Obtém horímetro atual do veículo via AJAX"""
    try:
        veiculo = VeiculoLocado.objects.get(id=veiculo_id)
        return JsonResponse({
            'success': True,
            'horimetro_atual': float(veiculo.horimetro_atual),
            'placa': veiculo.placa
        })
    except VeiculoLocado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Veículo não encontrado.'})


# Views adicionais de manutenção
@login_required
def detalhes_manutencao(request, manutencao_id):
    """Exibe detalhes de uma manutenção"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    manutencao = get_object_or_404(ManutencaoVeiculo, id=manutencao_id)

    context = {
        'manutencao': manutencao,
    }
    return render(request, 'frota_locada/detalhes_manutencao.html', context)


@login_required
def editar_manutencao(request, manutencao_id):
    """Edita uma manutenção"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')

    manutencao = get_object_or_404(ManutencaoVeiculo, id=manutencao_id)

    if request.method == 'POST':
        form = ManutencaoVeiculoForm(request.POST, instance=manutencao)
        if form.is_valid():
            manutencao_atualizada = form.save()
            messages.success(request, f'Manutenção do veículo {manutencao.veiculo.placa} atualizada!')
            return redirect('frota_locada:detalhes_manutencao', manutencao_id=manutencao.id)
    else:
        form = ManutencaoVeiculoForm(instance=manutencao)

    context = {
        'form': form,
        'manutencao': manutencao,
        'titulo': f'Editar Manutenção - {manutencao.veiculo.placa}',
        'botao_texto': 'Atualizar',
    }
    return render(request, 'frota_locada/form_manutencao.html', context)


# ==================== VIEWS PARA MARCAS DE VEÍCULOS ====================

@login_required
def listar_marcas(request):
    """Lista todas as marcas de veículos"""
    marcas = MarcaVeiculo.objects.all().order_by('nome')

    context = {
        'marcas': marcas,
        'titulo': 'Marcas de Veículos'
    }

    return render(request, 'frota_locada/listar_marcas.html', context)


@login_required
def cadastrar_marca_ajax(request):
    """Cadastra uma nova marca via AJAX"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'})

    if request.method == 'POST':
        form = MarcaVeiculoForm(request.POST)
        if form.is_valid():
            marca = form.save()
            return JsonResponse({
                'success': True,
                'marca': {
                    'id': marca.id,
                    'nome': marca.nome
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return JsonResponse({'success': False, 'error': 'Método não permitido.'})


@login_required
def cadastrar_marca(request):
    """Cadastra uma nova marca de veículo"""
    if request.method == 'POST':
        form = MarcaVeiculoForm(request.POST)
        if form.is_valid():
            marca = form.save()
            messages.success(request, f'Marca "{marca.nome}" cadastrada com sucesso!')
            return redirect('frota_locada:listar_marcas')
    else:
        form = MarcaVeiculoForm()

    context = {
        'form': form,
        'titulo': 'Cadastrar Nova Marca',
        'botao_texto': 'Cadastrar',
    }
    return render(request, 'frota_locada/form_marca.html', context)


@login_required
def editar_marca(request, marca_id):
    """Edita uma marca de veículo existente"""
    try:
        marca = get_object_or_404(MarcaVeiculo, id=marca_id)
    except:
        messages.error(request, 'Marca não encontrada.')
        return redirect('frota_locada:listar_marcas')

    if request.method == 'POST':
        form = MarcaVeiculoForm(request.POST, instance=marca)
        if form.is_valid():
            form.save()
            messages.success(request, f'Marca "{marca.nome}" editada com sucesso!')
            return redirect('frota_locada:listar_marcas')
    else:
        form = MarcaVeiculoForm(instance=marca)

    context = {
        'form': form,
        'marca': marca,
        'titulo': f'Editar Marca: {marca.nome}',
        'acao': 'Editar'
    }

    return render(request, 'frota_locada/form_marca.html', context)


@login_required
def excluir_marca(request, marca_id):
    """Exclui uma marca de veículo"""
    try:
        marca = get_object_or_404(MarcaVeiculo, id=marca_id)
    except:
        messages.error(request, 'Marca não encontrada.')
        return redirect('frota_locada:listar_marcas')

    # Verificar se a marca está sendo usada por algum veículo
    veiculos_usando = VeiculoLocado.objects.filter(marca=marca).count()

    if request.method == 'POST':
        if veiculos_usando > 0:
            messages.error(
                request,
                f'Não é possível excluir a marca "{marca.nome}" pois ela está sendo usada por {veiculos_usando} veículo(s).'
            )
        else:
            nome_marca = marca.nome
            marca.delete()
            messages.success(request, f'Marca "{nome_marca}" excluída com sucesso!')
        return redirect('frota_locada:listar_marcas')

    context = {
        'marca': marca,
        'veiculos_usando': veiculos_usando,
        'titulo': f'Excluir Marca: {marca.nome}'
    }

    return render(request, 'frota_locada/confirmar_exclusao_marca.html', context)


@login_required
def editar_marca_ajax(request, marca_id):
    """Edita uma marca via AJAX"""
    # Verificar permissões
    if not hasattr(request.user, 'perfil') or request.user.perfil.codigo_perfil not in ['ADMIN', 'SUPERVISOR']:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'})

    try:
        marca = MarcaVeiculo.objects.get(id=marca_id)
    except MarcaVeiculo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Marca não encontrada.'})

    if request.method == 'POST':
        form = MarcaVeiculoForm(request.POST, instance=marca)
        if form.is_valid():
            marca = form.save()
            return JsonResponse({
                'success': True,
                'marca': {
                    'id': marca.id,
                    'nome': marca.nome,
                    'ativo': marca.ativo,
                    'data_cadastro': marca.data_cadastro.strftime('%d/%m/%Y %H:%M')
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'error': 'Método não permitido.'})


# ============================================================================
# VIEWS PARA CHAMADOS DE MANUTENÇÃO DE MÁQUINAS/EQUIPAMENTOS
# ============================================================================

@login_required
def listar_chamados(request):
    """Lista chamados de manutenção baseado no perfil do usuário"""
    # Verificar se usuário tem perfil
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')

    perfil = request.user.perfil.codigo_perfil

    # Filtros
    status_filtro = request.GET.get('status', '')
    prioridade_filtro = request.GET.get('prioridade', '')
    tipo_equipamento_filtro = request.GET.get('tipo_equipamento', '')  # Filtro por tipo de equipamento locado

    # Converter tipo_equipamento_filtro para inteiro se não estiver vazio
    if tipo_equipamento_filtro:
        try:
            tipo_equipamento_filtro = int(tipo_equipamento_filtro)
        except (ValueError, TypeError):
            tipo_equipamento_filtro = None

    # Query base - filtrar por perfil e empresa
    # IMPORTANTE: Usar select_related com campos nullable (maquina e veiculo_locado podem ser None)
    if perfil in ['ADMIN', 'SUPERVISOR']:
        # Admin e Supervisor veem todos os chamados (máquinas E veículos locados)
        chamados = ChamadoManutencao.objects.select_related(
            'maquina', 'maquina__empresa',
            'veiculo_locado', 'veiculo_locado__fornecedor',
            'tipo_equipamento',
            'solicitante', 'mecanico'
        ).all()
    elif hasattr(request.user, 'perfil') and request.user.perfil.is_manutencao:
        # MECÂNICOS veem APENAS chamados da SUA EMPRESA:
        # 1. Chamados de máquinas da sua empresa
        # 2. Chamados de veículos locados atribuídos à sua empresa (via fornecedor)
        # 3. Chamados em QUALQUER status (AGUARDANDO, EM_ATENDIMENTO, etc.)
        # 4. Chamados iniciados por QUALQUER mecânico da mesma empresa

        from django.db.models import Q

        if hasattr(request.user, 'perfil') and request.user.perfil.empresa:
            # Mecânico com empresa vinculada vê APENAS chamados da sua empresa
            # - Chamados de máquinas da sua empresa
            # - Chamados de veículos locados onde o fornecedor tem vínculo com a empresa do mecânico
            chamados = ChamadoManutencao.objects.select_related(
                'maquina', 'maquina__empresa',
                'veiculo_locado', 'veiculo_locado__fornecedor', 'veiculo_locado__fornecedor__empresa',
                'tipo_equipamento',
                'solicitante', 'mecanico'
            ).filter(
                Q(maquina__empresa=request.user.perfil.empresa) |
                Q(veiculo_locado__fornecedor__empresa=request.user.perfil.empresa)  # Veículos cujo fornecedor tem vínculo com a empresa
            )
        else:
            # Mecânico sem vínculo vê todos os chamados (compatibilidade)
            chamados = ChamadoManutencao.objects.select_related(
                'maquina', 'maquina__empresa',
                'veiculo_locado', 'veiculo_locado__fornecedor',
                'tipo_equipamento',
                'solicitante', 'mecanico'
            ).all()
    else:
        # Demandantes e outros veem apenas seus próprios chamados
        chamados = ChamadoManutencao.objects.select_related(
            'maquina', 'maquina__empresa',
            'veiculo_locado', 'veiculo_locado__fornecedor',
            'tipo_equipamento',
            'solicitante', 'mecanico'
        ).filter(solicitante=request.user)

    # Aplicar filtros
    if status_filtro:
        chamados = chamados.filter(status=status_filtro)
    if prioridade_filtro:
        chamados = chamados.filter(prioridade=prioridade_filtro)

    # Filtro por tipo de equipamento
    # Busca tanto em veiculo_locado (equipamentos locados) quanto em maquina (equipamentos do estaleiro)
    print(f"\n🔍 VERIFICANDO FILTRO: tipo_equipamento_filtro = {tipo_equipamento_filtro}")

    if tipo_equipamento_filtro:
        from django.db.models import Q

        # Buscar o nome do tipo para comparar com maquina.tipo
        tipo_obj = TipoVeiculo.objects.filter(id=tipo_equipamento_filtro).first()

        print(f"🔍 Tipo encontrado: {tipo_obj}")

        if tipo_obj:
            # NOVO FILTRO SIMPLIFICADO: Usar o campo tipo_equipamento
            # Isso funciona tanto para veículos locados quanto máquinas do estaleiro
            print(f"\n{'='*80}")
            print(f"DEBUG FILTRO POR TIPO DE EQUIPAMENTO")
            print(f"{'='*80}")
            print(f"Tipo selecionado: {tipo_obj.nome} (ID: {tipo_equipamento_filtro})")
            print(f"Total de chamados ANTES do filtro: {chamados.count()}")

            # Listar os chamados antes do filtro
            print("\nChamados ANTES do filtro:")
            for ch in chamados[:5]:
                tipo_nome = ch.tipo_equipamento.nome if ch.tipo_equipamento else "None"
                print(f"  - {ch.numero_chamado}: tipo_equipamento = {tipo_nome}")

            # Filtrar pelo novo campo tipo_equipamento
            chamados = chamados.filter(tipo_equipamento_id=tipo_equipamento_filtro)

            print(f"\nTotal de chamados APÓS filtro: {chamados.count()}")

            # Listar os chamados após o filtro
            print("\nChamados APÓS o filtro:")
            for ch in chamados[:5]:
                tipo_nome = ch.tipo_equipamento.nome if ch.tipo_equipamento else "None"
                print(f"  - {ch.numero_chamado}: tipo_equipamento = {tipo_nome}")

            print(f"{'='*80}\n")
        else:
            print(f"❌ ERRO: Tipo com ID {tipo_equipamento_filtro} não encontrado!")
    else:
        print("ℹ️  Nenhum filtro de tipo de equipamento aplicado")

    # Ordenar chamados por data de abertura (mais recentes primeiro)
    chamados = chamados.order_by('-data_abertura')

    # DEBUG: Verificar quantos chamados existem
    print(f"\n{'='*80}")
    print(f"DEBUG: TOTAL DE CHAMADOS APÓS FILTROS")
    print(f"{'='*80}")
    print(f"Total de chamados: {chamados.count()}")
    print(f"Primeiros 10 chamados:")
    for ch in chamados[:10]:
        print(f"  - {ch.numero_chamado} | {ch.data_abertura} | {ch.maquina} | Tipo: {ch.tipo_equipamento}")
    print(f"{'='*80}\n")

    # Estatísticas
    stats = {
        'total': ChamadoManutencao.objects.count(),
        'aguardando': ChamadoManutencao.objects.filter(status='AGUARDANDO').count(),
        'em_atendimento': ChamadoManutencao.objects.filter(status='EM_ATENDIMENTO').count(),
        'concluidos': ChamadoManutencao.objects.filter(status='CONCLUIDO').count(),
        'criticos': ChamadoManutencao.objects.filter(prioridade='CRITICA', status__in=['AGUARDANDO', 'EM_ATENDIMENTO']).count(),
    }

    # Paginação
    paginator = Paginator(chamados, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dados para filtros - buscar tipos de equipamento do banco
    # Incluir contagem de chamados por tipo usando o novo campo tipo_equipamento
    from django.db.models import Q
    tipos_equipamento = TipoVeiculo.objects.filter(ativo=True).order_by('nome')

    # Adicionar contagem de chamados por tipo usando o campo tipo_equipamento
    for tipo in tipos_equipamento:
        tipo.total_chamados = ChamadoManutencao.objects.filter(tipo_equipamento=tipo).count()

    # Adicionar informação sobre quais chamados o usuário pode iniciar/finalizar
    for chamado in page_obj:
        # Pode iniciar se for mecânico da empresa responsável
        chamado.usuario_pode_iniciar = chamado.pode_ser_atendido_por(request.user)

        # Pode finalizar se:
        # 1. For mecânico (não solicitante)
        # 2. For da mesma empresa do chamado (ou admin/supervisor)
        # 3. Chamado estiver EM_ATENDIMENTO (independente de quem iniciou)
        if hasattr(request.user, 'perfil'):
            is_mecanico = request.user.perfil.is_manutencao
            is_admin_supervisor = request.user.perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR']

            # Admin/Supervisor podem finalizar qualquer chamado
            if is_admin_supervisor:
                chamado.usuario_pode_finalizar = True
            # Mecânicos podem finalizar chamados da sua empresa (mesmo que outro mecânico tenha iniciado)
            elif is_mecanico:
                chamado.usuario_pode_finalizar = chamado.pode_ser_atendido_por(request.user)
            else:
                chamado.usuario_pode_finalizar = False
        else:
            chamado.usuario_pode_finalizar = False

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'tipos_equipamento': tipos_equipamento,
        'status_filtro': status_filtro,
        'prioridade_filtro': prioridade_filtro,
        'tipo_equipamento_filtro': tipo_equipamento_filtro,
        'titulo': 'Chamados de Manutenção',
        'perfil': perfil,
    }

    return render(request, 'frota_locada/listar_chamados.html', context)


@login_required
def abrir_chamado(request):
    """Abre um novo chamado de manutenção"""
    # Verificar se usuário tem perfil
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')

    # Verificar se o perfil pode abrir chamados de manutenção
    try:
        if not request.user.perfil.pode_abrir_chamados_manutencao:
            messages.error(request, 'Acesso negado. Apenas ADMIN, SUPERVISOR, CONTROLE_MAN_PTA e CONTROLE_PROD_PTA podem abrir chamados de manutenção.')
            return redirect('dashboard')
    except AttributeError as e:
        messages.error(request, f'Erro ao verificar permissões do perfil. Por favor, contate o administrador. Erro: {str(e)}')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ChamadoManutencaoForm(request.POST, request.FILES)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.solicitante = request.user

            # Se não foi selecionado tipo_equipamento mas foi selecionado veiculo_locado,
            # preencher automaticamente com o tipo do veículo
            if not chamado.tipo_equipamento and chamado.veiculo_locado:
                chamado.tipo_equipamento = chamado.veiculo_locado.tipo_veiculo

            chamado.save()
            messages.success(request, f'Chamado {chamado.numero_chamado} aberto com sucesso!')
            return redirect('frota_locada:listar_chamados')
    else:
        form = ChamadoManutencaoForm()

    context = {
        'form': form,
        'titulo': 'Abrir Chamado de Manutenção equipamentos locados',
        'acao': 'Abrir'
    }

    return render(request, 'frota_locada/form_chamado.html', context)


@login_required
def iniciar_atendimento(request, chamado_id):
    """Inicia o atendimento de um chamado"""
    # Verificar permissões - apenas TERCEIRO_*, ADMIN e SUPERVISOR podem iniciar atendimento
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')

    perfil = request.user.perfil.codigo_perfil
    # Permitir TERCEIRO_* (mecânicos terceirizados), ADMIN e SUPERVISOR
    if not (perfil.startswith('TERCEIRO_') or perfil in ['ADMIN', 'SUPERVISOR']):
        messages.error(request, 'Apenas mecânicos, administradores e supervisores podem iniciar atendimentos.')
        return redirect('frota_locada:meus_chamados')

    chamado = get_object_or_404(ChamadoManutencao, id=chamado_id)

    # Verificar se o usuário pode atender este chamado
    if not chamado.pode_ser_atendido_por(request.user):
        messages.error(request, 'Você não tem permissão para atender chamados desta empresa.')
        return redirect('frota_locada:meus_chamados')

    # Verificar se já existe um atendimento em andamento para este mecânico neste chamado
    atendimento_existente = AtendimentoChamado.objects.filter(
        chamado=chamado,
        mecanico=request.user,
        status__in=['EM_ANDAMENTO', 'PAUSADO']
    ).first()

    if atendimento_existente:
        messages.info(request, 'Você já possui um atendimento em andamento para este chamado.')
        return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_existente.id)

    if request.method == 'POST':
        tipo_manutencao = request.POST.get('tipo_manutencao')

        if not tipo_manutencao:
            messages.error(request, 'Selecione o tipo de manutenção.')
            return redirect('frota_locada:iniciar_atendimento', chamado_id=chamado_id)

        # Criar novo atendimento
        atendimento = AtendimentoChamado.objects.create(
            chamado=chamado,
            mecanico=request.user,
            tipo_manutencao=tipo_manutencao,
            status='EM_ANDAMENTO'
        )

        # Atualizar status do chamado se estava aguardando
        if chamado.status == 'AGUARDANDO':
            chamado.status = 'EM_ATENDIMENTO'
            chamado.mecanico = request.user
            chamado.data_inicio_atendimento = timezone.now()
            chamado.save()

        messages.success(request, f'Atendimento do chamado {chamado.numero_chamado} iniciado!')
        return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento.id)

    # GET - Mostrar formulário de seleção de tipo de manutenção
    context = {
        'chamado': chamado,
        'titulo': f'Iniciar Atendimento - {chamado.numero_chamado}',
        'tipos_manutencao': AtendimentoChamado.TIPO_MANUTENCAO_CHOICES,
    }
    return render(request, 'frota_locada/iniciar_atendimento.html', context)


@login_required
def finalizar_chamado(request, chamado_id):
    """Finaliza um chamado de manutenção"""
    # Verificar permissões - apenas MANUTENCAO, ADMIN e SUPERVISOR podem finalizar
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')

    perfil = request.user.perfil.codigo_perfil
    if perfil not in ['MANUTENCAO', 'ADMIN', 'SUPERVISOR']:
        messages.error(request, 'Apenas mecânicos, administradores e supervisores podem finalizar atendimentos.')
        return redirect('frota_locada:listar_chamados')
    chamado = get_object_or_404(ChamadoManutencao, id=chamado_id)

    # Verificar se o usuário pode atender este chamado
    if not chamado.pode_ser_atendido_por(request.user):
        messages.error(request, 'Você não tem permissão para atender chamados desta empresa.')
        return redirect('frota_locada:listar_chamados')

    # Verificar se o chamado pode ser finalizado
    if chamado.status != 'EM_ATENDIMENTO':
        messages.error(request, 'Este chamado não pode ser finalizado.')
        return redirect('frota_locada:listar_chamados')

    if request.method == 'POST':
        form = FinalizarChamadoForm(request.POST, instance=chamado)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.status = 'CONCLUIDO'
            chamado.data_fim_atendimento = timezone.now()
            chamado.save()
            messages.success(request, f'Chamado {chamado.numero_chamado} finalizado com sucesso!')
            return redirect('frota_locada:listar_chamados')
    else:
        form = FinalizarChamadoForm(instance=chamado)

    context = {
        'form': form,
        'chamado': chamado,
        'titulo': f'Finalizar Chamado: {chamado.numero_chamado}',
        'acao': 'Finalizar'
    }

    return render(request, 'frota_locada/finalizar_chamado.html', context)


@login_required
def listar_maquinas(request):
    """Lista todas as máquinas"""
    maquinas = Maquina.objects.all().order_by('nome')

    # Estatísticas
    stats = {
        'total': maquinas.count(),
        'ativas': maquinas.filter(ativo=True).count(),
        'inativas': maquinas.filter(ativo=False).count(),
        'em_manutencao': sum(1 for m in maquinas if m.chamados_abertos > 0),
    }

    context = {
        'maquinas': maquinas,
        'stats': stats,
        'titulo': 'Máquinas e Equipamentos'
    }

    return render(request, 'frota_locada/listar_maquinas.html', context)


@login_required
def cadastrar_maquina(request):
    """Cadastra uma nova máquina"""
    if request.method == 'POST':
        form = MaquinaForm(request.POST)
        if form.is_valid():
            maquina = form.save()
            messages.success(request, f'Máquina "{maquina.nome}" cadastrada com sucesso!')
            return redirect('frota_locada:listar_maquinas')
    else:
        form = MaquinaForm()

    context = {
        'form': form,
        'titulo': 'Cadastrar Máquina',
        'acao': 'Cadastrar'
    }

    return render(request, 'frota_locada/form_maquina.html', context)


@login_required
def editar_maquina(request, maquina_id):
    """Edita uma máquina existente"""
    maquina = get_object_or_404(Maquina, id=maquina_id)

    if request.method == 'POST':
        form = MaquinaForm(request.POST, instance=maquina)
        if form.is_valid():
            maquina = form.save()
            messages.success(request, f'Máquina "{maquina.nome}" editada com sucesso!')
            return redirect('frota_locada:listar_maquinas')
    else:
        form = MaquinaForm(instance=maquina)

    context = {
        'form': form,
        'maquina': maquina,
        'titulo': f'Editar Máquina: {maquina.nome}',
        'acao': 'Editar'
    }

    return render(request, 'frota_locada/form_maquina.html', context)


@login_required
def detalhes_chamado(request, chamado_id):
    """Exibe detalhes de um chamado"""
    # Verificar se usuário tem perfil
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Perfil de usuário não encontrado.')
        return redirect('dashboard')

    perfil = request.user.perfil.codigo_perfil

    # Buscar chamado baseado no perfil
    if perfil in ['ADMIN', 'SUPERVISOR'] or request.user.perfil.is_manutencao:
        # Admin, Supervisor e Manutenção podem ver qualquer chamado
        chamado = get_object_or_404(ChamadoManutencao, id=chamado_id)
    else:
        # Outros perfis só veem seus próprios chamados
        chamado = get_object_or_404(ChamadoManutencao, id=chamado_id, solicitante=request.user)

    # Verificar se usuário pode atender este chamado
    pode_atender = chamado.pode_ser_atendido_por(request.user)

    context = {
        'chamado': chamado,
        'titulo': f'Detalhes do Chamado {chamado.numero_chamado}',
        'perfil': perfil,
        'pode_atender': pode_atender,
    }

    return render(request, 'frota_locada/detalhes_chamado.html', context)


# ============================================================================
# VIEWS PARA GERENCIAR VÍNCULOS MECÂNICO-FORNECEDOR
# ============================================================================

# VIEWS REMOVIDAS - listar_mecanicos_fornecedores e vincular_mecanico_fornecedor
# Agora usamos PerfilUsuario.empresa para vincular mecânicos às empresas
# O vínculo é feito diretamente no cadastro de usuário (core/views.py)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@login_required
def api_maquina_fornecedor(request, maquina_id):
    """API endpoint para buscar informações da empresa de uma máquina"""
    try:
        maquina = get_object_or_404(Maquina, id=maquina_id, ativo=True)

        return JsonResponse({
            'success': True,
            'empresa_id': maquina.empresa.id,
            'empresa_nome': maquina.empresa.nome,
            'empresa_cnpj': maquina.empresa.cnpj if hasattr(maquina.empresa, 'cnpj') else '',
            'maquina_nome': maquina.nome,
            'maquina_codigo': maquina.codigo
        })

    except Maquina.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Máquina não encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def api_veiculo_locado_fornecedor(request, veiculo_id):
    """API endpoint para buscar informações do fornecedor de um veículo locado"""
    try:
        veiculo = get_object_or_404(VeiculoLocado, id=veiculo_id, status='ATIVO')

        return JsonResponse({
            'success': True,
            'fornecedor_id': veiculo.fornecedor.id,
            'fornecedor_nome': veiculo.fornecedor.nome,
            'fornecedor_cnpj': veiculo.fornecedor.cnpj,
            'veiculo_placa': veiculo.placa,
            'veiculo_modelo': veiculo.modelo
        })

    except VeiculoLocado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Veículo/Equipamento não encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================================================
# VIEWS PARA MECÂNICOS - ATENDIMENTO DE CHAMADOS
# ============================================================================

@login_required
def meus_chamados(request):
    """
    Tela principal para mecânicos visualizarem chamados disponíveis para atendimento.
    Mostra apenas chamados de máquinas da empresa do mecânico.
    """
    # Verificar se usuário tem perfil
    if not hasattr(request.user, 'perfil'):
        messages.error(request, 'Usuário sem perfil definido.')
        return redirect('dashboard')

    perfil = request.user.perfil

    # Verificar se é mecânico terceirizado ou admin/supervisor
    if not (perfil.codigo_perfil.startswith('TERCEIRO_') or perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR']):
        messages.error(request, 'Acesso negado. Esta área é exclusiva para mecânicos.')
        return redirect('dashboard')

    # Filtrar chamados
    if perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR']:
        # Admin e Supervisor veem todos os chamados
        chamados_disponiveis = ChamadoManutencao.objects.filter(
            status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
        ).select_related('maquina', 'solicitante', 'mecanico').prefetch_related('atendimentos').order_by('-prioridade', 'data_abertura')
    else:
        # Mecânicos veem apenas chamados da sua empresa
        if not perfil.empresa:
            messages.warning(request, 'Você não está vinculado a nenhuma empresa. Entre em contato com o administrador.')
            return redirect('dashboard')

        chamados_disponiveis = ChamadoManutencao.objects.filter(
            maquina__empresa=perfil.empresa,
            status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
        ).select_related('maquina', 'solicitante', 'mecanico').prefetch_related('atendimentos').order_by('-prioridade', 'data_abertura')

    # Meus atendimentos em andamento
    meus_atendimentos = AtendimentoChamado.objects.filter(
        mecanico=request.user,
        status='EM_ANDAMENTO'
    ).select_related('chamado', 'chamado__maquina').order_by('-data_inicio')

    # Adicionar atendimento do mecânico em cada chamado (apenas atendimentos ativos)
    for chamado in chamados_disponiveis:
        chamado.meu_atendimento = chamado.atendimentos.filter(
            mecanico=request.user,
            status__in=['EM_ANDAMENTO', 'PAUSADO']  # Não incluir FINALIZADO
        ).first()

    # Estatísticas
    total_chamados = chamados_disponiveis.count()
    chamados_aguardando = chamados_disponiveis.filter(status='AGUARDANDO').count()
    chamados_em_atendimento = chamados_disponiveis.filter(status='EM_ATENDIMENTO').count()

    context = {
        'chamados': chamados_disponiveis,
        'meus_atendimentos': meus_atendimentos,
        'total_chamados': total_chamados,
        'chamados_aguardando': chamados_aguardando,
        'chamados_em_atendimento': chamados_em_atendimento,
        'perfil': perfil,
        'titulo': 'Meus Chamados',
        'perfil': perfil,
    }

    return render(request, 'frota_locada/meus_chamados.html', context)


@login_required
def detalhes_atendimento(request, atendimento_id):
    """
    Mostra detalhes de um atendimento em andamento.
    Permite ao mecânico visualizar e finalizar o atendimento.
    """
    atendimento = get_object_or_404(AtendimentoChamado, id=atendimento_id)

    # Verificar se usuário pode editar este atendimento
    if not atendimento.pode_ser_editado_por(request.user):
        messages.error(request, 'Você não tem permissão para visualizar este atendimento.')
        return redirect('frota_locada:meus_chamados')

    # Buscar todos os atendimentos deste chamado
    todos_atendimentos = AtendimentoChamado.objects.filter(
        chamado=atendimento.chamado
    ).select_related('mecanico').order_by('data_inicio')

    context = {
        'atendimento': atendimento,
        'chamado': atendimento.chamado,
        'todos_atendimentos': todos_atendimentos,
        'titulo': f'Atendimento - {atendimento.chamado.numero_chamado}',
        'tipos_manutencao': AtendimentoChamado.TIPO_MANUTENCAO_CHOICES,
    }

    return render(request, 'frota_locada/detalhes_atendimento.html', context)


@login_required
def finalizar_atendimento(request, atendimento_id):
    """
    Finaliza um atendimento, registrando as informações do serviço realizado.
    """
    atendimento = get_object_or_404(AtendimentoChamado, id=atendimento_id)

    # Verificar se usuário pode editar este atendimento
    if not atendimento.pode_ser_editado_por(request.user):
        messages.error(request, 'Você não tem permissão para finalizar este atendimento.')
        return redirect('frota_locada:meus_chamados')

    # Verificar se atendimento já foi finalizado
    if atendimento.status == 'FINALIZADO':
        messages.warning(request, 'Este atendimento já foi finalizado.')
        return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_id)

    if request.method == 'POST':
        descricao_servico = request.POST.get('descricao_servico', '').strip()
        pecas_trocadas = request.POST.get('pecas_trocadas', '').strip()
        observacoes = request.POST.get('observacoes', '').strip()
        mau_uso = request.POST.get('mau_uso') == 'true'
        finalizar_chamado = request.POST.get('finalizar_chamado') == 'true'

        # Validações
        if not descricao_servico:
            messages.error(request, 'A descrição do serviço é obrigatória.')
            return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_id)

        # Atualizar atendimento
        atendimento.descricao_servico = descricao_servico
        atendimento.pecas_trocadas = pecas_trocadas
        atendimento.observacoes = observacoes
        atendimento.mau_uso = mau_uso
        atendimento.data_finalizacao = timezone.now()
        atendimento.status = 'FINALIZADO'
        atendimento.save()

        # Verificar se deve finalizar o chamado
        chamado = atendimento.chamado

        if finalizar_chamado:
            # Usuário marcou para finalizar o chamado
            chamado.status = 'CONCLUIDO'
            chamado.data_fim_atendimento = timezone.now()
            chamado.descricao_solucao = descricao_servico
            chamado.pecas_utilizadas = pecas_trocadas
            chamado.observacoes = observacoes
            chamado.save()
            messages.success(request, f'Atendimento finalizado e chamado {chamado.numero_chamado} concluído com sucesso!')
        else:
            # Verificar se ainda existem atendimentos ativos
            atendimentos_ativos = chamado.atendimentos.filter(
                status__in=['EM_ANDAMENTO', 'PAUSADO']
            ).exists()

            if not atendimentos_ativos:
                # Não há mais atendimentos ativos, finalizar o chamado automaticamente
                chamado.status = 'CONCLUIDO'
                chamado.data_fim_atendimento = timezone.now()
                chamado.descricao_solucao = descricao_servico
                chamado.pecas_utilizadas = pecas_trocadas
                chamado.observacoes = observacoes
                chamado.save()
                messages.success(request, f'Atendimento finalizado! Chamado {chamado.numero_chamado} concluído automaticamente (sem atendimentos pendentes).')
            else:
                messages.success(request, 'Atendimento finalizado com sucesso! O chamado continua em atendimento.')

        return redirect('frota_locada:meus_chamados')

    # GET - Redirecionar para detalhes
    return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_id)


@login_required
def pausar_atendimento(request, atendimento_id):
    """
    Pausa um atendimento em andamento.
    """
    atendimento = get_object_or_404(AtendimentoChamado, id=atendimento_id)

    # Verificar permissões
    if not atendimento.pode_ser_editado_por(request.user):
        messages.error(request, 'Você não tem permissão para pausar este atendimento.')
        return redirect('frota_locada:meus_chamados')

    if atendimento.status != 'EM_ANDAMENTO':
        messages.error(request, 'Apenas atendimentos em andamento podem ser pausados.')
        return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_id)

    atendimento.status = 'PAUSADO'
    atendimento.save()

    messages.success(request, 'Atendimento pausado.')
    return redirect('frota_locada:meus_chamados')


@login_required
def retomar_atendimento(request, atendimento_id):
    """
    Retoma um atendimento pausado.
    """
    atendimento = get_object_or_404(AtendimentoChamado, id=atendimento_id)

    # Verificar permissões
    if not atendimento.pode_ser_editado_por(request.user):
        messages.error(request, 'Você não tem permissão para retomar este atendimento.')
        return redirect('frota_locada:meus_chamados')

    if atendimento.status != 'PAUSADO':
        messages.error(request, 'Apenas atendimentos pausados podem ser retomados.')
        return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_id)

    atendimento.status = 'EM_ANDAMENTO'
    atendimento.save()

    messages.success(request, 'Atendimento retomado.')
    return redirect('frota_locada:detalhes_atendimento', atendimento_id=atendimento_id)


# AJAX Views
@login_required
def atualizar_tempos_chamado(request, chamado_id):
    """
    View AJAX para atualizar tempos do chamado em tempo real.
    Retorna JSON com tempos atualizados.
    """
    try:
        chamado = get_object_or_404(ChamadoManutencao, id=chamado_id)

        # Calcular tempos atualizados
        data = {
            'success': True,
            'tempo_aguardando': chamado.tempo_aguardando_formatado,
            'tempo_total_indisponibilidade': chamado.tempo_total_indisponibilidade_formatado,
            'status': chamado.status,
        }

        # Se tem atendimento em andamento, incluir tempo decorrido
        if chamado.status == 'EM_ATENDIMENTO':
            atendimento_atual = chamado.atendimentos.filter(status='EM_ANDAMENTO').first()
            if atendimento_atual:
                data['tempo_decorrido'] = atendimento_atual.tempo_decorrido_formatado
                data['atendimento_id'] = atendimento_atual.id

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
