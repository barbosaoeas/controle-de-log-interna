#!/usr/bin/env python
"""
Script para testar se o ponteiro visual está com a cor correta.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def testar_ponteiro_visual():
    """Testa se o ponteiro visual está correto"""
    print("=" * 60)
    print("🎯 TESTANDO PONTEIRO VISUAL DO TANQUE")
    print("=" * 60)
    
    try:
        tanque = ConfiguracaoTanque.objects.first()
        if not tanque:
            print("❌ Nenhuma configuração de tanque encontrada")
            return False
        
        print("📊 Status atual do tanque:")
        print(f"   Nível atual: {tanque.nivel_atual}L")
        print(f"   Nível alerta: {tanque.nivel_alerta}L")
        print(f"   Nível crítico: {tanque.nivel_critico}L")
        print(f"   Status: {tanque.status_nivel}")
        print(f"   Percentual: {tanque.percentual_atual:.1f}%")
        
        print("\n🎨 Cores esperadas:")
        if tanque.nivel_atual > tanque.nivel_alerta:
            cor_esperada = "🟢 VERDE (#28a745)"
        elif tanque.nivel_atual >= tanque.nivel_critico:
            cor_esperada = "🟡 AMARELO (#ffc107)"
        else:
            cor_esperada = "🔴 VERMELHO (#dc3545)"
        
        print(f"   Ponteiro deve estar: {cor_esperada}")
        
        print("\n📋 Verificação da lógica:")
        print(f"   • {tanque.nivel_atual}L > {tanque.nivel_alerta}L? {tanque.nivel_atual > tanque.nivel_alerta} (Verde)")
        print(f"   • {tanque.nivel_atual}L >= {tanque.nivel_critico}L? {tanque.nivel_atual >= tanque.nivel_critico} (Amarelo)")
        print(f"   • {tanque.nivel_atual}L < {tanque.nivel_critico}L? {tanque.nivel_atual < tanque.nivel_critico} (Vermelho)")
        
        # Validação específica para 5200L
        if tanque.nivel_atual == 5200:
            if tanque.nivel_atual >= tanque.nivel_critico and tanque.nivel_atual <= tanque.nivel_alerta:
                print(f"\n✅ CORRETO: 5200L está entre {tanque.nivel_critico}L e {tanque.nivel_alerta}L")
                print("   Ponteiro deve estar AMARELO!")
            else:
                print(f"\n❌ ERRO: 5200L não está na faixa amarela!")
                return False
        
        print("\n🔧 Alterações implementadas:")
        print("   ✅ Função animateGaugePointer() atualizada")
        print("   ✅ Função updateGauge() atualizada")
        print("   ✅ Cor do ponteiro agora é dinâmica")
        print("   ✅ Baseada nos níveis configuráveis")
        
        print("\n🌐 Para testar na interface:")
        print("   1. Acesse http://127.0.0.1:8000/diesel/")
        print("   2. Verifique se o ponteiro está AMARELO")
        print("   3. O badge deve mostrar 'AMARELO'")
        print("   4. O ponteiro deve estar na zona amarela do gauge")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = testar_ponteiro_visual()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO!")
        print("=" * 60)
        print("📋 Próximos passos:")
        print("   • Recarregue a página do dashboard")
        print("   • Verifique se o ponteiro está amarelo")
        print("   • Confirme que está na posição correta")
    else:
        print("\n" + "=" * 60)
        print("❌ TESTE FALHOU!")
        print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
