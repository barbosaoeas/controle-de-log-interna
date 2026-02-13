#!/usr/bin/env python
"""Script para adicionar tipos de veículos faltantes"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_log.settings')
django.setup()

from frota_locada.models import TipoVeiculo

# Tipos que devem existir
tipos_necessarios = [
    {
        'nome': 'PTA',
        'descricao': 'Plataforma de Trabalho Aéreo'
    },
    {
        'nome': 'Empilhadeira',
        'descricao': 'Empilhadeira para movimentação de cargas'
    },
    {
        'nome': 'Guindaste',
        'descricao': 'Guindaste para elevação de cargas pesadas'
    },
    {
        'nome': 'Caminhão',
        'descricao': 'Caminhão para transporte'
    },
    {
        'nome': 'Caminhão de Sucção',
        'descricao': 'Caminhão de sucção para limpeza'
    },
    {
        'nome': 'Pickup',
        'descricao': 'Veículo pickup para transporte leve'
    },
]

print("=" * 80)
print("ADICIONANDO TIPOS DE VEÍCULOS")
print("=" * 80)

for tipo_data in tipos_necessarios:
    tipo, created = TipoVeiculo.objects.get_or_create(
        nome=tipo_data['nome'],
        defaults={
            'descricao': tipo_data['descricao'],
            'ativo': True
        }
    )
    
    if created:
        print(f"✅ CRIADO: {tipo.nome}")
    else:
        print(f"ℹ️  JÁ EXISTE: {tipo.nome}")

print("\n" + "=" * 80)
print("TIPOS CADASTRADOS NO SISTEMA:")
print("=" * 80)
tipos = TipoVeiculo.objects.filter(ativo=True).order_by('nome')
for tipo in tipos:
    print(f"  - {tipo.nome}: {tipo.descricao}")

print("\n✅ Concluído!")

