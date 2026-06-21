"""
auth.py - Desktop login window (CustomTkinter). Logic lives in auth_core.py.
"""

import customtkinter as ctk
from auth_core import (
    register_user, login_user, get_user_settings, update_user_settings,
    hash_password, verify_password,
)
from database import init_database

# Re-export for backward compatibility
__all__ = [
    "register_user", "login_user", "get_user_settings", "update_user_settings",
    "hash_password", "verify_password", "AuthWindow",
]


class AuthWindow(ctk.CTk):
    """Login and registration window."""

    def __init__(self, on_login_success):
        super().__init__()
        init_database()
        self.on_login_success = on_login_success
        self.title("Expense Tracker - Login")
        self.geometry("480x620")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        w, h = 480, 620
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=(40, 10), padx=40, fill="x")
        ctk.CTkLabel(header, text="💰", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(header, text="Daily Expense Tracker",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(8, 4))
        ctk.CTkLabel(header, text="Manage your finances smartly",
                     font=ctk.CTkFont(size=14), text_color="gray").pack()

        self.tabview = ctk.CTkTabview(self, width=400, height=380)
        self.tabview.pack(pady=20, padx=40, fill="both", expand=True)
        self.tabview.add("Login")
        self.tabview.add("Register")
        self._build_login_tab()
        self._build_register_tab()
        ctk.CTkLabel(self, text="Demo: username 'demo' / password 'demo123'",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 16))

    def _build_login_tab(self):
        tab = self.tabview.tab("Login")
        self.login_user = ctk.CTkEntry(tab, placeholder_text="Username", height=42, width=320)
        self.login_user.pack(pady=(20, 12))
        self.login_pass = ctk.CTkEntry(tab, placeholder_text="Password", show="•", height=42, width=320)
        self.login_pass.pack(pady=12)
        self.login_msg = ctk.CTkLabel(tab, text="", text_color="#e74c3c", font=ctk.CTkFont(size=12))
        self.login_msg.pack(pady=8)
        ctk.CTkButton(tab, text="Sign In", height=44, width=320,
                      font=ctk.CTkFont(size=15, weight="bold"), command=self._do_login).pack(pady=16)
        self.login_pass.bind("<Return>", lambda e: self._do_login())

    def _build_register_tab(self):
        tab = self.tabview.tab("Register")
        self.reg_user = ctk.CTkEntry(tab, placeholder_text="Username", height=40, width=320)
        self.reg_user.pack(pady=(16, 10))
        self.reg_email = ctk.CTkEntry(tab, placeholder_text="Email", height=40, width=320)
        self.reg_email.pack(pady=10)
        self.reg_pass = ctk.CTkEntry(tab, placeholder_text="Password (min 6 chars)", show="•", height=40, width=320)
        self.reg_pass.pack(pady=10)
        self.reg_confirm = ctk.CTkEntry(tab, placeholder_text="Confirm Password", show="•", height=40, width=320)
        self.reg_confirm.pack(pady=10)
        self.reg_msg = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12))
        self.reg_msg.pack(pady=6)
        ctk.CTkButton(tab, text="Create Account", height=44, width=320,
                      font=ctk.CTkFont(size=15, weight="bold"), command=self._do_register).pack(pady=12)

    def _do_login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get()
        if not username or not password:
            self.login_msg.configure(text="Please fill all fields.", text_color="#e74c3c")
            return
        ok, result = login_user(username, password)
        if ok:
            self.destroy()
            self.on_login_success(result)
        else:
            self.login_msg.configure(text=result, text_color="#e74c3c")

    def _do_register(self):
        username = self.reg_user.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_pass.get()
        confirm = self.reg_confirm.get()
        if password != confirm:
            self.reg_msg.configure(text="Passwords do not match.", text_color="#e74c3c")
            return
        ok, msg = register_user(username, email, password)
        color = "#2ecc71" if ok else "#e74c3c"
        self.reg_msg.configure(text=msg, text_color=color)
        if ok:
            self.tabview.set("Login")
            self.login_user.delete(0, "end")
            self.login_user.insert(0, username)
