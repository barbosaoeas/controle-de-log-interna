#!/usr/bin/env python
"""
Script para marcar as migrações como aplicadas no Django
"""
import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

def marcar_migracoes_aplicadas():
    print("🔧 MARCANDO MIGRAÇÕES COMO APLICADAS...")
    
    try:
        with connection.cursor() as cursor:
            # Verificar se a tabela django_migrations existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='django_migrations';
            """)
            
            if not cursor.fetchone():
                print("❌ Tabela django_migrations não encontrada")
                return False
            
            # Verificar migrações já aplicadas
            cursor.execute("""
                SELECT app, name FROM django_migrations 
                WHERE app = 'core' 
                ORDER BY applied;
            """)
            
            migracoes_aplicadas = cursor.fetchall()
            print(f"📋 Migrações já aplicadas: {len(migracoes_aplicadas)}")
            
            for app, name in migracoes_aplicadas:
                print(f"  ✅ {app}.{name}")
            
            # Migrações que precisam ser marcadas como aplicadas
            migracoes_pendentes = [
                '0020_unificar_equipamentos_veiculos',
                '0021_migrar_dados_veiculo_para_equipamento', 
                '0022_alterar_abastecimento_para_equipamento'
            ]
            
            for migracao in migracoes_pendentes:
                # Verificar se já está aplicada
                cursor.execute(
                    "SELECT id FROM django_migrations WHERE app = %s AND name = %s",
                    ['core', migracao]
                )

                if cursor.fetchone():
                    print(f"⚠️ Migração {migracao} já está marcada como aplicada")
                    continue

                # Marcar como aplicada
                cursor.execute(
                    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, datetime('now'))",
                    ['core', migracao]
                )
                
                print(f"✅ Migração {migracao} marcada como aplicada")
            
            print("✅ Todas as migrações foram marcadas como aplicadas!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao marcar migrações: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_status():
    print("\n📊 VERIFICANDO STATUS FINAL...")
    
    try:
        from django.core.management import execute_from_command_line
        import io
        import sys
        
        # Capturar output do showmigrations
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            execute_from_command_line(['manage.py', 'showmigrations', 'core'])
        except SystemExit:
            pass
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        print("Status das migrações:")
        print(output)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return False

if __name__ == '__main__':
    if marcar_migracoes_aplicadas():
        verificar_status()
    else:
        print("❌ Falha ao marcar migrações")
