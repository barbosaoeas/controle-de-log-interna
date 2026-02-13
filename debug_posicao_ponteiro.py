#!/usr/bin/env python
"""
Script para debugar a posição do ponteiro.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def debug_posicao_ponteiro():
    """Debug da posição do ponteiro"""
    print("=" * 70)
    print("🔍 DEBUG DA POSIÇÃO DO PONTEIRO")
    print("=" * 70)
    
    try:
        tanque = ConfiguracaoTanque.objects.first()
        if not tanque:
            print("❌ Nenhuma configuração de tanque encontrada")
            return False
        
        nivel_atual = float(tanque.nivel_atual)
        capacidade_total = float(tanque.capacidade_total)
        percentual = (nivel_atual / capacidade_total) * 100
        
        print("📊 Dados atuais:")
        print(f"   Nível atual: {nivel_atual}L")
        print(f"   Capacidade total: {capacidade_total}L")
        print(f"   Percentual: {percentual:.2f}%")
        
        # Calcular ângulo como no JavaScript
        # 0% = -90 graus (esquerda), 100% = 90 graus (direita)
        angulo = -90 + (percentual * 1.8)
        
        print(f"\n🧮 Cálculo do ângulo:")
        print(f"   Fórmula: -90 + (percentual * 1.8)")
        print(f"   -90 + ({percentual:.2f} * 1.8)")
        print(f"   -90 + {percentual * 1.8:.2f}")
        print(f"   = {angulo:.2f}°")
        
        print(f"\n📐 Interpretação dos ângulos:")
        print(f"   -90° = Extrema esquerda (0%)")
        print(f"   -45° = Meio da esquerda (25%)")
        print(f"   0° = Centro (50%)")
        print(f"   +45° = Meio da direita (75%)")
        print(f"   +90° = Extrema direita (100%)")
        
        print(f"\n🎯 Posição atual:")
        print(f"   {nivel_atual}L = {percentual:.2f}% = {angulo:.2f}°")
        
        if angulo < -60:
            posicao_visual = "Extrema esquerda (zona vermelha)"
        elif angulo < -30:
            posicao_visual = "Esquerda (zona vermelha/amarela)"
        elif angulo < 0:
            posicao_visual = "Centro-esquerda (zona amarela)"
        elif angulo < 30:
            posicao_visual = "Centro-direita (zona amarela/verde)"
        elif angulo < 60:
            posicao_visual = "Direita (zona verde)"
        else:
            posicao_visual = "Extrema direita (zona verde)"
        
        print(f"   Posição visual: {posicao_visual}")
        
        # Verificar onde deveria estar baseado nas zonas
        print(f"\n🎨 Verificação das zonas:")
        print(f"   Zona vermelha: 0% - 33.33% (ângulos -90° a -30°)")
        print(f"   Zona amarela: 33.33% - 40% (ângulos -30° a -18°)")
        print(f"   Zona verde: 40% - 100% (ângulos -18° a +90°)")
        
        # Calcular onde deveria estar na zona amarela
        inicio_amarelo = 33.33
        fim_amarelo = 40.0
        angulo_inicio_amarelo = -90 + (inicio_amarelo * 1.8)
        angulo_fim_amarelo = -90 + (fim_amarelo * 1.8)
        
        print(f"\n📍 Zona amarela detalhada:")
        print(f"   Início: {inicio_amarelo}% = {angulo_inicio_amarelo:.1f}°")
        print(f"   Fim: {fim_amarelo}% = {angulo_fim_amarelo:.1f}°")
        print(f"   Atual: {percentual:.2f}% = {angulo:.1f}°")
        
        if angulo_inicio_amarelo <= angulo <= angulo_fim_amarelo:
            print(f"   ✅ Ponteiro DEVERIA estar na zona amarela")
        else:
            print(f"   ❌ Ponteiro NÃO está na zona amarela")
        
        # Problema possível
        print(f"\n🔍 Possíveis problemas:")
        print(f"   1. Gradiente SVG não corresponde aos ângulos")
        print(f"   2. Cálculo do ângulo está errado")
        print(f"   3. Transformação CSS não está funcionando")
        print(f"   4. Cache do navegador")
        
        print(f"\n🛠️ Solução sugerida:")
        print(f"   O ponteiro está em {angulo:.1f}°")
        print(f"   Deveria estar entre {angulo_inicio_amarelo:.1f}° e {angulo_fim_amarelo:.1f}°")
        print(f"   Diferença: {abs(angulo - ((angulo_inicio_amarelo + angulo_fim_amarelo) / 2)):.1f}°")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = debug_posicao_ponteiro()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ DEBUG CONCLUÍDO!")
        print("=" * 70)
        print("📋 Próximos passos:")
        print("   • Verificar console do navegador (F12)")
        print("   • Confirmar se o ângulo calculado está correto")
        print("   • Verificar se o gradiente SVG corresponde")
    else:
        print("\n" + "=" * 70)
        print("❌ DEBUG FALHOU!")
        print("=" * 70)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
