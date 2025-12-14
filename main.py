import customtkinter as ctk
import winreg
import ctypes
import sys
import os
from tkinter import filedialog, messagebox

# Configuração inicial do tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ContextMenuManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Manage Context Menu")
        self.geometry("800x600")
        
        # Definição dos alvos no registro
        # Mapeia um nome amigável para uma lista de caminhos no registro
        self.target_map = {
            "Apenas Arquivos": [
                r"*\shell"
            ],
            "Apenas Pastas (Ícone + Fundo)": [
                r"Directory\shell", 
                r"Directory\Background\shell"
            ],
            "Global (Arquivos + Pastas)": [
                r"*\shell", 
                r"Directory\shell", 
                r"Directory\Background\shell"
            ]
        }
        
        # Mapeamento reverso para exibição na lista (Caminho -> Nome Amigável curto)
        self.path_labels = {
            r"*\shell": "Arquivo",
            r"Directory\shell": "Pasta",
            r"Directory\Background\shell": "Fundo Pasta"
        }

        # Layout Grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.load_registry_items()

    def setup_ui(self):
        # --- Painel Lateral (Adicionar Novo) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1) # Empurrar conteudo pra cima

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Novo Item", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Nome no Menu
        self.entry_name = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Nome no Menu (ex: Abrir App)")
        self.entry_name.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Caminho do Executável
        self.entry_path = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Caminho do App (.exe)")
        self.entry_path.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.btn_browse_app = ctk.CTkButton(self.sidebar_frame, text="Buscar App", command=self.browse_app, fg_color="transparent", border_width=2)
        self.btn_browse_app.grid(row=3, column=0, padx=20, pady=(5, 10), sticky="ew")

        # Ícone (Opcional)
        self.entry_icon = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Caminho do Ícone (Opcional)")
        self.entry_icon.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.btn_browse_icon = ctk.CTkButton(self.sidebar_frame, text="Buscar Ícone", command=self.browse_icon, fg_color="transparent", border_width=2)
        self.btn_browse_icon.grid(row=5, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Seletor de Tipo (Onde aplicar)
        self.lbl_target = ctk.CTkLabel(self.sidebar_frame, text="Onde deve aparecer?", anchor="w")
        self.lbl_target.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")

        self.option_target = ctk.CTkOptionMenu(self.sidebar_frame, values=list(self.target_map.keys()))
        self.option_target.grid(row=7, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Botão Adicionar
        self.btn_add = ctk.CTkButton(self.sidebar_frame, text="Adicionar ao Menu", command=self.add_registry_key, fg_color="green", hover_color="darkgreen")
        self.btn_add.grid(row=8, column=0, padx=20, pady=10, sticky="ew")

        # Aviso
        self.label_note = ctk.CTkLabel(self.sidebar_frame, text="Nota: Requer Admin", text_color="gray", font=("Arial", 10))
        self.label_note.grid(row=9, column=0, padx=20, pady=5, sticky="s")

        # --- Painel Principal (Lista) ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title_list = ctk.CTkLabel(self.main_frame, text="Itens Gerenciados", font=ctk.CTkFont(size=18))
        self.lbl_title_list.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Scrollable Frame para a lista
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Itens Encontrados no Registro")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Botão Remover
        self.btn_refresh = ctk.CTkButton(self.main_frame, text="Atualizar Lista", command=self.load_registry_items)
        self.btn_refresh.grid(row=2, column=0, sticky="e", pady=10)



    def browse_app(self):
        filename = filedialog.askopenfilename(title="Selecione o Executável", filetypes=[("Executáveis", "*.exe"), ("Todos", "*.*")])
        if filename:
            self.entry_path.delete(0, ctk.END)
            self.entry_path.insert(0, filename.replace('/', '\\'))

    def browse_icon(self):
        filename = filedialog.askopenfilename(title="Selecione o Ícone", filetypes=[("Ícones", "*.ico"), ("Executáveis", "*.exe"), ("Todos", "*.*")])
        if filename:
            self.entry_icon.delete(0, ctk.END)
            self.entry_icon.insert(0, filename.replace('/', '\\'))

    def add_registry_key(self):
        name = self.entry_name.get().strip()
        app_path = self.entry_path.get().strip()
        icon_path = self.entry_icon.get().strip()
        target_mode = self.option_target.get()

        if not name or not app_path:
            messagebox.showerror("Erro", "Nome e Caminho do App são obrigatórios.")
            return

        target_paths = self.target_map.get(target_mode, [])
        success_count = 0
        error_msg = ""

        for reg_base in target_paths:
            try:
                # Caminho completo: HKEY_CLASSES_ROOT\<BASE>\<Nome>
                key_path = f"{reg_base}\\{name}"
                
                # Criar a chave principal
                key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
                winreg.SetValue(key, '', winreg.REG_SZ, name)
                
                if icon_path:
                    winreg.SetValueEx(key, 'Icon', 0, winreg.REG_SZ, icon_path)
                
                winreg.CloseKey(key)

                # Criar a subchave 'command'
                command_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
                
                # Lógica importante: %V para fundo de pasta, %1 para arquivos/pastas
                # Directory\Background geralmente exige %V para pegar o diretório atual
                if "Background" in reg_base:
                    param = "%V"
                else:
                    param = "%1"
                    
                cmd_str = f'"{app_path}" "{param}"'
                
                winreg.SetValue(command_key, '', winreg.REG_SZ, cmd_str)
                winreg.CloseKey(command_key)
                
                success_count += 1

            except PermissionError:
                error_msg = "Permissão negada. Execute como Admin."
                break
            except Exception as e:
                error_msg = str(e)
                break

        if success_count > 0:
            messagebox.showinfo("Sucesso", f"Item adicionado em {success_count} locais!")
            self.entry_name.delete(0, ctk.END)
            self.entry_path.delete(0, ctk.END)
            self.entry_icon.delete(0, ctk.END)
            self.load_registry_items()
        else:
            messagebox.showerror("Erro", f"Falha ao adicionar: {error_msg}")

    def delete_registry_key(self, key_path, key_name):
        if not messagebox.askyesno("Confirmar", f"Tem certeza que deseja remover '{key_name}' de '{key_path}'?"):
            return

        try:
            full_path = f"{key_path}\\{key_name}"
            
            # Precisamos deletar subchaves primeiro (command)
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{full_path}\\command")
            except FileNotFoundError:
                pass 

            # Deletar a chave principal
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, full_path)
            
            self.load_registry_items()
            
        except PermissionError:
            messagebox.showerror("Erro", "Permissão negada. Execute como Administrador.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível remover: {e}")

    def load_registry_items(self):
        # Limpar lista visual atual
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Lista de locais para procurar (todos os caminhos conhecidos)
        search_paths = [
            r"*\shell", 
            r"Directory\shell", 
            r"Directory\Background\shell"
        ]

        found_items = False

        for path in search_paths:
            try:
                # Tenta abrir a chave para leitura
                reg_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                
                index = 0
                while True:
                    try:
                        key_name = winreg.EnumKey(reg_key, index)
                        # Ignorar chaves padrão do Windows que podem ser perigosas de mexer se não tiver cuidado
                        # (Opcional: implementar filtro se necessário. Aqui mostramos tudo da chave shell)
                        self.create_list_item(key_name, path)
                        found_items = True
                        index += 1
                    except OSError:
                        break # Fim da lista para este path
                
                winreg.CloseKey(reg_key)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Erro ao ler {path}: {e}")

        if not found_items:
            lbl = ctk.CTkLabel(self.scroll_frame, text="Nenhum item encontrado.")
            lbl.pack(pady=10)

    def create_list_item(self, name, path):
        # Container para cada item
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(fill="x", padx=5, pady=5)

        # Identificador do tipo (Arquivo, Pasta, Fundo)
        type_label = self.path_labels.get(path, path)
        lbl_type = ctk.CTkLabel(frame, text=f"[{type_label}]", width=80, text_color="cyan", font=("Arial", 11, "bold"))
        lbl_type.pack(side="left", padx=5)

        lbl_name = ctk.CTkLabel(frame, text=name, font=("Arial", 12, "bold"))
        lbl_name.pack(side="left", padx=5)

        # Tentar ler o comando para mostrar
        try:
            cmd_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{path}\\{name}\\command")
            val, _ = winreg.QueryValueEx(cmd_key, "")
            cmd_preview = val[:30] + "..." if len(val) > 30 else val
            lbl_cmd = ctk.CTkLabel(frame, text=cmd_preview, text_color="gray", font=("Arial", 10))
            lbl_cmd.pack(side="left", padx=10)
        except:
            pass

        # Passamos path e name para a função de deletar
        btn_del = ctk.CTkButton(frame, text="X", width=40, fg_color="#b30000", hover_color="#800000",
                                command=lambda p=path, n=name: self.delete_registry_key(p, n))
        btn_del.pack(side="right", padx=10, pady=5)

if __name__ == "__main__":
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if is_admin:
        app = ContextMenuManager()
        app.mainloop()
    else:
        # Re-executa o programa com privilégios de administrador
        # Prioriza o interpretador do .venv se existir na pasta do script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
        
        if os.path.exists(venv_python):
            executable = venv_python
        else:
            executable = sys.executable

        # Garante que o caminho do script seja absoluto
        script_path = os.path.abspath(sys.argv[0])
        args = [script_path] + sys.argv[1:]
        
        params = " ".join([f'"{arg}"' for arg in args])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
