import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, END, W, E, LEFT, RIGHT, BOTTOM, BOTH, Y, CENTER
import os
import csv
import shutil
from datetime import datetime
from banco import BancoDeDados

class SistemaEstoqueApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Estoque")
        self.root.geometry("1000x800")
        
        self.db = BancoDeDados()
        
        self.perfil_usuario = ""
        self.permissoes = {}
        self.produto_id_selecionado = None
        
        self.frame_login = None
        self.frame_principal = None
        
        self.montar_tela_login()

    # ==========================================
    # TELA DE LOGIN
    # ==========================================
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
        
        ctk.CTkLabel(self.frame_login, text="Usuários padrão: dono | caixa", text_color="gray", font=("Arial", 10)).pack(pady=(0, 20))

    def fazer_login(self):
        usuario = self.entry_user.get()
        senha = self.entry_senha.get()
        
        user_data = self.db.fazer_login(usuario, senha)
        
        if user_data:
            self.perfil_usuario = user_data[0]
            self.permissoes = {
                'ver_financeiro': user_data[1],
                'cadastrar_produto': user_data[2],
                'fazer_entrada': user_data[3],
                'ver_historico': user_data[4]
            }
            self.frame_login.destroy()
            self.montar_tela_principal()
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos")

    def fazer_logout(self):
        self.perfil_usuario = ""
        self.permissoes = {}
        self.produto_id_selecionado = None
        self.montar_tela_login()

    # ==========================================
    # TELA PRINCIPAL E MÁSCARAS
    # ==========================================
    def formatar_quantidade(self, var_name, index, mode):
        texto = self.var_qtd.get()
        texto_limpo = ''.join([c for c in texto if c.isdigit()])
        if texto != texto_limpo:
            self.var_qtd.set(texto_limpo)

    def formatar_preco(self, var_name, index, mode):
        texto = self.var_preco.get()
        texto_limpo = ''.join([c for c in texto if c.isdigit() or c in ',.'])
        texto_limpo = texto_limpo.replace('.', ',')
        
        if texto_limpo.count(',') > 1:
            partes = texto_limpo.split(',')
            texto_limpo = partes[0] + ',' + ''.join(partes[1:])
            
        if texto != texto_limpo:
            self.var_preco.set(texto_limpo)

    def formatar_qtd_mov(self, var_name, index, mode):
        texto = self.var_qtd_mov.get()
        texto_limpo = ''.join([c for c in texto if c.isdigit()])
        if texto != texto_limpo:
            self.var_qtd_mov.set(texto_limpo)

    def montar_tela_principal(self):
        self.frame_principal = ctk.CTkFrame(self.root, fg_color="transparent")
        self.frame_principal.pack(fill=BOTH, expand=True)
        
        frame_header = ctk.CTkFrame(self.frame_principal, corner_radius=0, height=50)
        frame_header.pack(fill="x")
        
        ctk.CTkLabel(frame_header, text=f"👤 Logado como: {self.perfil_usuario.title()}", font=("Arial", 14, "bold")).pack(side=LEFT, padx=20, pady=10)
        
        if self.perfil_usuario == "proprietario":
            ctk.CTkButton(frame_header, text="⚙️ Configurações", fg_color="#FF9800", hover_color="#E68A00", command=self.abrir_configuracoes).pack(side=LEFT, padx=20)
            
        ctk.CTkButton(frame_header, text="Sair", fg_color="#E74C3C", hover_color="#C0392B", width=80, command=self.fazer_logout).pack(side=RIGHT, padx=20)

        if self.permissoes.get('cadastrar_produto'):
            self.montar_area_cadastro()

        frame_meio = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        frame_meio.pack(fill="x", padx=20, pady=10)
        
        self.montar_area_movimentacao(frame_meio)
        self.montar_area_busca(frame_meio)

        self.montar_tabela()
        self.montar_rodape()
        self.carregar_dados()

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
        self.entry_cor = ctk.CTkEntry(frame_form, placeholder_text="Cor", width=120)
        self.entry_cor.grid(row=2, column=3, padx=10, pady=5, sticky=W)
        
        self.var_qtd = ctk.StringVar()
        self.var_qtd.trace_add("write", self.formatar_quantidade)
        self.entry_quantidade = ctk.CTkEntry(frame_form, placeholder_text="Qtd Inicial*", width=100, textvariable=self.var_qtd)
        self.entry_quantidade.grid(row=3, column=0, padx=10, pady=(5, 15), sticky=W)
        
        self.var_preco = ctk.StringVar()
        self.var_preco.trace_add("write", self.formatar_preco)
        self.entry_preco = ctk.CTkEntry(frame_form, placeholder_text="Preço (R$)*", width=120, textvariable=self.var_preco)
        self.entry_preco.grid(row=3, column=1, padx=10, pady=(5, 15), sticky=W)
        
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
        
        valores_mov = ["Saída", "Entrada"] if self.permissoes.get('fazer_entrada') else ["Saída"]
        estado_mov = "normal" if self.permissoes.get('fazer_entrada') else "disabled"
        
        self.combo_tipo_mov = ctk.CTkComboBox(frame_inputs, values=valores_mov, width=90, state=estado_mov)
        self.combo_tipo_mov.set("Saída")
        self.combo_tipo_mov.pack(side=LEFT, padx=(0, 5))
        
        self.entry_envolvido = ctk.CTkEntry(frame_inputs, placeholder_text="Cliente/Fornecedor", width=150)
        self.entry_envolvido.pack(side=LEFT, padx=5)
        
        self.var_qtd_mov = ctk.StringVar()
        self.var_qtd_mov.trace_add("write", self.formatar_qtd_mov)
        self.entry_qtd_mov = ctk.CTkEntry(frame_inputs, placeholder_text="Qtd", width=60, textvariable=self.var_qtd_mov)
        self.entry_qtd_mov.pack(side=LEFT, padx=5)
        
        ctk.CTkButton(frame_inputs, text="Confirmar", command=self.registrar_movimentacao, width=80).pack(side=LEFT, padx=10)

        # Atalho CORRETO do Enter para a aba de movimentação
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

        # Atalho CORRETO do Enter para a aba de busca
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
        
        if self.permissoes.get('ver_historico'):
            ctk.CTkButton(frame_resumo, text="📄 Ver Histórico", fg_color="#E74C3C", hover_color="#C0392B", command=self.ver_historico).pack(side=RIGHT, padx=(10, 30), pady=15)
        
        ctk.CTkButton(frame_resumo, text="📊 Exportar Excel", fg_color="#27AE60", hover_color="#1E8449", command=self.exportar_excel).pack(side=RIGHT, padx=10, pady=15)

    # ==========================================
    # LÓGICA DA INTERFACE (Ações)
    # ==========================================
    def carregar_dados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        termo = self.entry_busca.get().strip() if hasattr(self, 'entry_busca') else ""
        linhas = self.db.buscar_produtos(termo)
        
        total_pecas = 0
        valor_total = 0
        
        for i, linha in enumerate(linhas):
            linha_lista = list(linha)
            qtd = linha_lista[6]
            preco = linha_lista[7]
            
            total_pecas += qtd
            valor_total += (qtd * preco)
            linha_lista[7] = f"R$ {preco:.2f}".replace(".", ",")
            
            if qtd <= 5:
                tag = 'baixo_par' if i % 2 == 0 else 'baixo_impar'
            else:
                tag = 'par' if i % 2 == 0 else 'impar'
                
            self.tree.insert("", END, values=linha_lista, tags=(tag,))
            
        self.lbl_total_pecas.configure(text=f"Total de Peças: {total_pecas} un")
        if self.permissoes.get('ver_financeiro'):
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
        self.var_qtd.set("")
        self.var_preco.set("")

    def selecionar_produto(self, event):
        item_selecionado = self.tree.focus()
        if not item_selecionado: return
            
        valores = self.tree.item(item_selecionado, "values")
        self.produto_id_selecionado = valores[0]
        self.lbl_produto_mov.configure(text=f"Produto Selecionado: {valores[0]} - {valores[2]}")
        
        if self.permissoes.get('cadastrar_produto') and hasattr(self, 'entry_id'):
            self.limpar_campos_produto()
            self.entry_id.configure(state="normal")
            self.entry_id.insert(0, valores[0])
            self.entry_id.configure(state="disabled")
            self.entry_codigo.insert(0, valores[1])
            self.entry_nome.insert(0, valores[2])
            self.combo_categoria.set(valores[3])
            self.combo_tamanho.set(valores[4])
            self.entry_cor.insert(0, valores[5])
            
            self.var_qtd.set(valores[6])
            preco_limpo = str(valores[7]).replace("R$ ", "")
            self.var_preco.set(preco_limpo)

    def adicionar_produto(self):
        if not self.entry_nome.get() or not self.var_qtd.get() or not self.var_preco.get():
            messagebox.showerror("Erro", "Nome, Quantidade e Preço são obrigatórios.")
            return
        try:
            qtd = int(self.var_qtd.get())
            prc = float(self.var_preco.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Quantidade e Preço inválidos.")
            return

        self.db.adicionar_produto(self.entry_codigo.get(), self.entry_nome.get(), self.combo_categoria.get(), 
                                  self.combo_tamanho.get(), self.entry_cor.get(), qtd, prc)
        self.limpar_campos_produto()
        self.carregar_dados()
        messagebox.showinfo("Sucesso", "Produto adicionado!")

    def atualizar_produto(self):
        produto_id = self.entry_id.get()
        if not produto_id: return
        try:
            qtd = int(self.var_qtd.get())
            prc = float(self.var_preco.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos.")
            return

        self.db.atualizar_produto(produto_id, self.entry_codigo.get(), self.entry_nome.get(), 
                                  self.combo_categoria.get(), self.combo_tamanho.get(), self.entry_cor.get(), qtd, prc)
        self.limpar_campos_produto()
        self.carregar_dados()
        messagebox.showinfo("Sucesso", "Produto atualizado!")

    def excluir_produto(self):
        produto_id = self.entry_id.get()
        if not produto_id: return
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este produto?"):
            self.db.excluir_produto(produto_id)
            self.limpar_campos_produto()
            self.carregar_dados()
            messagebox.showinfo("Sucesso", "Produto excluído!")

    def registrar_movimentacao(self, event=None):
        if not self.produto_id_selecionado:
            if event is None:
                messagebox.showwarning("Aviso", "Clique em um produto na tabela primeiro.")
            return "break"
            
        tipo_mov = self.combo_tipo_mov.get()
        envolvido = self.entry_envolvido.get()
        qtd_mov_str = self.var_qtd_mov.get()
        
        if not envolvido or not qtd_mov_str:
            messagebox.showwarning("Aviso", "Preencha o Nome e a Quantidade.")
            return "break"
            
        try:
            qtd_mov = int(qtd_mov_str)
            if qtd_mov <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "A quantidade deve ser um número inteiro.")
            return "break"
            
        dados_prod = self.db.buscar_produto_por_id(self.produto_id_selecionado)
        if not dados_prod: return "break"
        nome_produto, estoque_atual = dados_prod
        
        if tipo_mov == "Saída":
            if estoque_atual - qtd_mov < 0:
                messagebox.showerror("Erro", f"Só existem {estoque_atual} peças.")
                return "break"
            novo_estoque = estoque_atual - qtd_mov
            msg = f"Saída! {qtd_mov}x vendidas para {envolvido}."
        else:
            novo_estoque = estoque_atual + qtd_mov
            msg = f"Entrada! {qtd_mov}x adicionadas via {envolvido}."
            
        self.db.registrar_movimentacao(self.produto_id_selecionado, tipo_mov, envolvido, qtd_mov, novo_estoque, nome_produto)
        
        self.entry_envolvido.delete(0, END)
        self.var_qtd_mov.set("")
        self.lbl_produto_mov.configure(text="Produto Selecionado: Nenhum")
        self.produto_id_selecionado = None
        self.carregar_dados()
        
        self.root.focus_set()
        messagebox.showinfo("Sucesso", msg)
        return "break"

    def exportar_excel(self):
        linhas = self.db.buscar_produtos("")
        if not linhas:
            messagebox.showwarning("Aviso", "O estoque está vazio, não há o que exportar.")
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivo Excel/CSV", "*.csv")],
            initialfile=f"relatorio_estoque_{datetime.now().strftime('%d_%m_%Y')}.csv",
            title="Salvar Relatório de Estoque"
        )
        
        if caminho:
            try:
                with open(caminho, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(["ID", "Código", "Nome", "Categoria", "Tamanho", "Cor", "Qtd", "Preço"])
                    for linha in linhas:
                        writer.writerow(linha)
                messagebox.showinfo("Sucesso", "Relatório exportado!\nVocê já pode abrir o arquivo no Excel.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar o relatório: {e}")

    def ver_historico(self):
        janela_hist = ctk.CTkToplevel(self.root)
        janela_hist.title("Histórico")
        janela_hist.geometry("750x450")
        janela_hist.focus()
        
        frame_tree = ctk.CTkFrame(janela_hist)
        frame_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        tree_h = ttk.Treeview(frame_tree, columns=("ID", "Tipo", "Produto", "Envolvido", "Qtd", "Data"), show="headings")
        for c, w in zip(tree_h["columns"], [40, 80, 200, 150, 60, 120]):
            tree_h.heading(c, text=c)
            tree_h.column(c, width=w, anchor=CENTER)
            
        tree_h.tag_configure('Entrada', background="#157B18", foreground='black')
        tree_h.tag_configure('Saída', background="#ca1123", foreground='black')
            
        tree_h.pack(fill=BOTH, expand=True, pady=5)
        
        for linha in self.db.buscar_historico():
            tree_h.insert("", END, values=linha, tags=(linha[1],))

        if self.perfil_usuario == "proprietario":
            def excluir_hist():
                sel = tree_h.focus()
                if sel and messagebox.askyesno("Confirmar", "Apagar registro?"):
                    self.db.excluir_historico(tree_h.item(sel, "values")[0])
                    tree_h.delete(sel)
            ctk.CTkButton(janela_hist, text="Excluir Histórico Selecionado", fg_color="#F44336", hover_color="#D32F2F", command=excluir_hist).pack(pady=10)

    # ==========================================
    # CONFIGURAÇÕES (Com Backup, Senhas e Permissões)
    # ==========================================
    def abrir_configuracoes(self):
        janela_cfg = ctk.CTkToplevel(self.root)
        janela_cfg.title("Configurações")
        janela_cfg.geometry("450x780") 
        janela_cfg.focus()
        
        # 1: TEMA VISUAL
        ctk.CTkLabel(janela_cfg, text="🎨 Aparência do Sistema", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        tema_atual = "System"
        if os.path.exists("tema.txt"):
            with open("tema.txt", "r") as arquivo:
                tema_atual = arquivo.read().strip()
                
        def mudar_tema(nova_escolha):
            ctk.set_appearance_mode(nova_escolha)
            with open("tema.txt", "w") as arquivo:
                arquivo.write(nova_escolha)
                
        combo_tema = ctk.CTkComboBox(janela_cfg, values=["System", "Dark", "Light"], command=mudar_tema, width=250)
        combo_tema.set(tema_atual)
        combo_tema.pack(pady=5)

        # 2: BACKUP
        ctk.CTkLabel(janela_cfg, text="💾 Segurança dos Dados", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        def fazer_backup():
            nome_padrao = f"backup_estoque_{datetime.now().strftime('%d_%m_%Y')}.db"
            caminho = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Banco de Dados", "*.db")],
                title="Salvar Cópia de Segurança",
                initialfile=nome_padrao
            )
            if caminho:
                try:
                    shutil.copy2("estoque.db", caminho)
                    messagebox.showinfo("Sucesso", "Backup gerado com sucesso!\nGuarde este arquivo em um local seguro.")
                except PermissionError:
                    messagebox.showerror("Acesso Negado", "O Windows bloqueou a cópia. Verifique se o arquivo não está aberto em outro programa.")
                except FileNotFoundError:
                    messagebox.showerror("Arquivo não encontrado", "Não foi possível encontrar o banco de dados atual para fazer o backup.")
                except Exception:
                    messagebox.showerror("Erro Inesperado", "Ocorreu um erro ao tentar salvar o backup. Tente salvar em outra pasta.")

        ctk.CTkButton(janela_cfg, text="Gerar Backup do Sistema", fg_color="#2980B9", hover_color="#1A5276", width=250, command=fazer_backup).pack(pady=5)

        # 3: RESTAURAR BACKUP
        def restaurar_backup():
            if not messagebox.askyesno("Aviso Crítico", "Restaurar um backup vai APAGAR o estoque atual e carregar os dados antigos. Tem certeza?"):
                return
                
            caminho = filedialog.askopenfilename(
                filetypes=[("Banco de Dados", "*.db")],
                title="Selecione o arquivo de Backup para Restaurar"
            )
            
            if caminho:
                try:
                    shutil.copy2(caminho, "estoque.db")
                    self.carregar_dados()
                    messagebox.showinfo("Sucesso", "Backup restaurado com sucesso! Os dados voltaram ao normal.")
                except PermissionError:
                    messagebox.showerror("Arquivo em Uso", "O Windows não deixou restaurar o banco de dados porque ele está em uso. Feche e abra o sistema novamente.")
                except FileNotFoundError:
                    messagebox.showerror("Arquivo Inválido", "O arquivo de backup selecionado não foi encontrado ou foi apagado.")
                except shutil.SameFileError:
                    messagebox.showerror("Aviso", "Você selecionou o banco de dados que já está em uso!")
                except Exception:
                    messagebox.showerror("Erro Corrompido", "Não foi possível ler este arquivo de backup. Ele pode estar corrompido.")

        ctk.CTkButton(janela_cfg, text="Restaurar Backup", fg_color="#E67E22", hover_color="#D35400", width=250, command=restaurar_backup).pack(pady=5)

        # 4: SENHAS
        ctk.CTkLabel(janela_cfg, text="🔑 Senhas", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        e_sd = ctk.CTkEntry(janela_cfg, placeholder_text="Nova senha Dono", show="*", width=250)
        e_sd.pack(pady=5)
        e_sc = ctk.CTkEntry(janela_cfg, placeholder_text="Nova senha Caixa", show="*", width=250)
        e_sc.pack(pady=5)
        
        # 5: PERMISSÕES
        ctk.CTkLabel(janela_cfg, text="⚙️ Permissões Caixa", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        perms = self.db.buscar_permissoes_caixa()
        v_fin = ctk.IntVar(value=perms[0])
        v_cad = ctk.IntVar(value=perms[1])
        v_ent = ctk.IntVar(value=perms[2])
        v_his = ctk.IntVar(value=perms[3])
        
        frame_checks = ctk.CTkFrame(janela_cfg, fg_color="transparent")
        frame_checks.pack(pady=5)
        ctk.CTkCheckBox(frame_checks, text="Ver Finanças", variable=v_fin).pack(anchor=W, pady=2)
        ctk.CTkCheckBox(frame_checks, text="Cadastrar Produto", variable=v_cad).pack(anchor=W, pady=2)
        ctk.CTkCheckBox(frame_checks, text="Entrada Mercadoria", variable=v_ent).pack(anchor=W, pady=2)
        ctk.CTkCheckBox(frame_checks, text="Ver Histórico", variable=v_his).pack(anchor=W, pady=2)
        
        def salvar_configs():
            self.db.salvar_configuracoes(e_sd.get(), e_sc.get(), v_fin.get(), v_cad.get(), v_ent.get(), v_his.get())
            messagebox.showinfo("Sucesso", "Configurações atualizadas!")
            janela_cfg.destroy()
            
        ctk.CTkButton(janela_cfg, text="Salvar Configurações", fg_color="#4CAF50", hover_color="#45a049", width=250, command=salvar_configs).pack(pady=15)