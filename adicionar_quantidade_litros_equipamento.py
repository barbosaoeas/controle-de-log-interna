#!/usr/bin/env python
"""
Script para adicionar o campo 'quantidade_litros' na tabela de equipamentos.
Este campo é importante para controlar a quantidade de litros que cada equipamento pode armazenar.
"""

import os
import sys
import django
import sqlite3
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento

def verificar_campo_existe():
    """Verifica se o campo quantidade_litros já existe na tabela"""
    try:
        # Conectar ao banco SQLite
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Verificar colunas da tabela core_equipamento
        cursor.execute("PRAGMA table_info(core_equipamento)")
        colunas = [coluna[1] for coluna in cursor.fetchall()]
        
        conn.close()
        return 'quantidade_litros' in colunas
    except Exception as e:
        print(f"❌ Erro ao verificar campo: {e}")
        return False

def adicionar_campo_quantidade_litros():
    """Adiciona o campo quantidade_litros na tabela de equipamentos"""
    try:
        print("🔍 Verificando se o campo 'quantidade_litros' já existe...")
        
        if verificar_campo_existe():
            print("✅ Campo 'quantidade_litros' já existe na tabela de equipamentos!")
            return True
        
        print("📝 Adicionando campo 'quantidade_litros' na tabela de equipamentos...")
        
        # Conectar ao banco SQLite
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Adicionar o campo quantidade_litros
        sql_add_field = """
        ALTER TABLE core_equipamento 
        ADD COLUMN quantidade_litros DECIMAL(8,2) NULL
        """
        
        cursor.execute(sql_add_field)
        conn.commit()
        conn.close()
        
        print("✅ Campo 'quantidade_litros' adicionado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar campo: {e}")
        return False

def atualizar_modelo_equipamento():
    """Atualiza alguns equipamentos com valores padrão de quantidade_litros"""
    try:
        print("📝 Atualizando equipamentos com valores padrão...")
        
        # Buscar equipamentos que são veículos (têm placa)
        equipamentos_veiculo = Equipamento.objects.filter(placa__isnull=False).exclude(placa='')
        
        for equipamento in equipamentos_veiculo:
            # Se já tem capacidade_tanque, usar como base para quantidade_litros
            if equipamento.capacidade_tanque:
                # Definir quantidade_litros como 80% da capacidade do tanque (valor conservador)
                quantidade_sugerida = equipamento.capacidade_tanque * Decimal('0.8')
                equipamento.quantidade_litros = quantidade_sugerida
                equipamento.save()
                print(f"✅ {equipamento.nome} - Quantidade litros: {quantidade_sugerida}L (baseado na capacidade do tanque)")
            else:
                # Valores padrão baseados na categoria
                valores_padrao = {
                    'TRATOR': Decimal('200.00'),
                    'PRANCHA_REBOQUE': Decimal('300.00'),
                    'EMPILHADEIRA': Decimal('50.00'),
                    'CAMINHAO_MUNCK': Decimal('250.00'),
                    'CARRETA_HIDRAULICA': Decimal('200.00'),
                    'GUINDASTE_RODOVIARIO': Decimal('300.00'),
                    'CAVALO_MECANICO': Decimal('400.00'),
                    'OUTROS': Decimal('100.00'),
                }
                
                quantidade_padrao = valores_padrao.get(equipamento.categoria, Decimal('100.00'))
                equipamento.quantidade_litros = quantidade_padrao
                equipamento.save()
                print(f"✅ {equipamento.nome} - Quantidade litros: {quantidade_padrao}L (valor padrão para {equipamento.categoria})")
        
        print(f"✅ {equipamentos_veiculo.count()} equipamentos atualizados!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar equipamentos: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 ADICIONANDO CAMPO 'QUANTIDADE_LITROS' AOS EQUIPAMENTOS")
    print("=" * 60)
    
    try:
        # Passo 1: Adicionar o campo na tabela
        if not adicionar_campo_quantidade_litros():
            return False
        
        # Passo 2: Atualizar equipamentos existentes
        if not atualizar_modelo_equipamento():
            return False
        
        print("\n" + "=" * 60)
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("📋 Resumo das alterações:")
        print("   • Campo 'quantidade_litros' adicionado na tabela core_equipamento")
        print("   • Equipamentos existentes atualizados com valores padrão")
        print("   • Valores baseados na capacidade do tanque ou categoria do equipamento")
        print("\n💡 Próximos passos:")
        print("   • Atualizar o modelo Equipamento no arquivo models.py")
        print("   • Atualizar formulários para incluir o novo campo")
        print("   • Testar a funcionalidade")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
