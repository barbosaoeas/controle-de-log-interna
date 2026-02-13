#!/usr/bin/env python
"""
Script para testar o carregamento de setores na edição de usuários.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import PerfilUsuario, Setor

def testar_setor_edicao():
    """Testa o carregamento de setores na edição"""
    print("=" * 70)
    print("🏢 TESTANDO CARREGAMENTO DE SETORES NA EDIÇÃO")
    print("=" * 70)
    
    try:
        # Listar setores disponíveis
        setores = Setor.objects.filter(ativo=True).order_by('nome')
        print(f"📊 Setores ativos encontrados: {setores.count()}")
        
        for setor in setores:
            usuarios_count = PerfilUsuario.objects.filter(setor=setor).count()
            print(f"   • ID: {setor.id} | Nome: {setor.nome} | Usuários: {usuarios_count}")
        
        # Listar usuários com seus setores
        print(f"\n👤 Usuários e seus setores:")
        usuarios = User.objects.all().order_by('username')
        
        for user in usuarios:
            try:
                perfil = user.perfil
                print(f"   • ID: {user.id} | Username: {user.username}")
                print(f"     Setor ID: {perfil.setor.id} | Setor Nome: {perfil.setor.nome}")
                print(f"     Perfil: {perfil.perfil}")
            except PerfilUsuario.DoesNotExist:
                print(f"   • ID: {user.id} | Username: {user.username} | SEM PERFIL")
        
        print(f"\n🔧 Problema identificado:")
        print(f"   • Select de edição não estava sendo carregado com setores")
        print(f"   • Função carregarSetoresParaUsuarios() só carregava select de criação")
        print(f"   • Valor do setor não era definido após carregamento")
        
        print(f"\n✅ Correções aplicadas:")
        print(f"   • Função carregarSetoresParaUsuarios() agora carrega AMBOS os selects:")
        print(f"     - setorUsuarioGlobal (formulário de criação)")
        print(f"     - editSetorUsuarioGlobal (formulário de edição)")
        print(f"   • Função retorna Promise para aguardar carregamento")
        print(f"   • Valor do setor é definido APÓS carregamento dos setores")
        print(f"   • Timeout de 100ms para garantir renderização")
        
        print(f"\n📋 Como testar:")
        print(f"   1. Faça login como ADMIN ou SUPERVISOR")
        print(f"   2. Clique em 'Usuários' no menu lateral")
        print(f"   3. Clique no botão de editar (lápis) de um usuário")
        print(f"   4. Verifique se o campo 'Setor' está preenchido corretamente")
        print(f"   5. Abra o console (F12) e verifique os logs:")
        print(f"      • '🏢 Carregando setores para select de usuários...'")
        print(f"      • '✅ Setores carregados no select de criação'")
        print(f"      • '✅ Setores carregados no select de edição'")
        print(f"      • '✅ Setor selecionado: <ID>'")
        
        print(f"\n🎯 Exemplo de teste:")
        if usuarios.exists():
            user_exemplo = usuarios.first()
            try:
                perfil_exemplo = user_exemplo.perfil
                print(f"   • Editar usuário: {user_exemplo.username}")
                print(f"   • Setor esperado: {perfil_exemplo.setor.nome} (ID: {perfil_exemplo.setor.id})")
                print(f"   • Verificar se o select mostra este setor selecionado")
            except PerfilUsuario.DoesNotExist:
                print(f"   • Usuário {user_exemplo.username} não tem perfil")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = testar_setor_edicao()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ TESTE DE CARREGAMENTO DE SETORES CONFIGURADO!")
        print("=" * 70)
        print("🎯 Próximos passos:")
        print("   1. Abra o navegador em: http://127.0.0.1:8000/")
        print("   2. Faça login como ADMIN")
        print("   3. Clique em 'Usuários' no menu")
        print("   4. Clique no botão de editar de um usuário")
        print("   5. Verifique se o campo 'Setor' está preenchido")
        print("\n🔍 O que verificar:")
        print("   • Campo 'Setor' no formulário de edição preenchido")
        print("   • Logs no console confirmando carregamento")
        print("   • Setor correto selecionado conforme usuário")
        print("\n🌐 URL: http://127.0.0.1:8000/")
    else:
        print("\n" + "=" * 70)
        print("❌ ERRO NO TESTE!")
        print("=" * 70)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
