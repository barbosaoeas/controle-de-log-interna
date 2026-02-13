from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Setor, Area, Cliente, Equipamento, PerfilUsuario, Pedido


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais'

    def handle(self, *args, **options):
        self.stdout.write('Criando dados iniciais...')

        # Criar setores
        setores_data = [
            {'nome': 'Produção', 'descricao': 'Setor de produção naval', 'responsavel': 'João Silva'},
            {'nome': 'Manutenção', 'descricao': 'Setor de manutenção de equipamentos', 'responsavel': 'Maria Santos'},
            {'nome': 'Soldagem', 'descricao': 'Setor de soldagem e estruturas', 'responsavel': 'Pedro Costa'},
            {'nome': 'Pintura', 'descricao': 'Setor de pintura e acabamento', 'responsavel': 'Ana Oliveira'},
            {'nome': 'Transportes', 'descricao': 'Setor de logística e transportes', 'responsavel': 'Carlos Lima'},
        ]

        for setor_data in setores_data:
            setor, created = Setor.objects.get_or_create(
                nome=setor_data['nome'],
                defaults=setor_data
            )
            if created:
                self.stdout.write(f'Setor criado: {setor.nome}')

        # Criar áreas
        areas_data = [
            {'nome': 'Doca 1', 'descricao': 'Primeira doca de construção', 'localizacao': 'Área Norte'},
            {'nome': 'Doca 2', 'descricao': 'Segunda doca de construção', 'localizacao': 'Área Norte'},
            {'nome': 'Oficina Mecânica', 'descricao': 'Oficina de manutenção mecânica', 'localizacao': 'Área Central'},
            {'nome': 'Almoxarifado Central', 'descricao': 'Depósito principal de materiais', 'localizacao': 'Área Sul'},
            {'nome': 'Pátio de Materiais', 'descricao': 'Área externa para materiais pesados', 'localizacao': 'Área Externa'},
        ]

        for area_data in areas_data:
            area, created = Area.objects.get_or_create(
                nome=area_data['nome'],
                defaults=area_data
            )
            if created:
                self.stdout.write(f'Área criada: {area.nome}')

        # Criar clientes
        clientes_data = [
            {'nome': 'Petrobras', 'documento': '33.000.167/0001-01', 'telefone': '(21) 3224-1234', 'email': 'contato@petrobras.com.br'},
            {'nome': 'Vale S.A.', 'documento': '33.592.510/0001-54', 'telefone': '(21) 3814-4477', 'email': 'suprimentos@vale.com'},
            {'nome': 'Transpetro', 'documento': '02.372.577/0001-93', 'telefone': '(21) 3224-9876', 'email': 'logistica@transpetro.com.br'},
        ]

        for cliente_data in clientes_data:
            cliente, created = Cliente.objects.get_or_create(
                nome=cliente_data['nome'],
                defaults=cliente_data
            )
            if created:
                self.stdout.write(f'Cliente criado: {cliente.nome}')

        # Criar equipamentos
        equipamentos_data = [
            {'nome': 'Chapa de Aço Naval', 'codigo': 'CAN-001', 'categoria': 'MATERIAL', 'descricao': 'Chapa de aço para construção naval'},
            {'nome': 'Solda Eletrodo E7018', 'codigo': 'SOL-E7018', 'categoria': 'CONSUMIVEL', 'descricao': 'Eletrodo para soldagem estrutural'},
            {'nome': 'Furadeira Industrial', 'codigo': 'FUR-001', 'categoria': 'FERRAMENTA', 'descricao': 'Furadeira para trabalhos pesados'},
            {'nome': 'Guindaste 50T', 'codigo': 'GUI-50T', 'categoria': 'EQUIPAMENTO', 'descricao': 'Guindaste para movimentação de cargas'},
            {'nome': 'Tinta Anticorrosiva', 'codigo': 'TIN-AC001', 'categoria': 'MATERIAL', 'descricao': 'Tinta para proteção anticorrosiva'},
        ]

        for equip_data in equipamentos_data:
            equipamento, created = Equipamento.objects.get_or_create(
                codigo=equip_data['codigo'],
                defaults=equip_data
            )
            if created:
                self.stdout.write(f'Equipamento criado: {equipamento.nome}')

        # Criar usuários de exemplo
        usuarios_data = [
            {'username': 'producao1', 'email': 'producao1@estaleiro.com', 'first_name': 'José', 'last_name': 'Ferreira', 'setor': 'Produção', 'perfil': 'DEMANDANTE'},
            {'username': 'manutencao1', 'email': 'manutencao1@estaleiro.com', 'first_name': 'Roberto', 'last_name': 'Alves', 'setor': 'Manutenção', 'perfil': 'DEMANDANTE'},
            {'username': 'transportes1', 'email': 'transportes1@estaleiro.com', 'first_name': 'Marcos', 'last_name': 'Silva', 'setor': 'Transportes', 'perfil': 'TRANSPORTES'},
        ]

        for user_data in usuarios_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            if created:
                user.set_password('123456')
                user.save()
                
                setor = Setor.objects.get(nome=user_data['setor'])
                PerfilUsuario.objects.create(
                    user=user,
                    setor=setor,
                    perfil=user_data['perfil']
                )
                self.stdout.write(f'Usuário criado: {user.username}')

        self.stdout.write(self.style.SUCCESS('Dados iniciais criados com sucesso!'))
