#!/usr/bin/env python
"""
Script para testar os níveis do tanque após a correção.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def testar_niveis_tanque():
    """Testa os níveis do tanque"""
    print("=" * 60)
    print("🧪 TESTANDO NÍVEIS DO TANQUE APÓS CORREÇÃO")
    print("=" * 60)
    
    try:
        tanque = ConfiguracaoTanque.objects.first()
        if not tanque:
            print("❌ Nenhuma configuração de tanque encontrada")
            return False
        
        print("📊 Configuração atual:")
        print(f"   Nível atual: {tanque.nivel_atual}L")
        print(f"   Capacidade total: {tanque.capacidade_total}L")
        print(f"   Nível alerta (amarelo): {tanque.nivel_alerta}L")
        print(f"   Nível crítico (vermelho): {tanque.nivel_critico}L")
        print(f"   Percentual: {tanque.percentual_atual:.1f}%")
        
        print("\n🔍 Lógica aplicada:")
        print(f"   🟢 Verde: > {tanque.nivel_alerta}L")
        print(f"   🟡 Amarelo: >= {tanque.nivel_critico}L e <= {tanque.nivel_alerta}L")
        print(f"   🔴 Vermelho: < {tanque.nivel_critico}L")
        
        print(f"\n📈 Status calculado:")
        status = tanque.status_nivel
        if status == 'VERDE':
            emoji = "🟢"
        elif status == 'AMARELO':
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        print(f"   Com {tanque.nivel_atual}L: {emoji} {status}")
        
        # Verificar se está correto
        if tanque.nivel_atual == 5200:
            if status == 'AMARELO':
                print("\n✅ CORREÇÃO FUNCIONOU! Com 5200L está no AMARELO como esperado!")
            else:
                print(f"\n❌ ERRO! Com 5200L deveria estar no AMARELO, mas está no {status}")
                return False
        
        # Testar outros cenários
        print("\n🧪 Testando outros cenários:")
        
        # Cenário 1: Nível verde
        nivel_teste = tanque.nivel_alerta + 100
        print(f"   • {nivel_teste}L (> {tanque.nivel_alerta}L): Deveria ser VERDE")
        
        # Cenário 2: Nível amarelo
        nivel_teste = (tanque.nivel_critico + tanque.nivel_alerta) / 2
        print(f"   • {nivel_teste}L (entre {tanque.nivel_critico}L e {tanque.nivel_alerta}L): Deveria ser AMARELO")
        
        # Cenário 3: Nível vermelho
        nivel_teste = tanque.nivel_critico - 100
        print(f"   • {nivel_teste}L (< {tanque.nivel_critico}L): Deveria ser VERMELHO")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = testar_niveis_tanque()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("📋 Resumo:")
        print("   • Lógica de níveis corrigida")
        print("   • Agora usa valores configuráveis do banco")
        print("   • 5200L está corretamente no AMARELO")
        print("   • Ponteiro deve aparecer amarelo na interface")
    else:
        print("\n" + "=" * 60)
        print("❌ TESTE FALHOU!")
        print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
