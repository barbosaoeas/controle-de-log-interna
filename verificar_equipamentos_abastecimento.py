#!/usr/bin/env python
"""
Script para verificar quais equipamentos aparecem no abastecimento
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento

def verificar_equipamentos_abastecimento():
    print("🔍 VERIFICANDO EQUIPAMENTOS PARA ABASTECIMENTO...")
    
    try:
        # Listar TODOS os equipamentos
        todos_equipamentos = Equipamento.objects.all().order_by('nome')
        print(f"\n📊 TOTAL DE EQUIPAMENTOS: {todos_equipamentos.count()}")
        
        for eq in todos_equipamentos:
            status_ativo = "✅ Ativo" if eq.ativo else "❌ Inativo"
            status_servico = "🟢 Em Serviço" if eq.em_servico else "🔴 Fora de Serviço"
            placa_info = f"({eq.placa})" if eq.placa else "(SEM PLACA)"
            
            print(f"  - {eq.nome} {placa_info} - {status_ativo} - {status_servico}")
        
        print("\n" + "="*60)
        
        # Aplicar filtros do abastecimento
        print("🚗 APLICANDO FILTROS DO ABASTECIMENTO...")
        
        # Filtro 1: Equipamentos ativos
        equipamentos_ativos = Equipamento.objects.filter(ativo=True)
        print(f"\n1️⃣ EQUIPAMENTOS ATIVOS: {equipamentos_ativos.count()}")
        
        for eq in equipamentos_ativos:
            placa_info = f"({eq.placa})" if eq.placa else "(SEM PLACA)"
            print(f"  ✅ {eq.nome} {placa_info}")
        
        # Filtro 2: Equipamentos ativos COM placa
        equipamentos_com_placa = equipamentos_ativos.filter(
            placa__isnull=False
        ).exclude(placa='')
        print(f"\n2️⃣ EQUIPAMENTOS ATIVOS COM PLACA: {equipamentos_com_placa.count()}")
        
        for eq in equipamentos_com_placa:
            status_servico = "🟢 Em Serviço" if eq.em_servico else "🔴 Fora de Serviço"
            print(f"  🚗 {eq.nome} ({eq.placa}) - {status_servico}")
        
        # Verificar equipamentos SEM placa
        equipamentos_sem_placa = equipamentos_ativos.filter(
            placa__isnull=True
        ) | equipamentos_ativos.filter(placa='')
        
        print(f"\n❌ EQUIPAMENTOS ATIVOS SEM PLACA: {equipamentos_sem_placa.count()}")
        for eq in equipamentos_sem_placa:
            print(f"  ⚠️ {eq.nome} - SEM PLACA")
        
        print("\n" + "="*60)
        print("🎯 RESULTADO FINAL PARA ABASTECIMENTO:")
        print(f"✅ {equipamentos_com_placa.count()} equipamentos disponíveis")
        
        return equipamentos_com_placa
        
    except Exception as e:
        print(f"❌ Erro ao verificar equipamentos: {e}")
        import traceback
        traceback.print_exc()
        return None

def verificar_placas_especificas():
    print("\n🔍 VERIFICANDO PLACAS ESPECÍFICAS...")
    
    placas_esperadas = ['ABC1234', 'DEF5678', 'x x', 'GHI9012', 'gdt 01', 'tr01', 'tr02']
    
    for placa in placas_esperadas:
        try:
            eq = Equipamento.objects.get(placa=placa)
            status_ativo = "✅ Ativo" if eq.ativo else "❌ Inativo"
            status_servico = "🟢 Em Serviço" if eq.em_servico else "🔴 Fora de Serviço"
            print(f"  {placa}: {eq.nome} - {status_ativo} - {status_servico}")
        except Equipamento.DoesNotExist:
            print(f"  {placa}: ❌ NÃO ENCONTRADO")
        except Exception as e:
            print(f"  {placa}: ❌ ERRO: {e}")

def simular_filtro_abastecimento():
    print("\n🎯 SIMULANDO FILTRO EXATO DO VIEWS_DIESEL.PY...")
    
    try:
        # Exatamente como está no código
        veiculos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').order_by('nome')
        
        print(f"✅ RESULTADO: {veiculos.count()} equipamentos para abastecimento")
        
        for i, veiculo in enumerate(veiculos, 1):
            status_servico = "🟢 Em Serviço" if veiculo.em_servico else "🔴 Fora de Serviço"
            print(f"  {i}. {veiculo.nome} ({veiculo.placa}) - {status_servico}")
        
        return veiculos.count()
        
    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        return 0

if __name__ == '__main__':
    verificar_equipamentos_abastecimento()
    verificar_placas_especificas()
    count = simular_filtro_abastecimento()
    
    print(f"\n🎯 CONCLUSÃO: {count} equipamentos devem aparecer no select de abastecimento")
