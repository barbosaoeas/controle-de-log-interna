import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("\n" + "="*80)
print("VERIFICANDO CHAMADOS DE MANUTENÇÃO NO BANCO DE DADOS")
print("="*80 + "\n")

# Verificar se a tabela existe
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name LIKE '%chamado%'
""")
tabelas = cursor.fetchall()
print(f"Tabelas relacionadas a 'chamado': {tabelas}\n")

# Buscar todos os chamados
try:
    cursor.execute("""
        SELECT 
            numero_chamado,
            data_abertura,
            status,
            tipo_equipamento_id,
            maquina_id
        FROM frota_locada_chamadomanutencao
        ORDER BY data_abertura DESC
    """)
    
    chamados = cursor.fetchall()
    
    print(f"Total de chamados encontrados: {len(chamados)}\n")
    
    if chamados:
        print("Lista de chamados:")
        print("-" * 80)
        for chamado in chamados:
            numero, data, status, tipo_eq_id, maquina_id = chamado
            print(f"📋 {numero}")
            print(f"   Data: {data}")
            print(f"   Status: {status}")
            print(f"   Tipo Equipamento ID: {tipo_eq_id}")
            print(f"   Máquina ID: {maquina_id}")
            print()
    else:
        print("❌ Nenhum chamado encontrado!")
        
except sqlite3.Error as e:
    print(f"❌ ERRO ao consultar banco: {e}")

print("="*80)

conn.close()

