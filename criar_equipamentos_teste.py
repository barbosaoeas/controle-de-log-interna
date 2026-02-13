#!/usr/bin/env python
"""
Script para criar equipamentos de teste com placas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento, Veiculo

def criar_equipamentos_teste():
    print("🚗 CRIANDO EQUIPAMENTOS DE TESTE COM PLACAS...")
    
    try:
        # Verificar se já existem equipamentos com placa
        equipamentos_com_placa = Equipamento.objects.exclude(placa='').exclude(placa__isnull=True)
        if equipamentos_com_placa.exists():
            print(f"✅ Já existem {equipamentos_com_placa.count()} equipamentos com placa")
            for eq in equipamentos_com_placa:
                print(f"  - {eq.nome} ({eq.placa})")
            return True
        
        # Buscar veículos existentes para usar como base
        veiculos = Veiculo.objects.filter(ativo=True)[:3]  # Pegar apenas 3 para teste
        
        if not veiculos.exists():
            print("⚠️ Nenhum veículo encontrado para usar como base")
            # Criar equipamentos de teste manualmente
            equipamentos_teste = [
                {
                    'nome': 'Caminhão Teste 1',
                    'placa': 'ABC1234',
                    'categoria': 'CAMINHAO',
                    'modelo': 'Mercedes-Benz',
                    'ano': 2020,
                    'capacidade_tanque': 200.0,
                    'consumo_medio': 8.5,
                },
                {
                    'nome': 'Trator Teste 2', 
                    'placa': 'DEF5678',
                    'categoria': 'TRATOR',
                    'modelo': 'John Deere',
                    'ano': 2019,
                    'capacidade_tanque': 150.0,
                    'consumo_medio': 12.0,
                },
                {
                    'nome': 'Empilhadeira Teste 3',
                    'placa': 'GHI9012',
                    'categoria': 'EMPILHADEIRA',
                    'modelo': 'Toyota',
                    'ano': 2021,
                    'capacidade_tanque': 80.0,
                    'consumo_medio': 6.0,
                }
            ]
        else:
            # Usar veículos existentes como base
            equipamentos_teste = []
            for veiculo in veiculos:
                equipamentos_teste.append({
                    'nome': veiculo.nome,
                    'placa': veiculo.placa,
                    'categoria': veiculo.tipo,
                    'modelo': veiculo.modelo or 'Não informado',
                    'ano': veiculo.ano or 2020,
                    'capacidade_tanque': veiculo.capacidade_tanque or 100.0,
                    'consumo_medio': veiculo.consumo_medio or 10.0,
                })
        
        # Criar os equipamentos
        for dados in equipamentos_teste:
            # Verificar se já existe
            if Equipamento.objects.filter(placa=dados['placa']).exists():
                print(f"⚠️ Equipamento com placa {dados['placa']} já existe")
                continue
            
            equipamento = Equipamento.objects.create(
                nome=dados['nome'],
                codigo=dados['placa'],
                categoria=dados['categoria'],
                status_operacional='OPERACIONAL',
                ativo=True,
                em_servico=True,
                placa=dados['placa'],
                modelo=dados['modelo'],
                ano=dados['ano'],
                capacidade_tanque=dados['capacidade_tanque'],
                consumo_medio=dados['consumo_medio'],
                tem_agenda=True,
                descricao=f"Equipamento de teste: {dados['nome']}"
            )
            
            print(f"✅ Equipamento criado: {equipamento.nome} ({equipamento.placa})")
        
        print("✅ Equipamentos de teste criados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar equipamentos: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_equipamentos():
    print("\n📊 VERIFICANDO EQUIPAMENTOS...")
    
    try:
        total = Equipamento.objects.count()
        com_placa = Equipamento.objects.exclude(placa='').exclude(placa__isnull=True).count()
        
        print(f"Total de equipamentos: {total}")
        print(f"Equipamentos com placa: {com_placa}")
        
        if com_placa > 0:
            print("\nEquipamentos com placa:")
            for eq in Equipamento.objects.exclude(placa='').exclude(placa__isnull=True):
                print(f"  - {eq.nome} ({eq.placa}) - {eq.categoria}")
        
        return com_placa > 0
        
    except Exception as e:
        print(f"❌ Erro ao verificar equipamentos: {e}")
        return False

if __name__ == '__main__':
    if criar_equipamentos_teste():
        verificar_equipamentos()
    else:
        print("❌ Falha ao criar equipamentos de teste")
