#!/usr/bin/env python
"""
Script para criar abastecimentos com clientes
"""
import os
import django
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Cliente, Veiculo, AbastecimentoVeiculo
from django.contrib.auth.models import User
from django.utils import timezone

def criar_abastecimentos_com_clientes():
    # Obter dados
    admin_user = User.objects.first()
    if not admin_user:
        print("❌ Nenhum usuário encontrado!")
        return

    clientes = list(Cliente.objects.all()[:4])
    veiculos = list(Veiculo.objects.all())
    
    if not clientes:
        print("❌ Nenhum cliente encontrado!")
        return
        
    if not veiculos:
        print("❌ Nenhum veículo encontrado!")
        return

    print(f"📊 Dados disponíveis:")
    print(f"   Clientes: {len(clientes)}")
    print(f"   Veículos: {len(veiculos)}")

    # Criar abastecimentos com clientes
    abastecimentos_com_cliente = [
        {'veiculo': veiculos[0], 'cliente': clientes[0], 'litros': 280, 'dias_atras': 7},
        {'veiculo': veiculos[1], 'cliente': clientes[1], 'litros': 320, 'dias_atras': 6},
        {'veiculo': veiculos[2], 'cliente': clientes[0], 'litros': 140, 'dias_atras': 5},
    ]
    
    # Adicionar mais se houver veículos e clientes suficientes
    if len(veiculos) > 3 and len(clientes) > 2:
        abastecimentos_com_cliente.extend([
            {'veiculo': veiculos[3], 'cliente': clientes[2], 'litros': 190, 'dias_atras': 4},
            {'veiculo': veiculos[0], 'cliente': clientes[1], 'litros': 260, 'dias_atras': 3},
        ])
    
    if len(clientes) > 3:
        abastecimentos_com_cliente.append(
            {'veiculo': veiculos[1], 'cliente': clientes[3], 'litros': 340, 'dias_atras': 2}
        )

    for dados in abastecimentos_com_cliente:
        data_abastecimento = timezone.now() - timedelta(days=dados['dias_atras'])
        
        # Verificar se já existe
        existe = AbastecimentoVeiculo.objects.filter(
            veiculo=dados['veiculo'],
            cliente=dados['cliente'],
            data_abastecimento__date=data_abastecimento.date()
        ).exists()
        
        if not existe:
            abastecimento = AbastecimentoVeiculo.objects.create(
                veiculo=dados['veiculo'],
                cliente=dados['cliente'],
                quantidade_litros=dados['litros'],
                data_abastecimento=data_abastecimento,
                operador=admin_user,
                observacoes=f'Abastecimento para {dados["cliente"].nome}'
            )
            print(f'✅ Abastecimento criado: {dados["veiculo"].nome} - {dados["cliente"].nome} - {dados["litros"]}L')
        else:
            print(f'ℹ️ Abastecimento já existe para {dados["veiculo"].nome} - {dados["cliente"].nome}')

    print(f'\n📊 Estatísticas finais:')
    print(f'   Total de abastecimentos: {AbastecimentoVeiculo.objects.count()}')
    print(f'   Abastecimentos com cliente: {AbastecimentoVeiculo.objects.filter(cliente__isnull=False).count()}')
    print(f'   Abastecimentos sem cliente: {AbastecimentoVeiculo.objects.filter(cliente__isnull=True).count()}')

if __name__ == '__main__':
    criar_abastecimentos_com_clientes()
