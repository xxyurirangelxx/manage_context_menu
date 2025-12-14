import customtkinter as ctk
import winreg
import ctypes
import sys
import os
from tkinter import filedialog, messagebox

# Configuração inicial do tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

TRANSLATIONS = {
    "pt-BR": {
        "title": "Gerenciador de Menu de Contexto",
        "new_item": "Novo Item",
        "name_placeholder": "Nome no Menu (ex: Abrir App)",
        "path_placeholder": "Caminho do App (.exe)",
        "browse_app": "Buscar App",
        "icon_placeholder": "Caminho do Ícone (Opcional)",
        "browse_icon": "Buscar Ícone",
        "target_label": "Onde deve aparecer?",
        "add_button": "Adicionar ao Menu",
        "note": "Nota: Requer Admin",
        "list_title": "Itens Gerenciados",
        "list_header": "Itens Encontrados no Registro",
        "refresh_button": "Atualizar Lista",
        "browse_app_title": "Selecione o Executável",
        "browse_icon_title": "Selecione o Ícone",
        "error_fields": "Nome e Caminho do App são obrigatórios.",
        "error_permission": "Permissão negada. Execute como Admin.",
        "success_add": "Item adicionado em {} locais!",
        "error_add": "Falha ao adicionar: {}",
        "confirm_delete": "Tem certeza que deseja remover '{}' de '{}'?",
        "error_delete_perm": "Permissão negada. Execute como Administrador.",
        "error_delete_fail": "Não foi possível remover: {}",
        "empty_list": "Nenhum item encontrado.",
        "target_files": "Apenas Arquivos",
        "target_folders": "Apenas Pastas (Ícone + Fundo)",
        "target_global": "Global (Arquivos + Pastas)",
        "type_file": "Arquivo",
        "type_folder": "Pasta",
        "type_background": "Fundo Vazio Pasta",
        "language": "Idioma / Language"
    },
    "en-US": {
        "title": "Context Menu Manager",
        "new_item": "New Item",
        "name_placeholder": "Menu Name (e.g. Open App)",
        "path_placeholder": "App Path (.exe)",
        "browse_app": "Browse App",
        "icon_placeholder": "Icon Path (Optional)",
        "browse_icon": "Browse Icon",
        "target_label": "Where should it appear?",
        "add_button": "Add to Menu",
        "note": "Note: Requires Admin",
        "list_title": "Managed Items",
        "list_header": "Items Found in Registry",
        "refresh_button": "Refresh List",
        "browse_app_title": "Select Executable",
        "browse_icon_title": "Select Icon",
        "error_fields": "Name and App Path are required.",
        "error_permission": "Permission denied. Run as Admin.",
        "success_add": "Item added in {} locations!",
        "error_add": "Failed to add: {}",
        "confirm_delete": "Are you sure you want to remove '{}' from '{}'?",
        "error_delete_perm": "Permission denied. Run as Administrator.",
        "error_delete_fail": "Could not remove: {}",
        "empty_list": "No items found.",
        "target_files": "Files Only",
        "target_folders": "Folders Only (Icon + Background)",
        "target_global": "Global (Files + Folders)",
        "type_file": "File",
        "type_folder": "Folder",
        "type_background": "Folder BG",
        "language": "Idioma / Language"
    }
}

class ContextMenuManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lang = "pt-BR"
        
        # Initialize with default language texts
        self.t = TRANSLATIONS[self.lang]

        self.title(self.t["title"])
        self.geometry("900x650")
        
        # Definição dos alvos no registro (Lógica Interna)
        self.target_paths = {
            "target_files": [
                r"*\shell"
            ],
            "target_folders": [
                r"Directory\shell", 
                r"Directory\Background\shell"
            ],
            "target_global": [
                r"*\shell", 
                r"Directory\shell", 
                r"Directory\Background\shell"
            ]
        }
        
        # Mapeamento reverso para exibição na lista (Caminho -> Chave de Tradução)
        self.path_labels_keys = {
            r"*\shell": "type_file",
            r"Directory\shell": "type_folder",
            r"Directory\Background\shell": "type_background"
        }

        # Layout Grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.update_ui_text() # Aplica textos iniciais
        self.load_registry_items()

    def setup_ui(self):
        # --- Painel Lateral (Adicionar Novo) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1) # Empurrar conteudo pra cima

        # Seletor de Idioma
        self.lbl_lang = ctk.CTkLabel(self.sidebar_frame, text="Idioma / Language", anchor="w", font=("Arial", 12, "bold"))
        self.lbl_lang.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.option_lang = ctk.CTkOptionMenu(self.sidebar_frame, values=["pt-BR", "en-US"], command=self.change_language)
        self.option_lang.set(self.lang)
        self.option_lang.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Titulo Novo Item
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="placeholder", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=2, column=0, padx=20, pady=(10, 10))

        # Nome no Menu
        self.entry_name = ctk.CTkEntry(self.sidebar_frame, placeholder_text="placeholder")
        self.entry_name.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Caminho do Executável
        self.entry_path = ctk.CTkEntry(self.sidebar_frame, placeholder_text="placeholder")
        self.entry_path.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.btn_browse_app = ctk.CTkButton(self.sidebar_frame, text="placeholder", command=self.browse_app, fg_color="transparent", border_width=2)
        self.btn_browse_app.grid(row=5, column=0, padx=20, pady=(5, 10), sticky="ew")

        # Ícone (Opcional)
        self.entry_icon = ctk.CTkEntry(self.sidebar_frame, placeholder_text="placeholder")
        self.entry_icon.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.btn_browse_icon = ctk.CTkButton(self.sidebar_frame, text="placeholder", command=self.browse_icon, fg_color="transparent", border_width=2)
        self.btn_browse_icon.grid(row=7, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Seletor de Tipo (Onde aplicar)
        self.lbl_target = ctk.CTkLabel(self.sidebar_frame, text="placeholder", anchor="w")
        self.lbl_target.grid(row=8, column=0, padx=20, pady=(10, 0), sticky="w")

        self.option_target = ctk.CTkOptionMenu(self.sidebar_frame, values=[])
        self.option_target.grid(row=9, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Botão Adicionar
        self.btn_add = ctk.CTkButton(self.sidebar_frame, text="placeholder", command=self.add_registry_key, fg_color="green", hover_color="darkgreen")
        self.btn_add.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # Aviso
        self.label_note = ctk.CTkLabel(self.sidebar_frame, text="placeholder", text_color="gray", font=("Arial", 10))
        self.label_note.grid(row=12, column=0, padx=20, pady=5, sticky="s")

        # --- Painel Principal (Lista) ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title_list = ctk.CTkLabel(self.main_frame, text="placeholder", font=ctk.CTkFont(size=18))
        self.lbl_title_list.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Scrollable Frame para a lista
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="placeholder")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Botão Atualizar
        self.btn_refresh = ctk.CTkButton(self.main_frame, text="placeholder", command=self.load_registry_items)
        self.btn_refresh.grid(row=2, column=0, sticky="e", pady=10)

    def change_language(self, new_lang):
        self.lang = new_lang
        self.t = TRANSLATIONS[self.lang]
        self.update_ui_text()
        self.load_registry_items()

    def update_ui_text(self):
        t = self.t
        self.title(t["title"])
        self.lbl_lang.configure(text=t["language"])
        self.logo_label.configure(text=t["new_item"])
        self.entry_name.configure(placeholder_text=t["name_placeholder"])
        self.entry_path.configure(placeholder_text=t["path_placeholder"])
        self.btn_browse_app.configure(text=t["browse_app"])
        self.entry_icon.configure(placeholder_text=t["icon_placeholder"])
        self.btn_browse_icon.configure(text=t["browse_icon"])
        self.lbl_target.configure(text=t["target_label"])
        self.btn_add.configure(text=t["add_button"])
        self.label_note.configure(text=t["note"])
        
        self.lbl_title_list.configure(text=t["list_title"])
        self.scroll_frame.configure(label_text=t["list_header"])
        self.btn_refresh.configure(text=t["refresh_button"])

        # Atualizar OptionMenu de Alvos
        display_values = [t["target_files"], t["target_folders"], t["target_global"]]
        self.option_target.configure(values=display_values)
        self.option_target.set(display_values[0])

    def get_target_key_from_display(self, display_text):
        t = self.t
        if display_text == t["target_files"]: return "target_files"
        if display_text == t["target_folders"]: return "target_folders"
        if display_text == t["target_global"]: return "target_global"
        return "target_files"

    def browse_app(self):
        filename = filedialog.askopenfilename(
            title=self.t["browse_app_title"], 
            filetypes=[("Executáveis", "*.exe"), ("Todos", "*.*")]
        )
        if filename:
            self.entry_path.delete(0, ctk.END)
            self.entry_path.insert(0, filename.replace('/', '\\'))

    def browse_icon(self):
        filename = filedialog.askopenfilename(
            title=self.t["browse_icon_title"], 
            filetypes=[("Ícones", "*.ico"), ("Executáveis", "*.exe"), ("Todos", "*.*")]
        )
        if filename:
            self.entry_icon.delete(0, ctk.END)
            self.entry_icon.insert(0, filename.replace('/', '\\'))

    def add_registry_key(self):
        name = self.entry_name.get().strip()
        app_path = self.entry_path.get().strip()
        icon_path = self.entry_icon.get().strip()
        target_display = self.option_target.get()
        target_key = self.get_target_key_from_display(target_display)

        if not name or not app_path:
            messagebox.showerror(self.t["error_add"].format(""), self.t["error_fields"])
            return

        target_paths = self.target_paths.get(target_key, [])
        success_count = 0
        error_msg = ""

        for reg_base in target_paths:
            try:
                key_path = f"{reg_base}\\{name}"
                
                key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
                winreg.SetValue(key, '', winreg.REG_SZ, name)
                
                if icon_path:
                    winreg.SetValueEx(key, 'Icon', 0, winreg.REG_SZ, icon_path)
                
                winreg.CloseKey(key)

                command_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
                
                if "Background" in reg_base:
                    param = "%V"
                else:
                    param = "%1"
                    
                cmd_str = f'"{app_path}" "{param}"'
                
                winreg.SetValue(command_key, '', winreg.REG_SZ, cmd_str)
                winreg.CloseKey(command_key)
                
                success_count += 1

            except PermissionError:
                error_msg = self.t["error_permission"]
                break
            except Exception as e:
                error_msg = str(e)
                break

        if success_count > 0:
            messagebox.showinfo(self.t["success_add"].split(" ")[0], self.t["success_add"].format(success_count))
            self.entry_name.delete(0, ctk.END)
            self.entry_path.delete(0, ctk.END)
            self.entry_icon.delete(0, ctk.END)
            self.load_registry_items()
        else:
            messagebox.showerror(self.t["error_add"].split(":")[0], self.t["error_add"].format(error_msg))

    def delete_registry_key(self, key_path, key_name):
        if not messagebox.askyesno(
            self.t["confirm_delete"].split(" ")[0], 
            self.t["confirm_delete"].format(key_name, key_path)
        ):
            return

        try:
            full_path = f"{key_path}\\{key_name}"
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{full_path}\\command")
            except FileNotFoundError:
                pass 

            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, full_path)
            
            self.load_registry_items()
            
        except PermissionError:
            messagebox.showerror(self.t["error_delete_fail"].split(":")[0], self.t["error_delete_perm"])
        except Exception as e:
            messagebox.showerror(self.t["error_delete_fail"].split(":")[0], self.t["error_delete_fail"].format(e))

    def load_registry_items(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        search_paths = [
            r"*\shell", 
            r"Directory\shell", 
            r"Directory\Background\shell"
        ]

        found_items = False

        for path in search_paths:
            try:
                reg_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                index = 0
                while True:
                    try:
                        key_name = winreg.EnumKey(reg_key, index)
                        self.create_list_item(key_name, path)
                        found_items = True
                        index += 1
                    except OSError:
                        break 
                winreg.CloseKey(reg_key)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Erro ao ler {path}: {e}")

        if not found_items:
            lbl = ctk.CTkLabel(self.scroll_frame, text=self.t["empty_list"])
            lbl.pack(pady=10)

    def create_list_item(self, name, path):
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(fill="x", padx=5, pady=5)

        # Obter tradução do tipo
        type_key = self.path_labels_keys.get(path)
        type_label = self.t.get(type_key, path) if type_key else path
        
        lbl_type = ctk.CTkLabel(frame, text=f"[{type_label}]", width=80, text_color="cyan", font=("Arial", 11, "bold"))
        lbl_type.pack(side="left", padx=5)

        lbl_name = ctk.CTkLabel(frame, text=name, font=("Arial", 12, "bold"))
        lbl_name.pack(side="left", padx=5)

        try:
            cmd_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{path}\\{name}\\command")
            val, _ = winreg.QueryValueEx(cmd_key, "")
            cmd_preview = val[:30] + "..." if len(val) > 30 else val
            lbl_cmd = ctk.CTkLabel(frame, text=cmd_preview, text_color="gray", font=("Arial", 10))
            lbl_cmd.pack(side="left", padx=10)
        except:
            pass

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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
        
        if os.path.exists(venv_python):
            executable = venv_python
        else:
            executable = sys.executable

        script_path = os.path.abspath(sys.argv[0])
        args = [script_path] + sys.argv[1:]
        
        params = " ".join([f'"{arg}"' for arg in args])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
