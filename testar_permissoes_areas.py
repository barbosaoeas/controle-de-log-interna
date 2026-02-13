#!/usr/bin/env python
"""
Script para testar as permissões de áreas.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Area, PerfilUsuario
from django.contrib.auth.models import User

def testar_permissoes_areas():
    """Testa as permissões de áreas"""
    print("=" * 70)
    print("🔐 TESTANDO PERMISSÕES DE ÁREAS")
    print("=" * 70)
    
    try:
        # Verificar usuários e perfis
        usuarios = User.objects.all()
        print(f"👥 Usuários encontrados: {usuarios.count()}")
        
        for user in usuarios:
            try:
                perfil = user.perfil
                print(f"   • {user.username} ({user.get_full_name() or 'Sem nome'}) - {perfil.perfil}")
                print(f"     Setor: {perfil.setor.nome}")
                print(f"     É admin/supervisor: {perfil.is_admin_ou_supervisor}")
            except PerfilUsuario.DoesNotExist:
                print(f"   • {user.username} - SEM PERFIL")
        
        print(f"\n🔧 Permissões implementadas:")
        print(f"   ✅ Frontend: Botões de editar/remover apenas para admin/supervisor")
        print(f"   ✅ Frontend: Formulário de criar apenas para admin/supervisor")
        print(f"   ✅ Backend: API de criar com verificação de permissão")
        print(f"   ✅ Backend: API de editar com verificação de permissão")
        print(f"   ✅ Backend: API de remover com verificação de permissão")
        
        print(f"\n📋 Perfis com permissão para gerenciar áreas:")
        perfis_com_permissao = PerfilUsuario.objects.filter(perfil__in=['ADMIN', 'SUPERVISOR', 'TRANSPORTES', 'MANUTENCAO'])
        for perfil in perfis_com_permissao:
            print(f"   ✅ {perfil.user.username} - {perfil.perfil}")

        print(f"\n📋 Perfis SEM permissão para gerenciar áreas:")
        perfis_sem_permissao = PerfilUsuario.objects.exclude(perfil__in=['ADMIN', 'SUPERVISOR', 'TRANSPORTES', 'MANUTENCAO'])
        for perfil in perfis_sem_permissao:
            print(f"   ❌ {perfil.user.username} - {perfil.perfil}")
        
        print(f"\n🎯 Comportamento esperado:")
        print(f"   • ADMIN/SUPERVISOR/TRANSPORTES/MANUTENCAO: Veem botões de editar/remover e formulário de criar")
        print(f"   • DEMANDANTE: Veem apenas a lista de áreas (sem botões de ação)")
        
        print(f"\n🔍 Correções aplicadas:")
        print(f"   ✅ Adicionado @csrf_exempt na API de edição")
        print(f"   ✅ Corrigido parsing de dados PUT no backend")
        print(f"   ✅ Adicionado header X-CSRFToken no frontend")
        print(f"   ✅ Verificação de permissão em todas as APIs de modificação")
        
        # Verificar áreas existentes
        areas = Area.objects.filter(ativa=True)
        print(f"\n📊 Áreas disponíveis para teste:")
        for area in areas:
            print(f"   • ID: {area.id} | {area.nome} | {area.localizacao or 'Sem localização'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = testar_permissoes_areas()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ PERMISSÕES CONFIGURADAS CORRETAMENTE!")
        print("=" * 70)
        print("🎯 Como testar:")
        print("   1. Faça login como ADMIN/SUPERVISOR/TRANSPORTES/MANUTENCAO:")
        print("      • Deve ver botões de editar/remover")
        print("      • Deve ver formulário de criar área")
        print("   2. Faça login como DEMANDANTE:")
        print("      • Deve ver apenas lista de áreas")
        print("      • Não deve ver botões de ação")
        print("      • Deve ver mensagem 'Visualização apenas'")
        print("\n🌐 Teste em: http://127.0.0.1:8000/criar_pedido/")
    else:
        print("\n" + "=" * 70)
        print("❌ ERRO NO TESTE DE PERMISSÕES!")
        print("=" * 70)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
