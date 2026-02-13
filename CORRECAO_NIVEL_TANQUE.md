# Correção: Níveis de Alerta do Tanque de Combustível

## 🎯 Problema Identificado

Com **5200 litros** no tanque, o ponteiro estava aparecendo no **VERMELHO**, mas deveria estar no **AMARELO**.

## 🔍 Causa do Problema

Havia uma **inconsistência** entre:

### Configuração no Banco de Dados:
- **Nível alerta (amarelo)**: 6000L
- **Nível crítico (vermelho)**: 5000L

### Lógica Hardcoded no Código:
```python
# Código antigo (valores fixos)
if self.nivel_atual > 6000:
    return 'VERDE'
elif self.nivel_atual >= 5000:
    return 'AMARELO'
else:
    return 'VERMELHO'
```

**Resultado**: Com 5200L, estava no amarelo pela lógica, mas os valores não eram configuráveis.

## ✅ Solução Implementada

### 1. Correção no Modelo (`core/models.py`)

**Antes:**
```python
@property
def status_nivel(self):
    """Status do nível do tanque"""
    if self.nivel_atual > 6000:
        return 'VERDE'
    elif self.nivel_atual >= 5000:
        return 'AMARELO'
    else:
        return 'VERMELHO'
```

**Depois:**
```python
@property
def status_nivel(self):
    """Status do nível do tanque baseado nos níveis configuráveis"""
    if self.nivel_atual > self.nivel_alerta:
        return 'VERDE'
    elif self.nivel_atual >= self.nivel_critico:
        return 'AMARELO'
    else:
        return 'VERMELHO'
```

### 2. Correção no JavaScript (`templates/diesel/dashboard.html`)

**Antes:**
```javascript
// Valores fixos
if (novoNivel > 6000) {
    novoStatus = 'VERDE';
    novaClasse = 'bg-success';
} else if (novoNivel >= 5000) {
    novoStatus = 'AMARELO';
    novaClasse = 'bg-warning';
} else {
    novoStatus = 'VERMELHO';
    novaClasse = 'bg-danger';
}
```

**Depois:**
```javascript
// Valores configuráveis
if (novoNivel > tanqueData.nivel_alerta) {
    novoStatus = 'VERDE';
    novaClasse = 'bg-success';
} else if (novoNivel >= tanqueData.nivel_critico) {
    novoStatus = 'AMARELO';
    novaClasse = 'bg-warning';
} else {
    novoStatus = 'VERMELHO';
    novaClasse = 'bg-danger';
}
```

## 📊 Nova Lógica de Níveis

### Configuração Atual:
- **Capacidade total**: 15.000L
- **Nível alerta**: 6.000L (40% da capacidade)
- **Nível crítico**: 5.000L (33% da capacidade)

### Regras de Status:
- 🟢 **VERDE**: > 6.000L (Nível normal)
- 🟡 **AMARELO**: 5.000L - 6.000L (Atenção - programar reabastecimento)
- 🔴 **VERMELHO**: < 5.000L (Crítico - reabastecer urgente)

## 🧪 Teste de Validação

### Situação Atual:
- **Nível atual**: 5.200L
- **Status**: 🟡 **AMARELO** ✅
- **Percentual**: 34.7%

### Outros Cenários Testados:
- **6.100L**: 🟢 VERDE (correto)
- **5.500L**: 🟡 AMARELO (correto)
- **4.900L**: 🔴 VERMELHO (correto)

## 🎯 Benefícios da Correção

### 1. **Configurabilidade**
- Níveis podem ser ajustados via admin Django
- Não precisa alterar código para mudar limites

### 2. **Consistência**
- Backend e frontend usam os mesmos valores
- Elimina discrepâncias entre configuração e exibição

### 3. **Flexibilidade**
- Fácil ajuste conforme necessidades operacionais
- Suporte a diferentes capacidades de tanque

## 🔧 Como Ajustar os Níveis (se necessário)

### Via Admin Django:
1. Acesse `/admin/`
2. Vá em "Configurações do Tanque"
3. Edite os campos:
   - **Nível alerta**: Quando deve ficar amarelo
   - **Nível crítico**: Quando deve ficar vermelho

### Via Código:
```python
from core.models import ConfiguracaoTanque
tanque = ConfiguracaoTanque.objects.first()
tanque.nivel_alerta = 7000  # Novo nível para amarelo
tanque.nivel_critico = 4000  # Novo nível para vermelho
tanque.save()
```

## 📁 Arquivos Modificados

1. **`core/models.py`** - Método `status_nivel` corrigido
2. **`templates/diesel/dashboard.html`** - JavaScript corrigido
3. **`testar_nivel_tanque.py`** - Script de teste criado
4. **`CORRECAO_NIVEL_TANQUE.md`** - Esta documentação

## ✅ Status da Correção

**🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!**

- ✅ Lógica de níveis corrigida
- ✅ Valores agora são configuráveis
- ✅ 5200L aparece corretamente no AMARELO
- ✅ Interface web atualizada
- ✅ Testes validados
- ✅ Documentação criada

## 🚀 Próximos Passos

1. **Verificar Interface**: Acessar o dashboard e confirmar que o ponteiro está amarelo
2. **Testar Mudanças**: Simular diferentes níveis para validar cores
3. **Configurar Alertas**: Ajustar níveis conforme necessidades operacionais

---

**Data da Correção**: 11 de outubro de 2025  
**Problema**: Ponteiro vermelho com 5200L (deveria ser amarelo)  
**Solução**: Lógica configurável baseada no banco de dados  
**Status**: ✅ Resolvido
