"""
Comando para criar empresas de exemplo no sistema
"""
from django.core.management.base import BaseCommand
from core.models import Empresa


class Command(BaseCommand):
    help = 'Cria empresas de exemplo no sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏢 Criando empresas de exemplo...'))

        empresas_exemplo = [
            {
                'nome': 'Estaleiro Atlântico Sul',
                'cnpj': '00.000.000/0001-00',
                'tipo': 'PROPRIA',
                'contato': 'Administração',
                'telefone': '(00) 0000-0000',
                'email': 'contato@estaleiro.com.br',
                'observacoes': 'Empresa própria - Estaleiro Atlântico Sul',
            },
            {
                'nome': 'Lokar Locações',
                'cnpj': '11.111.111/0001-11',
                'contrato': 'CONT-2024-001',
                'tipo': 'TERCEIRIZADA',
                'contato': 'João Silva',
                'telefone': '(11) 1111-1111',
                'email': 'contato@lokar.com.br',
                'observacoes': 'Empresa terceirizada - Locação de equipamentos',
            },
            {
                'nome': 'TechServ Manutenção',
                'cnpj': '22.222.222/0001-22',
                'contrato': 'CONT-2024-002',
                'tipo': 'TERCEIRIZADA',
                'contato': 'Maria Santos',
                'telefone': '(22) 2222-2222',
                'email': 'contato@techserv.com.br',
                'observacoes': 'Empresa terceirizada - Serviços de manutenção',
            },
            {
                'nome': 'LogTrans Transportes',
                'cnpj': '33.333.333/0001-33',
                'contrato': 'CONT-2024-003',
                'tipo': 'TERCEIRIZADA',
                'contato': 'Pedro Oliveira',
                'telefone': '(33) 3333-3333',
                'email': 'contato@logtrans.com.br',
                'observacoes': 'Empresa terceirizada - Serviços de transporte',
            },
        ]

        criadas = 0
        atualizadas = 0

        for empresa_data in empresas_exemplo:
            empresa, created = Empresa.objects.update_or_create(
                nome=empresa_data['nome'],
                defaults=empresa_data
            )
            
            if created:
                criadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Criada: {empresa.nome}'))
            else:
                atualizadas += 1
                self.stdout.write(self.style.WARNING(f'  ⚠️  Atualizada: {empresa.nome}'))

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Processo concluído!'))
        self.stdout.write(self.style.SUCCESS(f'   📊 {criadas} empresas criadas'))
        self.stdout.write(self.style.SUCCESS(f'   📊 {atualizadas} empresas atualizadas'))

