#!/usr/bin/env python
"""Script para preencher o campo tipo_equipamento nos chamados existentes"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_log.settings')
django.setup()

from frota_locada.models import ChamadoManutencao

print("=" * 80)
print("PREENCHENDO CAMPO tipo_equipamento NOS CHAMADOS EXISTENTES")
print("=" * 80)

# Buscar todos os chamados
chamados = ChamadoManutencao.objects.all()
total = chamados.count()
atualizados = 0
sem_equipamento = 0

print(f"\nTotal de chamados: {total}")

for chamado in chamados:
    # Se já tem tipo_equipamento, pular
    if chamado.tipo_equipamento:
        continue
    
    # Se tem veiculo_locado, pegar o tipo do veículo
    if chamado.veiculo_locado and chamado.veiculo_locado.tipo_veiculo:
        chamado.tipo_equipamento = chamado.veiculo_locado.tipo_veiculo
        chamado.save()
        atualizados += 1
        print(f"✅ {chamado.numero_chamado}: tipo_equipamento = {chamado.tipo_equipamento.nome}")
    else:
        sem_equipamento += 1
        print(f"⚠️  {chamado.numero_chamado}: SEM tipo_equipamento (sem veiculo_locado)")

print("\n" + "=" * 80)
print(f"✅ Chamados atualizados: {atualizados}")
print(f"⚠️  Chamados sem equipamento: {sem_equipamento}")
print("=" * 80)

