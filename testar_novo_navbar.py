#!/usr/bin/env python3
"""
🧪 TESTE DO NOVO NAVBAR COM DROPDOWNS
Script para validar se o novo navbar está funcionando corretamente
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import PerfilUsuario, Pedido, ConfiguracaoTanque, AbastecimentoTanque
from core.context_processors import navbar_context, user_permissions_context

def testar_context_processors():
    """Testa se os context processors estão funcionando"""
    print("🧪 Testando Context Processors...")
    
    # Criar mock request
    class MockRequest:
        def __init__(self, user):
            self.user = user
            self.GET = {'novo_navbar': '1'}
    
    # Testar com usuário admin
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            request = MockRequest(admin_user)
            
            # Testar navbar_context
            navbar_data = navbar_context(request)
            print(f"✅ Navbar context: {navbar_data}")
            
            # Testar user_permissions_context
            permissions_data = user_permissions_context(request)
            print(f"✅ Permissions context: {permissions_data}")
            
        else:
            print("❌ Nenhum usuário admin encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao testar context processors: {e}")

def testar_dados_navbar():
    """Testa se os dados necessários para o navbar existem"""
    print("\n🧪 Testando Dados do Navbar...")
    
    # Testar pedidos
    try:
        total_pedidos = Pedido.objects.count()
        pedidos_pendentes = Pedido.objects.filter(status='PENDENTE').count()
        print(f"✅ Pedidos: {total_pedidos} total, {pedidos_pendentes} pendentes")
    except Exception as e:
        print(f"❌ Erro ao buscar pedidos: {e}")
    
    # Testar configuração de tanque
    try:
        config_tanque = ConfiguracaoTanque.objects.first()
        if config_tanque:
            print(f"✅ Configuração de tanque: {config_tanque.capacidade_total}L")
            
            # Testar abastecimentos
            ultimo_abastecimento = AbastecimentoTanque.objects.order_by('-data_abastecimento').first()
            if ultimo_abastecimento:
                nivel_atual = ultimo_abastecimento.nivel_apos_abastecimento
                percentual = (nivel_atual / config_tanque.capacidade_total) * 100
                print(f"✅ Nível atual: {nivel_atual}L ({percentual:.1f}%)")
            else:
                print("⚠️ Nenhum abastecimento encontrado")
        else:
            print("❌ Configuração de tanque não encontrada")
    except Exception as e:
        print(f"❌ Erro ao buscar dados de combustível: {e}")

def testar_usuarios_perfis():
    """Testa se os usuários têm perfis adequados"""
    print("\n🧪 Testando Usuários e Perfis...")
    
    try:
        usuarios = User.objects.filter(is_active=True)
        print(f"✅ {usuarios.count()} usuários ativos encontrados")
        
        for user in usuarios[:5]:  # Mostrar apenas os primeiros 5
            if hasattr(user, 'perfil'):
                perfil = user.perfil.perfil
                setor = user.perfil.setor.nome if user.perfil.setor else 'Sem setor'
                print(f"   👤 {user.username} - {perfil} - {setor}")
            else:
                print(f"   ❌ {user.username} - SEM PERFIL")
                
    except Exception as e:
        print(f"❌ Erro ao buscar usuários: {e}")

def testar_arquivos_criados():
    """Verifica se todos os arquivos necessários foram criados"""
    print("\n🧪 Testando Arquivos Criados...")
    
    arquivos_necessarios = [
        'static/css/navbar-novo.css',
        'templates/components/navbar-novo.html',
        'core/context_processors.py',
    ]
    
    for arquivo in arquivos_necessarios:
        caminho_completo = os.path.join(settings.BASE_DIR, arquivo)
        if os.path.exists(caminho_completo):
            tamanho = os.path.getsize(caminho_completo)
            print(f"✅ {arquivo} - {tamanho} bytes")
        else:
            print(f"❌ {arquivo} - NÃO ENCONTRADO")

def testar_urls_acesso():
    """Testa URLs que serão usadas no navbar"""
    print("\n🧪 Testando URLs do Navbar...")
    
    from django.urls import reverse, NoReverseMatch
    
    urls_navbar = [
        'dashboard',
        'criar_pedido',
        'listar_pedidos',
        'relatorios_pedidos',
        'dashboard_diesel',
        'abastecer_veiculo',
        'historico_abastecimentos',
        'relatorio_compras_diesel',
        'alterar_senha',
        'logout',
    ]
    
    for url_name in urls_navbar:
        try:
            url = reverse(url_name)
            print(f"✅ {url_name} -> {url}")
        except NoReverseMatch:
            print(f"❌ {url_name} -> URL NÃO ENCONTRADA")

def main():
    """Função principal de teste"""
    print("🎨 TESTE DO NOVO NAVBAR COM DROPDOWNS")
    print("=" * 50)
    
    testar_arquivos_criados()
    testar_context_processors()
    testar_dados_navbar()
    testar_usuarios_perfis()
    testar_urls_acesso()
    
    print("\n" + "=" * 50)
    print("🎯 COMO TESTAR O NOVO NAVBAR:")
    print("1. Execute: python manage.py runserver")
    print("2. Acesse: http://127.0.0.1:8000/?novo_navbar=1")
    print("3. Faça login e verifique o novo navbar")
    print("4. Para voltar ao antigo: http://127.0.0.1:8000/")
    print("\n✅ TESTE CONCLUÍDO!")

if __name__ == '__main__':
    main()
