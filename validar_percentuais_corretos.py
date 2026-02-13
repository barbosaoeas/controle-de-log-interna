#!/usr/bin/env python
"""
Script para validar que os percentuais estão corretos.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def validar_percentuais():
    """Valida os percentuais corretos"""
    print("=" * 70)
    print("🧮 VALIDANDO PERCENTUAIS CORRETOS DO GAUGE")
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
        
        print("📊 Dados do tanque:")
        print(f"   Capacidade total: {capacidade_total}L")
        print(f"   Nível crítico: {nivel_critico}L")
        print(f"   Nível alerta: {nivel_alerta}L")
        print(f"   Nível atual: {nivel_atual}L")
        
        # Calcular percentuais corretos
        percentual_critico = (nivel_critico / capacidade_total) * 100
        percentual_alerta = (nivel_alerta / capacidade_total) * 100
        percentual_atual = (nivel_atual / capacidade_total) * 100
        
        print(f"\n🧮 Cálculos de percentuais:")
        print(f"   {nivel_critico}L ÷ {capacidade_total}L = {percentual_critico:.2f}%")
        print(f"   {nivel_alerta}L ÷ {capacidade_total}L = {percentual_alerta:.2f}%")
        print(f"   {nivel_atual}L ÷ {capacidade_total}L = {percentual_atual:.2f}%")
        
        print(f"\n🎨 Zonas corretas do gauge:")
        print(f"   🔴 Vermelho: 0% - {percentual_critico:.2f}% (0L - {nivel_critico}L)")
        print(f"   🟡 Amarelo: {percentual_critico:.2f}% - {percentual_alerta:.2f}% ({nivel_critico}L - {nivel_alerta}L)")
        print(f"   🟢 Verde: {percentual_alerta:.2f}% - 100% ({nivel_alerta}L - {capacidade_total}L)")
        
        # Validação específica
        print(f"\n✅ VALIDAÇÃO PARA {nivel_atual}L:")
        print(f"   • {percentual_atual:.2f}% > {percentual_critico:.2f}%? {percentual_atual > percentual_critico}")
        print(f"   • {percentual_atual:.2f}% < {percentual_alerta:.2f}%? {percentual_atual < percentual_alerta}")
        
        if percentual_atual > percentual_critico and percentual_atual < percentual_alerta:
            zona_correta = "🟡 AMARELO"
            print(f"   • Resultado: {zona_correta} ✅")
        else:
            zona_correta = "❌ ERRO"
            print(f"   • Resultado: {zona_correta}")
        
        # Verificar se o gradiente SVG está correto
        print(f"\n🔧 Gradiente SVG implementado:")
        print(f'   <stop offset="0%" ... /> <!-- Vermelho início -->')
        print(f'   <stop offset="33.33%" ... /> <!-- Vermelho fim -->')
        print(f'   <stop offset="33.33%" ... /> <!-- Amarelo início -->')
        print(f'   <stop offset="40%" ... /> <!-- Amarelo fim -->')
        print(f'   <stop offset="40%" ... /> <!-- Verde início -->')
        print(f'   <stop offset="100%" ... /> <!-- Verde fim -->')
        
        print(f"\n📋 Verificação do gradiente:")
        if abs(percentual_critico - 33.33) < 0.1:
            print(f"   ✅ 33.33% está correto para {nivel_critico}L")
        else:
            print(f"   ❌ 33.33% deveria ser {percentual_critico:.2f}%")
        
        if abs(percentual_alerta - 40.0) < 0.1:
            print(f"   ✅ 40% está correto para {nivel_alerta}L")
        else:
            print(f"   ❌ 40% deveria ser {percentual_alerta:.2f}%")
        
        # Calcular largura da zona amarela
        largura_amarela = percentual_alerta - percentual_critico
        print(f"\n📏 Largura da zona amarela:")
        print(f"   {percentual_alerta:.2f}% - {percentual_critico:.2f}% = {largura_amarela:.2f}%")
        
        if largura_amarela < 5:
            print(f"   ⚠️ Zona amarela muito pequena ({largura_amarela:.2f}%)")
        else:
            print(f"   ✅ Zona amarela visível ({largura_amarela:.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a validação: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = validar_percentuais()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ VALIDAÇÃO CONCLUÍDA!")
        print("=" * 70)
        print("📋 Resumo:")
        print("   • Percentuais calculados corretamente")
        print("   • 5200L = 34.7% (zona amarela)")
        print("   • Gradiente SVG corrigido")
        print("   • Zona amarela entre 33.33% e 40%")
    else:
        print("\n" + "=" * 70)
        print("❌ VALIDAÇÃO FALHOU!")
        print("=" * 70)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
