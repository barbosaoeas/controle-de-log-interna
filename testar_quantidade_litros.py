#!/usr/bin/env python
"""
Script para testar o campo 'quantidade_litros' nos equipamentos.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento

def testar_campo_quantidade_litros():
    """Testa se o campo quantidade_litros está funcionando corretamente"""
    print("=" * 60)
    print("🧪 TESTANDO CAMPO 'QUANTIDADE_LITROS' NOS EQUIPAMENTOS")
    print("=" * 60)
    
    try:
        # Teste 1: Verificar se o campo existe no modelo
        print("📋 Teste 1: Verificando se o campo existe no modelo...")
        equipamento_teste = Equipamento()
        if hasattr(equipamento_teste, 'quantidade_litros'):
            print("✅ Campo 'quantidade_litros' existe no modelo Equipamento")
        else:
            print("❌ Campo 'quantidade_litros' NÃO existe no modelo Equipamento")
            return False
        
        # Teste 2: Listar equipamentos existentes e seus valores
        print("\n📋 Teste 2: Verificando equipamentos existentes...")
        equipamentos = Equipamento.objects.all()
        
        if not equipamentos.exists():
            print("⚠️ Nenhum equipamento encontrado no banco de dados")
            return True
        
        print(f"📊 Total de equipamentos: {equipamentos.count()}")
        print("\n📝 Equipamentos e suas quantidades de litros:")
        print("-" * 80)
        print(f"{'Nome':<25} {'Código':<15} {'Categoria':<20} {'Qtd Litros':<15}")
        print("-" * 80)
        
        for eq in equipamentos:
            nome = eq.nome[:24] if len(eq.nome) > 24 else eq.nome
            codigo = eq.codigo[:14] if eq.codigo and len(eq.codigo) > 14 else (eq.codigo or '-')
            categoria = eq.categoria[:19] if len(eq.categoria) > 19 else eq.categoria
            qtd_litros = f"{eq.quantidade_litros}L" if eq.quantidade_litros else "Não definido"
            
            print(f"{nome:<25} {codigo:<15} {categoria:<20} {qtd_litros:<15}")
        
        # Teste 3: Criar um equipamento de teste
        print("\n📋 Teste 3: Criando equipamento de teste...")
        nome_teste = "Equipamento Teste Litros"
        
        # Verificar se já existe
        if Equipamento.objects.filter(nome=nome_teste).exists():
            print("⚠️ Equipamento de teste já existe, removendo...")
            Equipamento.objects.filter(nome=nome_teste).delete()
        
        # Criar novo equipamento
        equipamento_novo = Equipamento.objects.create(
            nome=nome_teste,
            codigo="TEST-LITROS",
            categoria="OUTROS",
            status_operacional="OPERACIONAL",
            ativo=True,
            em_servico=True,
            descricao="Equipamento criado para testar o campo quantidade_litros",
            quantidade_litros=Decimal('150.50')
        )
        
        print(f"✅ Equipamento criado: {equipamento_novo.nome}")
        print(f"   Quantidade de litros: {equipamento_novo.quantidade_litros}L")
        
        # Teste 4: Atualizar o equipamento
        print("\n📋 Teste 4: Atualizando quantidade de litros...")
        equipamento_novo.quantidade_litros = Decimal('200.75')
        equipamento_novo.save()
        
        # Recarregar do banco
        equipamento_novo.refresh_from_db()
        print(f"✅ Quantidade atualizada para: {equipamento_novo.quantidade_litros}L")
        
        # Teste 5: Testar valor nulo
        print("\n📋 Teste 5: Testando valor nulo...")
        equipamento_novo.quantidade_litros = None
        equipamento_novo.save()
        equipamento_novo.refresh_from_db()
        print(f"✅ Valor nulo aceito: {equipamento_novo.quantidade_litros}")
        
        # Limpar equipamento de teste
        print("\n🧹 Limpando equipamento de teste...")
        equipamento_novo.delete()
        print("✅ Equipamento de teste removido")
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 60)
        print("📋 Resumo dos testes:")
        print("   ✅ Campo existe no modelo")
        print("   ✅ Equipamentos existentes listados")
        print("   ✅ Criação com quantidade_litros funciona")
        print("   ✅ Atualização funciona")
        print("   ✅ Valor nulo é aceito")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_estrutura_banco():
    """Verifica a estrutura do banco de dados"""
    print("\n📋 Verificando estrutura do banco de dados...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Verificar colunas da tabela core_equipamento
        cursor.execute("PRAGMA table_info(core_equipamento)")
        colunas = cursor.fetchall()
        
        print("📊 Colunas da tabela core_equipamento:")
        for coluna in colunas:
            nome_coluna = coluna[1]
            tipo_coluna = coluna[2]
            nulo = "NULL" if coluna[3] == 0 else "NOT NULL"
            print(f"   • {nome_coluna} ({tipo_coluna}) {nulo}")
        
        # Verificar se quantidade_litros existe
        nomes_colunas = [coluna[1] for coluna in colunas]
        if 'quantidade_litros' in nomes_colunas:
            print("✅ Campo 'quantidade_litros' encontrado na tabela!")
        else:
            print("❌ Campo 'quantidade_litros' NÃO encontrado na tabela!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura do banco: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 INICIANDO TESTES DO CAMPO QUANTIDADE_LITROS")
    
    # Verificar estrutura do banco
    if not verificar_estrutura_banco():
        return False
    
    # Executar testes do modelo
    if not testar_campo_quantidade_litros():
        return False
    
    print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
