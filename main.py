import customtkinter as ctk
from interface import SistemaEstoqueApp
import os

if __name__ == "__main__":
    # 1. Verifica qual tema o usuário salvou da última vez
    tema_atual = "System"
    if os.path.exists("tema.txt"):
        with open("tema.txt", "r") as arquivo:
            tema_atual = arquivo.read().strip()

    # 2. Aplica o tema
    ctk.set_appearance_mode(tema_atual)
    ctk.set_default_color_theme("blue")
    
    # 3. Inicia o sistema
    root = ctk.CTk()
    app = SistemaEstoqueApp(root)
    root.mainloop()