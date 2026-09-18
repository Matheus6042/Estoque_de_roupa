"""
Módulo de persistência de dados.
Contém a classe BancoDeDados, responsável por gerenciar a conexão com o SQLite
e executar todas as operações de CRUD (Create, Read, Update, Delete) do sistema.
"""
import sqlite3
import hashlib
import os
import shutil
from datetime import datetime
from contextlib import contextmanager

# ==========================================
# EXCEÇÕES PERSONALIZADAS (Regras de Negócio)
# ==========================================
class ErroBanco(Exception):
    """Erro conhecido da camada de persistência."""

class DadosInvalidosError(ErroBanco, ValueError):
    """Dados de domínio inválidos."""

class EstoqueInsuficienteError(ErroBanco):
    """A saída solicitada é maior que o saldo disponível."""

class BackupInvalidoError(ErroBanco):
    """O arquivo informado não é um backup válido da aplicação."""

# ==========================================
# GERENCIADOR DO BANCO DE DADOS
# ==========================================
class BancoDeDados:
    """Classe responsável por gerenciar as conexões e queries do banco de dados SQLite."""
    
    def __init__(self, db_name="estoque.db"):
        """Inicializa a instância e garante a criação estrutural das tabelas no diretório absoluto."""
        diretorio_base = os.path.dirname(os.path.abspath(__file__))
        self.db_name = os.path.join(diretorio_base, db_name)
        self._criar_tabelas()

    @contextmanager
    def _conexao(self):
        """
        Gerenciador de Contexto para transações. 
        Garante a abertura, commit, rollback em caso de falha e fechamento automático. (Resolve Ponto 6)
        """
        conn = sqlite3.connect(self.db_name, timeout=5)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _gerar_hash_senha(self, senha):
        """Aplica hash SHA-256 nas senhas para não salvar texto puro. (Resolve Ponto 2)"""
        return hashlib.sha256(senha.encode('utf-8')).hexdigest()

    def _criar_tabelas(self):
        """Cria as tabelas com travas de segurança (CHECK constraints) e insere usuários padrão."""
        with self._conexao() as conn:
            cursor = conn.cursor()
            
            # Resolve Ponto 7 (Checks) e Ponto 5 (Preço em centavos inteiros)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sku TEXT, 
                    nome TEXT NOT NULL CHECK (length(nome) > 0),
                    categoria TEXT, 
                    tamanho TEXT, 
                    cor TEXT, 
                    quantidade INTEGER NOT NULL CHECK (quantidade >= 0), 
                    preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    produto_nome TEXT, 
                    cliente TEXT,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0), 
                    data_hora TEXT, 
                    tipo TEXT DEFAULT 'Saída' CHECK (tipo IN ('Entrada', 'Saída'))
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    usuario TEXT UNIQUE, 
                    senha TEXT,
                    perfil TEXT, 
                    p_ver_financeiro INTEGER, 
                    p_cadastrar_produto INTEGER,
                    p_fazer_entrada INTEGER, 
                    p_ver_historico INTEGER
                )
            """)
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            if cursor.fetchone()[0] == 0:
                senha_padrao = self._gerar_hash_senha('123')
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico) VALUES (?, ?, 'proprietario', 1, 1, 1, 1)", 
                    ('dono', senha_padrao)
                )
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico) VALUES (?, ?, 'funcionario', 0, 0, 0, 1)", 
                    ('caixa', senha_padrao)
                )

    def fazer_login(self, usuario, senha):
        """Valida credenciais comparando hashes criptográficos."""
        with self._conexao() as conn:
            cursor = conn.cursor()
            senha_hash = self._gerar_hash_senha(senha)
            cursor.execute(
                "SELECT perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico FROM usuarios WHERE usuario=? AND senha=?", 
                (usuario, senha_hash)
            )
            return cursor.fetchone()

    def buscar_produtos(self, termo=""):
        """Retorna produtos, convertendo os centavos do banco para decimal visível na interface."""
        with self._conexao() as conn:
            cursor = conn.cursor()
            if termo:
                busca_sql = f"%{termo}%"
                cursor.execute("SELECT id, sku, nome, categoria, tamanho, cor, quantidade, preco_centavos FROM estoque WHERE nome LIKE ? OR sku LIKE ?", (busca_sql, busca_sql))
            else:
                cursor.execute("SELECT id, sku, nome, categoria, tamanho, cor, quantidade, preco_centavos FROM estoque")
            linhas = cursor.fetchall()
            # Retorna convertendo centavos em float
            return [(*linha[:7], linha[7] / 100.0) for linha in linhas]

    def adicionar_produto(self, sku, nome, categoria, tamanho, cor, qtd, preco):
        preco_centavos = int(round(preco * 100))
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO estoque (sku, nome, categoria, tamanho, cor, quantidade, preco_centavos) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                (sku, nome, categoria, tamanho, cor, qtd, preco_centavos)
            )

    def atualizar_produto(self, id_prod, sku, nome, categoria, tamanho, cor, qtd, preco):
        preco_centavos = int(round(preco * 100))
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE estoque SET sku=?, nome=?, categoria=?, tamanho=?, cor=?, quantidade=?, preco_centavos=? WHERE id=?", 
                (sku, nome, categoria, tamanho, cor, qtd, preco_centavos, id_prod)
            )

    def excluir_produto(self, id_prod):
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM estoque WHERE id=?", (id_prod,))
            cursor.execute("SELECT COUNT(*) FROM estoque")
            if cursor.fetchone()[0] == 0:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='estoque'")

    def buscar_produto_por_id(self, id_prod):
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome, quantidade FROM estoque WHERE id=?", (id_prod,))
            return cursor.fetchone()

    def movimentar_estoque(self, id_prod, tipo_mov, envolvido, qtd_mov):
        """
        Lógica transacional atômica. Lê, calcula e salva o estoque em bloco bloqueado. (Resolve Ponto 4)
        """
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE") # Bloqueia leitura de outros terminais durante a venda
            
            cursor.execute("SELECT nome, quantidade FROM estoque WHERE id=?", (id_prod,))
            produto = cursor.fetchone()
            if not produto:
                raise DadosInvalidosError("Produto não encontrado.")
            
            nome_produto, estoque_atual = produto
            
            if tipo_mov == 'Saída':
                if estoque_atual < qtd_mov:
                    raise EstoqueInsuficienteError(f"Saldo atual: {estoque_atual} unidades.")
                novo_estoque = estoque_atual - qtd_mov
            else:
                novo_estoque = estoque_atual + qtd_mov
                
            cursor.execute("UPDATE estoque SET quantidade=? WHERE id=?", (novo_estoque, id_prod))
            cursor.execute(
                "INSERT INTO historico (tipo, produto_nome, cliente, quantidade, data_hora) VALUES (?, ?, ?, ?, ?)", 
                (tipo_mov, nome_produto, envolvido, qtd_mov, datetime.now().strftime("%d/%m/%Y %H:%M"))
            )
            return novo_estoque

    def buscar_historico(self):
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, tipo, produto_nome, cliente, quantidade, data_hora FROM historico ORDER BY id DESC")
            return cursor.fetchall()

    def excluir_historico(self, id_hist):
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historico WHERE id=?", (id_hist,))

    def buscar_permissoes_caixa(self):
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico FROM usuarios WHERE usuario='caixa'")
            return cursor.fetchone()

    def salvar_configuracoes(self, s_dono, s_caixa, p_fin, p_cad, p_ent, p_his):
        with self._conexao() as conn:
            cursor = conn.cursor()
            if s_dono: 
                cursor.execute("UPDATE usuarios SET senha=? WHERE usuario='dono'", (self._gerar_hash_senha(s_dono),))
            if s_caixa: 
                cursor.execute("UPDATE usuarios SET senha=? WHERE usuario='caixa'", (self._gerar_hash_senha(s_caixa),))
            cursor.execute(
                "UPDATE usuarios SET p_ver_financeiro=?, p_cadastrar_produto=?, p_fazer_entrada=?, p_ver_historico=? WHERE usuario='caixa'", 
                (p_fin, p_cad, p_ent, p_his)
            )

    def criar_backup(self, caminho_destino):
        """Cópia de segurança em tempo de execução usando a API do SQLite. (Resolve Ponto 3)"""
        origem_conn = sqlite3.connect(self.db_name)
        destino_conn = sqlite3.connect(caminho_destino)
        with origem_conn, destino_conn:
            origem_conn.backup(destino_conn)
        origem_conn.close()
        destino_conn.close()

    def restaurar_backup(self, caminho_origem):
        """Inspeciona a integridade do arquivo antes de permitir a substituição. (Resolve Ponto 3)"""
        if not os.path.exists(caminho_origem):
            raise BackupInvalidoError("Arquivo de backup não encontrado.")
        try:
            temp_conn = sqlite3.connect(caminho_origem)
            cursor = temp_conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            resultado = cursor.fetchone()[0]
            temp_conn.close()
            if resultado != "ok":
                raise BackupInvalidoError("O arquivo de backup possui inconsistências internas.")
        except sqlite3.Error:
            raise BackupInvalidoError("O arquivo selecionado não é um banco de dados SQLite válido.")
        
        shutil.copy2(caminho_origem, self.db_name)