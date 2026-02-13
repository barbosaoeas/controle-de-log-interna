#!/usr/bin/env python
"""
Script para criar abastecimentos de teste
"""
import os
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Veiculo, AbastecimentoVeiculo, ConfiguracaoTanque
from django.contrib.auth.models import User
from django.utils import timezone

def criar_abastecimentos_teste():
    # Obter usuário admin para os abastecimentos
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()

    if not admin_user:
        print("❌ Nenhum usuário encontrado!")
        return

    # Obter veículos
    veiculos = list(Veiculo.objects.all())
    if not veiculos:
        print("❌ Nenhum veículo encontrado!")
        return

    tanque = ConfiguracaoTanque.objects.first()
    if not tanque:
        print("❌ Configuração do tanque não encontrada!")
        return

    print(f'📊 Situação inicial:')
    print(f'   Tanque: {tanque.nivel_atual}L')
    print(f'   Veículos: {len(veiculos)}')

    # Criar alguns abastecimentos de exemplo
    abastecimentos_exemplo = [
        {'veiculo': veiculos[0], 'litros': 250, 'odometro': 125000, 'dias_atras': 5},
        {'veiculo': veiculos[1], 'litros': 350, 'odometro': 89000, 'dias_atras': 4},
        {'veiculo': veiculos[0], 'litros': 200, 'odometro': 125800, 'dias_atras': 3},
        {'veiculo': veiculos[2], 'litros': 120, 'odometro': 45000, 'dias_atras': 2},
    ]

    # Adicionar mais veículos se disponíveis
    if len(veiculos) > 3:
        abastecimentos_exemplo.extend([
            {'veiculo': veiculos[3], 'litros': 180, 'odometro': 67000, 'dias_atras': 1},
            {'veiculo': veiculos[1], 'litros': 300, 'odometro': 89500, 'dias_atras': 0},
        ])

    for dados in abastecimentos_exemplo:
        data_abastecimento = timezone.now() - timedelta(days=dados['dias_atras'])
        
        # Verificar se já existe abastecimento similar
        existe = AbastecimentoVeiculo.objects.filter(
            veiculo=dados['veiculo'],
            data_abastecimento__date=data_abastecimento.date()
        ).exists()
        
        if not existe:
            abastecimento = AbastecimentoVeiculo.objects.create(
                veiculo=dados['veiculo'],
                quantidade_litros=dados['litros'],
                odometro_atual=dados['odometro'],
                data_abastecimento=data_abastecimento,
                operador=admin_user,
                observacoes=f'Abastecimento de teste - {dados["dias_atras"]} dias atrás'
            )
            
            print(f'✅ Abastecimento criado: {dados["veiculo"].nome} - {dados["litros"]}L')
        else:
            print(f'ℹ️ Abastecimento já existe: {dados["veiculo"].nome} - {data_abastecimento.date()}')

    # Verificar situação final
    tanque.refresh_from_db()
    total_abastecimentos = AbastecimentoVeiculo.objects.count()

    print(f'\n📊 Situação final:')
    print(f'   Tanque: {tanque.nivel_atual}L')
    print(f'   Total de abastecimentos: {total_abastecimentos}')
    print(f'   Status do tanque: {tanque.status_nivel}')

if __name__ == '__main__':
    criar_abastecimentos_teste()
