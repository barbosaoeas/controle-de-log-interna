#!/usr/bin/env python3
"""
🔍 DEBUG DO NOVO NAVBAR
Script para diagnosticar problemas com o novo navbar
"""

import os
from pathlib import Path

def verificar_arquivos():
    """Verifica se todos os arquivos necessários existem"""
    print("🔍 Verificando arquivos...")
    
    arquivos = {
        'CSS': 'static/css/navbar-novo.css',
        'Template': 'templates/components/navbar-novo.html',
        'Context Processor': 'core/context_processors.py',
    }
    
    for nome, caminho in arquivos.items():
        arquivo = Path(caminho)
        if arquivo.exists():
            tamanho = arquivo.stat().st_size
            print(f"✅ {nome}: {caminho} ({tamanho} bytes)")
        else:
            print(f"❌ {nome}: {caminho} - NÃO ENCONTRADO")

def verificar_configuracao():
    """Verifica configurações do Django"""
    print("\n⚙️ Verificando configurações...")

    # Verificar se o context processor foi adicionado
    try:
        with open('controle_materiais/settings.py', 'r', encoding='utf-8') as f:
            settings_content = f.read()

        if 'core.context_processors.navbar_context' in settings_content:
            print("✅ Context processor navbar_context adicionado")
        else:
            print("❌ Context processor navbar_context NÃO encontrado")

        if 'core.context_processors.user_permissions_context' in settings_content:
            print("✅ Context processor user_permissions_context adicionado")
        else:
            print("❌ Context processor user_permissions_context NÃO encontrado")

    except Exception as e:
        print(f"❌ Erro ao verificar settings.py: {e}")

def verificar_base_template():
    """Verifica se o base.html foi modificado corretamente"""
    print("\n📄 Verificando template base...")

    try:
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            base_content = f.read()

        if 'request.GET.novo_navbar' in base_content:
            print("✅ Condição novo_navbar encontrada no base.html")
        else:
            print("❌ Condição novo_navbar NÃO encontrada no base.html")

        if 'navbar-novo.css' in base_content:
            print("✅ Referência ao CSS novo encontrada")
        else:
            print("❌ Referência ao CSS novo NÃO encontrada")

        if 'components/navbar-novo.html' in base_content:
            print("✅ Include do template novo encontrado")
        else:
            print("❌ Include do template novo NÃO encontrado")

    except Exception as e:
        print(f"❌ Erro ao verificar base.html: {e}")

def gerar_url_teste():
    """Gera URLs de teste"""
    print("\n🔗 URLs para teste:")
    print("1. Navbar antigo: http://127.0.0.1:8000/")
    print("2. Navbar novo: http://127.0.0.1:8000/?novo_navbar=1")
    print("3. Login com navbar novo: http://127.0.0.1:8000/login/?novo_navbar=1")

def main():
    print("🔍 DEBUG DO NOVO NAVBAR")
    print("=" * 50)

    verificar_arquivos()
    verificar_configuracao()
    verificar_base_template()
    gerar_url_teste()
    
    print("\n" + "=" * 50)
    print("💡 DICAS DE TROUBLESHOOTING:")
    print("1. Certifique-se que o servidor está rodando")
    print("2. Acesse com ?novo_navbar=1 na URL")
    print("3. Abra o console do navegador (F12)")
    print("4. Procure por erros de JavaScript ou CSS")
    print("5. Verifique se aparece '🎨 Novo navbar ativado!' no console")

if __name__ == '__main__':
    main()
