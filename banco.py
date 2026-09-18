"""Módulo de Persistência de Dados (Data Layer)."""

import sqlite3
import hashlib
import os
import shutil
import base64
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

class ErroBanco(Exception):
    pass

class DadosInvalidosError(ErroBanco, ValueError):
    pass

class EstoqueInsuficienteError(ErroBanco):
    pass

class BackupInvalidoError(ErroBanco):
    pass

class BancoDeDados:
    """Repositório central de conexões e transações SQLite."""

    def __init__(self, db_name: str = "estoque.db") -> None:
        diretorio_base = os.path.dirname(os.path.abspath(__file__))
        self.db_name = os.path.join(diretorio_base, db_name)
        self._criar_tabelas()

    @contextmanager
    def _conexao(self):
        conn = sqlite3.connect(self.db_name, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _gerar_hash_senha(self, senha: str) -> str:
        salt = os.urandom(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), salt, 100_000)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        hash_b64 = base64.b64encode(hash_obj).decode('utf-8')
        return f"{salt_b64}${hash_b64}"

    def _verificar_senha(self, senha_digitada: str, hash_armazenado: str) -> bool:
        try:
            salt_b64, hash_b64 = hash_armazenado.split('$')
            salt = base64.b64decode(salt_b64)
            hash_esperado = base64.b64decode(hash_b64)
            hash_calculado = hashlib.pbkdf2_hmac('sha256', senha_digitada.encode('utf-8'), salt, 100_000)
            return hash_calculado == hash_esperado
        except ValueError:
            return False

    def _criar_tabelas(self) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sku TEXT, 
                    nome TEXT NOT NULL CHECK (length(nome) > 0),
                    categoria TEXT, 
                    tamanho TEXT, 
                    cor TEXT NOT NULL, 
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
                    """INSERT INTO usuarios 
                    (usuario, senha, perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico) 
                    VALUES (?, ?, 'proprietario', 1, 1, 1, 1)""", 
                    ('dono', senha_padrao)
                )
                cursor.execute(
                    """INSERT INTO usuarios 
                    (usuario, senha, perfil, p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico) 
                    VALUES (?, ?, 'funcionario', 0, 0, 0, 1)""", 
                    ('caixa', senha_padrao)
                )

    def fazer_login(self, usuario: str, senha_digitada: str) -> Optional[Dict]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
            user = cursor.fetchone()
            
            if user and self._verificar_senha(senha_digitada, user['senha']):
                return dict(user)
            return None

    def buscar_produtos(self, termo: str = "") -> List[Dict]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            if termo:
                busca_sql = f"%{termo}%"
                cursor.execute("""
                    SELECT id, sku, nome, categoria, tamanho, cor, quantidade, preco_centavos 
                    FROM estoque WHERE nome LIKE ? OR sku LIKE ?
                """, (busca_sql, busca_sql))
            else:
                cursor.execute("SELECT id, sku, nome, categoria, tamanho, cor, quantidade, preco_centavos FROM estoque")
            return [dict(row) for row in cursor.fetchall()]

    def adicionar_produto(self, sku: str, nome: str, categoria: str, tamanho: str, cor: str, qtd: int, preco_centavos: int) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO estoque 
                (sku, nome, categoria, tamanho, cor, quantidade, preco_centavos) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                (sku, nome, categoria, tamanho, cor, qtd, preco_centavos)
            )

    def atualizar_produto(self, id_prod: int, sku: str, nome: str, categoria: str, tamanho: str, cor: str, qtd: int, preco_centavos: int) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE estoque 
                SET sku=?, nome=?, categoria=?, tamanho=?, cor=?, quantidade=?, preco_centavos=? 
                WHERE id=?""", 
                (sku, nome, categoria, tamanho, cor, qtd, preco_centavos, id_prod)
            )

    def excluir_produto(self, id_prod: int) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM estoque WHERE id=?", (id_prod,))
            cursor.execute("SELECT COUNT(*) FROM estoque")
            if cursor.fetchone()[0] == 0:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='estoque'")

    def movimentar_estoque(self, id_prod: int, tipo_mov: str, envolvido: str, qtd_mov: int) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE") 
            
            cursor.execute("SELECT nome, quantidade FROM estoque WHERE id=?", (id_prod,))
            produto = cursor.fetchone()
            if not produto:
                raise DadosInvalidosError("Produto não encontrado.")
            
            nome_produto = produto['nome']
            estoque_atual = produto['quantidade']
            
            if tipo_mov == 'Saída':
                if estoque_atual < qtd_mov:
                    raise EstoqueInsuficienteError(f"Saldo atual: {estoque_atual} unidades.")
                novo_estoque = estoque_atual - qtd_mov
            else:
                novo_estoque = estoque_atual + qtd_mov
                
            cursor.execute("UPDATE estoque SET quantidade=? WHERE id=?", (novo_estoque, id_prod))
            cursor.execute(
                """INSERT INTO historico 
                (tipo, produto_nome, cliente, quantidade, data_hora) 
                VALUES (?, ?, ?, ?, ?)""", 
                (tipo_mov, nome_produto, envolvido, qtd_mov, datetime.now().strftime("%d/%m/%Y %H:%M"))
            )

    def buscar_historico(self) -> List[Dict]:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM historico ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def excluir_historico(self, id_hist: int) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historico WHERE id=?", (id_hist,))

    def buscar_permissoes_caixa(self) -> Dict:
        with self._conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT p_ver_financeiro, p_cadastrar_produto, p_fazer_entrada, p_ver_historico FROM usuarios WHERE usuario='caixa'")
            row = cursor.fetchone()
            return dict(row) if row else {}

    def salvar_configuracoes(self, s_dono: str, s_caixa: str, p_fin: int, p_cad: int, p_ent: int, p_his: int) -> None:
        with self._conexao() as conn:
            cursor = conn.cursor()
            if s_dono: 
                cursor.execute("UPDATE usuarios SET senha=? WHERE usuario='dono'", (self._gerar_hash_senha(s_dono),))
            if s_caixa: 
                cursor.execute("UPDATE usuarios SET senha=? WHERE usuario='caixa'", (self._gerar_hash_senha(s_caixa),))
            cursor.execute(
                """UPDATE usuarios 
                SET p_ver_financeiro=?, p_cadastrar_produto=?, p_fazer_entrada=?, p_ver_historico=? 
                WHERE usuario='caixa'""", 
                (p_fin, p_cad, p_ent, p_his)
            )

    def criar_backup(self, caminho_destino: str) -> None:
        origem_conn = sqlite3.connect(self.db_name)
        destino_conn = sqlite3.connect(caminho_destino)
        with origem_conn, destino_conn:
            origem_conn.backup(destino_conn)
        origem_conn.close()
        destino_conn.close()

    def restaurar_backup(self, caminho_origem: str) -> None:
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