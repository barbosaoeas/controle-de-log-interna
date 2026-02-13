#!/usr/bin/env python
"""Script para debugar chamados e filtros"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_log.settings')
django.setup()

from frota_locada.models import ChamadoManutencao, VeiculoLocado, Maquina, TipoVeiculo
from django.db.models import Q

print("=" * 80)
print("DEBUG: ANÁLISE DE CHAMADOS")
print("=" * 80)

# Estatísticas gerais
total = ChamadoManutencao.objects.count()
com_veiculo = ChamadoManutencao.objects.filter(veiculo_locado__isnull=False).count()
com_maquina = ChamadoManutencao.objects.filter(maquina__isnull=False).count()
sem_nenhum = ChamadoManutencao.objects.filter(veiculo_locado__isnull=True, maquina__isnull=True).count()

print(f"\nESTATÍSTICAS GERAIS:")
print(f"  Total de chamados: {total}")
print(f"  Com veiculo_locado: {com_veiculo}")
print(f"  Com maquina: {com_maquina}")
print(f"  Sem equipamento: {sem_nenhum}")

# Listar TODOS os chamados
print("\n" + "=" * 80)
print("TODOS OS CHAMADOS:")
print("=" * 80)

chamados = ChamadoManutencao.objects.all().select_related(
    'veiculo_locado', 'veiculo_locado__tipo_veiculo', 'maquina'
).order_by('-data_abertura')

for ch in chamados:
    print(f"\n{ch.numero_chamado} - Status: {ch.status}")
    if ch.veiculo_locado:
        print(f"  ✅ VEICULO_LOCADO:")
        print(f"     Placa: {ch.veiculo_locado.placa}")
        print(f"     Modelo: {ch.veiculo_locado.modelo}")
        print(f"     Tipo: {ch.veiculo_locado.tipo_veiculo.nome} (ID: {ch.veiculo_locado.tipo_veiculo.id})")
    elif ch.maquina:
        print(f"  ✅ MAQUINA:")
        print(f"     Código: {ch.maquina.codigo}")
        print(f"     Nome: {ch.maquina.nome}")
        print(f"     Tipo: {ch.maquina.tipo}")
    else:
        print(f"  ❌ SEM EQUIPAMENTO VINCULADO!")

# Testar filtro por PTA
print("\n" + "=" * 80)
print("TESTE DE FILTRO POR PTA:")
print("=" * 80)

tipo_pta = TipoVeiculo.objects.filter(nome__icontains='PTA').first()
if tipo_pta:
    print(f"\nTipo PTA encontrado: {tipo_pta.nome} (ID: {tipo_pta.id})")
    
    # Filtro 1: Apenas veiculo_locado
    filtro1 = ChamadoManutencao.objects.filter(veiculo_locado__tipo_veiculo=tipo_pta)
    print(f"\nFiltro 1 (veiculo_locado__tipo_veiculo={tipo_pta.id}): {filtro1.count()} chamados")
    for ch in filtro1:
        print(f"  - {ch.numero_chamado}: {ch.veiculo_locado.placa}")
    
    # Filtro 2: Apenas maquina
    filtro2 = ChamadoManutencao.objects.filter(maquina__tipo='PTA')
    print(f"\nFiltro 2 (maquina__tipo='PTA'): {filtro2.count()} chamados")
    for ch in filtro2:
        print(f"  - {ch.numero_chamado}: {ch.maquina.codigo}")
    
    # Filtro 3: Combinado (OR)
    filtro3 = ChamadoManutencao.objects.filter(
        Q(veiculo_locado__tipo_veiculo=tipo_pta) |
        Q(maquina__tipo='PTA')
    )
    print(f"\nFiltro 3 (veiculo_locado OU maquina): {filtro3.count()} chamados")
    for ch in filtro3:
        if ch.veiculo_locado:
            print(f"  - {ch.numero_chamado}: veiculo {ch.veiculo_locado.placa}")
        else:
            print(f"  - {ch.numero_chamado}: maquina {ch.maquina.codigo}")
else:
    print("\n❌ Tipo PTA não encontrado no banco!")

# Listar tipos disponíveis
print("\n" + "=" * 80)
print("TIPOS DE VEÍCULOS CADASTRADOS:")
print("=" * 80)
tipos = TipoVeiculo.objects.filter(ativo=True).order_by('nome')
for tipo in tipos:
    veiculos = VeiculoLocado.objects.filter(tipo_veiculo=tipo, status='ATIVO').count()
    print(f"  {tipo.id}: {tipo.nome} ({veiculos} veículos ativos)")

# Listar tipos de máquinas
print("\n" + "=" * 80)
print("TIPOS DE MÁQUINAS CADASTRADAS:")
print("=" * 80)
from django.db.models import Count
tipos_maquina = Maquina.objects.values('tipo').annotate(total=Count('id')).order_by('tipo')
for t in tipos_maquina:
    print(f"  {t['tipo']}: {t['total']} máquinas")

print("\n" + "=" * 80)
print("✅ Análise concluída!")
print("=" * 80)

