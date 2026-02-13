#!/usr/bin/env python
"""
Script para testar se os equipamentos estão sendo carregados corretamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento, Veiculo

def testar_equipamentos():
    print("🔍 TESTANDO CARREGAMENTO DE EQUIPAMENTOS...")
    
    try:
        # Testar a lógica que está sendo usada no views_diesel.py
        print("\n1️⃣ TESTANDO LÓGICA DO VIEWS_DIESEL...")
        
        # Tentar usar equipamentos que são veículos (têm placa)
        veiculos_equipamentos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').order_by('nome')
        
        print(f"✅ Equipamentos com placa encontrados: {veiculos_equipamentos.count()}")
        
        for eq in veiculos_equipamentos:
            print(f"  - {eq.nome} ({eq.placa}) - {eq.categoria}")
        
        # Se não houver equipamentos com placa, usar tabela Veiculo como fallback
        if not veiculos_equipamentos.exists():
            print("⚠️ Nenhum equipamento com placa, usando fallback para Veiculo")
            veiculos_fallback = Veiculo.objects.filter(ativo=True).order_by('nome')
            print(f"Veículos encontrados: {veiculos_fallback.count()}")
            for v in veiculos_fallback:
                print(f"  - {v.nome} ({v.placa}) - {v.tipo}")
        else:
            print(f"✅ Sistema usará {veiculos_equipamentos.count()} equipamentos para abastecimento")
        
        print("\n2️⃣ TESTANDO CAMPOS DOS EQUIPAMENTOS...")
        
        # Testar se os campos existem
        primeiro_equipamento = Equipamento.objects.first()
        if primeiro_equipamento:
            print(f"Equipamento teste: {primeiro_equipamento.nome}")
            print(f"  - Tem campo placa: {hasattr(primeiro_equipamento, 'placa')}")
            print(f"  - Valor da placa: '{primeiro_equipamento.placa}'")
            print(f"  - Tem campo modelo: {hasattr(primeiro_equipamento, 'modelo')}")
            print(f"  - Valor do modelo: '{primeiro_equipamento.modelo}'")
            print(f"  - Tem campo tem_agenda: {hasattr(primeiro_equipamento, 'tem_agenda')}")
            print(f"  - Valor tem_agenda: {primeiro_equipamento.tem_agenda}")
        
        print("\n3️⃣ COMPARANDO TABELAS...")
        
        total_equipamentos = Equipamento.objects.count()
        equipamentos_com_placa = Equipamento.objects.exclude(placa='').exclude(placa__isnull=True).count()
        total_veiculos = Veiculo.objects.count()
        veiculos_ativos = Veiculo.objects.filter(ativo=True).count()
        
        print(f"📊 Total equipamentos: {total_equipamentos}")
        print(f"📊 Equipamentos com placa: {equipamentos_com_placa}")
        print(f"📊 Total veículos: {total_veiculos}")
        print(f"📊 Veículos ativos: {veiculos_ativos}")
        
        if equipamentos_com_placa > 0:
            print("✅ SISTEMA DEVE USAR TABELA EQUIPAMENTO")
        else:
            print("⚠️ SISTEMA USARÁ TABELA VEICULO COMO FALLBACK")
        
        return equipamentos_com_placa > 0
        
    except Exception as e:
        print(f"❌ Erro ao testar equipamentos: {e}")
        import traceback
        traceback.print_exc()
        return False

def simular_view_diesel():
    print("\n🎯 SIMULANDO LÓGICA DO VIEW DIESEL...")
    
    try:
        # Simular exatamente o que está no views_diesel.py
        veiculos = None
        
        try:
            # Tentar usar equipamentos que são veículos (têm placa)
            veiculos = Equipamento.objects.filter(
                ativo=True,
                placa__isnull=False
            ).exclude(placa='').order_by('nome')
            
            # Se não houver equipamentos com placa, usar tabela Veiculo como fallback
            if not veiculos.exists():
                print("DEBUG: Nenhum equipamento com placa encontrado, usando tabela Veiculo")
                veiculos = Veiculo.objects.filter(ativo=True).order_by('nome')
            else:
                print(f"DEBUG: Encontrados {veiculos.count()} equipamentos com placa para abastecimento")
                
        except Exception as e:
            print(f"DEBUG: Erro ao acessar equipamentos, usando Veiculo como fallback: {e}")
            veiculos = Veiculo.objects.filter(ativo=True).order_by('nome')
        
        print(f"🎯 RESULTADO: {veiculos.count()} veículos serão mostrados no select")
        
        for i, veiculo in enumerate(veiculos[:5]):  # Mostrar apenas os primeiros 5
            if hasattr(veiculo, 'placa'):
                print(f"  {i+1}. {veiculo.nome} ({veiculo.placa})")
            else:
                print(f"  {i+1}. {veiculo.nome} (sem placa)")
        
        if veiculos.count() > 5:
            print(f"  ... e mais {veiculos.count() - 5} veículos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao simular view: {e}")
        return False

if __name__ == '__main__':
    if testar_equipamentos():
        simular_view_diesel()
    else:
        print("❌ Falha nos testes")
