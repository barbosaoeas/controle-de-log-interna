from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Setor, Area, Cliente, Equipamento, Pedido, HistoricoPedido
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Cria pedidos de exemplo para demonstração'

    def handle(self, *args, **options):
        self.stdout.write('Criando pedidos de exemplo...')

        # Buscar dados necessários
        try:
            setor_producao = Setor.objects.get(nome='Produção')
            setor_manutencao = Setor.objects.get(nome='Manutenção')
            setor_soldagem = Setor.objects.get(nome='Soldagem')
            
            user_producao = User.objects.get(username='producao1')
            user_manutencao = User.objects.get(username='manutencao1')
            
            area_doca1 = Area.objects.get(nome='Doca 1')
            area_doca2 = Area.objects.get(nome='Doca 2')
            area_almoxarifado = Area.objects.get(nome='Almoxarifado Central')
            area_oficina = Area.objects.get(nome='Oficina Mecânica')
            
            cliente_petrobras = Cliente.objects.get(nome='Petrobras')
            cliente_vale = Cliente.objects.get(nome='Vale S.A.')
            
            equip_chapa = Equipamento.objects.get(codigo='CAN-001')
            equip_solda = Equipamento.objects.get(codigo='SOL-E7018')
            equip_furadeira = Equipamento.objects.get(codigo='FUR-001')
            equip_tinta = Equipamento.objects.get(codigo='TIN-AC001')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao buscar dados: {e}'))
            return

        # Lista de pedidos de exemplo
        pedidos_exemplo = [
            {
                'setor_solicitante': setor_producao,
                'criado_por': user_producao,
                'tipo_pedido': 'ENTREGA',
                'descricao': 'Transporte de chapas de aço naval para a Doca 1 - Projeto Navio Petroleiro',
                'quantidade': 15,
                'unidade_medida': 'UN',
                'prioridade': 'ALTA',
                'equipamento': equip_chapa,
                'area_origem': area_almoxarifado,
                'area_destino': area_doca1,
                'cliente': cliente_petrobras,
                'observacoes': 'Cuidado especial no transporte. Chapas de 12mm de espessura.',
                'status': 'PENDENTE'
            },
            {
                'setor_solicitante': setor_soldagem,
                'criado_por': user_producao,
                'tipo_pedido': 'RECOLHIMENTO',
                'descricao': 'Recolher eletrodos de solda usados e restos de material da Doca 2',
                'quantidade': 50,
                'unidade_medida': 'KG',
                'prioridade': 'MEDIA',
                'equipamento': equip_solda,
                'area_origem': area_doca2,
                'area_destino': area_almoxarifado,
                'observacoes': 'Material para reciclagem. Separar por tipo de eletrodo.',
                'status': 'EM_ANDAMENTO'
            },
            {
                'setor_solicitante': setor_manutencao,
                'criado_por': user_manutencao,
                'tipo_pedido': 'ENTREGA',
                'descricao': 'Transporte de furadeira industrial para manutenção na oficina',
                'quantidade': 1,
                'unidade_medida': 'UN',
                'prioridade': 'URGENTE',
                'equipamento': equip_furadeira,
                'area_origem': area_doca1,
                'area_destino': area_oficina,
                'observacoes': 'URGENTE: Equipamento com defeito, produção parada aguardando reparo.',
                'status': 'PENDENTE'
            },
            {
                'setor_solicitante': setor_producao,
                'criado_por': user_producao,
                'tipo_pedido': 'ENTREGA',
                'descricao': 'Entrega de tinta anticorrosiva para acabamento do casco',
                'quantidade': 200,
                'unidade_medida': 'L',
                'prioridade': 'MEDIA',
                'equipamento': equip_tinta,
                'area_origem': area_almoxarifado,
                'area_destino': area_doca2,
                'cliente': cliente_vale,
                'observacoes': 'Tinta especial para ambiente marinho. Verificar validade.',
                'status': 'CONCLUIDO'
            },
            {
                'setor_solicitante': setor_manutencao,
                'criado_por': user_manutencao,
                'tipo_pedido': 'RECOLHIMENTO',
                'descricao': 'Recolher ferramentas e equipamentos após manutenção preventiva',
                'quantidade': 1,
                'unidade_medida': 'CX',
                'prioridade': 'BAIXA',
                'area_origem': area_doca1,
                'area_destino': area_oficina,
                'observacoes': 'Caixa com ferramentas diversas. Conferir inventário.',
                'status': 'PENDENTE'
            },
            {
                'setor_solicitante': setor_soldagem,
                'criado_por': user_producao,
                'tipo_pedido': 'ENTREGA',
                'descricao': 'Transporte de estruturas metálicas soldadas para montagem',
                'quantidade': 8,
                'unidade_medida': 'PC',
                'prioridade': 'ALTA',
                'area_origem': area_oficina,
                'area_destino': area_doca1,
                'cliente': cliente_petrobras,
                'observacoes': 'Estruturas pesadas, usar guindaste. Cuidado com soldas recentes.',
                'status': 'PENDENTE'
            }
        ]

        # Criar os pedidos
        for i, pedido_data in enumerate(pedidos_exemplo):
            # Ajustar data de solicitação para simular pedidos em diferentes momentos
            data_base = timezone.now() - timezone.timedelta(days=random.randint(0, 7))
            
            pedido = Pedido.objects.create(
                setor_solicitante=pedido_data['setor_solicitante'],
                criado_por=pedido_data['criado_por'],
                tipo_pedido=pedido_data['tipo_pedido'],
                descricao=pedido_data['descricao'],
                quantidade=pedido_data['quantidade'],
                unidade_medida=pedido_data['unidade_medida'],
                prioridade=pedido_data['prioridade'],
                equipamento=pedido_data.get('equipamento'),
                area_origem=pedido_data.get('area_origem'),
                area_destino=pedido_data.get('area_destino'),
                cliente=pedido_data.get('cliente'),
                observacoes=pedido_data['observacoes'],
                status=pedido_data['status'],
                ordem_manual=i
            )
            
            # Ajustar data de solicitação
            pedido.data_solicitacao = data_base
            
            # Ajustar datas baseado no status
            if pedido_data['status'] == 'EM_ANDAMENTO':
                pedido.data_inicio = data_base + timezone.timedelta(hours=random.randint(1, 24))
            elif pedido_data['status'] == 'CONCLUIDO':
                pedido.data_inicio = data_base + timezone.timedelta(hours=random.randint(1, 12))
                pedido.data_conclusao = pedido.data_inicio + timezone.timedelta(hours=random.randint(1, 8))
            
            pedido.save()
            
            # Criar histórico inicial
            HistoricoPedido.objects.create(
                pedido=pedido,
                status_novo='PENDENTE',
                observacao='Pedido criado',
                usuario=pedido_data['criado_por'],
                data_alteracao=data_base
            )
            
            # Criar histórico adicional para pedidos em andamento ou concluídos
            if pedido_data['status'] == 'EM_ANDAMENTO':
                HistoricoPedido.objects.create(
                    pedido=pedido,
                    status_anterior='PENDENTE',
                    status_novo='EM_ANDAMENTO',
                    observacao='Pedido iniciado pelo setor de transportes',
                    usuario=User.objects.get(username='transportes1'),
                    data_alteracao=pedido.data_inicio
                )
            elif pedido_data['status'] == 'CONCLUIDO':
                # Histórico de início
                HistoricoPedido.objects.create(
                    pedido=pedido,
                    status_anterior='PENDENTE',
                    status_novo='EM_ANDAMENTO',
                    observacao='Pedido iniciado pelo setor de transportes',
                    usuario=User.objects.get(username='transportes1'),
                    data_alteracao=pedido.data_inicio
                )
                # Histórico de conclusão
                HistoricoPedido.objects.create(
                    pedido=pedido,
                    status_anterior='EM_ANDAMENTO',
                    status_novo='CONCLUIDO',
                    observacao='Pedido concluído com sucesso',
                    usuario=User.objects.get(username='transportes1'),
                    data_alteracao=pedido.data_conclusao
                )
            
            self.stdout.write(f'Pedido #{pedido.id} criado: {pedido.descricao[:50]}...')

        self.stdout.write(self.style.SUCCESS(f'{len(pedidos_exemplo)} pedidos de exemplo criados com sucesso!'))
