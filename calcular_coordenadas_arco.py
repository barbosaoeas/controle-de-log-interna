#!/usr/bin/env python
"""
Script para calcular as coordenadas corretas dos arcos SVG.
"""

import math

def calcular_coordenadas_arco():
    """Calcula as coordenadas dos arcos SVG"""
    print("=" * 70)
    print("📐 CALCULANDO COORDENADAS DOS ARCOS SVG")
    print("=" * 70)
    
    # Parâmetros do gauge
    centro_x = 200
    centro_y = 200
    raio = 150
    
    # Percentuais das zonas
    percentuais = [0, 33.33, 40, 100]
    
    print("📊 Percentuais das zonas:")
    print(f"   Vermelho: {percentuais[0]}% - {percentuais[1]}%")
    print(f"   Amarelo: {percentuais[1]}% - {percentuais[2]}%")
    print(f"   Verde: {percentuais[2]}% - {percentuais[3]}%")
    
    # Converter percentuais para ângulos
    angulos = []
    for p in percentuais:
        angulo = -90 + (p * 1.8)  # Mesmo cálculo do JavaScript
        angulos.append(angulo)
    
    print(f"\n📐 Ângulos correspondentes:")
    for i, (p, a) in enumerate(zip(percentuais, angulos)):
        print(f"   {p}% = {a}°")
    
    # Converter ângulos para coordenadas
    coordenadas = []
    for angulo in angulos:
        # Converter para radianos
        rad = math.radians(angulo)
        
        # Calcular coordenadas
        x = centro_x + raio * math.cos(rad)
        y = centro_y + raio * math.sin(rad)
        
        coordenadas.append((x, y))
        print(f"   {angulo}° = ({x:.1f}, {y:.1f})")
    
    print(f"\n🎨 Paths SVG corretos:")
    
    # Arco vermelho: 0% - 33.33%
    x1, y1 = coordenadas[0]
    x2, y2 = coordenadas[1]
    print(f"\n🔴 Arco vermelho (0% - 33.33%):")
    print(f'   <path d="M {x1:.1f} {y1:.1f} A {raio} {raio} 0 0 1 {x2:.1f} {y2:.1f}"')
    print(f'         stroke="#dc3545" stroke-width="20" fill="none"/>')
    
    # Arco amarelo: 33.33% - 40%
    x1, y1 = coordenadas[1]
    x2, y2 = coordenadas[2]
    print(f"\n🟡 Arco amarelo (33.33% - 40%):")
    print(f'   <path d="M {x1:.1f} {y1:.1f} A {raio} {raio} 0 0 1 {x2:.1f} {y2:.1f}"')
    print(f'         stroke="#ffc107" stroke-width="20" fill="none"/>')
    
    # Arco verde: 40% - 100%
    x1, y1 = coordenadas[2]
    x2, y2 = coordenadas[3]
    print(f"\n🟢 Arco verde (40% - 100%):")
    print(f'   <path d="M {x1:.1f} {y1:.1f} A {raio} {raio} 0 0 1 {x2:.1f} {y2:.1f}"')
    print(f'         stroke="#28a745" stroke-width="20" fill="none"/>')
    
    # Verificação para 5200L
    percentual_5200 = 34.67
    angulo_5200 = -90 + (percentual_5200 * 1.8)
    rad_5200 = math.radians(angulo_5200)
    x_5200 = centro_x + raio * math.cos(rad_5200)
    y_5200 = centro_y + raio * math.sin(rad_5200)
    
    print(f"\n🎯 Verificação para 5200L:")
    print(f"   Percentual: {percentual_5200}%")
    print(f"   Ângulo: {angulo_5200:.1f}°")
    print(f"   Coordenada: ({x_5200:.1f}, {y_5200:.1f})")
    
    # Verificar em qual arco está
    if percentual_5200 <= 33.33:
        arco_correto = "🔴 Vermelho"
    elif percentual_5200 <= 40:
        arco_correto = "🟡 Amarelo"
    else:
        arco_correto = "🟢 Verde"
    
    print(f"   Deveria estar no arco: {arco_correto}")
    
    return coordenadas

def main():
    """Função principal"""
    coordenadas = calcular_coordenadas_arco()
    
    print("\n" + "=" * 70)
    print("✅ CÁLCULOS CONCLUÍDOS!")
    print("=" * 70)
    print("📋 Próximos passos:")
    print("   • Atualizar os paths SVG com as coordenadas corretas")
    print("   • Testar se o ponteiro aponta para a zona correta")
    
    return coordenadas

if __name__ == "__main__":
    main()
