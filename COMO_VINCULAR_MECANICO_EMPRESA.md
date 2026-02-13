# 🎯 COMO VINCULAR MECÂNICO À EMPRESA

## 📍 LOCALIZAÇÃO

O vínculo do mecânico à empresa é feito no **CADASTRO DE USUÁRIO**, não no cadastro de empresa!

---

## 🚀 PASSO A PASSO

### **1. Cadastrar a Empresa** (se ainda não existir)

1. Faça login como **Admin** ou **Supervisor**
2. Clique em **"Empresas"** no menu lateral
3. Preencha o formulário:
   - Nome da Empresa: `Lokar Locações`
   - CNPJ: `11.111.111/0001-11`
   - Tipo: `Empresa Terceirizada`
   - Número do Contrato: `CONT-2024-001`
   - Nome do Contato: `João Silva`
   - Telefone: `(11) 1111-1111`
4. Clique em **"Adicionar Empresa"**

✅ **Empresa cadastrada!**

---

### **2. Cadastrar o Mecânico e Vincular à Empresa**

1. Clique em **"Usuários"** no menu lateral (ou "Gerenciar Usuários")
2. Preencha o formulário de **"Adicionar Novo Usuário"**:

```
┌─────────────────────────────────────────────────────────┐
│  📝 ADICIONAR NOVO USUÁRIO                              │
├─────────────────────────────────────────────────────────┤
│  Nome de Usuário: joao.lokar                            │
│  Primeiro Nome: João                                    │
│  Sobrenome: Silva                                       │
│                                                         │
│  Email: joao@lokar.com.br                               │
│  Telefone: (11) 98765-4321                              │
│  Setor: Manutenção                                      │
│                                                         │
│  Perfil de Acesso: Terceiro - Manutenção PTA ⭐        │
│  Empresa: Lokar Locações ⭐⭐⭐                          │
│  ☑️ Mecânico Disponível                                 │
│                                                         │
│  Senha Inicial: 123456 (padrão)                        │
│                                                         │
│  [Adicionar Usuário]                                    │
└─────────────────────────────────────────────────────────┘
```

3. Clique em **"Adicionar Usuário"**

✅ **Mecânico cadastrado e vinculado à empresa!**

---

## 🔍 CAMPOS IMPORTANTES

### **Perfil de Acesso**
Escolha um perfil que comece com **"Terceiro -"**:
- `Terceiro - Manutenção PTA`
- `Terceiro - Manutenção Empilhadeiras`
- `Terceiro - Manutenção Guindastes`
- `Terceiro - Manutenção Solda`
- `Terceiro - Manutenção Geral`

### **Empresa** ⭐ **OBRIGATÓRIO PARA TERCEIROS**
- Selecione a empresa à qual o mecânico pertence
- **Não pode ficar vazio** para perfis terceirizados
- Se deixar vazio, o sistema mostrará erro

### **Mecânico Disponível**
- ☑️ **Marcado**: Mecânico aparece nos chamados
- ☐ **Desmarcado**: Mecânico não aparece nos chamados

---

## ✅ VALIDAÇÕES AUTOMÁTICAS

O sistema valida automaticamente:

1. **Empresa obrigatória para terceiros**
   - Se selecionar perfil "Terceiro - ...", DEVE selecionar uma empresa
   - Caso contrário, mostra erro: ❌ "Empresa é obrigatória para perfis terceirizados"

2. **Empresa opcional para internos**
   - Perfis internos (Admin, Supervisor, Demandante, etc.) não precisam de empresa

---

## 📋 VERIFICAR VÍNCULOS

### **Opção 1: Na Lista de Usuários**

1. Vá em **"Usuários"** no menu lateral
2. Veja a coluna **"Empresa"** na tabela
3. Mecânicos terceirizados mostram a empresa em verde

```
┌──────────────────────────────────────────────────────────────┐
│  Usuário      │ Nome         │ Perfil          │ Empresa      │
├──────────────────────────────────────────────────────────────┤
│  joao.lokar   │ João Silva   │ Terceiro - PTA  │ Lokar Locações │
│  maria.lokar  │ Maria Santos │ Terceiro - Emp  │ Lokar Locações │
│  admin        │ Admin User   │ Administrador   │ -            │
└──────────────────────────────────────────────────────────────┘
```

### **Opção 2: Editando o Usuário**

1. Clique no botão **✏️ Editar** ao lado do usuário
2. Veja o campo **"Empresa"** preenchido
3. Pode alterar a empresa se necessário

---

## 🎯 COMO FUNCIONA NO SISTEMA

### **Quando criar um chamado:**

1. Usuário seleciona uma **máquina** (ex: PTA-LOKAR-01)
2. Sistema identifica que a máquina pertence à **Lokar Locações**
3. Sistema filtra automaticamente apenas mecânicos da **Lokar Locações**
4. Dropdown mostra:
   - ✅ João Silva (Lokar)
   - ✅ Maria Santos (Lokar)
   - ❌ Carlos Oliveira (TechServ) - **NÃO APARECE**
   - ❌ Pedro Ferreira (MecPro) - **NÃO APARECE**

### **Quando mecânico faz login:**

1. João Silva faz login (joao.lokar / 123456)
2. Dashboard mostra apenas chamados de máquinas da **Lokar Locações**
3. Não vê chamados de outras empresas

---

## 🛠️ EDITAR VÍNCULO

Para alterar a empresa de um mecânico:

1. Vá em **"Usuários"**
2. Clique em **✏️ Editar** ao lado do mecânico
3. Altere o campo **"Empresa"**
4. Clique em **"Salvar Alterações"**

---

## ❓ PERGUNTAS FREQUENTES

**P: Posso vincular um mecânico a mais de uma empresa?**
R: Não. Cada mecânico pertence a apenas uma empresa.

**P: E se eu não selecionar empresa para um terceiro?**
R: O sistema mostrará erro e não permitirá salvar.

**P: Posso mudar a empresa depois?**
R: Sim! Basta editar o usuário e alterar a empresa.

**P: Funcionários internos precisam de empresa?**
R: Não. Apenas terceirizados precisam.

**P: Como desativar um mecânico temporariamente?**
R: Desmarque a opção "Mecânico Disponível" ou mude o status para "Inativo".

---

## 🎊 RESUMO

1. **Cadastre a Empresa** (menu "Empresas")
2. **Cadastre o Usuário** (menu "Usuários")
3. **Selecione o Perfil** "Terceiro - ..."
4. **Selecione a Empresa** ⭐ **OBRIGATÓRIO**
5. **Marque "Disponível"** se o mecânico pode atender chamados
6. **Salve!**

✅ **Pronto! Mecânico vinculado à empresa!**

