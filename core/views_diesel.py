"""
Views para o controle de diesel
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from .models import (
    Veiculo, Equipamento, ConfiguracaoTanque, AbastecimentoVeiculo, AbastecimentoTanque,
    PerfilUsuario, Cliente, AlertaDiesel
)


def verificar_permissao_diesel(user):
    """Verifica se o usuário tem permissão para acessar o controle de diesel"""
    if not user.is_authenticated:
        return False

    # Verificar se é superuser
    if user.is_superuser:
        return True

    try:
        perfil = user.perfil
        return perfil.is_admin_ou_supervisor
    except (PerfilUsuario.DoesNotExist, AttributeError):
        return False


@login_required
def dashboard_diesel(request):
    """Dashboard principal do controle de diesel - Apenas Admin e Supervisor"""
    # Verificar permissão
    if not verificar_permissao_diesel(request.user):
        messages.error(request, 'Você não tem permissão para acessar o controle de diesel.')
        return redirect('dashboard')
    
    # Obter configuração do tanque
    tanque = ConfiguracaoTanque.objects.first()
    if not tanque:
        # Criar configuração padrão se não existir
        tanque = ConfiguracaoTanque.objects.create()
    
    # Estatísticas gerais - usar Equipamento como fonte principal
    from .models import Veiculo
    try:
        # Tentar usar equipamentos que são veículos (têm placa)
        total_veiculos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').count()

        veiculos_com_agenda = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False,
            tem_agenda=True
        ).exclude(placa='').count()

        # Se não houver equipamentos com placa, usar tabela Veiculo
        if total_veiculos == 0:
            total_veiculos = Veiculo.objects.filter(ativo=True).count()
            veiculos_com_agenda = Veiculo.objects.filter(ativo=True, tem_agenda=True).count()

    except Exception as e:
        print(f"DEBUG: Erro ao acessar equipamentos no dashboard, usando Veiculo: {e}")
        total_veiculos = Veiculo.objects.filter(ativo=True).count()
        veiculos_com_agenda = Veiculo.objects.filter(ativo=True, tem_agenda=True).count()
    
    # Abastecimentos hoje
    hoje = timezone.now().date()
    abastecimentos_hoje = AbastecimentoVeiculo.objects.filter(
        data_abastecimento__date=hoje
    ).count()
    
    # Litros abastecidos hoje
    litros_hoje = AbastecimentoVeiculo.objects.filter(
        data_abastecimento__date=hoje
    ).aggregate(total=Sum('quantidade_litros'))['total'] or 0
    
    # Últimos 7 dias
    data_inicio = hoje - timedelta(days=7)
    abastecimentos_semana = AbastecimentoVeiculo.objects.filter(
        data_abastecimento__date__gte=data_inicio
    )
    
    # Veículos mais abastecidos (últimos 30 dias)
    data_inicio_mes = hoje - timedelta(days=30)
    veiculos_mais_abastecidos = AbastecimentoVeiculo.objects.filter(
        data_abastecimento__date__gte=data_inicio_mes
    ).values(
        'veiculo__nome', 'veiculo__placa'
    ).annotate(
        total_litros=Sum('quantidade_litros'),
        total_abastecimentos=Count('id')
    ).order_by('-total_litros')[:10]
    
    # Últimos abastecimentos
    ultimos_abastecimentos = AbastecimentoVeiculo.objects.select_related(
        'veiculo', 'operador'
    ).order_by('-data_abastecimento')[:10]
    
    context = {
        'tanque': tanque,
        'total_veiculos': total_veiculos,
        'veiculos_com_agenda': veiculos_com_agenda,
        'abastecimentos_hoje': abastecimentos_hoje,
        'litros_hoje': litros_hoje,
        'veiculos_mais_abastecidos': veiculos_mais_abastecidos,
        'ultimos_abastecimentos': ultimos_abastecimentos,
    }
    
    return render(request, 'diesel/dashboard.html', context)


@login_required
def registrar_chegada_diesel(request):
    """Registrar chegada de diesel no tanque - Apenas Admin e Supervisor"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)

    if request.method == 'POST':
        try:
            quantidade = Decimal(request.POST.get('quantidade_litros'))
            valor_por_litro = Decimal(request.POST.get('valor_por_litro'))
            data_chegada = request.POST.get('data_chegada')
            fornecedor = request.POST.get('fornecedor', '')
            numero_nota_fiscal = request.POST.get('numero_nota_fiscal', '')
            observacoes = request.POST.get('observacoes', '')

            # Validações
            if quantidade <= 0:
                return JsonResponse({'success': False, 'error': 'Quantidade deve ser maior que zero'})

            if valor_por_litro <= 0:
                return JsonResponse({'success': False, 'error': 'Valor por litro deve ser maior que zero'})

            # Converter data
            if data_chegada:
                data_chegada = datetime.strptime(data_chegada, '%Y-%m-%dT%H:%M')
                data_chegada = timezone.make_aware(data_chegada)
            else:
                data_chegada = timezone.now()

            # Verificar se não excede a capacidade total de recebimento (tanque + extra)
            tanque = ConfiguracaoTanque.objects.first()
            if tanque:
                if not tanque.pode_receber(quantidade):
                    return JsonResponse({
                        'success': False,
                        'error': f'Quantidade excede capacidade total de recebimento. Máximo possível: {tanque.espaco_disponivel_recebimento}L (Tanque: {tanque.capacidade_total}L + Extra: {tanque.capacidade_extra}L)'
                    })

            # Criar registro
            abastecimento = AbastecimentoTanque.objects.create(
                quantidade_litros=quantidade,
                valor_por_litro=valor_por_litro,
                data_chegada=data_chegada,
                fornecedor=fornecedor,
                numero_nota_fiscal=numero_nota_fiscal,
                observacoes=observacoes,
                operador=request.user
            )

            return JsonResponse({
                'success': True,
                'message': f'Chegada de {quantidade}L registrada com sucesso!',
                'novo_nivel': float(abastecimento.nivel_posterior),
                'valor_total': float(abastecimento.valor_total)
            })

        except ValueError as e:
            return JsonResponse({'success': False, 'error': 'Dados inválidos'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def testar_alerta_email(request):
    """Testar envio de alerta por email - Apenas Admin e Supervisor"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)

    try:
        tanque = ConfiguracaoTanque.objects.first()
        if tanque:
            # Forçar verificação de alertas
            tanque.verificar_e_enviar_alertas()

            return JsonResponse({
                'success': True,
                'message': f'Teste de alerta executado! Nível atual: {tanque.nivel_atual}L - Status: {tanque.status_nivel}',
                'nivel': float(tanque.nivel_atual),
                'status': tanque.status_nivel
            })
        else:
            return JsonResponse({'success': False, 'error': 'Configuração do tanque não encontrada'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def abastecer_veiculo(request):
    """Formulário para abastecer veículo - Apenas Admin e Supervisor"""
    if not verificar_permissao_diesel(request.user):
        messages.error(request, 'Você não tem permissão para acessar o controle de diesel.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        veiculo_id = request.POST.get('veiculo')
        cliente_id = request.POST.get('cliente')
        quantidade = request.POST.get('quantidade_litros')
        odometro = request.POST.get('odometro_atual')
        observacoes = request.POST.get('observacoes', '')

        try:
            # Usar Equipamento como fonte principal
            try:
                veiculo = get_object_or_404(Equipamento, id=veiculo_id, ativo=True)
                print(f"DEBUG: Equipamento encontrado: {veiculo.nome} ({veiculo.placa})")
            except Equipamento.DoesNotExist:
                # Fallback para Veiculo se não encontrar equipamento
                print(f"DEBUG: Equipamento {veiculo_id} não encontrado, tentando Veiculo")
                veiculo = get_object_or_404(Veiculo, id=veiculo_id, ativo=True)
                print(f"DEBUG: Veiculo encontrado: {veiculo.nome} ({veiculo.placa})")

            cliente = get_object_or_404(Cliente, id=cliente_id) if cliente_id else None
            quantidade = Decimal(quantidade)

            # Verificar se há diesel suficiente no tanque
            tanque = ConfiguracaoTanque.objects.first()
            if not tanque or not tanque.pode_abastecer(quantidade):
                messages.error(request, f'Não há diesel suficiente no tanque. Disponível: {tanque.nivel_atual if tanque else 0}L')
                return redirect('abastecer_veiculo')

            # Criar abastecimento
            # Se veiculo é um Equipamento, precisamos encontrar ou criar um Veiculo correspondente
            if isinstance(veiculo, Equipamento):
                print(f"DEBUG: Criando/encontrando Veiculo para Equipamento {veiculo.nome}")
                # Tentar encontrar um Veiculo com a mesma placa
                veiculo_obj, created = Veiculo.objects.get_or_create(
                    placa=veiculo.placa,
                    defaults={
                        'nome': veiculo.nome,
                        'tipo': veiculo.categoria,
                        'modelo': veiculo.modelo or '',
                        'ano': veiculo.ano,
                        'capacidade_tanque': veiculo.capacidade_tanque or 100,
                        'consumo_medio': veiculo.consumo_medio or 10,
                        'tem_agenda': veiculo.tem_agenda,
                        'ativo': veiculo.ativo,
                        'status': 'ATIVO' if veiculo.ativo else 'INATIVO'
                    }
                )
                if created:
                    print(f"DEBUG: Veiculo criado: {veiculo_obj.nome}")
                else:
                    print(f"DEBUG: Veiculo encontrado: {veiculo_obj.nome}")
                veiculo_para_abastecimento = veiculo_obj
            else:
                veiculo_para_abastecimento = veiculo

            abastecimento = AbastecimentoVeiculo.objects.create(
                veiculo=veiculo_para_abastecimento,
                cliente=cliente,
                quantidade_litros=quantidade,
                odometro_atual=int(odometro) if odometro else None,
                observacoes=observacoes,
                operador=request.user
            )

            cliente_info = f" - Cliente: {cliente.nome}" if cliente else ""
            messages.success(request, f'Abastecimento registrado com sucesso! {veiculo.nome} - {quantidade}L{cliente_info}')
            return redirect('dashboard_diesel')

        except Exception as e:
            messages.error(request, f'Erro ao registrar abastecimento: {str(e)}')

    # Usar Equipamento como fonte principal de veículos
    try:
        # Tentar usar equipamentos que são veículos (têm placa)
        # Incluir equipamentos ativos com placa, independente do status de serviço
        # (equipamentos fora de serviço podem precisar de combustível para manutenção)
        veiculos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').order_by('nome')

        # Se não houver equipamentos com placa, usar tabela Veiculo como fallback
        if not veiculos.exists():
            print("DEBUG: Nenhum equipamento com placa encontrado, usando tabela Veiculo")
            veiculos = Veiculo.objects.filter(ativo=True).order_by('nome')
        else:
            print(f"DEBUG: Encontrados {veiculos.count()} equipamentos com placa para abastecimento")
            # Log dos equipamentos encontrados
            for v in veiculos:
                status_servico = "Em Serviço" if v.em_servico else "Fora de Serviço"
                print(f"DEBUG: - {v.nome} ({v.placa}) - {status_servico}")

    except Exception as e:
        print(f"DEBUG: Erro ao acessar equipamentos, usando Veiculo como fallback: {e}")
        veiculos = Veiculo.objects.filter(ativo=True).order_by('nome')

    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    tanque = ConfiguracaoTanque.objects.first()

    context = {
        'veiculos': veiculos,
        'clientes': clientes,
        'tanque': tanque,
    }
    
    return render(request, 'diesel/abastecer.html', context)


@login_required
def historico_abastecimentos(request):
    """Histórico de abastecimentos com filtros"""
    if not verificar_permissao_diesel(request.user):
        messages.error(request, 'Você não tem permissão para acessar o controle de diesel.')
        return redirect('dashboard')

    # Filtros
    veiculo_id = request.GET.get('veiculo')
    cliente_id = request.GET.get('cliente')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    mes_ano = request.GET.get('mes_ano')

    # Query base
    abastecimentos = AbastecimentoVeiculo.objects.select_related(
        'veiculo', 'cliente', 'operador'
    ).order_by('-data_abastecimento')

    # Aplicar filtros
    if veiculo_id:
        abastecimentos = abastecimentos.filter(veiculo_id=veiculo_id)

    if cliente_id:
        abastecimentos = abastecimentos.filter(cliente_id=cliente_id)

    # Filtro por mês/ano tem prioridade sobre datas específicas
    if mes_ano:
        try:
            ano, mes = mes_ano.split('-')
            abastecimentos = abastecimentos.filter(
                data_abastecimento__year=int(ano),
                data_abastecimento__month=int(mes)
            )
        except ValueError:
            pass
    else:
        if data_inicio:
            abastecimentos = abastecimentos.filter(data_abastecimento__date__gte=data_inicio)

        if data_fim:
            abastecimentos = abastecimentos.filter(data_abastecimento__date__lte=data_fim)

    # Paginação (opcional - implementar depois se necessário)
    abastecimentos_list = abastecimentos[:100]  # Limitar a 100 registros por enquanto

    # Estatísticas dos filtros aplicados
    total_litros = abastecimentos.aggregate(total=Sum('quantidade_litros'))['total'] or 0
    total_abastecimentos = abastecimentos.count()
    media_litros = total_litros / total_abastecimentos if total_abastecimentos > 0 else 0

    # Custo estimado (assumindo R$ 6,00 por litro)
    preco_litro = Decimal('6.00')
    custo_estimado = total_litros * preco_litro

    # Verificar se é solicitação de exportação
    if request.GET.get('export') == 'excel':
        return exportar_historico_excel(abastecimentos, filtros={
            'veiculo_id': veiculo_id,
            'cliente_id': cliente_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'mes_ano': mes_ano,
        }, estatisticas={
            'total_litros': total_litros,
            'total_abastecimentos': total_abastecimentos,
            'media_litros': media_litros,
            'custo_estimado': custo_estimado,
        })

    # Dados para filtros - usar Equipamento como fonte principal
    try:
        # Tentar usar equipamentos que são veículos (têm placa)
        veiculos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').order_by('nome')

        # Se não houver equipamentos com placa, usar tabela Veiculo como fallback
        if not veiculos.exists():
            veiculos = Veiculo.objects.filter(ativo=True).order_by('nome')

    except Exception as e:
        print(f"DEBUG: Erro ao acessar equipamentos no histórico, usando Veiculo: {e}")
        veiculos = Veiculo.objects.filter(ativo=True).order_by('nome')

    clientes = Cliente.objects.filter(ativo=True).order_by('nome')

    context = {
        'abastecimentos': abastecimentos_list,
        'veiculos': veiculos,
        'clientes': clientes,
        'total_litros': total_litros,
        'total_abastecimentos': total_abastecimentos,
        'media_litros': media_litros,
        'custo_estimado': custo_estimado,
        'filtros': {
            'veiculo_id': veiculo_id,
            'cliente_id': cliente_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'mes_ano': mes_ano,
        }
    }

    return render(request, 'diesel/historico.html', context)


@login_required
def gerenciar_veiculos(request):
    """Gestão de veículos da frota"""
    if not verificar_permissao_diesel(request.user):
        messages.error(request, 'Você não tem permissão para acessar o controle de diesel.')
        return redirect('dashboard')

    # Temporariamente usando Veiculo até migração
    veiculos_raw = Veiculo.objects.prefetch_related('abastecimentos').order_by('nome')

    # Criar lista com informações extras para cada veículo
    veiculos = []
    for veiculo in veiculos_raw:
        # Criar dicionário com dados do veículo e informações extras
        veiculo_data = {
            'objeto': veiculo,
            'id': veiculo.id,
            'nome': veiculo.nome,
            'placa': veiculo.placa,
            'tipo': veiculo.tipo,
            'get_tipo_display': veiculo.get_tipo_display(),
            'modelo': veiculo.modelo,
            'ano': veiculo.ano,
            'capacidade_tanque': veiculo.capacidade_tanque,
            'consumo_medio': veiculo.consumo_medio,
            'status': veiculo.status,
            'tem_agenda': veiculo.tem_agenda,
            'ativo': veiculo.ativo,
            'abastecimentos': veiculo.abastecimentos,
        }

        # Status CSS class para badges
        if veiculo.status == 'ATIVO':
            veiculo_data['status_css_class'] = 'badge bg-success'
            veiculo_data['status_display'] = 'Ativo'
        elif veiculo.status == 'MANUTENCAO':
            veiculo_data['status_css_class'] = 'badge bg-warning text-dark'
            veiculo_data['status_display'] = 'Manutenção'
        else:
            veiculo_data['status_css_class'] = 'badge bg-danger'
            veiculo_data['status_display'] = 'Inativo'

        veiculos.append(veiculo_data)

    context = {
        'veiculos': veiculos,
    }

    return render(request, 'diesel/veiculos.html', context)


@login_required
def api_dados_tanque(request):
    """API para dados do tanque (para gráfico de ponteiro)"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    tanque = ConfiguracaoTanque.objects.first()
    if not tanque:
        return JsonResponse({'error': 'Configuração do tanque não encontrada'}, status=404)
    
    data = {
        'nivel_atual': float(tanque.nivel_atual),
        'capacidade_total': float(tanque.capacidade_total),
        'percentual': tanque.percentual_atual,
        'status': tanque.status_nivel,
        'nivel_alerta': float(tanque.nivel_alerta),
        'nivel_critico': float(tanque.nivel_critico),
    }
    
    return JsonResponse(data)


@login_required
def api_veiculos_mais_abastecidos(request):
    """API para gráfico de veículos mais abastecidos"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    # Período (últimos 30 dias por padrão)
    dias = int(request.GET.get('dias', 30))
    data_inicio = timezone.now().date() - timedelta(days=dias)
    
    dados = AbastecimentoVeiculo.objects.filter(
        data_abastecimento__date__gte=data_inicio
    ).values(
        'veiculo__nome'
    ).annotate(
        total_litros=Sum('quantidade_litros')
    ).order_by('-total_litros')[:10]
    
    return JsonResponse(list(dados), safe=False)


def exportar_historico_excel(abastecimentos, filtros, estatisticas):
    """Exportar histórico de abastecimentos para Excel"""
    # Criar workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Histórico de Abastecimentos"

    # Estilos
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")

    # Título
    ws.merge_cells('A1:I1')
    ws['A1'] = "RELATÓRIO DE ABASTECIMENTOS - CONTROLE DE DIESEL"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = center_alignment

    # Informações dos filtros
    row = 3
    if any(filtros.values()):
        ws[f'A{row}'] = "FILTROS APLICADOS:"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        if filtros['veiculo_id']:
            veiculo = Veiculo.objects.get(id=filtros['veiculo_id'])
            ws[f'A{row}'] = f"Veículo: {veiculo.nome} ({veiculo.placa})"
            row += 1

        if filtros['cliente_id']:
            cliente = Cliente.objects.get(id=filtros['cliente_id'])
            ws[f'A{row}'] = f"Cliente: {cliente.nome}"
            row += 1

        if filtros['mes_ano']:
            ws[f'A{row}'] = f"Período: {filtros['mes_ano']}"
            row += 1
        elif filtros['data_inicio'] or filtros['data_fim']:
            periodo = f"Período: {filtros['data_inicio'] or 'Início'} até {filtros['data_fim'] or 'Fim'}"
            ws[f'A{row}'] = periodo
            row += 1

    # Estatísticas
    row += 1
    ws[f'A{row}'] = "RESUMO:"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1

    ws[f'A{row}'] = f"Total de Abastecimentos: {estatisticas['total_abastecimentos']}"
    ws[f'D{row}'] = f"Total de Litros: {estatisticas['total_litros']:.2f}L"
    row += 1

    ws[f'A{row}'] = f"Média por Abastecimento: {estatisticas['media_litros']:.2f}L"
    ws[f'D{row}'] = f"Custo Estimado: R$ {estatisticas['custo_estimado']:.2f}"
    row += 2

    # Cabeçalhos da tabela
    headers = [
        'Data', 'Hora', 'Veículo', 'Placa', 'Tipo', 'Cliente',
        'Quantidade (L)', 'Odômetro (km)', 'Consumo (km/L)', 'Operador', 'Observações'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    # Dados
    for abastecimento in abastecimentos:
        row += 1
        data = [
            abastecimento.data_abastecimento.strftime('%d/%m/%Y'),
            abastecimento.data_abastecimento.strftime('%H:%M'),
            abastecimento.veiculo.nome,
            abastecimento.veiculo.placa,
            abastecimento.veiculo.get_tipo_display(),
            abastecimento.cliente.nome if abastecimento.cliente else '-',
            float(abastecimento.quantidade_litros),
            abastecimento.odometro_atual or '-',
            float(abastecimento.consumo_calculado) if abastecimento.consumo_calculado else '-',
            abastecimento.operador.get_full_name() or abastecimento.operador.username,
            abastecimento.observacoes or '-'
        ]

        for col, value in enumerate(data, 1):
            ws.cell(row=row, column=col, value=value)

    # Ajustar largura das colunas
    for col in range(1, len(headers) + 1):
        column_letter = get_column_letter(col)
        ws.column_dimensions[column_letter].width = 15

    # Preparar resposta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Nome do arquivo
    data_atual = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f'historico_abastecimentos_{data_atual}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Salvar workbook na resposta
    wb.save(response)
    return response


@login_required
def api_alterar_agenda_veiculo(request, veiculo_id):
    """API para alterar configuração de agenda do veículo"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        tem_agenda = data.get('tem_agenda', False)

        veiculo = get_object_or_404(Veiculo, id=veiculo_id)
        veiculo.tem_agenda = tem_agenda
        veiculo.save()

        return JsonResponse({
            'success': True,
            'message': f'Configuração de agenda atualizada para {veiculo.nome}',
            'tem_agenda': veiculo.tem_agenda
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao atualizar: {str(e)}'
        }, status=500)


@login_required
def api_alterar_status_veiculo(request, veiculo_id):
    """API para alterar status do veículo"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        status = data.get('status', 'ATIVO')

        veiculo = get_object_or_404(Veiculo, id=veiculo_id)
        veiculo.status = status
        veiculo.save()

        return JsonResponse({
            'success': True,
            'message': f'Status atualizado para {veiculo.nome}',
            'status': veiculo.status
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao atualizar: {str(e)}'
        }, status=500)


@login_required
def api_alterar_ativo_veiculo(request, veiculo_id):
    """API para alterar se veículo está ativo no sistema"""
    if not verificar_permissao_diesel(request.user):
        return JsonResponse({'success': False, 'error': 'Sem permissão'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        ativo = data.get('ativo', True)

        veiculo = get_object_or_404(Veiculo, id=veiculo_id)
        veiculo.ativo = ativo
        veiculo.save()

        return JsonResponse({
            'success': True,
            'message': f'Status ativo atualizado para {veiculo.nome}',
            'ativo': veiculo.ativo
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao atualizar: {str(e)}'
        }, status=500)


@login_required
def relatorio_compras_diesel(request):
    """Relatório de compras de diesel com gráfico por mês"""
    if not verificar_permissao_diesel(request.user):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard')

    from django.db.models.functions import TruncMonth
    import json

    # Filtros
    ano_atual = datetime.now().year
    ano_filtro = request.GET.get('ano', ano_atual)

    try:
        ano_filtro = int(ano_filtro)
    except (ValueError, TypeError):
        ano_filtro = ano_atual

    # Buscar compras do ano
    compras = AbastecimentoTanque.objects.filter(
        data_chegada__year=ano_filtro
    ).order_by('data_chegada')

    # Dados por mês
    compras_por_mes = compras.annotate(
        mes=TruncMonth('data_chegada')
    ).values('mes').annotate(
        total_valor=Sum('valor_total'),
        total_litros=Sum('quantidade_litros'),
        total_compras=Count('id')
    ).order_by('mes')

    # Preparar dados para o gráfico
    meses_nomes = [
        'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
    ]

    # Inicializar com zeros
    valores_por_mes = [0] * 12
    litros_por_mes = [0] * 12

    # Preencher com dados reais
    for compra in compras_por_mes:
        mes_index = compra['mes'].month - 1
        valores_por_mes[mes_index] = float(compra['total_valor'] or 0)
        litros_por_mes[mes_index] = float(compra['total_litros'] or 0)

    # Totalizadores
    total_geral_valor = sum(valores_por_mes)
    total_geral_litros = sum(litros_por_mes)
    total_compras_ano = compras.count()

    # Média mensal
    media_mensal = total_geral_valor / 12 if total_geral_valor > 0 else 0

    # Preço médio por litro
    preco_medio_litro = total_geral_valor / total_geral_litros if total_geral_litros > 0 else 0

    # Últimas compras
    ultimas_compras = compras.order_by('-data_chegada')[:10]

    # Anos disponíveis para filtro
    anos_disponiveis = AbastecimentoTanque.objects.dates('data_chegada', 'year').values_list('data_chegada__year', flat=True)

    context = {
        'ano_filtro': ano_filtro,
        'anos_disponiveis': sorted(set(anos_disponiveis), reverse=True),
        'meses_labels': json.dumps(meses_nomes),
        'valores_data': json.dumps(valores_por_mes),
        'litros_data': json.dumps(litros_por_mes),
        'total_geral_valor': total_geral_valor,
        'total_geral_litros': total_geral_litros,
        'total_compras_ano': total_compras_ano,
        'media_mensal': media_mensal,
        'preco_medio_litro': preco_medio_litro,
        'ultimas_compras': ultimas_compras,
    }

    return render(request, 'diesel/relatorio_compras.html', context)
