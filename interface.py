"""Módulo de Interface Gráfica (Presentation Layer)."""

import os
from datetime import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, END, W, E, LEFT, RIGHT, BOTTOM, BOTH, Y, CENTER

from controller import EstoqueController
from banco import EstoqueInsuficienteError, DadosInvalidosError, BackupInvalidoError

DIRETORIO_BASE = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_TEMA = os.path.join(DIRETORIO_BASE, "tema.txt")
MOV_SAIDA = "Saída"
MOV_ENTRADA = "Entrada"

class SistemaEstoqueApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estoque")
        self.root.geometry("1000x800")
        
        self.controller = EstoqueController()
        self.produto_id_selecionado = None
        
        self.frame_login = None
        self.frame_principal = None
        
        self.montar_tela_login()
        # Substitui o "crash" no terminal por alertas amigáveis
        self.root.report_callback_exception = self.manipular_erro_global

    def manipular_erro_global(self, exc_type, exc_value, exc_traceback):
        """Captura falhas críticas do sistema e exibe uma mensagem amigável."""
        mensagem_amigavel = (
            "Desculpe, o sistema encontrou uma instabilidade inesperada.\n"
            "Tente realizar a operação novamente."
        )
        messagebox.showerror("Aviso do Sistema", f"{mensagem_amigavel}\n\nDetalhe Técnico: {exc_value}")

    def montar_tela_login(self):
        if self.frame_principal:
            self.frame_principal.destroy()
            
        self.frame_login = ctk.CTkFrame(self.root, width=400, height=350)
        self.frame_login.place(relx=0.5, rely=0.5, anchor=CENTER)

        ctk.CTkLabel(self.frame_login, text="🔐 Acesso ao Sistema", font=("Arial", 20, "bold")).pack(pady=(30, 20))
        self.entry_user = ctk.CTkEntry(self.frame_login, placeholder_text="Usuário", width=250)
        self.entry_user.pack(pady=10)
        self.entry_senha = ctk.CTkEntry(self.frame_login, placeholder_text="Senha", show="*", width=250)
        self.entry_senha.pack(pady=10)
        
        ctk.CTkButton(self.frame_login, text="Entrar", font=("Arial", 14, "bold"), command=self.fazer_login, width=250).pack(pady=(20, 10))
        ctk.CTkLabel(self.frame_login, text="Usuários padrão: dona | caixa", text_color="gray", font=("Arial", 10)).pack(pady=(0, 20))

    def fazer_login(self):
        usuario = self.entry_user.get()
        senha = self.entry_senha.get()
        
        if self.controller.autenticar(usuario, senha):
            self.frame_login.destroy()
            self.montar_tela_principal()
        else:
            messagebox.showerror("Erro de Autenticação", "Usuário ou senha incorretos.")

    def fazer_logout(self):
        self.controller.encerrar_sessao()
        self.produto_id_selecionado = None
        self.montar_tela_login()

    def formatar_quantidade(self, event=None):
        texto = self.entry_quantidade.get()
        texto_limpo = ''.join([c for c in texto if c.isdigit()])
        if texto != texto_limpo:
            self.entry_quantidade.delete(0, END)
            self.entry_quantidade.insert(0, texto_limpo)

    def formatar_preco(self, event=None):
        texto = self.entry_preco.get()
        texto_limpo = ''.join([c for c in texto if c.isdigit() or c in ',.'])
        texto_limpo = texto_limpo.replace('.', ',')
        if texto_limpo.count(',') > 1:
            partes = texto_limpo.split(',')
            texto_limpo = partes[0] + ',' + ''.join(partes[1:])
        if texto != texto_limpo:
            self.entry_preco.delete(0, END)
            self.entry_preco.insert(0, texto_limpo)

    def formatar_qtd_mov(self, event=None):
        texto = self.entry_qtd_mov.get()
        texto_limpo = ''.join([c for c in texto if c.isdigit()])
        if texto != texto_limpo:
            self.entry_qtd_mov.delete(0, END)
            self.entry_qtd_mov.insert(0, texto_limpo)

    def montar_tela_principal(self):
        self.frame_principal = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_principal.pack(fill=BOTH, expand=True)
        
        frame_header = ctk.CTkFrame(self.frame_principal, corner_radius=0, height=50)
        frame_header.pack(fill="x")
        
        ctk.CTkLabel(frame_header, text=f"👤 Logado como: {self.controller.perfil_usuario.title()}", font=("Arial", 14, "bold")).pack(side=LEFT, padx=20, pady=10)
        
        if self.controller.perfil_usuario == "proprietario":
            ctk.CTkButton(frame_header, text="⚙️ Configurações", fg_color="#FF9800", hover_color="#E68A00", command=self.abrir_configuracoes).pack(side=LEFT, padx=20)
            
        ctk.CTkButton(frame_header, text="Sair", fg_color="#E74C3C", hover_color="#C0392B", width=80, command=self.fazer_logout).pack(side=RIGHT, padx=20)

        if self.controller.permissoes.get('cadastrar_produto'):
            self.montar_area_cadastro()

        frame_meio = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_meio.pack(fill="x", padx=20, pady=10)
        
        self.montar_area_movimentacao(frame_meio)
        self.montar_area_busca(frame_meio)

        self.montar_tabela()
        self.montar_rodape()
        self.carregar_dados()
        
        self.root.update_idletasks()
        self.root.focus_set()

    def montar_area_cadastro(self):
        frame_form = ctk.CTkFrame(self.frame_principal)
        frame_form.pack(fill="x", padx=20, pady=(10, 0))
        
        ctk.CTkLabel(frame_form, text="📦 Gerenciamento de Produto", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=4, sticky=W, padx=10, pady=(10, 5))
        
        self.entry_id = ctk.CTkEntry(frame_form, placeholder_text="ID", width=60, state="disabled")
        self.entry_id.grid(row=1, column=0, padx=10, pady=5, sticky=W)
        self.entry_codigo = ctk.CTkEntry(frame_form, placeholder_text="Código (SKU)", width=150)
        self.entry_codigo.grid(row=1, column=1, padx=10, pady=5, sticky=W)
        self.entry_nome = ctk.CTkEntry(frame_form, placeholder_text="Nome do Produto*", width=300)
        self.entry_nome.grid(row=1, column=2, columnspan=2, padx=10, pady=5, sticky=W)
        
        self.combo_categoria = ctk.CTkComboBox(frame_form, values=["Camiseta", "Calça", "Bermuda", "Casaco", "Acessório"], width=150)
        self.combo_categoria.set("Categoria")
        self.combo_categoria.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky=W)
        self.combo_tamanho = ctk.CTkComboBox(frame_form, values=["Único", "PP", "P", "M", "G", "GG"], width=100)
        self.combo_tamanho.set("Tamanho")
        self.combo_tamanho.grid(row=2, column=2, padx=10, pady=5, sticky=W)
        self.entry_cor = ctk.CTkEntry(frame_form, placeholder_text="Cor*", width=120)
        self.entry_cor.grid(row=2, column=3, padx=10, pady=5, sticky=W)
        
        self.entry_quantidade = ctk.CTkEntry(frame_form, placeholder_text="Qtd Inicial*", width=100)
        self.entry_quantidade.grid(row=3, column=0, padx=10, pady=(5, 15), sticky=W)
        self.entry_quantidade.bind("<KeyRelease>", self.formatar_quantidade)
        
        self.entry_preco = ctk.CTkEntry(frame_form, placeholder_text="Preço (R$)*", width=120)
        self.entry_preco.grid(row=3, column=1, padx=10, pady=(5, 15), sticky=W)
        self.entry_preco.bind("<KeyRelease>", self.formatar_preco)
        
        frame_btn = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_btn.grid(row=3, column=2, columnspan=2, sticky=E, padx=10, pady=(5, 15))
        
        ctk.CTkButton(frame_btn, text="Salvar Novo", fg_color="#4CAF50", hover_color="#45a049", width=100, command=self.adicionar_produto).pack(side=LEFT, padx=5)
        ctk.CTkButton(frame_btn, text="Atualizar", width=100, command=self.atualizar_produto).pack(side=LEFT, padx=5)
        ctk.CTkButton(frame_btn, text="Limpar", fg_color="gray", hover_color="#555555", width=80, command=self.limpar_campos_produto).pack(side=LEFT, padx=5)
        ctk.CTkButton(frame_btn, text="Excluir", fg_color="#F44336", hover_color="#D32F2F", width=80, command=self.excluir_produto).pack(side=LEFT, padx=5)

    def montar_area_movimentacao(self, parent_frame):
        frame_mov = ctk.CTkFrame(parent_frame)
        frame_mov.pack(side=LEFT, fill="x", expand=True, padx=(0, 10))
        
        self.lbl_produto_mov = ctk.CTkLabel(frame_mov, text="Produto Selecionado: Nenhum", font=("Arial", 12, "bold"), text_color="#D35400")
        self.lbl_produto_mov.pack(anchor=W, padx=10, pady=(10, 5))
        
        frame_inputs = ctk.CTkFrame(frame_mov, fg_color="transparent")
        frame_inputs.pack(fill="x", padx=10, pady=(0, 10))
        
        valores_mov = [MOV_SAIDA, MOV_ENTRADA] if self.controller.permissoes.get('fazer_entrada') else [MOV_SAIDA]
        estado_mov = "normal" if self.controller.permissoes.get('fazer_entrada') else "disabled"
        
        self.combo_tipo_mov = ctk.CTkComboBox(frame_inputs, values=valores_mov, width=90, state=estado_mov)
        self.combo_tipo_mov.set(MOV_SAIDA) 
        self.combo_tipo_mov.pack(side=LEFT, padx=(0, 5))
        
        self.entry_envolvido = ctk.CTkEntry(frame_inputs, placeholder_text="Cliente/Fornecedor", width=150)
        self.entry_envolvido.pack(side=LEFT, padx=5)
        
        self.entry_qtd_mov = ctk.CTkEntry(frame_inputs, placeholder_text="Qtd", width=60)
        self.entry_qtd_mov.pack(side=LEFT, padx=5)
        self.entry_qtd_mov.bind("<KeyRelease>", self.formatar_qtd_mov)
        
        ctk.CTkButton(frame_inputs, text="Confirmar", command=self.registrar_movimentacao, width=80).pack(side=LEFT, padx=10)
        self.entry_qtd_mov.bind("<Return>", self.registrar_movimentacao)

    def montar_area_busca(self, parent_frame):
        frame_busca = ctk.CTkFrame(parent_frame)
        frame_busca.pack(side=RIGHT, fill="both")
        
        ctk.CTkLabel(frame_busca, text="🔍 Buscar Produto", font=("Arial", 12, "bold")).pack(anchor=W, padx=10, pady=(10, 5))
        frame_inputs = ctk.CTkFrame(frame_busca, fg_color="transparent")
        frame_inputs.pack(fill="x", padx=10, pady=(0, 10))
        
        self.entry_busca = ctk.CTkEntry(frame_inputs, placeholder_text="Nome ou Código", width=150)
        self.entry_busca.pack(side=LEFT, padx=(0, 5))
        
        ctk.CTkButton(frame_inputs, text="Buscar", fg_color="#4CAF50", hover_color="#45a049", width=60, command=self.carregar_dados).pack(side=LEFT, padx=5)
        ctk.CTkButton(frame_inputs, text="Limpar", fg_color="gray", hover_color="#555555", width=60, command=lambda: [self.entry_busca.delete(0, END), self.carregar_dados()]).pack(side=LEFT, padx=5)
        self.entry_busca.bind("<Return>", lambda event: self.carregar_dados())

    def montar_tabela(self):
        frame_tabela = ctk.CTkFrame(self.frame_principal)
        frame_tabela.pack(fill=BOTH, expand=True, padx=20, pady=5)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, rowheight=30)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", font=("Arial", 10, "bold"))
        
        self.tree = ttk.Treeview(frame_tabela, columns=("ID", "Código", "Nome", "Categoria", "Tamanho", "Cor", "Qtd", "Preço"), show="headings")
        
        self.tree.tag_configure('impar', background='#2b2b2b')
        self.tree.tag_configure('par', background='#383838')
        self.tree.tag_configure('baixo_impar', background='#2b2b2b', foreground='#FF5252')
        self.tree.tag_configure('baixo_par', background='#383838', foreground='#FF5252')
        
        larguras = [40, 80, 250, 100, 70, 80, 60, 90]
        for i, col in enumerate(self.tree["columns"]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=larguras[i], anchor=CENTER)

        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.pack(fill=BOTH, expand=True, pady=2)
        
        self.tree.bind("<ButtonRelease-1>", self.selecionar_produto)

    def montar_rodape(self):
        frame_resumo = ctk.CTkFrame(self.frame_principal, corner_radius=0, height=60)
        frame_resumo.pack(fill="x", side=BOTTOM)
        
        self.lbl_total_pecas = ctk.CTkLabel(frame_resumo, text="Total de Peças: 0 un", font=("Arial", 16, "bold"))
        self.lbl_total_pecas.pack(side=LEFT, padx=30, pady=15)
        
        self.lbl_valor_total = ctk.CTkLabel(frame_resumo, text="Valor do Inventário: R$ 0,00", font=("Arial", 16, "bold"))
        self.lbl_valor_total.pack(side=LEFT, padx=30, pady=15)
        
        # Novos botões de integração
        ctk.CTkButton(frame_resumo, text="📱 Copiar Resumo", fg_color="#8E44AD", hover_color="#732D91", width=120, command=self.copiar_para_celular).pack(side=RIGHT, padx=10, pady=15)
        
        ctk.CTkButton(frame_resumo, text="📄 PDF", fg_color="#C0392B", hover_color="#922B21", width=80, command=self.exportar_pdf).pack(side=RIGHT, padx=10, pady=15)
        
        ctk.CTkButton(frame_resumo, text="📊 Excel", fg_color="#27AE60", hover_color="#1E8449", width=80, command=self.exportar_excel).pack(side=RIGHT, padx=10, pady=15)
        
        if self.controller.permissoes.get('ver_historico'):
            ctk.CTkButton(frame_resumo, text="🕒 Histórico", fg_color="#E67E22", hover_color="#D35400", width=100, command=self.ver_historico).pack(side=RIGHT, padx=(10, 20), pady=15)

    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        termo = self.entry_busca.get().strip() if hasattr(self, 'entry_busca') else ""
        produtos = self.controller.listar_produtos(termo)
        
        total_pecas = 0
        valor_total = 0
        pode_ver_financeiro = self.controller.permissoes.get('ver_financeiro')
        
        for i, prod in enumerate(produtos):
            total_pecas += prod['quantidade']
            valor_total += (prod['quantidade'] * prod['preco'])
            
            preco_formatado = f"R$ {prod['preco']:.2f}".replace(".", ",") if pode_ver_financeiro else "R$ ***"
            tag = 'baixo_par' if prod['quantidade'] <= 5 and i % 2 == 0 else \
                  'baixo_impar' if prod['quantidade'] <= 5 else \
                  'par' if i % 2 == 0 else 'impar'
                  
            valores = (prod['id'], prod['sku'], prod['nome'], prod['categoria'], prod['tamanho'], prod['cor'], prod['quantidade'], preco_formatado)
            self.tree.insert("", END, values=valores, tags=(tag,))
            
        self.lbl_total_pecas.configure(text=f"Total de Peças: {total_pecas} un")
        
        if pode_ver_financeiro:
            self.lbl_valor_total.configure(text=f"Valor do Inventário: R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            self.lbl_valor_total.configure(text="Valor do Inventário: 🔒 Oculto")

    def limpar_campos_produto(self):
        if not hasattr(self, 'entry_id'): return
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, END)
        self.entry_id.configure(state="disabled")
        self.entry_codigo.delete(0, END)
        self.entry_nome.delete(0, END)
        self.combo_categoria.set("Categoria")
        self.combo_tamanho.set("Tamanho")
        self.entry_cor.delete(0, END)
        self.entry_quantidade.delete(0, END)
        self.entry_preco.delete(0, END)

    def selecionar_produto(self, event):
        item_selecionado = self.tree.focus()
        if not item_selecionado: return
            
        valores = self.tree.item(item_selecionado, "values")
        self.produto_id_selecionado = valores[0]
        self.lbl_produto_mov.configure(text=f"Produto Selecionado: {valores[0]} - {valores[2]}")
        
        if self.controller.permissoes.get('cadastrar_produto') and hasattr(self, 'entry_id'):
            self.limpar_campos_produto()
            self.entry_id.configure(state="normal")
            self.entry_id.insert(0, valores[0])
            self.entry_id.configure(state="disabled")
            self.entry_codigo.insert(0, valores[1])
            self.entry_nome.insert(0, valores[2])
            self.combo_categoria.set(valores[3])
            self.combo_tamanho.set(valores[4])
            self.entry_cor.insert(0, valores[5])
            self.entry_quantidade.insert(0, valores[6])
            
            preco_limpo = str(valores[7]).replace("R$ ", "")
            self.entry_preco.insert(0, preco_limpo)

    def _extrair_dados_formulario(self):
        nome = self.entry_nome.get().strip()
        categoria = self.combo_categoria.get()
        tamanho = self.combo_tamanho.get()
        cor = self.entry_cor.get().strip()
        qtd_str = self.entry_quantidade.get()
        preco_str = self.entry_preco.get()

        if not nome or not cor or not qtd_str or not preco_str:
            raise DadosInvalidosError("Nome, Cor, Quantidade e Preço são campos obrigatórios.")
            
        if categoria == "Categoria" or tamanho == "Tamanho":
            raise DadosInvalidosError("Selecione uma Categoria e um Tamanho válidos.")
            
        if nome.isdigit():
            raise DadosInvalidosError("O nome do produto não pode ser composto exclusivamente por números.")
            
        if any(char.isdigit() for char in cor):
            raise DadosInvalidosError("A cor do produto não deve conter caracteres numéricos.")
            
        try:
            qtd = int(qtd_str)
            prc = float(preco_str.replace(",", "."))
            return nome, categoria, tamanho, cor, qtd, prc
        except ValueError as exc:
            raise DadosInvalidosError("Quantidade e Preço contêm valores numéricos inválidos.") from exc

    def adicionar_produto(self):
        try:
            nome, categoria, tamanho, cor, qtd, prc = self._extrair_dados_formulario()
            self.controller.processar_cadastro(
                self.entry_codigo.get(), nome, categoria, tamanho, cor, qtd, prc
            )
            self.limpar_campos_produto()
            self.carregar_dados()
            messagebox.showinfo("Operação Concluída", "Produto registado com sucesso no sistema.")
        except DadosInvalidosError as e:
            messagebox.showerror("Erro de Validação", str(e))

    def atualizar_produto(self):
        produto_id = self.entry_id.get()
        if not produto_id: return
        try:
            nome, categoria, tamanho, cor, qtd, prc = self._extrair_dados_formulario()
            self.controller.processar_atualizacao(
                produto_id, self.entry_codigo.get(), nome, categoria, tamanho, cor, qtd, prc
            )
            self.limpar_campos_produto()
            self.carregar_dados()
            messagebox.showinfo("Operação Concluída", "Dados do produto atualizados com sucesso.")
        except DadosInvalidosError as e:
            messagebox.showerror("Erro de Validação", str(e))

    def excluir_produto(self):
        produto_id = self.entry_id.get()
        if not produto_id: return
        if messagebox.askyesno("Aviso de Exclusão", "Confirma a exclusão permanente deste registro?"):
            self.controller.processar_exclusao(produto_id)
            self.limpar_campos_produto()
            self.carregar_dados()
            messagebox.showinfo("Operação Concluída", "Produto removido da base de dados.")

    def registrar_movimentacao(self, event=None):
        if not self.produto_id_selecionado:
            if event is None:
                messagebox.showwarning("Seleção Necessária", "Selecione um item no inventário previamente.")
            return "break"
            
        tipo_mov = self.combo_tipo_mov.get()
        envolvido = self.entry_envolvido.get()
        qtd_mov_str = self.entry_qtd_mov.get()
        
        if not envolvido or not qtd_mov_str:
            messagebox.showwarning("Dados Incompletos", "É necessário preencher a Entidade e a Quantidade.")
            return "break"
            
        try:
            qtd_mov = int(qtd_mov_str)
            if qtd_mov <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro de Formato", "A quantidade transacionada deve ser um inteiro positivo.")
            return "break"
            
        try:
            self.controller.registrar_transacao(self.produto_id_selecionado, tipo_mov, envolvido, qtd_mov)
            msg = f"Transação de {tipo_mov} registrada: {qtd_mov} un. (Referência: {envolvido})."
            
            self.entry_envolvido.delete(0, END)
            self.entry_qtd_mov.delete(0, END)
            self.lbl_produto_mov.configure(text="Produto Selecionado: Nenhum")
            self.produto_id_selecionado = None
            self.carregar_dados()
            self.root.focus_set()
            messagebox.showinfo("Transação Concluída", msg)
            
        except Exception as e:
            messagebox.showerror("Aviso do Sistema", str(e))
            
        return "break"

    def exportar_excel(self):
        caminho = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivo Excel/CSV", "*.csv")],
            initialfile=f"relatorio_estoque_{datetime.now().strftime('%d_%m_%Y')}.csv",
            title="Exportar Dados do Sistema"
        )
        if caminho:
            try:
                self.controller.exportar_inventario_csv(caminho)
                messagebox.showinfo("Sucesso", "Dados exportados com sucesso para o diretório informado.")
            except Exception as e:
                messagebox.showerror("Falha na Exportação", f"Ocorreu um erro ao processar o arquivo: {e}")
    def exportar_pdf(self):
        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=f"relatorio_estoque_{datetime.now().strftime('%d_%m_%Y')}.pdf",
            title="Exportar Dados do Sistema (PDF)"
        )
        if caminho:
            try:
                self.controller.exportar_inventario_pdf(caminho)
                messagebox.showinfo("Sucesso", "Relatório PDF gerado e salvo com sucesso!")
            except Exception as e:
                messagebox.showerror("Falha na Exportação", f"Não foi possível salvar o arquivo. Verifique se ele está aberto em outro programa.\nErro: {e}")

    def copiar_para_celular(self):
        """Gera um relatório completo e categorizado para o WhatsApp, priorizando estoque baixo."""
        produtos = self.controller.listar_produtos()
        if not produtos:
            messagebox.showwarning("Aviso", "Não há produtos no inventário para gerar o relatório.")
            return

        pode_ver_financeiro = self.controller.permissoes.get('ver_financeiro', False)
        
        # Filtra e separa os produtos pela regra de negócio (Estoque Crítico <= 5)
        baixo_estoque = [p for p in produtos if p['quantidade'] <= 5]
        estoque_normal = [p for p in produtos if p['quantidade'] > 5]
        
        # Cabeçalho
        texto = f"📦 *POSIÇÃO DE ESTOQUE*\n"
        texto += f"📅 _{datetime.now().strftime('%d/%m/%Y às %H:%M')}_\n\n"
        
        # Bloco 1: Prioridade Máxima (Em Vermelho/Alerta)
        if baixo_estoque:
            texto += "🚨 *ESTOQUE CRÍTICO (Requer Atenção)*\n"
            for p in baixo_estoque:
                preco_str = f" - R$ {p['preco']:.2f}".replace('.', ',') if pode_ver_financeiro else ""
                texto += f"🔴 *{p['nome']}* (SKU: {p['sku']})\n"
                texto += f"      Qtd: {p['quantidade']} un{preco_str}\n"
            texto += "\n"
            
        # Bloco 2: Estoque Saudável
        if estoque_normal:
            texto += "✅ *ESTOQUE REGULAR*\n"
            for p in estoque_normal:
                preco_str = f" - R$ {p['preco']:.2f}".replace('.', ',') if pode_ver_financeiro else ""
                texto += f"🔹 {p['nome']} (SKU: {p['sku']})\n"
                texto += f"      Qtd: {p['quantidade']} un{preco_str}\n"
            texto += "\n"
            
        # Rodapé Financeiro e Quantitativo
        texto += "━━━━━━━━━━━━━━━━━━\n"
        
        # Puxa os totais já calculados nos labels da tela
        txt_pecas = self.lbl_total_pecas.cget("text").replace("Total de Peças: ", "")
        texto += f"📊 *Total Geral:* {txt_pecas}\n"
        
        if pode_ver_financeiro:
            txt_valor = self.lbl_valor_total.cget("text").replace("Valor do Inventário: ", "")
            texto += f"💰 *Patrimônio:* {txt_valor}\n"
        
        # Joga para a área de transferência do Windows
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.root.update() 
        
        messagebox.showinfo(
            "Relatório Copiado!", 
            "O relatório completo foi gerado e copiado!\n\n"
            "Itens com estoque crítico (5 ou menos) estão destacados no topo.\n"
            "Cole (Ctrl+V) no WhatsApp para visualizar a formatação aplicada."
        )

    def ver_historico(self):
        janela_hist = ctk.CTkToplevel(self.root)
        janela_hist.title("Log de Transações")
        janela_hist.geometry("750x450")
        janela_hist.focus()
        
        frame_tree = ctk.CTkFrame(janela_hist)
        frame_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        tree_h = ttk.Treeview(frame_tree, columns=("ID", "Tipo", "Produto", "Envolvido", "Qtd", "Data"), show="headings")
        for c, w in zip(tree_h["columns"], [40, 80, 200, 150, 60, 120]):
            tree_h.heading(c, text=c)
            tree_h.column(c, width=w, anchor=CENTER)
            
        tree_h.tag_configure(MOV_ENTRADA, background="#157B18", foreground='black')
        tree_h.tag_configure(MOV_SAIDA, background="#ca1123", foreground='black')
        tree_h.pack(fill=BOTH, expand=True, pady=5)
        
        historico = self.controller.obter_historico()
        for h in historico:
            valores = (h['id'], h['tipo'], h['produto_nome'], h['cliente'], h['quantidade'], h['data_hora'])
            tree_h.insert("", END, values=valores, tags=(h['tipo'],))

        if self.controller.perfil_usuario == "proprietario":
            def excluir_hist():
                sel = tree_h.focus()
                if sel and messagebox.askyesno("Aviso de Exclusão", "Confirma a exclusão deste registro de transação?"):
                    self.controller.processar_exclusao_historico(tree_h.item(sel, "values")[0])
                    tree_h.delete(sel)
            ctk.CTkButton(janela_hist, text="Deletar Registro Selecionado", fg_color="#F44336", hover_color="#D32F2F", command=excluir_hist).pack(pady=10)

    def abrir_configuracoes(self):
        janela_cfg = ctk.CTkToplevel(self.root)
        janela_cfg.title("Preferências do Sistema")
        janela_cfg.geometry("450x780") 
        janela_cfg.focus()
        
        ctk.CTkLabel(janela_cfg, text="🎨 Aparência da Interface", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        tema_atual = "System"
        if os.path.exists(ARQUIVO_TEMA):
            with open(ARQUIVO_TEMA, "r") as arquivo:
                tema_atual = arquivo.read().strip()
                
        combo_tema = ctk.CTkComboBox(janela_cfg, values=["System", "Dark", "Light"], command=self.mudar_tema, width=250)
        combo_tema.set(tema_atual)
        combo_tema.pack(pady=5)

        ctk.CTkLabel(janela_cfg, text="💾 Segurança da Informação", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkButton(janela_cfg, text="Criar Ponto de Restauração", fg_color="#2980B9", hover_color="#1A5276", width=250, command=self.fazer_backup).pack(pady=5)
        ctk.CTkButton(janela_cfg, text="Recuperar Banco de Dados", fg_color="#E67E22", hover_color="#D35400", width=250, command=self.restaurar_backup).pack(pady=5)

        ctk.CTkLabel(janela_cfg, text="🔑 Credenciais de Acesso", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        e_sd = ctk.CTkEntry(janela_cfg, placeholder_text="Nova Credencial: Administrativa", show="*", width=250)
        e_sd.pack(pady=5)
        e_sc = ctk.CTkEntry(janela_cfg, placeholder_text="Nova Credencial: Operacional", show="*", width=250)
        e_sc.pack(pady=5)
        
        ctk.CTkLabel(janela_cfg, text="⚙️ Matriz de Permissões (Operacional)", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        perms = self.controller.obter_permissoes_operacionais()
        v_fin = ctk.IntVar(value=perms.get('p_ver_financeiro', 0))
        v_cad = ctk.IntVar(value=perms.get('p_cadastrar_produto', 0))
        v_ent = ctk.IntVar(value=perms.get('p_fazer_entrada', 0))
        v_his = ctk.IntVar(value=perms.get('p_ver_historico', 0))
        
        frame_checks = ctk.CTkFrame(janela_cfg, fg_color="transparent")
        frame_checks.pack(pady=5)
        ctk.CTkCheckBox(frame_checks, text="Consulta a Dados Financeiros", variable=v_fin).pack(anchor=W, pady=2)
        ctk.CTkCheckBox(frame_checks, text="Modificação do Inventário Base", variable=v_cad).pack(anchor=W, pady=2)
        ctk.CTkCheckBox(frame_checks, text="Processamento de Entradas", variable=v_ent).pack(anchor=W, pady=2)
        ctk.CTkCheckBox(frame_checks, text="Consulta a Logs de Transação", variable=v_his).pack(anchor=W, pady=2)
        
        ctk.CTkButton(janela_cfg, text="Aplicar Modificações", fg_color="#4CAF50", hover_color="#45a049", width=250, 
                      command=lambda: self.salvar_configs(janela_cfg, e_sd.get(), e_sc.get(), v_fin.get(), v_cad.get(), v_ent.get(), v_his.get())).pack(pady=15)

    def mudar_tema(self, nova_escolha):
        ctk.set_appearance_mode(nova_escolha)
        with open(ARQUIVO_TEMA, "w") as arquivo:
            arquivo.write(nova_escolha)

    def fazer_backup(self):
        nome_padrao = f"backup_estoque_{datetime.now().strftime('%d_%m_%Y')}.db"
        caminho = filedialog.asksaveasfilename(
            defaultextension=".db", filetypes=[("Banco de Dados", "*.db")],
            initialdir=DIRETORIO_BASE,
            title="Definir Diretório de Contingência", initialfile=nome_padrao
        )
        if caminho:
            try:
                self.controller.consolidar_backup(caminho)
                messagebox.showinfo("Operação Concluída", "Ponto de restauração estabelecido com sucesso.")
            except Exception as e:
                messagebox.showerror("Falha de Contingência", f"Impossível consolidar backup: {e}")

    def restaurar_backup(self):
        if not messagebox.askyesno("Sobrescrita de Dados", "A restauração removerá irreversivelmente os dados não contidos no backup. Prosseguir?"):
            return
            
        caminho = filedialog.askopenfilename(filetypes=[("Banco de Dados", "*.db")], title="Localizar Snapshot")
        if caminho:
            try:
                self.controller.recuperar_backup(caminho)
                self.carregar_dados()
                messagebox.showinfo("Operação Concluída", "Estado do banco de dados revertido com sucesso.")
            except BackupInvalidoError as e:
                messagebox.showerror("Arquivo Corrompido", str(e))
            except DadosInvalidosError as e:
                messagebox.showerror("Operação Inválida", str(e))
            except Exception as e:
                messagebox.showerror("Falha de Restauração", f"Ocorreu um erro inesperado:\n{type(e).__name__}: {str(e)}")

    def salvar_configs(self, janela, s_dona, s_caixa, v_fin, v_cad, v_ent, v_his):
        self.controller.aplicar_configuracoes(s_dona, s_caixa, v_fin, v_cad, v_ent, v_his)
        messagebox.showinfo("Atualização Sistêmica", "Preferências administrativas sincronizadas.")
        janela.destroy()