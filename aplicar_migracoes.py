#!/usr/bin/env python
"""
Script para aplicar migrações manualmente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print("🔧 Aplicando migrações...")
    
    try:
        # Aplicar migração 0020 (adicionar campos)
        print("📝 Aplicando migração 0020 - Adicionando campos ao Equipamento...")
        execute_from_command_line(['manage.py', 'migrate', 'core', '0020'])
        print("✅ Migração 0020 aplicada com sucesso!")
        
        # Aplicar migração 0021 (migrar dados)
        print("📝 Aplicando migração 0021 - Migrando dados de Veiculo para Equipamento...")
        execute_from_command_line(['manage.py', 'migrate', 'core', '0021'])
        print("✅ Migração 0021 aplicada com sucesso!")
        
        # Aplicar migração 0022 (alterar ForeignKey)
        print("📝 Aplicando migração 0022 - Alterando ForeignKey de AbastecimentoVeiculo...")
        execute_from_command_line(['manage.py', 'migrate', 'core', '0022'])
        print("✅ Migração 0022 aplicada com sucesso!")
        
        print("🎉 Todas as migrações foram aplicadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar migrações: {e}")
        sys.exit(1)
