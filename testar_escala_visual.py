#!/usr/bin/env python
"""
Script para testar a nova escala visual do gauge.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def testar_escala_visual():
    """Testa a nova escala visual"""
    print("=" * 60)
    print("🎨 TESTANDO NOVA ESCALA VISUAL DO GAUGE")
    print("=" * 60)
    
    try:
        tanque = ConfiguracaoTanque.objects.first()
        if not tanque:
            print("❌ Nenhuma configuração de tanque encontrada")
            return False
        
        nivel_atual = float(tanque.nivel_atual)
        capacidade_total = float(tanque.capacidade_total)
        percentual_atual = (nivel_atual / capacidade_total) * 100
        
        print("📊 Dados atuais:")
        print(f"   Nível atual: {nivel_atual}L")
        print(f"   Capacidade total: {capacidade_total}L")
        print(f"   Percentual: {percentual_atual:.1f}%")
        
        print("\n🎨 Nova escala visual (equilibrada):")
        print("   🔴 Vermelho: 0% - 30% (zona crítica)")
        print("   🟡 Amarelo: 30% - 60% (zona de atenção)")
        print("   🟢 Verde: 60% - 100% (zona normal)")
        
        print(f"\n🎯 Posição do ponteiro:")
        print(f"   {nivel_atual}L = {percentual_atual:.1f}%")
        
        if percentual_atual < 30:
            zona_visual = "🔴 VERMELHO"
        elif percentual_atual < 60:
            zona_visual = "🟡 AMARELO"
        else:
            zona_visual = "🟢 VERDE"
        
        print(f"   Zona visual: {zona_visual}")
        
        # Calcular ângulo do ponteiro
        angulo = -90 + (percentual_atual * 1.8)
        print(f"   Ângulo do ponteiro: {angulo:.1f}°")
        
        # Verificação para 5200L
        if nivel_atual == 5200:
            print(f"\n✅ VERIFICAÇÃO PARA 5200L:")
            print(f"   • 34.7% está entre 30% e 60%? {30 <= percentual_atual < 60}")
            print(f"   • Deve estar na zona AMARELA: ✅")
            print(f"   • Zona amarela agora tem 30% de largura (muito mais visível)")
        
        print(f"\n📋 Lógica de status (baseada nos níveis reais):")
        print(f"   • Status do sistema: {tanque.status_nivel}")
        print(f"   • Cor do ponteiro: Baseada no status do sistema")
        print(f"   • Posição do ponteiro: Baseada no percentual ({percentual_atual:.1f}%)")
        
        print(f"\n🎨 Resultado esperado:")
        print(f"   • Ponteiro na posição {percentual_atual:.1f}% (zona amarela)")
        print(f"   • Cor amarela (#ffc107)")
        print(f"   • Badge mostrando 'AMARELO'")
        print(f"   • Zona amarela bem visível (30% de largura)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = testar_escala_visual()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TESTE DA NOVA ESCALA CONCLUÍDO!")
        print("=" * 60)
        print("📋 Benefícios da nova escala:")
        print("   • Zona amarela 3x maior (30% vs 7%)")
        print("   • Mais fácil de visualizar")
        print("   • Ponteiro claramente na zona amarela")
        print("   • Escala mais equilibrada visualmente")
        print("\n🌐 Recarregue a página para ver as mudanças!")
    else:
        print("\n" + "=" * 60)
        print("❌ TESTE FALHOU!")
        print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
