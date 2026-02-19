#!/usr/bin/env python
"""
Script para criar áreas padrão do estaleiro
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Area

def criar_areas_estaleiro():
    """Criar áreas padrão do estaleiro"""
    print("=" * 70)
    print("🏭 CRIANDO ÁREAS PADRÃO DO ESTALEIRO")
    print("=" * 70)
    
    areas_padrao = [
        {
            'nome': 'Oficina Tubulação',
            'localizacao': 'Galpão 1',
            'descricao': 'Área destinada aos trabalhos de tubulação e soldagem de tubos'
        },
        {
            'nome': 'Oficina Elétrica',
            'localizacao': 'Galpão 2',
            'descricao': 'Área para serviços elétricos e instalações elétricas'
        },
        {
            'nome': 'Paiol de Tinta',
            'localizacao': 'Área Externa - Setor A',
            'descricao': 'Armazenamento de tintas, solventes e materiais de pintura'
        },
        {
            'nome': 'Oficina Mecânica',
            'localizacao': 'Galpão 1',
            'descricao': 'Área para manutenção mecânica e usinagem'
        },
        {
            'nome': 'Almoxarifado',
            'localizacao': 'Prédio Administrativo',
            'descricao': 'Estoque geral de materiais e ferramentas'
        },
        {
            'nome': 'Oficina Caldeiraria',
            'localizacao': 'Galpão 3',
            'descricao': 'Área para trabalhos de caldeiraria e estruturas metálicas'
        },
        {
            'nome': 'Área de Jateamento',
            'localizacao': 'Área Externa - Setor B',
            'descricao': 'Área para jateamento e preparação de superfícies'
        },
        {
            'nome': 'Oficina Hidráulica',
            'localizacao': 'Galpão 2',
            'descricao': 'Serviços hidráulicos e sistemas de fluidos'
        },
        {
            'nome': 'Doca Seca',
            'localizacao': 'Área Portuária',
            'descricao': 'Área de manutenção e reparo de embarcações'
        },
        {
            'nome': 'Pátio de Materiais',
            'localizacao': 'Área Externa - Setor C',
            'descricao': 'Armazenamento temporário de materiais pesados'
        },
    ]
    
    criadas = 0
    existentes = 0
    
    for area_data in areas_padrao:
        # Verificar se já existe
        if Area.objects.filter(nome__iexact=area_data['nome']).exists():
            print(f"⚠️  Área '{area_data['nome']}' já existe - pulando...")
            existentes += 1
            continue
        
        # Criar área
        area = Area.objects.create(**area_data)
        print(f"✅ Área criada: {area.nome} ({area.localizacao})")
        criadas += 1
    
    print("\n" + "=" * 70)
    print(f"📊 RESUMO:")
    print(f"   ✅ Áreas criadas: {criadas}")
    print(f"   ⚠️  Áreas já existentes: {existentes}")
    print(f"   📋 Total de áreas no sistema: {Area.objects.filter(ativa=True).count()}")
    print("=" * 70)
    
    if criadas > 0:
        print("\n🎉 Áreas criadas com sucesso!")
        print("💡 Acesse o sistema e vá em 'Gerenciar Áreas' para visualizar")
    else:
        print("\n✅ Todas as áreas já estavam cadastradas!")

if __name__ == '__main__':
    criar_areas_estaleiro()

