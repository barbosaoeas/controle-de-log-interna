#!/usr/bin/env python
"""
Script para adicionar placas aos equipamentos que não têm e ajustar status
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento

def adicionar_placas_equipamentos():
    print("🚗 ADICIONANDO PLACAS AOS EQUIPAMENTOS...")
    
    try:
        # Buscar equipamentos sem placa
        equipamentos_sem_placa = Equipamento.objects.filter(
            placa__isnull=True
        ) | Equipamento.objects.filter(placa='')
        
        print(f"📊 Encontrados {equipamentos_sem_placa.count()} equipamentos sem placa")
        
        # Mapeamento de equipamentos para placas
        placas_sugeridas = {
            'Guindaste rodoviario': 'GDT0001',
            'Trator': 'TRT0001', 
            'Trator02': 'TRT0002',
            'Caminhão Munck 01': 'CMK0001',  # Caso não tenha placa
        }
        
        for equipamento in equipamentos_sem_placa:
            nome_equipamento = equipamento.nome
            
            # Buscar placa sugerida
            placa_sugerida = None
            for nome_key, placa in placas_sugeridas.items():
                if nome_key.lower() in nome_equipamento.lower():
                    placa_sugerida = placa
                    break
            
            # Se não encontrou uma placa específica, gerar uma genérica
            if not placa_sugerida:
                # Gerar placa baseada na categoria
                categoria = equipamento.categoria
                if categoria == 'TRATOR':
                    placa_sugerida = f"TRT{equipamento.id:04d}"
                elif categoria == 'EMPILHADEIRA':
                    placa_sugerida = f"EMP{equipamento.id:04d}"
                elif categoria == 'CAMINHAO_MUNCK':
                    placa_sugerida = f"CMK{equipamento.id:04d}"
                elif categoria == 'GUINDASTE_RODOVIARIO':
                    placa_sugerida = f"GDT{equipamento.id:04d}"
                else:
                    placa_sugerida = f"EQP{equipamento.id:04d}"
            
            # Verificar se a placa já existe
            if Equipamento.objects.filter(placa=placa_sugerida).exists():
                print(f"⚠️ Placa {placa_sugerida} já existe, gerando alternativa...")
                placa_sugerida = f"EQP{equipamento.id:04d}"
            
            # Atualizar equipamento
            equipamento.placa = placa_sugerida
            
            # Se não tem modelo, adicionar um genérico
            if not equipamento.modelo:
                equipamento.modelo = f"Modelo {equipamento.categoria}"
            
            # Se não tem capacidade de tanque, adicionar uma padrão
            if not equipamento.capacidade_tanque:
                if equipamento.categoria in ['TRATOR', 'CAMINHAO_MUNCK']:
                    equipamento.capacidade_tanque = 200.0
                elif equipamento.categoria == 'EMPILHADEIRA':
                    equipamento.capacidade_tanque = 80.0
                else:
                    equipamento.capacidade_tanque = 100.0
            
            # Se não tem consumo médio, adicionar um padrão
            if not equipamento.consumo_medio:
                if equipamento.categoria == 'TRATOR':
                    equipamento.consumo_medio = 12.0
                elif equipamento.categoria == 'EMPILHADEIRA':
                    equipamento.consumo_medio = 6.0
                else:
                    equipamento.consumo_medio = 10.0
            
            # Garantir que tem_agenda está definido
            if not hasattr(equipamento, 'tem_agenda') or equipamento.tem_agenda is None:
                equipamento.tem_agenda = True
            
            equipamento.save()
            
            print(f"✅ {equipamento.nome} -> Placa: {placa_sugerida}")
        
        print("✅ Placas adicionadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar placas: {e}")
        import traceback
        traceback.print_exc()
        return False

def ajustar_status_servico():
    print("\n🔧 AJUSTANDO STATUS DE SERVIÇO...")
    
    try:
        # Buscar equipamentos que estão operacionais mas fora de serviço
        equipamentos_fora_servico = Equipamento.objects.filter(
            status_operacional='OPERACIONAL',
            em_servico=False
        )
        
        print(f"📊 Encontrados {equipamentos_fora_servico.count()} equipamentos operacionais mas fora de serviço")
        
        for equipamento in equipamentos_fora_servico:
            print(f"⚠️ {equipamento.nome} está operacional mas fora de serviço")
            
            # Perguntar se deve colocar em serviço (para este script, vamos assumir que sim)
            # Em produção, isso seria uma decisão manual
            equipamento.em_servico = True
            equipamento.save()
            
            print(f"✅ {equipamento.nome} colocado em serviço")
        
        print("✅ Status de serviço ajustados!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao ajustar status: {e}")
        return False

def verificar_equipamentos_para_abastecimento():
    print("\n🚗 VERIFICANDO EQUIPAMENTOS DISPONÍVEIS PARA ABASTECIMENTO...")
    
    try:
        # Usar a mesma lógica do views_diesel.py
        veiculos = Equipamento.objects.filter(
            ativo=True,
            placa__isnull=False
        ).exclude(placa='').order_by('nome')
        
        print(f"✅ {veiculos.count()} equipamentos disponíveis para abastecimento:")
        
        for veiculo in veiculos:
            status_servico = "🟢 Em Serviço" if veiculo.em_servico else "🔴 Fora de Serviço"
            print(f"  - {veiculo.nome} ({veiculo.placa}) - {veiculo.categoria} - {status_servico}")
        
        return veiculos.count() > 0
        
    except Exception as e:
        print(f"❌ Erro ao verificar equipamentos: {e}")
        return False

if __name__ == '__main__':
    if adicionar_placas_equipamentos():
        ajustar_status_servico()
        verificar_equipamentos_para_abastecimento()
    else:
        print("❌ Falha ao processar equipamentos")
