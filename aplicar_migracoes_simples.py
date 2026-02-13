#!/usr/bin/env python
"""
Script simples para aplicar migrações
"""
import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

def aplicar_migracoes():
    print("🔧 APLICANDO MIGRAÇÕES...")
    
    try:
        # Aplicar migrações usando SQL direto
        with connection.cursor() as cursor:
            print("📋 Adicionando campos à tabela core_equipamento...")
            
            # Verificar se os campos já existem
            cursor.execute("PRAGMA table_info(core_equipamento);")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Colunas existentes: {columns}")
            
            # Adicionar campos se não existirem
            if 'placa' not in columns:
                cursor.execute("ALTER TABLE core_equipamento ADD COLUMN placa VARCHAR(10) DEFAULT '';")
                print("✅ Campo 'placa' adicionado")
            else:
                print("⚠️ Campo 'placa' já existe")
                
            if 'modelo' not in columns:
                cursor.execute("ALTER TABLE core_equipamento ADD COLUMN modelo VARCHAR(100) DEFAULT '';")
                print("✅ Campo 'modelo' adicionado")
            else:
                print("⚠️ Campo 'modelo' já existe")
                
            if 'ano' not in columns:
                cursor.execute("ALTER TABLE core_equipamento ADD COLUMN ano INTEGER;")
                print("✅ Campo 'ano' adicionado")
            else:
                print("⚠️ Campo 'ano' já existe")
                
            if 'capacidade_tanque' not in columns:
                cursor.execute("ALTER TABLE core_equipamento ADD COLUMN capacidade_tanque DECIMAL(8,2);")
                print("✅ Campo 'capacidade_tanque' adicionado")
            else:
                print("⚠️ Campo 'capacidade_tanque' já existe")
                
            if 'consumo_medio' not in columns:
                cursor.execute("ALTER TABLE core_equipamento ADD COLUMN consumo_medio DECIMAL(5,2);")
                print("✅ Campo 'consumo_medio' adicionado")
            else:
                print("⚠️ Campo 'consumo_medio' já existe")
                
            if 'tem_agenda' not in columns:
                cursor.execute("ALTER TABLE core_equipamento ADD COLUMN tem_agenda BOOLEAN DEFAULT 1;")
                print("✅ Campo 'tem_agenda' adicionado")
            else:
                print("⚠️ Campo 'tem_agenda' já existe")
        
        print("✅ Campos adicionados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar campos: {e}")
        return False

def migrar_dados():
    print("\n🔄 MIGRANDO DADOS DE VEICULO PARA EQUIPAMENTO...")
    
    try:
        from core.models import Veiculo, Equipamento
        
        veiculos = Veiculo.objects.all()
        print(f"📊 Encontrados {veiculos.count()} veículos para migrar")
        
        for veiculo in veiculos:
            # Verificar se já existe um equipamento com essa placa
            equipamento_existente = Equipamento.objects.filter(placa=veiculo.placa).first()
            
            if equipamento_existente:
                print(f"⚠️ Equipamento com placa {veiculo.placa} já existe")
                continue
            
            # Criar novo equipamento baseado no veículo
            equipamento = Equipamento.objects.create(
                nome=veiculo.nome,
                codigo=veiculo.placa,  # Usar placa como código
                categoria=veiculo.tipo,
                status_operacional='OPERACIONAL' if veiculo.status == 'ATIVO' else veiculo.status,
                ativo=veiculo.ativo,
                em_servico=True,
                placa=veiculo.placa,
                modelo=veiculo.modelo or '',
                ano=veiculo.ano,
                capacidade_tanque=veiculo.capacidade_tanque,
                consumo_medio=veiculo.consumo_medio,
                tem_agenda=veiculo.tem_agenda,
                descricao=f"Migrado de veículo: {veiculo.nome}"
            )
            
            print(f"✅ Equipamento criado: {equipamento.nome} ({equipamento.placa})")
        
        print("✅ Migração de dados concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao migrar dados: {e}")
        return False

if __name__ == '__main__':
    if aplicar_migracoes():
        migrar_dados()
    else:
        print("❌ Falha ao aplicar migrações")
