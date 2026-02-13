from django.core.management.base import BaseCommand
from frota_locada.models import TipoVeiculo, Fornecedor, TipoManutencao


class Command(BaseCommand):
    help = 'Cria dados iniciais para o sistema de frota locada'

    def handle(self, *args, **options):
        self.stdout.write('Criando dados iniciais para Frota Locada...')

        # Criar tipos de veículos
        tipos_veiculo = [
            {'nome': 'Caminhão', 'descricao': 'Veículos de carga pesada'},
            {'nome': 'Van', 'descricao': 'Veículos para transporte de pessoas e cargas leves'},
            {'nome': 'Carro', 'descricao': 'Veículos de passeio'},
            {'nome': 'Pickup', 'descricao': 'Veículos utilitários com caçamba'},
            {'nome': 'Ônibus', 'descricao': 'Veículos para transporte coletivo'},
        ]

        for tipo_data in tipos_veiculo:
            tipo, created = TipoVeiculo.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✅ Tipo de veículo criado: {tipo.nome}')
            else:
                self.stdout.write(f'⚠️  Tipo de veículo já existe: {tipo.nome}')

        # Criar fornecedores exemplo
        fornecedores = [
            {
                'nome': 'Locadora Exemplo LTDA',
                'cnpj': '12.345.678/0001-90',
                'telefone': '(11) 99999-9999',
                'email': 'contato@locadoraexemplo.com.br',
                'endereco': 'Rua das Flores, 123 - Centro - São Paulo/SP',
                'contato_responsavel': 'João Silva'
            },
            {
                'nome': 'Frota Fácil Locações',
                'cnpj': '98.765.432/0001-10',
                'telefone': '(21) 88888-8888',
                'email': 'vendas@frotafacil.com.br',
                'endereco': 'Av. Principal, 456 - Zona Sul - Rio de Janeiro/RJ',
                'contato_responsavel': 'Maria Santos'
            }
        ]

        for fornecedor_data in fornecedores:
            fornecedor, created = Fornecedor.objects.get_or_create(
                cnpj=fornecedor_data['cnpj'],
                defaults={
                    'nome': fornecedor_data['nome'],
                    'telefone': fornecedor_data['telefone'],
                    'email': fornecedor_data['email'],
                    'endereco': fornecedor_data['endereco'],
                    'contato_responsavel': fornecedor_data['contato_responsavel'],
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✅ Fornecedor criado: {fornecedor.nome}')
            else:
                self.stdout.write(f'⚠️  Fornecedor já existe: {fornecedor.nome}')

        # Criar tipos de manutenção
        tipos_manutencao = [
            {'nome': 'Preventiva', 'descricao': 'Manutenção preventiva programada'},
            {'nome': 'Corretiva', 'descricao': 'Manutenção para correção de problemas'},
            {'nome': 'Revisão', 'descricao': 'Revisão geral do veículo'},
            {'nome': 'Troca de Óleo', 'descricao': 'Troca de óleo e filtros'},
            {'nome': 'Pneus', 'descricao': 'Serviços relacionados a pneus'},
        ]

        for tipo_data in tipos_manutencao:
            tipo, created = TipoManutencao.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✅ Tipo de manutenção criado: {tipo.nome}')
            else:
                self.stdout.write(f'⚠️  Tipo de manutenção já existe: {tipo.nome}')

        self.stdout.write(
            self.style.SUCCESS('🎉 Dados iniciais criados com sucesso!')
        )
        self.stdout.write('Agora você pode cadastrar veículos no sistema.')
