#!/usr/bin/env python
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from core.models import PerfilUsuario

def test_users():
    print("=== TESTE DE USUÁRIOS ===")
    
    # Listar todos os usuários
    users = User.objects.all()
    print(f"\nUsuários cadastrados: {users.count()}")
    
    for user in users:
        print(f"\n- Usuário: {user.username}")
        print(f"  Nome: {user.get_full_name() or 'Não informado'}")
        print(f"  Email: {user.email or 'Não informado'}")
        print(f"  Ativo: {user.is_active}")
        print(f"  Staff: {user.is_staff}")
        print(f"  Superuser: {user.is_superuser}")
        
        # Verificar perfil
        try:
            perfil = user.perfil
            print(f"  Perfil: {perfil.get_perfil_display()}")
            print(f"  Setor: {perfil.setor.nome}")
        except PerfilUsuario.DoesNotExist:
            print(f"  Perfil: NÃO ENCONTRADO")
    
    print("\n=== TESTE DE AUTENTICAÇÃO ===")
    
    # Testar autenticação dos usuários de exemplo
    test_credentials = [
        ('admin', 'admin123'),
        ('producao1', '123456'),
        ('transportes1', '123456'),
    ]
    
    for username, password in test_credentials:
        print(f"\nTestando login: {username}")
        user = authenticate(username=username, password=password)
        if user:
            print(f"  ✅ Login bem-sucedido")
            print(f"  Ativo: {user.is_active}")
            try:
                perfil = user.perfil
                print(f"  Perfil: {perfil.get_perfil_display()}")
                print(f"  Setor: {perfil.setor.nome}")
            except PerfilUsuario.DoesNotExist:
                print(f"  ❌ Perfil não encontrado")
        else:
            print(f"  ❌ Falha no login")

if __name__ == '__main__':
    test_users()
