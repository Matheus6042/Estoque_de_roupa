# 📦 Sistema Desktop de Controle de Estoque e Vendas

Uma aplicação desktop desenvolvida em **Python**, utilizando **CustomTkinter** para uma interface moderna e **SQLite3** para armazenamento de dados local. Projetada para controle de inventário e operação de caixa no comércio varejista.

---

## 🚀 Destaques da Aplicação

- **🎨 Interface Moderna & Temas**: Suporte a modo Claro (*Light*), Escuro (*Dark*) e Automático (*System*), mantendo a preferência salva localmente.
- **🔐 Autenticação & Permissões por Perfil**:
  - **Proprietário**: Acesso total a configurações, gestão de usuários, relatórios e controle financeiro.
  - **Caixa**: Permissões personalizáveis diretamente pelo painel administrativo.
- **⚡ Alta Eficiência no Atendimento**:
  - Validação em tempo real (bloqueio de caracteres inválidos nos campos numéricos de preço e quantidade).
  - Atalhos de teclado (`Enter`) integrados na busca e na confirmação de movimentações (pronto para leitor de código de barras).
- **📊 Alerta Visual de Estoque**: Destaque automático em vermelho para produtos com quantidade igual ou inferior a 5 unidades.
- **📄 Histórico de Movimentações**: Registro visual colorido diferenciando **Entradas** (Verde) e **Saídas/Vendas** (Vermelho).
- **📊 Exportação de Dados**: Geração de relatórios em formato `.csv` (compatível com Microsoft Excel e codificado em UTF-8 com BOM para preservar acentuação).
- **💾 Gestão de Backup**: Módulo integrado para backup e restauração do banco de dados SQLite com tratamento amigável de erros do sistema operacional.

---

## 🛠️ Arquitetura do Projeto

```text
├── main.py        # Ponto de entrada da aplicação e inicialização do tema
├── interface.py   # Camada de apresentação (UI/UX) construída com CustomTkinter
└── banco.py       # Camada de dados e regras de negócio usando SQLite3
```

---

## ⚙️ Como Executar o Projeto

### Pré-requisitos
- Python 3.10 ou superior instalado.

### Passo a Passo
1. Clone este repositório:
   ```bash
   git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
   ```
2. Instale a biblioteca da interface:
   ```bash
   pip install customtkinter
   ```
3. Inicie o sistema a partir do arquivo principal:
   ```bash
   python main.py
   ```

---

## 🔐 Credenciais Padrão (Primeiro Acesso)

Ao iniciar o sistema pela primeira vez, o banco de dados é criado automaticamente com as seguintes credenciais de teste:

| Usuário | Senha | Perfil |
| :--- | :--- | :--- |
| `dono` | `123` | Proprietário (Acesso Total) |
| `caixa` | `123` | Operador de Caixa |

*As senhas podem ser alteradas dentro do menu de Configurações.*