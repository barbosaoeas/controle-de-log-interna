#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_log.settings')
django.setup()

from frota_locada.models import ChamadoManutencao

print("\n" + "="*80)
print("VERIFICANDO TODOS OS CHAMADOS NO BANCO DE DADOS")
print("="*80 + "\n")

chamados = ChamadoManutencao.objects.all().order_by('-data_abertura')

print(f"Total de chamados: {chamados.count()}\n")

for chamado in chamados:
    print(f"📋 {chamado.numero_chamado}")
    print(f"   Data: {chamado.data_abertura}")
    print(f"   Equipamento: {chamado.maquina}")
    print(f"   Tipo: {chamado.tipo_equipamento}")
    print(f"   Status: {chamado.status}")
    print(f"   Solicitante: {chamado.solicitante}")
    print()

print("="*80)

