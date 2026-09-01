"""
Módulo de persistência de dados.
Contém a classe BancoDeDados, responsável por gerenciar a conexão com o SQLite
e executar todas as operações de CRUD (Create, Read, Update, Delete) do sistema.
"""
import sqlite3
from datetime import datetime

class BancoDeDados:
    """Classe responsável por gerenciar as conexões e queries do banco de dados SQLite."""
    
    def __init__(self, db_name="estoque.db"):
        """Inicializa a instância e garante a criação estrutural das tabelas."""
        self.db_name = db_name
        self._criar_tabelas()

    def conectar(self):
        """Estabelece e retorna uma nova conexão com o banco de dados."""
        return sqlite3.connect(self.db_name)

    def _criar_tabelas(self):
        """Cria as tabelas 'estoque', 'historico' e 'usuarios' caso não existam, e insere usuários padrão."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT NOT NULL,
                    categoria TEXT, tamanho TEXT, cor TEXT, quantidade INTEGER NOT NULL, preco REAL NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, produto_nome TEXT, cliente TEXT,
                    quantidade INTEGER, data_hora TEXT, tipo TEXT DEFAULT 'Saída'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT,
                    perfil TEXT, p_ver_financeiro INTEGER, p_cadastrar_produto INTEGER,
                    p_fazer_entrada INTEGER, p_ver_historico INTEGER
                )
            """)
            
            # Verificação de integridade para atualizações de versão do banco
            cursor.execute("PRAGMA table_info(historico)")
            if "tipo" not in [col[1] for col in cursor.fetchall()]:
                cursor.execute("ALTER TABLE historico ADD COLUMN tipo TEXT DEFAULT 'Saída'")
                
            # População inicial de credenciais (se o banco for novo)
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO usuarios (usuario, senha, perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico) VALUES ('dono', '123', 'proprietario', 1, 1, 1, 1)")
                cursor.execute("INSERT INTO usuarios (usuario, senha, perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico) VALUES ('caixa', '123', 'funcionario', 0, 0, 0, 1)")
            conn.commit()

    def fazer_login(self, usuario, senha):
        """
        Valida as credenciais do usuário.
        Retorna uma tupla com o perfil e permissões, ou None se inválido.
        """
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
            return cursor.fetchone()

    def buscar_produtos(self, termo=""):
        """Retorna todos os produtos, filtrando por nome ou SKU caso um termo seja fornecido."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            if termo:
                busca_sql = f"%{termo}%"
                cursor.execute("SELECT * FROM estoque WHERE nome LIKE ? OR sku LIKE ?", (busca_sql, busca_sql))
            else:
                cursor.execute("SELECT * FROM estoque")
            return cursor.fetchall()

    def adicionar_produto(self, sku, nome, categoria, tamanho, cor, qtd, preco):
        """Insere um novo registro de produto no inventário."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO estoque (sku, nome, categoria, tamanho, cor, quantidade, preco) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (sku, nome, categoria, tamanho, cor, qtd, preco))
            conn.commit()

    def atualizar_produto(self, id_prod, sku, nome, categoria, tamanho, cor, qtd, preco):
        """Sobrescreve os dados de um produto existente baseado no seu ID primário."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE estoque SET sku=?, nome=?, categoria=?, tamanho=?, cor=?, quantidade=?, preco=? WHERE id=?", 
                           (sku, nome, categoria, tamanho, cor, qtd, preco, id_prod))
            conn.commit()

    def excluir_produto(self, id_prod):
        """Remove um produto do banco de dados e reseta o auto-incremento se a tabela ficar vazia."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM estoque WHERE id=?", (id_prod,))
            cursor.execute("SELECT COUNT(*) FROM estoque")
            if cursor.fetchone()[0] == 0:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='estoque'")
            conn.commit()

    def buscar_produto_por_id(self, id_prod):
        """Recupera o nome e a quantidade atual de um produto específico."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome, quantidade FROM estoque WHERE id=?", (id_prod,))
            return cursor.fetchone()

    def registrar_movimentacao(self, id_prod, tipo_mov, envolvido, qtd_mov, novo_estoque, nome_produto):
        """Atualiza o saldo do produto no estoque e gera um registro de transação no histórico."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE estoque SET quantidade=? WHERE id=?", (novo_estoque, id_prod))
            cursor.execute("INSERT INTO historico (tipo, produto_nome, cliente, quantidade, data_hora) VALUES (?, ?, ?, ?, ?)", 
                           (tipo_mov, nome_produto, envolvido, qtd_mov, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()

    def buscar_historico(self):
        """Retorna o log completo de movimentações de estoque, ordenado do mais recente para o mais antigo."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, tipo, produto_nome, cliente, quantidade, data_hora FROM historico ORDER BY id DESC")
            return cursor.fetchall()

    def excluir_historico(self, id_hist):
        """Deleta permanentemente um registro específico do histórico de transações."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historico WHERE id=?", (id_hist,))
            conn.commit()

    def buscar_permissoes_caixa(self):
        """Consulta a matriz de permissões atribuída ao perfil 'caixa'."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico FROM usuarios WHERE usuario='caixa'")
            return cursor.fetchone()

    def salvar_configuracoes(self, s_dono, s_caixa, p_fin, p_cad, p_ent, p_his):
        """Atualiza senhas e permissões administrativas no banco de dados."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            if s_dono: 
                cursor.execute("UPDATE usuarios SET senha=? WHERE usuario='dono'", (s_dono,))
            if s_caixa: 
                cursor.execute("UPDATE usuarios SET senha=? WHERE usuario='caixa'", (s_caixa,))
            cursor.execute("""
                UPDATE usuarios 
                SET p_ver_financeiro=?, p_cadastrar_produto=?, p_fazer_entrada=?, p_ver_historico=? 
                WHERE usuario='caixa'
            """, (p_fin, p_cad, p_ent, p_his))
            conn.commit()