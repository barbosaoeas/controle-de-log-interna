#!/usr/bin/env python
"""
Script para calcular os percentuais corretos do gauge baseado nos níveis configuráveis.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def calcular_percentuais_gauge():
    """Calcula os percentuais corretos para o gauge"""
    print("=" * 70)
    print("📊 CALCULANDO PERCENTUAIS CORRETOS DO GAUGE")
    print("=" * 70)
    
    try:
        tanque = ConfiguracaoTanque.objects.first()
        if not tanque:
            print("❌ Nenhuma configuração de tanque encontrada")
            return False
        
        capacidade_total = float(tanque.capacidade_total)
        nivel_critico = float(tanque.nivel_critico)
        nivel_alerta = float(tanque.nivel_alerta)
        nivel_atual = float(tanque.nivel_atual)
        
        print("📋 Configuração atual:")
        print(f"   Capacidade total: {capacidade_total}L")
        print(f"   Nível crítico: {nivel_critico}L")
        print(f"   Nível alerta: {nivel_alerta}L")
        print(f"   Nível atual: {nivel_atual}L")
        
        # Calcular percentuais
        percentual_critico = (nivel_critico / capacidade_total) * 100
        percentual_alerta = (nivel_alerta / capacidade_total) * 100
        percentual_atual = (nivel_atual / capacidade_total) * 100
        
        print(f"\n📊 Percentuais calculados:")
        print(f"   Nível crítico ({nivel_critico}L): {percentual_critico:.1f}%")
        print(f"   Nível alerta ({nivel_alerta}L): {percentual_alerta:.1f}%")
        print(f"   Nível atual ({nivel_atual}L): {percentual_atual:.1f}%")
        
        print(f"\n🎨 Zonas do gauge:")
        print(f"   🔴 Vermelho: 0% - {percentual_critico:.1f}% (0L - {nivel_critico}L)")
        print(f"   🟡 Amarelo: {percentual_critico:.1f}% - {percentual_alerta:.1f}% ({nivel_critico}L - {nivel_alerta}L)")
        print(f"   🟢 Verde: {percentual_alerta:.1f}% - 100% ({nivel_alerta}L - {capacidade_total}L)")
        
        print(f"\n🎯 Posição atual:")
        if percentual_atual < percentual_critico:
            zona = "🔴 VERMELHO"
        elif percentual_atual < percentual_alerta:
            zona = "🟡 AMARELO"
        else:
            zona = "🟢 VERDE"
        
        print(f"   {nivel_atual}L ({percentual_atual:.1f}%) = {zona}")
        
        # Verificação específica para 5200L
        if nivel_atual == 5200:
            print(f"\n✅ VERIFICAÇÃO PARA 5200L:")
            print(f"   • 5200L = {percentual_atual:.1f}%")
            print(f"   • Está entre {percentual_critico:.1f}% e {percentual_alerta:.1f}%? {percentual_critico <= percentual_atual < percentual_alerta}")
            print(f"   • Deveria estar na zona AMARELA: ✅")
            
            if percentual_critico <= percentual_atual < percentual_alerta:
                print(f"   • Ponteiro deve estar na posição {percentual_atual:.1f}% do gauge")
                
                # Calcular ângulo do ponteiro
                angulo = -90 + (percentual_atual * 1.8)
                print(f"   • Ângulo do ponteiro: {angulo:.1f}°")
        
        print(f"\n🔧 Gradiente SVG correto:")
        print(f'   <stop offset="0%" style="stop-color:#dc3545;stop-opacity:1" />')
        print(f'   <stop offset="{percentual_critico:.1f}%" style="stop-color:#dc3545;stop-opacity:1" />')
        print(f'   <stop offset="{percentual_critico:.1f}%" style="stop-color:#ffc107;stop-opacity:1" />')
        print(f'   <stop offset="{percentual_alerta:.1f}%" style="stop-color:#ffc107;stop-opacity:1" />')
        print(f'   <stop offset="{percentual_alerta:.1f}%" style="stop-color:#28a745;stop-opacity:1" />')
        print(f'   <stop offset="100%" style="stop-color:#28a745;stop-opacity:1" />')
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o cálculo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = calcular_percentuais_gauge()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ CÁLCULOS CONCLUÍDOS!")
        print("=" * 70)
        print("📋 Próximos passos:")
        print("   • Recarregue a página do dashboard")
        print("   • O gradiente será atualizado automaticamente")
        print("   • O ponteiro deve aparecer na zona amarela")
    else:
        print("\n" + "=" * 70)
        print("❌ CÁLCULOS FALHARAM!")
        print("=" * 70)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
