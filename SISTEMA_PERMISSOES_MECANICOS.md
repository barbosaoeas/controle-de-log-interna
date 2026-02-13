# 🔐 SISTEMA DE PERMISSÕES - MECÂNICOS TERCEIRIZADOS

## 📋 VISÃO GERAL

Sistema de controle de acesso para mecânicos terceirizados atenderem chamados de manutenção.

---

## 🎯 CRITÉRIOS DE ACESSO

### **Para Acessar a Página "Meus Chamados":**

✅ **Mecânicos Terceirizados:**
- **Perfil:** `TERCEIRO_MANUTENCAO_PTA` (ou qualquer perfil que comece com `TERCEIRO_`)
- **Empresa:** Deve estar vinculado a uma empresa (ex: Lokar Locações)
- **Setor:** Manutenção PTA (definido no perfil)
- **Disponível:** Checkbox marcado no cadastro

✅ **Admin/Supervisor:**
- **Perfil:** `ADMIN` ou `SUPERVISOR`
- Veem **TODOS** os chamados de **TODAS** as empresas

---

## 🔒 REGRAS DE PERMISSÃO

### **1. Visualização de Chamados**

| Perfil | O que vê |
|--------|----------|
| **TERCEIRO_MANUTENCAO_PTA** | Apenas chamados de máquinas da **Lokar Locações** |
| **TERCEIRO_MANUTENCAO_EMPILHADEIRA** | Apenas chamados de máquinas da **sua empresa** |
| **ADMIN** | Todos os chamados de todas as empresas |
| **SUPERVISOR** | Todos os chamados de todas as empresas |

### **2. Iniciar Atendimento**

✅ **Pode iniciar:**
- Mecânico da mesma empresa da máquina
- Admin/Supervisor (qualquer chamado)

❌ **Não pode iniciar:**
- Mecânico de outra empresa
- Usuário sem empresa vinculada
- Chamado já finalizado ou cancelado

### **3. Finalizar Atendimento**

✅ **Pode finalizar:**
- Mecânico que iniciou o atendimento
- Outro mecânico da **mesma empresa** (trabalho colaborativo)
- Admin/Supervisor (qualquer atendimento)

❌ **Não pode finalizar:**
- Mecânico de outra empresa
- Atendimento já finalizado

---

## 👥 EXEMPLOS DE PERFIS

### **Exemplo 1: Mecânico da Lokar**
```
Nome: João Silva
Username: joao.lokar
Perfil: TERCEIRO_MANUTENCAO_PTA
Empresa: Lokar Locações
Setor: Manutenção PTA
Disponível: ✅ Sim

O que vê:
- Chamados de máquinas da Lokar Locações
- Apenas chamados AGUARDANDO ou EM_ATENDIMENTO
- Seus próprios atendimentos em andamento
```

### **Exemplo 2: Mecânico da TechServ**
```
Nome: Maria Santos
Username: maria.techserv
Perfil: TERCEIRO_MANUTENCAO_EMPILHADEIRA
Empresa: TechServ Manutenção
Setor: Manutenção Empilhadeira
Disponível: ✅ Sim

O que vê:
- Chamados de máquinas da TechServ Manutenção
- Apenas chamados AGUARDANDO ou EM_ATENDIMENTO
- Seus próprios atendimentos em andamento
```

### **Exemplo 3: Supervisor**
```
Nome: Carlos Admin
Username: carlos.admin
Perfil: SUPERVISOR
Empresa: (pode ser vazio ou Estaleiro Atlântico Sul)
Setor: Administração
Disponível: ✅ Sim

O que vê:
- TODOS os chamados de TODAS as empresas
- Todos os atendimentos
- Pode atender qualquer chamado
```

---

## 🚀 FLUXO DE TRABALHO

### **1. Cadastro do Mecânico**

**Admin cadastra o mecânico:**
```
Menu → Usuários → Adicionar

Nome: João Silva
Username: joao.lokar
Email: joao@lokar.com.br
Senha: 123456

Perfil: TERCEIRO_MANUTENCAO_PTA ⭐
Empresa: Lokar Locações ⭐
☑️ Disponível ⭐

[Salvar]
```

### **2. Login do Mecânico**

```
Username: joao.lokar
Senha: 123456

[Entrar]
```

### **3. Acesso à Página de Atendimento**

```
Menu Lateral → 🔧 Meus Chamados

✅ Sistema verifica:
   - Perfil começa com "TERCEIRO_"? ✅ Sim
   - Tem empresa vinculada? ✅ Sim (Lokar)
   - Está disponível? ✅ Sim

✅ ACESSO PERMITIDO!

Mostra:
- Chamados de máquinas da Lokar
- Atendimentos em andamento do João
```

### **4. Iniciar Atendimento**

```
João clica em [Iniciar] no chamado MAN-2024-001

✅ Sistema verifica:
   - Máquina é da Lokar? ✅ Sim
   - João é da Lokar? ✅ Sim
   - Chamado está AGUARDANDO? ✅ Sim

✅ ATENDIMENTO INICIADO!

Seleciona tipo: Manutenção Mecânica
[Confirmar]

→ Redireciona para Detalhes do Atendimento
```

### **5. Trabalho Colaborativo**

```
João iniciou o atendimento mas precisa sair.

Maria (também da Lokar) faz login:
Menu → Meus Chamados

Maria vê:
- Chamado MAN-2024-001 (EM_ATENDIMENTO)
- Atendimento iniciado por João

Maria clica em [Ver Detalhes]

✅ Sistema verifica:
   - Maria é da Lokar? ✅ Sim
   - Atendimento é da Lokar? ✅ Sim

✅ MARIA PODE FINALIZAR!

Maria preenche:
- Descrição: "Trocada correia dentada"
- Peças: "Correia XYZ-123"
☑️ Finalizar chamado completamente

[Finalizar Atendimento]

✅ ATENDIMENTO FINALIZADO!
✅ CHAMADO CONCLUÍDO!
```

---

## 🛡️ VALIDAÇÕES DE SEGURANÇA

### **View: meus_chamados**
```python
# 1. Verificar se tem perfil
if not hasattr(request.user, 'perfil'):
    ❌ ACESSO NEGADO

# 2. Verificar se é mecânico terceirizado ou admin/supervisor
if not (perfil.perfil.startswith('TERCEIRO_') or perfil.perfil in ['ADMIN', 'SUPERVISOR']):
    ❌ ACESSO NEGADO

# 3. Verificar se tem empresa (exceto admin/supervisor)
if perfil.perfil.startswith('TERCEIRO_') and not perfil.empresa:
    ❌ ACESSO NEGADO (mensagem: "Você não está vinculado a nenhuma empresa")

# 4. Filtrar chamados por empresa
if perfil.perfil in ['ADMIN', 'SUPERVISOR']:
    ✅ Todos os chamados
else:
    ✅ Apenas chamados da empresa do mecânico
```

### **View: iniciar_atendimento**
```python
# 1. Verificar se pode atender
if not chamado.pode_ser_atendido_por(request.user):
    ❌ ACESSO NEGADO

# 2. Verificar status do chamado
if chamado.status not in ['AGUARDANDO', 'EM_ATENDIMENTO']:
    ❌ ACESSO NEGADO
```

### **View: finalizar_atendimento**
```python
# 1. Verificar se pode editar
if not atendimento.pode_ser_editado_por(request.user):
    ❌ ACESSO NEGADO

# 2. Verificar status do atendimento
if atendimento.status == 'FINALIZADO':
    ❌ ACESSO NEGADO
```

---

## 📊 RESUMO DAS PERMISSÕES

| Ação | Mecânico Terceiro | Admin/Supervisor |
|------|-------------------|------------------|
| Ver chamados da sua empresa | ✅ | ✅ |
| Ver chamados de outras empresas | ❌ | ✅ |
| Iniciar atendimento (sua empresa) | ✅ | ✅ |
| Iniciar atendimento (outra empresa) | ❌ | ✅ |
| Finalizar seu atendimento | ✅ | ✅ |
| Finalizar atendimento de colega (mesma empresa) | ✅ | ✅ |
| Finalizar atendimento de outra empresa | ❌ | ✅ |

---

## ✅ SISTEMA COMPLETO E SEGURO!

**Todas as permissões estão implementadas e funcionando!** 🚀

