# REFATORAÇÃO MANUAL DAS VIEWS

## Views que precisam ser atualizadas:

### 1. `api_editar_perfil` (linha ~3207)
**Substituir:**
```python
# Verificar se o perfil existe nos perfis padrão
perfis_existentes = dict(PerfilUsuario.PERFIL_CHOICES)
if codigo not in perfis_existentes:
    return JsonResponse({'success': False, 'error': 'Perfil não encontrado nos perfis padrão do sistema'})

# Buscar ou criar registro de descrição personalizada
descricao_perfil, created = DescricaoPerfil.objects.get_or_create(...)
```

**Por:**
```python
from .models import TipoPerfil

# Buscar o tipo de perfil
try:
    tipo_perfil = TipoPerfil.objects.get(codigo=codigo)
except TipoPerfil.DoesNotExist:
    return JsonResponse({'success': False, 'error': f'Perfil {codigo} não encontrado'})

# Atualizar
tipo_perfil.nome = nome
tipo_perfil.descricao = descricao
tipo_perfil.save()
```

### 2. `api_remover_perfil` (linha ~3288)
**Substituir:**
```python
from .models import DescricaoPerfil
descricao_perfil = DescricaoPerfil.objects.get(codigo_perfil=codigo)
```

**Por:**
```python
from .models import TipoPerfil
tipo_perfil = TipoPerfil.objects.get(codigo=codigo)

# Verificar se pode excluir
if excluir_completamente:
    pode_excluir, mensagem = tipo_perfil.pode_ser_excluido()
    if not pode_excluir:
        return JsonResponse({'success': False, 'error': mensagem})
    tipo_perfil.delete()
else:
    tipo_perfil.ativo = False
    tipo_perfil.save()
```

### 3. `api_reativar_perfil` (linha ~3440)
**Substituir:**
```python
from .models import DescricaoPerfil
descricao_perfil = DescricaoPerfil.objects.get(codigo_perfil=codigo)
descricao_perfil.ativo = True
descricao_perfil.save()
```

**Por:**
```python
from .models import TipoPerfil
tipo_perfil = TipoPerfil.objects.get(codigo=codigo)
tipo_perfil.ativo = True
tipo_perfil.save()
```

### 4. Todas as referências a `perfil.perfil` devem ser substituídas por `perfil.codigo_perfil`

Exemplo:
```python
# ANTES:
f'👤 Perfil do usuário: {perfil.perfil}'

# DEPOIS:
f'👤 Perfil do usuário: {perfil.codigo_perfil}'
```

## IMPORTANTE:
Após fazer essas alterações manualmente, rode as migrações:
```bash
python manage.py makemigrations
python manage.py migrate
```

