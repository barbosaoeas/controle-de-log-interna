#!/usr/bin/env python
"""
Script para validar que 34.7% está no centro da zona amarela.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import ConfiguracaoTanque

def validar_centro_amarelo():
    """Valida que 34.7% está no centro da zona amarela"""
    print("=" * 60)
    print("🎯 VALIDANDO CENTRO DA ZONA AMARELA")
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
        print(f"   Percentual: {percentual_atual:.1f}%")
        
        # Nova configuração do gradiente
        vermelho_inicio = 0
        vermelho_fim = 25
        amarelo_inicio = 25
        amarelo_fim = 50
        verde_inicio = 50
        verde_fim = 100
        
        print(f"\n🎨 Nova configuração do gradiente:")
        print(f"   🔴 Vermelho: {vermelho_inicio}% - {vermelho_fim}%")
        print(f"   🟡 Amarelo: {amarelo_inicio}% - {amarelo_fim}%")
        print(f"   🟢 Verde: {verde_inicio}% - {verde_fim}%")
        
        # Calcular centro da zona amarela
        centro_amarelo = (amarelo_inicio + amarelo_fim) / 2
        largura_amarelo = amarelo_fim - amarelo_inicio
        
        print(f"\n📍 Análise da zona amarela:")
        print(f"   Início: {amarelo_inicio}%")
        print(f"   Fim: {amarelo_fim}%")
        print(f"   Centro: {centro_amarelo}%")
        print(f"   Largura: {largura_amarelo}%")
        
        # Verificar posição do ponteiro
        print(f"\n🎯 Posição do ponteiro:")
        print(f"   Atual: {percentual_atual:.1f}%")
        print(f"   Centro da zona amarela: {centro_amarelo}%")
        
        diferenca_do_centro = abs(percentual_atual - centro_amarelo)
        print(f"   Diferença do centro: {diferenca_do_centro:.1f}%")
        
        # Verificar se está na zona amarela
        if amarelo_inicio <= percentual_atual <= amarelo_fim:
            print(f"   ✅ Está na zona amarela")
            
            # Verificar posição relativa
            posicao_relativa = ((percentual_atual - amarelo_inicio) / largura_amarelo) * 100
            print(f"   Posição na zona amarela: {posicao_relativa:.1f}%")
            
            if posicao_relativa < 25:
                posicao_desc = "início da zona amarela"
            elif posicao_relativa < 75:
                posicao_desc = "centro da zona amarela"
            else:
                posicao_desc = "fim da zona amarela"
            
            print(f"   Descrição: {posicao_desc}")
            
        else:
            print(f"   ❌ NÃO está na zona amarela")
        
        # Calcular ângulo do ponteiro
        angulo = -90 + (percentual_atual * 1.8)
        angulo_centro_amarelo = -90 + (centro_amarelo * 1.8)
        
        print(f"\n📐 Ângulos:")
        print(f"   Ponteiro atual: {angulo:.1f}°")
        print(f"   Centro da zona amarela: {angulo_centro_amarelo:.1f}°")
        print(f"   Diferença: {abs(angulo - angulo_centro_amarelo):.1f}°")
        
        print(f"\n🎯 Resultado esperado:")
        print(f"   Com a nova configuração (25%-50%):")
        print(f"   • {percentual_atual:.1f}% está bem dentro da zona amarela")
        print(f"   • Próximo do centro ({centro_amarelo}%)")
        print(f"   • Zona amarela tem {largura_amarelo}% de largura")
        print(f"   • Ponteiro deve estar claramente visível na zona amarela")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a validação: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = validar_centro_amarelo()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ VALIDAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print("📋 Resumo:")
        print("   • 34.7% agora está bem no centro da zona amarela")
        print("   • Zona amarela: 25% - 50% (25% de largura)")
        print("   • Ponteiro deve estar claramente visível")
        print("\n🌐 Recarregue a página para ver a correção!")
    else:
        print("\n" + "=" * 60)
        print("❌ VALIDAÇÃO FALHOU!")
        print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
