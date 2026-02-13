#!/usr/bin/env python
"""
Script para adicionar campos ao modelo Equipamento diretamente no banco
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.db import connection

def adicionar_campos_equipamento():
    """Adiciona campos ao modelo Equipamento"""
    with connection.cursor() as cursor:
        try:
            print("🔧 Adicionando campos ao modelo Equipamento...")
            
            # Verificar se os campos já existem
            cursor.execute("PRAGMA table_info(core_equipamento)")
            colunas = [row[1] for row in cursor.fetchall()]
            
            campos_para_adicionar = [
                ('placa', 'ALTER TABLE core_equipamento ADD COLUMN placa VARCHAR(10) DEFAULT ""'),
                ('modelo', 'ALTER TABLE core_equipamento ADD COLUMN modelo VARCHAR(100) DEFAULT ""'),
                ('ano', 'ALTER TABLE core_equipamento ADD COLUMN ano INTEGER NULL'),
                ('capacidade_tanque', 'ALTER TABLE core_equipamento ADD COLUMN capacidade_tanque DECIMAL(8,2) NULL'),
                ('consumo_medio', 'ALTER TABLE core_equipamento ADD COLUMN consumo_medio DECIMAL(5,2) NULL'),
                ('tem_agenda', 'ALTER TABLE core_equipamento ADD COLUMN tem_agenda BOOLEAN DEFAULT 1'),
            ]
            
            for campo, sql in campos_para_adicionar:
                if campo not in colunas:
                    print(f"📝 Adicionando campo: {campo}")
                    cursor.execute(sql)
                else:
                    print(f"✅ Campo {campo} já existe")
            
            print("✅ Campos adicionados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar campos: {e}")
            return False

def migrar_dados_veiculo():
    """Migra dados da tabela Veiculo para Equipamento"""
    try:
        print("🔄 Migrando dados de Veiculo para Equipamento...")
        
        from core.models import Veiculo, Equipamento
        
        # Mapear tipos de veículo para categorias de equipamento
        tipo_para_categoria = {
            'CAMINHAO': 'OUTROS',
            'CARRETA': 'CARRETA_HIDRAULICA',
            'TRATOR': 'TRATOR',
            'EMPILHADEIRA': 'EMPILHADEIRA',
            'MUNCK': 'CAMINHAO_MUNCK',
            'GUINDASTE': 'GUINDASTE_RODOVIARIO',
            'OUTROS': 'OUTROS',
        }
        
        # Mapear status de veículo para status operacional
        status_para_operacional = {
            'ATIVO': 'OPERACIONAL',
            'MANUTENCAO': 'MANUTENCAO',
            'INATIVO': 'INATIVO',
        }
        
        veiculos_migrados = 0
        
        for veiculo in Veiculo.objects.all():
            # Verificar se já existe um equipamento com a mesma placa
            equipamento_existente = Equipamento.objects.filter(placa=veiculo.placa).first()
            
            if equipamento_existente:
                # Atualizar equipamento existente com dados do veículo
                equipamento_existente.modelo = veiculo.modelo or ''
                equipamento_existente.ano = veiculo.ano
                equipamento_existente.capacidade_tanque = veiculo.capacidade_tanque
                equipamento_existente.consumo_medio = veiculo.consumo_medio
                equipamento_existente.tem_agenda = veiculo.tem_agenda
                equipamento_existente.categoria = tipo_para_categoria.get(veiculo.tipo, 'OUTROS')
                equipamento_existente.status_operacional = status_para_operacional.get(veiculo.status, 'OPERACIONAL')
                equipamento_existente.ativo = veiculo.ativo
                equipamento_existente.save()
                print(f"✅ Atualizado equipamento existente: {equipamento_existente.nome}")
            else:
                # Criar novo equipamento baseado no veículo
                equipamento = Equipamento.objects.create(
                    nome=veiculo.nome,
                    codigo=veiculo.placa,  # Usar placa como código
                    categoria=tipo_para_categoria.get(veiculo.tipo, 'OUTROS'),
                    status_operacional=status_para_operacional.get(veiculo.status, 'OPERACIONAL'),
                    descricao=f'Migrado de veículo: {veiculo.modelo or ""}',
                    ativo=veiculo.ativo,
                    em_servico=True,
                    placa=veiculo.placa,
                    modelo=veiculo.modelo or '',
                    ano=veiculo.ano,
                    capacidade_tanque=veiculo.capacidade_tanque,
                    consumo_medio=veiculo.consumo_medio,
                    tem_agenda=veiculo.tem_agenda,
                )
                print(f"✅ Criado novo equipamento: {equipamento.nome}")
            
            veiculos_migrados += 1
        
        print(f"🎉 {veiculos_migrados} veículos migrados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao migrar dados: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando migração de Veículos para Equipamentos...")
    
    # Passo 1: Adicionar campos
    if not adicionar_campos_equipamento():
        sys.exit(1)
    
    # Passo 2: Migrar dados
    if not migrar_dados_veiculo():
        sys.exit(1)
    
    print("🎉 Migração concluída com sucesso!")
    print("📝 Agora você pode atualizar as views para usar Equipamento em vez de Veiculo")
