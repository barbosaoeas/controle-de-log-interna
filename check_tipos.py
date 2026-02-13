#!/usr/bin/env python
"""Script para verificar tipos de veículos e chamados"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_log.settings')
django.setup()

from frota_locada.models import TipoVeiculo, VeiculoLocado, ChamadoManutencao

print("=" * 80)
print("TIPOS DE VEÍCULOS CADASTRADOS:")
print("=" * 80)
tipos = TipoVeiculo.objects.filter(ativo=True).order_by('nome')
for tipo in tipos:
    print(f"ID: {tipo.id} | Nome: {tipo.nome}")
    veiculos = VeiculoLocado.objects.filter(tipo_veiculo=tipo, status='ATIVO')
    print(f"  → Veículos ativos deste tipo: {veiculos.count()}")
    for v in veiculos[:3]:  # Mostrar apenas 3 primeiros
        print(f"     - {v.placa} - {v.modelo}")

print("\n" + "=" * 80)
print("CHAMADOS DE MANUTENÇÃO:")
print("=" * 80)
total_chamados = ChamadoManutencao.objects.count()
chamados_com_veiculo = ChamadoManutencao.objects.filter(veiculo_locado__isnull=False).count()
chamados_com_maquina = ChamadoManutencao.objects.filter(maquina__isnull=False).count()

print(f"Total de chamados: {total_chamados}")
print(f"Chamados com veiculo_locado: {chamados_com_veiculo}")
print(f"Chamados com maquina: {chamados_com_maquina}")

print("\n" + "=" * 80)
print("CHAMADOS COM VEÍCULO LOCADO (últimos 5):")
print("=" * 80)
chamados = ChamadoManutencao.objects.filter(veiculo_locado__isnull=False).select_related('veiculo_locado', 'veiculo_locado__tipo_veiculo').order_by('-data_abertura')[:5]
for c in chamados:
    print(f"Chamado: {c.numero_chamado}")
    print(f"  Veículo: {c.veiculo_locado.placa} - {c.veiculo_locado.modelo}")
    print(f"  Tipo: {c.veiculo_locado.tipo_veiculo.nome} (ID: {c.veiculo_locado.tipo_veiculo.id})")
    print(f"  Status: {c.status}")
    print()

print("\n" + "=" * 80)
print("TESTE DE FILTRO:")
print("=" * 80)
if tipos.exists():
    primeiro_tipo = tipos.first()
    print(f"Testando filtro com tipo: {primeiro_tipo.nome} (ID: {primeiro_tipo.id})")
    chamados_filtrados = ChamadoManutencao.objects.filter(
        veiculo_locado__isnull=False,
        veiculo_locado__tipo_veiculo_id=primeiro_tipo.id
    )
    print(f"Chamados encontrados: {chamados_filtrados.count()}")
    for c in chamados_filtrados[:3]:
        print(f"  - {c.numero_chamado}: {c.veiculo_locado.placa} - {c.veiculo_locado.modelo}")

