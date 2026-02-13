#!/usr/bin/env python
"""
Script para criar uma foto de teste para demonstrar as thumbnails
"""
import os
import django
from PIL import Image, ImageDraw, ImageFont
import io

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Pedido
from django.core.files.base import ContentFile

def criar_imagem_teste():
    """Criar uma imagem de teste simples"""
    # Criar imagem 400x300 com fundo azul
    img = Image.new('RGB', (400, 300), color='#007bff')
    draw = ImageDraw.Draw(img)
    
    # Adicionar texto
    try:
        # Tentar usar fonte padrão
        font = ImageFont.load_default()
    except:
        font = None
    
    # Texto centralizado
    text = "FOTO DE COMPROVAÇÃO\nSERVIÇO CONCLUÍDO"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (400 - text_width) // 2
    y = (300 - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font, align='center')
    
    # Adicionar bordas decorativas
    draw.rectangle([10, 10, 390, 290], outline='white', width=3)
    
    # Salvar em bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=85)
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def adicionar_foto_teste():
    """Adicionar foto de teste a um pedido concluído"""
    # Buscar um pedido concluído sem foto
    pedido = Pedido.objects.filter(status='CONCLUIDO', foto_comprovacao__isnull=True).first()
    
    if not pedido:
        print("❌ Nenhum pedido concluído sem foto encontrado")
        return
    
    # Criar imagem de teste
    img_data = criar_imagem_teste()
    
    # Adicionar foto ao pedido
    pedido.foto_comprovacao.save(
        f'comprovacao_teste_pedido_{pedido.id}.jpg',
        ContentFile(img_data),
        save=True
    )
    
    print(f"✅ Foto de teste adicionada ao pedido #{pedido.id}")
    print(f"   Descrição: {pedido.descricao[:50]}...")
    print(f"   Status: {pedido.status}")
    print(f"   Foto URL: {pedido.foto_comprovacao.url}")
    print(f"   Acesse: http://127.0.0.1:8000/pedidos/{pedido.id}/")

if __name__ == '__main__':
    adicionar_foto_teste()
