#!/usr/bin/env python
"""Script para migrar chamados antigos de maquina para veiculo_locado"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_log.settings')
django.setup()

from frota_locada.models import ChamadoManutencao, VeiculoLocado, Maquina

print("=" * 80)
print("ANÁLISE DE CHAMADOS")
print("=" * 80)

# Estatísticas
total_chamados = ChamadoManutencao.objects.count()
com_veiculo = ChamadoManutencao.objects.filter(veiculo_locado__isnull=False).count()
com_maquina = ChamadoManutencao.objects.filter(maquina__isnull=False).count()
sem_nenhum = ChamadoManutencao.objects.filter(veiculo_locado__isnull=True, maquina__isnull=True).count()

print(f"Total de chamados: {total_chamados}")
print(f"  Com veiculo_locado: {com_veiculo}")
print(f"  Com maquina: {com_maquina}")
print(f"  Sem nenhum: {sem_nenhum}")

print("\n" + "=" * 80)
print("CHAMADOS COM MÁQUINA (podem ser veículos locados):")
print("=" * 80)

chamados_maquina = ChamadoManutencao.objects.filter(
    maquina__isnull=False,
    veiculo_locado__isnull=True
).select_related('maquina')

for chamado in chamados_maquina:
    print(f"\nChamado: {chamado.numero_chamado}")
    print(f"  Máquina: {chamado.maquina.codigo} - {chamado.maquina.nome}")
    print(f"  Tipo Máquina: {chamado.maquina.tipo}")
    
    # Tentar encontrar veículo locado correspondente
    # Procurar por placa/código similar
    codigo_maquina = chamado.maquina.codigo
    veiculo = VeiculoLocado.objects.filter(placa=codigo_maquina).first()
    
    if veiculo:
        print(f"  ✅ ENCONTRADO veículo locado: {veiculo.placa} - {veiculo.modelo}")
        print(f"     Tipo: {veiculo.tipo_veiculo.nome}")
        print(f"     Pode migrar? SIM")
    else:
        print(f"  ❌ NÃO encontrado veículo locado com placa '{codigo_maquina}'")
        print(f"     Pode migrar? NÃO")

print("\n" + "=" * 80)
print("CHAMADOS COM VEICULO_LOCADO:")
print("=" * 80)

chamados_veiculo = ChamadoManutencao.objects.filter(
    veiculo_locado__isnull=False
).select_related('veiculo_locado', 'veiculo_locado__tipo_veiculo')

for chamado in chamados_veiculo:
    print(f"\nChamado: {chamado.numero_chamado}")
    print(f"  Veículo: {chamado.veiculo_locado.placa} - {chamado.veiculo_locado.modelo}")
    print(f"  Tipo: {chamado.veiculo_locado.tipo_veiculo.nome}")
    print(f"  Status: {chamado.status}")

print("\n" + "=" * 80)
print("VEÍCULOS LOCADOS CADASTRADOS:")
print("=" * 80)

veiculos = VeiculoLocado.objects.filter(status='ATIVO').select_related('tipo_veiculo')
for v in veiculos:
    print(f"  {v.placa} - {v.modelo} (Tipo: {v.tipo_veiculo.nome})")

print("\n✅ Análise concluída!")

