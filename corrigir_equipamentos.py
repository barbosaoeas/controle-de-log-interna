#!/usr/bin/env python
"""
Script para corrigir os problemas dos equipamentos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento

def corrigir_equipamentos():
    print("🔧 CORRIGINDO PROBLEMAS DOS EQUIPAMENTOS...")
    
    try:
        # 1. Ativar o Caminhão Munck 01
        try:
            caminhao = Equipamento.objects.get(nome="Caminhão Munck 01")
            if not caminhao.ativo:
                caminhao.ativo = True
                caminhao.save()
                print("✅ Caminhão Munck 01 ativado")
            else:
                print("ℹ️ Caminhão Munck 01 já estava ativo")
        except Equipamento.DoesNotExist:
            print("❌ Caminhão Munck 01 não encontrado")
        
        # 2. Adicionar placa à Empilhadeira sem placa
        try:
            empilhadeira_sem_placa = Equipamento.objects.filter(
                nome="Empilhadeira",
                placa__isnull=True
            ).first() or Equipamento.objects.filter(
                nome="Empilhadeira",
                placa=""
            ).first()
            
            if empilhadeira_sem_placa:
                empilhadeira_sem_placa.placa = "EMP0001"
                empilhadeira_sem_placa.save()
                print("✅ Empilhadeira sem placa recebeu placa EMP0001")
            else:
                print("ℹ️ Não encontrada empilhadeira sem placa")
        except Exception as e:
            print(f"❌ Erro ao corrigir empilhadeira: {e}")
        
        # 3. Corrigir placas para coincidir com a listagem
        correcoes_placas = [
            ("GDT0001", "gdt 01"),  # Guindaste
            ("TRT0001", "tr01"),    # Trator
            ("EQP0010", "tr02"),    # Trator02
        ]
        
        for placa_atual, placa_nova in correcoes_placas:
            try:
                equipamento = Equipamento.objects.get(placa=placa_atual)
                equipamento.placa = placa_nova
                equipamento.save()
                print(f"✅ {equipamento.nome}: {placa_atual} → {placa_nova}")
            except Equipamento.DoesNotExist:
                print(f"❌ Equipamento com placa {placa_atual} não encontrado")
            except Exception as e:
                print(f"❌ Erro ao corrigir placa {placa_atual}: {e}")
        
        print("✅ Correções aplicadas!")
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_resultado():
    print("\n📊 VERIFICANDO RESULTADO APÓS CORREÇÕES...")
    
    try:
        # Aplicar filtro do abastecimento
        veiculos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').order_by('nome')
        
        print(f"✅ EQUIPAMENTOS PARA ABASTECIMENTO: {veiculos.count()}")
        
        for i, veiculo in enumerate(veiculos, 1):
            status_servico = "🟢 Em Serviço" if veiculo.em_servico else "🔴 Fora de Serviço"
            print(f"  {i}. {veiculo.nome} ({veiculo.placa}) - {status_servico}")
        
        # Verificar se agora temos 7 equipamentos
        if veiculos.count() == 7:
            print("🎉 PERFEITO! Todos os 7 equipamentos agora aparecem no abastecimento!")
        elif veiculos.count() == 6:
            print("⚠️ Ainda faltam equipamentos. Verificando...")
            
            # Listar equipamentos que ainda não aparecem
            todos = Equipamento.objects.all()
            for eq in todos:
                if eq not in veiculos:
                    motivo = []
                    if not eq.ativo:
                        motivo.append("INATIVO")
                    if not eq.placa:
                        motivo.append("SEM PLACA")
                    print(f"  ❌ {eq.nome}: {' + '.join(motivo)}")
        
        return veiculos.count()
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return 0

def listar_todos_equipamentos():
    print("\n📋 LISTAGEM COMPLETA APÓS CORREÇÕES:")
    
    try:
        equipamentos = Equipamento.objects.all().order_by('nome')
        
        for eq in equipamentos:
            status_ativo = "✅ Ativo" if eq.ativo else "❌ Inativo"
            status_servico = "🟢 Em Serviço" if eq.em_servico else "🔴 Fora de Serviço"
            placa_info = f"({eq.placa})" if eq.placa else "(SEM PLACA)"
            
            print(f"  {eq.nome} {placa_info} - {status_ativo} - {status_servico}")
        
    except Exception as e:
        print(f"❌ Erro na listagem: {e}")

if __name__ == '__main__':
    if corrigir_equipamentos():
        count = verificar_resultado()
        listar_todos_equipamentos()
        print(f"\n🎯 RESULTADO FINAL: {count} equipamentos no select de abastecimento")
    else:
        print("❌ Falha nas correções")
