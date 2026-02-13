#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import AbastecimentoTanque, ConfiguracaoTanque
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

def criar_dados_exemplo():
    print("🚛 Criando dados de exemplo para relatório de compras...")
    
    # Obter usuário admin
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()
    
    if not user:
        print("❌ Nenhum usuário encontrado!")
        return
    
    # Obter tanque
    tanque = ConfiguracaoTanque.objects.first()
    
    # Dados de exemplo para 2024
    dados_exemplo = [
        {'mes': 1, 'litros': 8000, 'preco': 5.85},
        {'mes': 2, 'litros': 6500, 'preco': 5.92},
        {'mes': 3, 'litros': 7200, 'preco': 6.05},
        {'mes': 4, 'litros': 5800, 'preco': 6.12},
        {'mes': 5, 'litros': 9200, 'preco': 6.08},
        {'mes': 6, 'litros': 7800, 'preco': 6.15},
        {'mes': 7, 'litros': 8500, 'preco': 6.22},
        {'mes': 8, 'litros': 7100, 'preco': 6.18},
        {'mes': 9, 'litros': 8800, 'preco': 6.25},
        {'mes': 10, 'litros': 9500, 'preco': 6.30},
    ]
    
    fornecedores = ['Petrobras Distribuidora', 'Shell Brasil', 'Ipiranga', 'Raízen']
    
    for dados in dados_exemplo:
        # Verificar se já existe dados para este mês
        if AbastecimentoTanque.objects.filter(
            data_chegada__month=dados['mes'], 
            data_chegada__year=2024
        ).exists():
            print(f"⚠️  Dados já existem para {dados['mes']}/2024")
            continue
        
        # Data aleatória no mês
        dia = random.randint(1, 28)
        hora = random.randint(8, 17)
        minuto = random.randint(0, 59)
        
        data_chegada = timezone.make_aware(
            datetime(2024, dados['mes'], dia, hora, minuto)
        )
        
        # Nível anterior (simulado)
        nivel_anterior = Decimal(str(random.randint(3000, 8000)))
        quantidade = Decimal(str(dados['litros']))
        valor_por_litro = Decimal(str(dados['preco']))
        valor_total = quantidade * valor_por_litro
        nivel_posterior = nivel_anterior + quantidade
        
        # Criar registro
        abastecimento = AbastecimentoTanque.objects.create(
            quantidade_litros=quantidade,
            valor_por_litro=valor_por_litro,
            valor_total=valor_total,
            data_chegada=data_chegada,
            fornecedor=random.choice(fornecedores),
            numero_nota_fiscal=f'NF-{random.randint(100000, 999999)}',
            observacoes='Dados de exemplo para demonstração do relatório',
            operador=user,
            nivel_anterior=nivel_anterior,
            nivel_posterior=nivel_posterior
        )
        
        print(f"✅ Criado: {dados['mes']:02d}/2024 - {dados['litros']:,}L - R$ {dados['preco']:.2f}/L - Total: R$ {valor_total:,.2f}")
    
    # Estatísticas finais
    total_compras = AbastecimentoTanque.objects.filter(data_chegada__year=2024).count()
    total_valor = sum(d['litros'] * d['preco'] for d in dados_exemplo)
    total_litros = sum(d['litros'] for d in dados_exemplo)
    
    print("\n📊 RESUMO DOS DADOS CRIADOS:")
    print(f"   Total de compras: {total_compras}")
    print(f"   Total de litros: {total_litros:,}L")
    print(f"   Total gasto: R$ {total_valor:,.2f}")
    print(f"   Preço médio: R$ {total_valor/total_litros:.3f}/L")
    print("\n🎉 Dados de exemplo criados com sucesso!")
    print("   Acesse: http://127.0.0.1:8000/diesel/relatorio-compras/")

if __name__ == '__main__':
    criar_dados_exemplo()
