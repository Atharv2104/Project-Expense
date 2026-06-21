"""
settings.py - Application settings: theme, budget, currency, password change.
"""

import customtkinter as ctk
from tkinter import messagebox
from auth_core import update_user_settings, hash_password, verify_password, get_user_settings
from expense_manager import set_budget, get_budget
from database import get_connection
from datetime import datetime


class SettingsPage(ctk.CTkScrollableFrame):
    """Settings page for theme, budget, and account preferences."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w", padx=8, pady=(0, 20))

        # ── Appearance ──
        section = self._section("🎨 Appearance")
        ctk.CTkLabel(section, text="Theme Mode", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(12, 4))
        self.theme_var = ctk.StringVar(value="dark")
        theme_frame = ctk.CTkFrame(section, fg_color="transparent")
        theme_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkRadioButton(
            theme_frame, text="Dark Mode", variable=self.theme_var, value="dark",
            command=self._apply_theme,
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            theme_frame, text="Light Mode", variable=self.theme_var, value="light",
            command=self._apply_theme,
        ).pack(side="left")

        ctk.CTkLabel(section, text="Currency Symbol", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(8, 4))
        self.currency_entry = ctk.CTkEntry(section, width=80, placeholder_text="₹")
        self.currency_entry.pack(anchor="w", padx=16, pady=(0, 12))
        ctk.CTkButton(section, text="Save Currency", width=140, command=self._save_currency).pack(
            anchor="w", padx=16, pady=(0, 16),
        )

        # ── Budget ──
        budget_sec = self._section("🎯 Monthly Budget")
        now = datetime.now()
        ctk.CTkLabel(
            budget_sec,
            text=f"Set budget for {now.strftime('%B %Y')}",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(anchor="w", padx=16, pady=(12, 4))

        budget_row = ctk.CTkFrame(budget_sec, fg_color="transparent")
        budget_row.pack(fill="x", padx=16, pady=(0, 12))
        self.budget_entry = ctk.CTkEntry(budget_row, width=200, placeholder_text="Enter amount")
        self.budget_entry.pack(side="left", padx=(0, 12))
        ctk.CTkButton(budget_row, text="Set Budget", width=120, command=self._save_budget).pack(side="left")

        self.budget_status = ctk.CTkLabel(budget_sec, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.budget_status.pack(anchor="w", padx=16, pady=(0, 16))

        # ── Password ──
        pwd_sec = self._section("🔒 Change Password")
        self.old_pass = ctk.CTkEntry(pwd_sec, placeholder_text="Current password", show="•", width=280)
        self.old_pass.pack(anchor="w", padx=16, pady=(12, 8))
        self.new_pass = ctk.CTkEntry(pwd_sec, placeholder_text="New password (min 6 chars)", show="•", width=280)
        self.new_pass.pack(anchor="w", padx=16, pady=8)
        self.confirm_pass = ctk.CTkEntry(pwd_sec, placeholder_text="Confirm new password", show="•", width=280)
        self.confirm_pass.pack(anchor="w", padx=16, pady=8)
        ctk.CTkButton(pwd_sec, text="Update Password", width=160, command=self._change_password).pack(
            anchor="w", padx=16, pady=(8, 16),
        )

        # ── About ──
        about = self._section("ℹ️ About")
        ctk.CTkLabel(
            about,
            text="Daily Life Expense Tracker v1.0\n"
                 "Track small & big expenses, budgets, income, savings & goals.\n"
                 "Built with Python, CustomTkinter & SQLite.",
            font=ctk.CTkFont(size=12), text_color="gray", justify="left",
        ).pack(anchor="w", padx=16, pady=16)

    def _section(self, title):
        frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        frame.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=16, pady=(12, 0),
        )
        return frame

    def _apply_theme(self):
        theme = self.theme_var.get()
        self.app.apply_theme(theme)
        update_user_settings(self.app.user["id"], theme=theme)

    def _save_currency(self):
        sym = self.currency_entry.get().strip() or "₹"
        update_user_settings(self.app.user["id"], currency_symbol=sym)
        self.app.currency = sym
        messagebox.showinfo("Settings", f"Currency set to {sym}")
        self.app.refresh_all()

    def _save_budget(self):
        try:
            amount = float(self.budget_entry.get())
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid budget amount.")
            return
        now = datetime.now()
        set_budget(self.app.user["id"], now.month, now.year, amount)
        self.budget_status.configure(text=f"Budget set to {self.app.currency}{amount:,.2f}")
        messagebox.showinfo("Budget", "Monthly budget updated successfully!")
        self.app.refresh_all()

    def _change_password(self):
        old = self.old_pass.get()
        new = self.new_pass.get()
        confirm = self.confirm_pass.get()
        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match.")
            return
        if len(new) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters.")
            return

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash, salt FROM users WHERE id=?",
                (self.app.user["id"],),
            )
            row = cursor.fetchone()
            if not row or not verify_password(old, row["password_hash"], row["salt"]):
                messagebox.showerror("Error", "Current password is incorrect.")
                return
            pwd_hash, salt = hash_password(new)
            cursor.execute(
                "UPDATE users SET password_hash=?, salt=? WHERE id=?",
                (pwd_hash, salt, self.app.user["id"]),
            )

        messagebox.showinfo("Success", "Password updated successfully!")
        self.old_pass.delete(0, "end")
        self.new_pass.delete(0, "end")
        self.confirm_pass.delete(0, "end")

    def refresh(self):
        settings = get_user_settings(self.app.user["id"])
        self.theme_var.set(settings.get("theme", "dark"))
        self.currency_entry.delete(0, "end")
        self.currency_entry.insert(0, settings.get("currency_symbol", "₹"))

        now = datetime.now()
        budget = get_budget(self.app.user["id"], now.month, now.year)
        if budget > 0:
            self.budget_status.configure(
                text=f"Current budget: {self.app.currency}{budget:,.2f}",
            )
