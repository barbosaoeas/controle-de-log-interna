#!/usr/bin/env python
"""
Script para aplicar migrações e testar se os campos existem na tabela Equipamento
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from core.models import Equipamento

def main():
    print("🔧 APLICANDO MIGRAÇÕES...")
    
    try:
        # Aplicar migrações
        print("📋 Aplicando migrações pendentes...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrações aplicadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar migrações: {e}")
        print("🔄 Tentando verificar se os campos já existem...")
    
    # Verificar se os campos existem
    print("\n🔍 VERIFICANDO CAMPOS NA TABELA EQUIPAMENTO...")
    
    try:
        # Tentar acessar os campos
        equipamento = Equipamento.objects.first()
        if equipamento:
            print(f"✅ Campo 'placa': {hasattr(equipamento, 'placa')}")
            print(f"✅ Campo 'modelo': {hasattr(equipamento, 'modelo')}")
            print(f"✅ Campo 'ano': {hasattr(equipamento, 'ano')}")
            print(f"✅ Campo 'capacidade_tanque': {hasattr(equipamento, 'capacidade_tanque')}")
            print(f"✅ Campo 'consumo_medio': {hasattr(equipamento, 'consumo_medio')}")
            print(f"✅ Campo 'tem_agenda': {hasattr(equipamento, 'tem_agenda')}")
            
            # Tentar acessar os valores
            try:
                placa = equipamento.placa
                print(f"✅ Valor da placa: '{placa}'")
            except Exception as e:
                print(f"❌ Erro ao acessar campo placa: {e}")
                
        else:
            print("⚠️ Nenhum equipamento encontrado na base de dados")
            
    except Exception as e:
        print(f"❌ Erro ao verificar campos: {e}")
    
    # Verificar estrutura da tabela
    print("\n📊 ESTRUTURA DA TABELA EQUIPAMENTO:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(core_equipamento);")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  - {column[1]} ({column[2]})")
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")
    
    # Contar equipamentos que podem ser veículos
    print("\n🚗 EQUIPAMENTOS QUE PODEM SER VEÍCULOS:")
    try:
        total_equipamentos = Equipamento.objects.count()
        print(f"📊 Total de equipamentos: {total_equipamentos}")
        
        # Se o campo placa existir, contar equipamentos com placa
        try:
            equipamentos_com_placa = Equipamento.objects.exclude(placa='').exclude(placa__isnull=True).count()
            print(f"🚗 Equipamentos com placa: {equipamentos_com_placa}")
        except Exception as e:
            print(f"⚠️ Campo placa ainda não existe: {e}")
            
    except Exception as e:
        print(f"❌ Erro ao contar equipamentos: {e}")

if __name__ == '__main__':
    main()
