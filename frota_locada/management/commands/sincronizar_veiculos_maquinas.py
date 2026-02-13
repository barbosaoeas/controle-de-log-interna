from django.core.management.base import BaseCommand
from frota_locada.models import VeiculoLocado, Maquina, Fornecedor


class Command(BaseCommand):
    help = 'Sincroniza veículos locados ativos com máquinas para chamados de manutenção'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria feito sem executar as alterações',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita'))
        
        # Buscar veículos locados ativos
        veiculos_ativos = VeiculoLocado.objects.filter(status='ATIVO')
        
        self.stdout.write(f'Encontrados {veiculos_ativos.count()} veículos locados ativos')
        
        criados = 0
        atualizados = 0
        
        for veiculo in veiculos_ativos:
            # Verificar se já existe máquina com este código
            maquina, created = Maquina.objects.get_or_create(
                codigo=veiculo.placa,
                defaults={
                    'nome': f'{veiculo.modelo} - {veiculo.marca.nome}',
                    'tipo': self.mapear_tipo_veiculo(veiculo.tipo_veiculo.nome),
                    'localizacao': 'Campo/Operação',
                    'marca': veiculo.marca.nome,
                    'modelo': veiculo.modelo,
                    'ano_fabricacao': veiculo.ano_fabricacao,
                    'fornecedor': veiculo.fornecedor,
                    'ativo': True,
                    'observacoes': f'Sincronizado automaticamente do veículo locado {veiculo.placa}'
                }
            )
            
            if not dry_run:
                if created:
                    criados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Criada máquina: {maquina.codigo} - {maquina.nome}')
                    )
                else:
                    # Atualizar informações se necessário
                    atualizado = False
                    if not maquina.ativo:
                        maquina.ativo = True
                        atualizado = True
                    if maquina.fornecedor != veiculo.fornecedor:
                        maquina.fornecedor = veiculo.fornecedor
                        atualizado = True
                    
                    if atualizado:
                        maquina.save()
                        atualizados += 1
                        self.stdout.write(
                            self.style.WARNING(f'↻ Atualizada máquina: {maquina.codigo} - {maquina.nome}')
                        )
                    else:
                        self.stdout.write(f'- Máquina já existe: {maquina.codigo} - {maquina.nome}')
            else:
                if created:
                    self.stdout.write(f'[DRY-RUN] Criaria máquina: {veiculo.placa} - {veiculo.modelo}')
                else:
                    self.stdout.write(f'[DRY-RUN] Máquina já existe: {veiculo.placa}')
        
        # Desativar máquinas de veículos que não estão mais ativos
        if not dry_run:
            placas_ativas = list(veiculos_ativos.values_list('placa', flat=True))
            maquinas_desativadas = Maquina.objects.filter(
                ativo=True,
                observacoes__contains='Sincronizado automaticamente'
            ).exclude(codigo__in=placas_ativas)
            
            desativados = maquinas_desativadas.count()
            if desativados > 0:
                maquinas_desativadas.update(ativo=False)
                self.stdout.write(
                    self.style.WARNING(f'✗ Desativadas {desativados} máquinas de veículos não ativos')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nResumo: {criados} criadas, {atualizados} atualizadas'
            )
        )

    def mapear_tipo_veiculo(self, tipo_nome):
        """Mapeia tipos de veículo para tipos de máquina"""
        mapeamento = {
            'PTA': 'PONTE_ROLANTE',
            'EMPILHADEIRA': 'EMPILHADEIRA',
            'GUINDASTE': 'GUINDASTE',
            'COMPRESSOR': 'COMPRESSOR',
            'GERADOR': 'GERADOR',
            'SOLDA': 'SOLDA',
        }
        
        tipo_upper = tipo_nome.upper()
        for key, value in mapeamento.items():
            if key in tipo_upper:
                return value
        
        return 'OUTROS'
