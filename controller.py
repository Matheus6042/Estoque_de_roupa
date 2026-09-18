"""Módulo de Controle e Regras de Negócio (Application Layer)."""
from fpdf import FPDF
import csv
import os
from datetime import datetime
from banco import BancoDeDados

class EstoqueController:
    """Orquestra a comunicação entre a interface gráfica e o banco de dados."""

    def __init__(self) -> None:
        self.db = BancoDeDados()
        self.perfil_usuario = ""
        self.permissoes = {}

    def autenticar(self, usuario: str, senha: str) -> bool:
        user_data = self.db.fazer_login(usuario, senha)
        if user_data:
            self.perfil_usuario = user_data['perfil']
            self.permissoes = {
                'ver_financeiro': bool(user_data['p_ver_financeiro']),
                'cadastrar_produto': bool(user_data['p_cadastrar_produto']),
                'fazer_entrada': bool(user_data['p_fazer_entrada']),
                'ver_historico': bool(user_data['p_ver_historico'])
            }
            return True
        return False

    def encerrar_sessao(self) -> None:
        self.perfil_usuario = ""
        self.permissoes = {}

    def listar_produtos(self, termo: str = "") -> list:
        produtos = self.db.buscar_produtos(termo)
        for p in produtos:
            p['preco'] = p['preco_centavos'] / 100.0
        return produtos

    def processar_cadastro(self, codigo: str, nome: str, categoria: str, tamanho: str, cor: str, qtd: int, preco: float) -> None:
        preco_centavos = int(round(preco * 100))
        self.db.adicionar_produto(codigo, nome, categoria, tamanho, cor, qtd, preco_centavos)

    def processar_atualizacao(self, id_prod: int, codigo: str, nome: str, categoria: str, tamanho: str, cor: str, qtd: int, preco: float) -> None:
        preco_centavos = int(round(preco * 100))
        self.db.atualizar_produto(id_prod, codigo, nome, categoria, tamanho, cor, qtd, preco_centavos)

    def processar_exclusao(self, id_prod: int) -> None:
        self.db.excluir_produto(id_prod)

    def registrar_transacao(self, id_prod: int, tipo_mov: str, envolvido: str, qtd_mov: int) -> None:
        self.db.movimentar_estoque(id_prod, tipo_mov, envolvido, qtd_mov)

    def obter_historico(self) -> list:
        return self.db.buscar_historico()

    def processar_exclusao_historico(self, id_hist: int) -> None:
        self.db.excluir_historico(id_hist)

    def consolidar_backup(self, caminho: str) -> None:
        self.db.criar_backup(caminho)

    def recuperar_backup(self, caminho: str) -> None:
        self.db.restaurar_backup(caminho)

    def obter_permissoes_operacionais(self) -> dict:
        return self.db.buscar_permissoes_caixa()

    def aplicar_configuracoes(self, s_dono: str, s_caixa: str, p_fin: int, p_cad: int, p_ent: int, p_his: int) -> None:
        self.db.salvar_configuracoes(s_dono, s_caixa, p_fin, p_cad, p_ent, p_his)

    def exportar_inventario_csv(self, caminho_arquivo: str) -> None:
        produtos = self.listar_produtos()
        pode_ver_financeiro = self.permissoes.get('ver_financeiro', False)
        
        with open(caminho_arquivo, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["ID", "Código", "Nome", "Categoria", "Tamanho", "Cor", "Qtd", "Preço"])
            for p in produtos:
                preco_format = f"{p['preco']:.2f}".replace('.', ',') if pode_ver_financeiro else "***"
                writer.writerow([
                    p['id'], p['sku'], p['nome'], p['categoria'], 
                    p['tamanho'], p['cor'], p['quantidade'], preco_format
                ])
    def exportar_inventario_pdf(self, caminho_arquivo: str) -> None:
        """Gera um relatório de inventário formatado em PDF."""
        produtos = self.listar_produtos()
        pode_ver_financeiro = self.permissoes.get('ver_financeiro', False)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Cabeçalho do Relatório
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Relatório de Inventário - Controle de Estoque", ln=True, align="C")
        
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", ln=True, align="C")
        pdf.ln(5)
        
        # Cabeçalho da Tabela
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(20, 10, "SKU", border=1, fill=True, align="C")
        pdf.cell(80, 10, "Produto", border=1, fill=True, align="L")
        pdf.cell(30, 10, "Tamanho", border=1, fill=True, align="C")
        pdf.cell(25, 10, "Qtd", border=1, fill=True, align="C")
        pdf.cell(35, 10, "Preço (R$)", border=1, fill=True, align="C")
        pdf.ln()
        
        # Linhas de Dados
        pdf.set_font("helvetica", "", 10)
        for p in produtos:
            preco_str = f"{p['preco']:.2f}".replace('.', ',') if pode_ver_financeiro else "***"
            
            # Limita o nome a 40 caracteres para não quebrar a tabela
            nome_curto = p['nome'][:37] + "..." if len(p['nome']) > 40 else p['nome']
            
            pdf.cell(20, 10, str(p['sku']), border=1, align="C")
            pdf.cell(80, 10, nome_curto, border=1, align="L")
            pdf.cell(30, 10, str(p['tamanho']), border=1, align="C")
            pdf.cell(25, 10, str(p['quantidade']), border=1, align="C")
            pdf.cell(35, 10, preco_str, border=1, align="C")
            pdf.ln()
            
        pdf.output(caminho_arquivo)