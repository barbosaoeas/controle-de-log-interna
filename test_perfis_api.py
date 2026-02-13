#!/usr/bin/env python3
"""
Script de teste para verificar se as APIs de perfis estão funcionando
"""

import requests
import json

# Configurações
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/login/"
CRIAR_PERFIL_URL = f"{BASE_URL}/api/perfis/criar/"
EDITAR_PERFIL_URL = f"{BASE_URL}/api/perfis/editar/"

def test_apis():
    print("🧪 TESTANDO APIs DE PERFIS")
    print("=" * 50)
    
    # Criar sessão
    session = requests.Session()
    
    # 1. Testar se o servidor está rodando
    try:
        response = session.get(BASE_URL)
        print(f"✅ Servidor respondendo: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao conectar com servidor: {e}")
        return
    
    # 2. Testar URL de criar perfil
    try:
        # Tentar sem autenticação (deve dar erro)
        response = session.post(CRIAR_PERFIL_URL, 
                               json={"codigo": "TESTE", "nome": "Teste"})
        print(f"📡 API criar perfil (sem auth): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Resposta: {data}")
        else:
            print(f"📋 Resposta: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Erro ao testar API criar: {e}")
    
    # 3. Testar URL de editar perfil
    try:
        response = session.post(EDITAR_PERFIL_URL, 
                               json={"codigo": "ADMIN", "nome": "Administrador Teste"})
        print(f"📡 API editar perfil (sem auth): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Resposta: {data}")
        else:
            print(f"📋 Resposta: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Erro ao testar API editar: {e}")

if __name__ == "__main__":
    test_apis()
