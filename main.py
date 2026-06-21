"""
main.py - Application entry point with sidebar navigation and all feature pages.
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime

from database import init_database, create_sample_data
from auth import AuthWindow, get_user_settings
from dashboard import DashboardPage
from settings import SettingsPage
from expense_manager import (
    CATEGORIES, EXPENSE_TYPES, validate_date, validate_amount,
    add_expense, update_expense, delete_expense, search_expenses,
    add_income, update_income, delete_income, get_income_list,
    add_savings, delete_savings, get_savings_list, get_savings_balance,
    add_goal, update_goal_progress, delete_goal, get_goals,
    get_monthly_summary, get_weekly_summary, get_spending_by_category,
    get_analytics,
)
from charts import create_pie_chart, create_bar_chart, create_trend_chart
from reports import show_export_dialog, export_to_csv


# ─── Navigation items ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("dashboard", "📊  Dashboard"),
    ("expenses", "💸  Expenses"),
    ("income", "💵  Income"),
    ("savings", "🏦  Savings"),
    ("goals", "🎯  Goals"),
    ("analytics", "📈  Analytics"),
    ("reports", "📄  Reports"),
    ("settings", "⚙️  Settings"),
]


class ExpenseFormDialog(ctk.CTkToplevel):
    """Modal dialog to add or edit an expense."""

    def __init__(self, parent, app, expense=None, on_save=None):
        super().__init__(parent)
        self.app = app
        self.expense = expense
        self.on_save = on_save
        self.title("Edit Expense" if expense else "Add Expense")
        self.geometry("440x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._center_on_parent(parent)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(8, 20))
        btn_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_row.pack(anchor="center")
        save_label = "Add" if not expense else "Save"
        ctk.CTkButton(btn_row, text=save_label, width=160, command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", width=160, fg_color="gray", command=self.destroy).pack(
            side="left", padx=8,
        )

        pad = {"padx": 20, "pady": 6}
        ctk.CTkLabel(self, text="Date (YYYY-MM-DD)").pack(anchor="w", **pad)
        self.date_entry = ctk.CTkEntry(self, width=380)
        self.date_entry.pack(**pad)

        ctk.CTkLabel(self, text="Title").pack(anchor="w", **pad)
        self.title_entry = ctk.CTkEntry(self, width=380, placeholder_text="e.g. Morning Tea")
        self.title_entry.pack(**pad)

        ctk.CTkLabel(self, text="Category").pack(anchor="w", **pad)
        self.category_menu = ctk.CTkOptionMenu(self, width=380, values=CATEGORIES)
        self.category_menu.pack(**pad)

        ctk.CTkLabel(self, text="Expense Type").pack(anchor="w", **pad)
        self.type_menu = ctk.CTkOptionMenu(self, width=380, values=EXPENSE_TYPES)
        self.type_menu.pack(**pad)

        ctk.CTkLabel(self, text="Amount").pack(anchor="w", **pad)
        self.amount_entry = ctk.CTkEntry(self, width=380, placeholder_text="0.00")
        self.amount_entry.pack(**pad)

        ctk.CTkLabel(self, text="Notes (optional)").pack(anchor="w", **pad)
        self.notes_entry = ctk.CTkEntry(self, width=380)
        self.notes_entry.pack(**pad)

        if expense:
            self.date_entry.insert(0, expense["date"])
            self.title_entry.insert(0, expense["title"])
            self.category_menu.set(expense["category"])
            self.type_menu.set(expense["expense_type"])
            self.amount_entry.insert(0, str(expense["amount"]))
            self.notes_entry.insert(0, expense.get("notes", "") or "")
        else:
            self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.bind("<Return>", lambda e: self._save())
        self.after(50, self.date_entry.focus)

    def _center_on_parent(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = 440, 560
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _save(self):
        date = self.date_entry.get().strip()
        title = self.title_entry.get().strip()
        category = self.category_menu.get()
        etype = self.type_menu.get()
        notes = self.notes_entry.get().strip()
        if not validate_date(date):
            messagebox.showerror("Error", "Please enter a valid date (YYYY-MM-DD).")
            return
        if not title:
            messagebox.showerror("Error", "Title is required.")
            return
        if not validate_amount(self.amount_entry.get()):
            messagebox.showerror("Error", "Please enter a valid amount greater than zero.")
            return
        amount = float(self.amount_entry.get())

        uid = self.app.user["id"]
        if self.expense:
            update_expense(
                self.expense["id"], uid, date, title, category, etype, amount, notes,
            )
        else:
            add_expense(uid, date, title, category, etype, amount, notes)

        if self.on_save:
            self.on_save()
        self.destroy()


class ExpensesPage(ctk.CTkFrame):
    """Expense list with search, add, edit, delete."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(0, 12))
        ctk.CTkLabel(header, text="Expenses", font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Add Expense", width=140, command=self._add).pack(side="right")

        # Filters
        filt = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        filt.pack(fill="x", padx=8, pady=8)

        self.search_entry = ctk.CTkEntry(filt, placeholder_text="Search title/notes...", width=180)
        self.search_entry.pack(side="left", padx=12, pady=12)

        self.cat_filter = ctk.CTkOptionMenu(filt, values=["All"] + CATEGORIES, width=130)
        self.cat_filter.pack(side="left", padx=8, pady=12)

        self.type_filter = ctk.CTkOptionMenu(filt, values=["All"] + EXPENSE_TYPES, width=100)
        self.type_filter.pack(side="left", padx=8, pady=12)

        self.date_from = ctk.CTkEntry(filt, placeholder_text="From YYYY-MM-DD", width=130)
        self.date_from.pack(side="left", padx=8, pady=12)
        self.date_to = ctk.CTkEntry(filt, placeholder_text="To YYYY-MM-DD", width=130)
        self.date_to.pack(side="left", padx=8, pady=12)

        ctk.CTkButton(filt, text="Search", width=80, command=self.refresh).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(filt, text="Clear", width=70, fg_color="gray", command=self._clear_filters).pack(
            side="left", padx=4, pady=12,
        )

        # Summary bar
        self.summary_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13), text_color="gray")
        self.summary_label.pack(anchor="w", padx=12, pady=4)

        # Table
        table_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Expense.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Expense.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols = ("id", "date", "title", "category", "type", "amount", "notes")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", height=14, style="Expense.Treeview",
        )
        headings = {
            "id": ("ID", 40), "date": ("Date", 90), "title": ("Title", 140),
            "category": ("Category", 90), "type": ("Type", 60),
            "amount": ("Amount", 80), "notes": ("Notes", 120),
        }
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center" if col in ("id", "amount", "type") else "w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scroll.pack(side="right", fill="y", pady=8)

        # Actions
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(actions, text="✏️ Edit", width=100, command=self._edit).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="🗑️ Delete", width=100, fg_color="#c0392b", command=self._delete).pack(
            side="left", padx=4,
        )
        ctk.CTkButton(actions, text="📊 Weekly Summary", width=150, fg_color="#8e44ad",
                      command=self._show_weekly).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="📅 Monthly Summary", width=160, fg_color="#2980b9",
                      command=self._show_monthly).pack(side="left", padx=4)

    def _clear_filters(self):
        self.search_entry.delete(0, "end")
        self.cat_filter.set("All")
        self.type_filter.set("All")
        self.date_from.delete(0, "end")
        self.date_to.delete(0, "end")
        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        expenses = search_expenses(
            self.app.user["id"],
            date_from=self.date_from.get().strip() or None,
            date_to=self.date_to.get().strip() or None,
            category=self.cat_filter.get(),
            expense_type=self.type_filter.get(),
            search_text=self.search_entry.get().strip() or None,
        )
        cur = self.app.currency
        total = 0
        for e in expenses:
            self.tree.insert("", "end", values=(
                e["id"], e["date"], e["title"], e["category"],
                e["expense_type"], f"{cur}{e['amount']:,.2f}", e.get("notes", "")[:30],
            ))
            total += e["amount"]

        self.summary_label.configure(
            text=f"Showing {len(expenses)} expenses | Total: {cur}{total:,.2f}",
        )
        self._style_tree()

    def _style_tree(self):
        appearance = self.app.theme
        bg = "#2b2b2b" if appearance == "dark" else "#ffffff"
        fg = "#ffffff" if appearance == "dark" else "#333333"
        style = ttk.Style()
        style.configure("Expense.Treeview", background=bg, foreground=fg, fieldbackground=bg)
        style.configure("Expense.Treeview.Heading", background="#3498db", foreground="white")

    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an expense.")
            return None
        vals = self.tree.item(sel[0])["values"]
        return {"id": vals[0], "date": vals[1], "title": vals[2], "category": vals[3],
                "expense_type": vals[4]}

    def _add(self):
        ExpenseFormDialog(self, self.app, on_save=self._on_saved)

    def _edit(self):
        sel = self._get_selected()
        if not sel:
            return
        from expense_manager import get_expense
        expense = get_expense(sel["id"], self.app.user["id"])
        if expense:
            ExpenseFormDialog(self, self.app, expense=expense, on_save=self._on_saved)

    def _delete(self):
        sel = self._get_selected()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete this expense?"):
            delete_expense(sel["id"], self.app.user["id"])
            self.refresh()
            self.app.refresh_all()

    def _on_saved(self):
        self.refresh()
        self.app.refresh_all()

    def _show_weekly(self):
        w = get_weekly_summary(self.app.user["id"])
        cur = self.app.currency
        msg = (
            f"Week: {w['start_date']} to {w['end_date']}\n"
            f"Total: {cur}{w['total']:,.2f}\n"
            f"Small: {cur}{w['small']:,.2f} | Big: {cur}{w['big']:,.2f}\n"
            f"Transactions: {w['count']}"
        )
        messagebox.showinfo("Weekly Summary", msg)

    def _show_monthly(self):
        m = get_monthly_summary(self.app.user["id"])
        cur = self.app.currency
        cats = "\n".join(f"  {k}: {cur}{v:,.2f}" for k, v in m["by_category"].items())
        msg = (
            f"Month: {m['start_date']} to {m['end_date']}\n"
            f"Total: {cur}{m['total']:,.2f}\n"
            f"Small: {cur}{m['small']:,.2f} | Big: {cur}{m['big']:,.2f}\n"
            f"By Category:\n{cats or '  (none)'}"
        )
        messagebox.showinfo("Monthly Summary", msg)


class IncomePage(ctk.CTkScrollableFrame):
    """Income tracker page."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Income Tracker", font=ctk.CTkFont(size=28, weight="bold")).pack(
            anchor="w", padx=8, pady=(0, 16),
        )

        form = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        form.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(form, text="Add Income", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=16, pady=(12, 8),
        )
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)
        self.inc_date = ctk.CTkEntry(row, placeholder_text="Date", width=120)
        self.inc_date.pack(side="left", padx=4)
        self.inc_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.inc_title = ctk.CTkEntry(row, placeholder_text="Title (e.g. Salary)", width=180)
        self.inc_title.pack(side="left", padx=4)
        self.inc_amount = ctk.CTkEntry(row, placeholder_text="Amount", width=100)
        self.inc_amount.pack(side="left", padx=4)
        self.inc_notes = ctk.CTkEntry(row, placeholder_text="Notes", width=140)
        self.inc_notes.pack(side="left", padx=4)
        ctk.CTkButton(row, text="Add", width=80, command=self._add_income).pack(side="left", padx=8)

        self.inc_list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inc_list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _add_income(self):
        date = self.inc_date.get().strip()
        if not validate_date(date):
            messagebox.showerror("Error", "Please enter a valid date (YYYY-MM-DD).")
            return
        title = self.inc_title.get().strip()
        if not title:
            messagebox.showerror("Error", "Title required.")
            return
        if not validate_amount(self.inc_amount.get()):
            messagebox.showerror("Error", "Please enter a valid amount greater than zero.")
            return
        amount = float(self.inc_amount.get())
        add_income(
            self.app.user["id"], date,
            title, amount, self.inc_notes.get().strip(),
        )
        self.inc_title.delete(0, "end")
        self.inc_amount.delete(0, "end")
        self.inc_notes.delete(0, "end")
        self.refresh()
        self.app.refresh_all()

    def refresh(self):
        for w in self.inc_list_frame.winfo_children():
            w.destroy()
        items = get_income_list(self.app.user["id"])
        cur = self.app.currency
        total = sum(i["amount"] for i in items)
        ctk.CTkLabel(
            self.inc_list_frame,
            text=f"Total Income: {cur}{total:,.2f} ({len(items)} entries)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=8)

        for item in items:
            row = ctk.CTkFrame(self.inc_list_frame, corner_radius=8, fg_color=("gray85", "gray20"))
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row,
                text=f"{item['date']}  |  {item['title']}  |  {cur}{item['amount']:,.2f}",
                font=ctk.CTkFont(size=13),
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkButton(
                row, text="✕", width=36, height=28, fg_color="#c0392b",
                command=lambda i=item: self._delete(i["id"]),
            ).pack(side="right", padx=8, pady=6)

    def _delete(self, income_id):
        if messagebox.askyesno("Confirm", "Delete this income entry?"):
            delete_income(income_id, self.app.user["id"])
            self.refresh()
            self.app.refresh_all()


class SavingsPage(ctk.CTkScrollableFrame):
    """Savings tracker page."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Savings Tracker", font=ctk.CTkFont(size=28, weight="bold")).pack(
            anchor="w", padx=8, pady=(0, 16),
        )
        self.balance_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1abc9c",
        )
        self.balance_label.pack(anchor="w", padx=12, pady=8)

        form = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        form.pack(fill="x", padx=8, pady=8)
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=16)
        self.sav_date = ctk.CTkEntry(row, placeholder_text="Date", width=110)
        self.sav_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.sav_date.pack(side="left", padx=4)
        self.sav_title = ctk.CTkEntry(row, placeholder_text="Title", width=150)
        self.sav_title.pack(side="left", padx=4)
        self.sav_amount = ctk.CTkEntry(row, placeholder_text="Amount", width=90)
        self.sav_amount.pack(side="left", padx=4)
        self.sav_type = ctk.CTkOptionMenu(row, values=["Deposit", "Withdrawal"], width=120)
        self.sav_type.pack(side="left", padx=4)
        ctk.CTkButton(row, text="Add", width=70, command=self._add).pack(side="left", padx=8)

        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _add(self):
        date = self.sav_date.get().strip()
        if not validate_date(date):
            messagebox.showerror("Error", "Please enter a valid date (YYYY-MM-DD).")
            return
        title = self.sav_title.get().strip()
        if not title:
            messagebox.showerror("Error", "Title required.")
            return
        if not validate_amount(self.sav_amount.get()):
            messagebox.showerror("Error", "Please enter a valid amount greater than zero.")
            return
        amount = float(self.sav_amount.get())
        txn_type = self.sav_type.get()
        if txn_type == "Withdrawal":
            balance = get_savings_balance(self.app.user["id"])
            if amount > balance:
                messagebox.showerror(
                    "Error",
                    f"Insufficient savings balance ({self.app.currency}{balance:,.2f}).",
                )
                return
        add_savings(self.app.user["id"], date, title, amount, txn_type)
        self.sav_title.delete(0, "end")
        self.sav_amount.delete(0, "end")
        self.refresh()
        self.app.refresh_all()

    def refresh(self):
        cur = self.app.currency
        balance = get_savings_balance(self.app.user["id"])
        self.balance_label.configure(text=f"Current Balance: {cur}{balance:,.2f}")
        for w in self.list_frame.winfo_children():
            w.destroy()
        for item in get_savings_list(self.app.user["id"]):
            sign = "+" if item["transaction_type"] == "Deposit" else "-"
            color = "#2ecc71" if item["transaction_type"] == "Deposit" else "#e74c3c"
            row = ctk.CTkFrame(self.list_frame, corner_radius=8, fg_color=("gray85", "gray20"))
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row,
                text=f"{item['date']}  |  {item['title']}  |  {sign}{cur}{item['amount']:,.2f}",
                font=ctk.CTkFont(size=13), text_color=color,
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkButton(
                row, text="✕", width=36, height=28, fg_color="#c0392b",
                command=lambda i=item: self._delete(i["id"]),
            ).pack(side="right", padx=8, pady=6)

    def _delete(self, sid):
        if messagebox.askyesno("Confirm", "Delete this entry?"):
            delete_savings(sid, self.app.user["id"])
            self.refresh()
            self.app.refresh_all()


class GoalsPage(ctk.CTkScrollableFrame):
    """Financial goals page."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Financial Goals", font=ctk.CTkFont(size=28, weight="bold")).pack(
            anchor="w", padx=8, pady=(0, 16),
        )

        form = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        form.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(form, text="New Goal", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=16, pady=(12, 8),
        )
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=4)
        self.goal_title = ctk.CTkEntry(r1, placeholder_text="Goal title", width=200)
        self.goal_title.pack(side="left", padx=4)
        self.goal_target = ctk.CTkEntry(r1, placeholder_text="Target amount", width=120)
        self.goal_target.pack(side="left", padx=4)
        self.goal_deadline = ctk.CTkEntry(r1, placeholder_text="Deadline YYYY-MM-DD", width=150)
        self.goal_deadline.pack(side="left", padx=4)
        self.goal_desc = ctk.CTkEntry(r1, placeholder_text="Description", width=180)
        self.goal_desc.pack(side="left", padx=4)
        ctk.CTkButton(r1, text="Add Goal", width=100, command=self._add).pack(side="left", padx=8)

        self.goals_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.goals_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _add(self):
        title = self.goal_title.get().strip()
        if not title:
            messagebox.showerror("Error", "Title required.")
            return
        if not validate_amount(self.goal_target.get()):
            messagebox.showerror("Error", "Please enter a valid target amount greater than zero.")
            return
        target = float(self.goal_target.get())
        deadline = self.goal_deadline.get().strip()
        if deadline and not validate_date(deadline):
            messagebox.showerror("Error", "Please enter a valid deadline (YYYY-MM-DD) or leave it empty.")
            return
        add_goal(self.app.user["id"], title, target, deadline, self.goal_desc.get().strip())
        self.goal_title.delete(0, "end")
        self.goal_target.delete(0, "end")
        self.goal_deadline.delete(0, "end")
        self.goal_desc.delete(0, "end")
        self.refresh()
        self.app.refresh_all()

    def refresh(self):
        for w in self.goals_frame.winfo_children():
            w.destroy()
        cur = self.app.currency
        for g in get_goals(self.app.user["id"]):
            card = ctk.CTkFrame(self.goals_frame, corner_radius=12, fg_color=("gray90", "gray17"))
            card.pack(fill="x", pady=6, padx=4)

            progress = min(g["current_amount"] / g["target_amount"], 1.0) if g["target_amount"] > 0 else 0
            ctk.CTkLabel(
                card, text=f"🎯 {g['title']}  [{g['status']}]",
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(
                card,
                text=f"Target: {cur}{g['target_amount']:,.2f}  |  "
                     f"Saved: {cur}{g['current_amount']:,.2f}  |  "
                     f"Deadline: {g.get('deadline') or 'N/A'}",
                font=ctk.CTkFont(size=12), text_color="gray",
            ).pack(anchor="w", padx=16)
            ctk.CTkProgressBar(card, width=400, progress_color="#3498db").pack(
                anchor="w", padx=16, pady=8,
            )
            card.winfo_children()[-1].set(progress)

            if g.get("description"):
                ctk.CTkLabel(card, text=g["description"], font=ctk.CTkFont(size=11), text_color="gray").pack(
                    anchor="w", padx=16,
                )

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(anchor="w", padx=16, pady=(4, 12))
            prog_entry = ctk.CTkEntry(btn_row, placeholder_text="Update saved amount", width=160)
            prog_entry.pack(side="left", padx=4)
            ctk.CTkButton(
                btn_row, text="Update", width=80,
                command=lambda g=g, e=prog_entry: self._update_progress(g["id"], e),
            ).pack(side="left", padx=4)
            ctk.CTkButton(
                btn_row, text="Delete", width=80, fg_color="#c0392b",
                command=lambda g=g: self._delete(g["id"]),
            ).pack(side="left", padx=4)

    def _update_progress(self, goal_id, entry):
        if not validate_amount(entry.get(), allow_zero=True):
            messagebox.showerror("Error", "Please enter a valid saved amount (0 or more).")
            return
        update_goal_progress(goal_id, self.app.user["id"], float(entry.get()))
        entry.delete(0, "end")
        self.refresh()
        self.app.refresh_all()

    def _delete(self, goal_id):
        if messagebox.askyesno("Confirm", "Delete this goal?"):
            delete_goal(goal_id, self.app.user["id"])
            self.refresh()
            self.app.refresh_all()


class AnalyticsPage(ctk.CTkScrollableFrame):
    """Advanced expense analytics with charts."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Expense Analytics", font=ctk.CTkFont(size=28, weight="bold")).pack(
            anchor="w", padx=8, pady=(0, 12),
        )
        self.stats_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13), justify="left")
        self.stats_label.pack(anchor="w", padx=12, pady=8)
        self.charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True, padx=4, pady=8)

    def refresh(self):
        analytics = get_analytics(self.app.user["id"])
        cur = self.app.currency
        self.stats_label.configure(text=(
            f"Monthly Spending: {cur}{analytics['monthly_total']:,.2f}\n"
            f"Income: {cur}{analytics['income']:,.2f}  |  "
            f"Net: {cur}{analytics['net_balance']:,.2f}  |  "
            f"Savings: {cur}{analytics['savings_balance']:,.2f}\n"
            f"Budget Used: {cur}{analytics['monthly_total']:,.2f} / "
            f"{cur}{analytics['budget']:,.2f}"
        ))

        for w in self.charts_frame.winfo_children():
            w.destroy()

        self.charts_frame.grid_columnconfigure(0, weight=1)
        self.charts_frame.grid_columnconfigure(1, weight=1)

        pie_host = ctk.CTkFrame(self.charts_frame, corner_radius=12, fg_color=("gray90", "gray17"))
        pie_host.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        create_pie_chart(pie_host, analytics["by_category"], appearance=self.app.theme)

        bar_host = ctk.CTkFrame(self.charts_frame, corner_radius=12, fg_color=("gray90", "gray17"))
        bar_host.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        create_bar_chart(
            bar_host,
            analytics["by_category"],
            title="Category Spending",
            appearance=self.app.theme,
        )

        # Trend chart from recent expenses
        from expense_manager import search_expenses
        expenses = search_expenses(self.app.user["id"])
        daily = {}
        for e in expenses:
            daily[e["date"]] = daily.get(e["date"], 0) + e["amount"]
        dates = sorted(daily.keys())[-14:]
        amounts = [daily[d] for d in dates]

        trend_host = ctk.CTkFrame(self.charts_frame, corner_radius=12, fg_color=("gray90", "gray17"))
        trend_host.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")
        create_trend_chart(trend_host, dates, amounts, appearance=self.app.theme)


class ReportsPage(ctk.CTkFrame):
    """Reports and export page."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Reports & Export", font=ctk.CTkFont(size=28, weight="bold")).pack(
            anchor="w", padx=8, pady=(0, 20),
        )

        card = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        card.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(
            card, text="Export your expense data",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            card,
            text="Export all expenses to CSV or generate a monthly PDF summary report.",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkButton(
            card, text="📄 Export CSV", width=200, height=44,
            command=lambda: self._export_csv(),
        ).pack(anchor="w", padx=20, pady=6)
        ctk.CTkButton(
            card, text="📑 Export PDF Report", width=200, height=44,
            command=lambda: show_export_dialog(self, self.app.user["id"], self.app.currency),
        ).pack(anchor="w", padx=20, pady=(6, 20))

        # Quick summaries
        sum_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        sum_card.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(sum_card, text="Quick Reports", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=20, pady=(16, 8),
        )
        self.report_text = ctk.CTkTextbox(sum_card, height=200, font=ctk.CTkFont(size=13))
        self.report_text.pack(fill="x", padx=20, pady=(0, 16))

    def _export_csv(self):
        ok, msg = export_to_csv(self.app.user["id"], currency=self.app.currency)
        if ok:
            messagebox.showinfo("Export", f"CSV saved to:\n{msg}")
        else:
            messagebox.showwarning("Export", msg)

    def refresh(self):
        m = get_monthly_summary(self.app.user["id"])
        w = get_weekly_summary(self.app.user["id"])
        cur = self.app.currency
        text = (
            f"═══ MONTHLY REPORT ═══\n"
            f"Period: {m['start_date']} to {m['end_date']}\n"
            f"Total Expenses: {cur}{m['total']:,.2f}\n"
            f"Small: {cur}{m['small']:,.2f} | Big: {cur}{m['big']:,.2f}\n"
            f"Transactions: {m['count']}\n\n"
            f"Category Breakdown:\n"
        )
        for cat, amt in sorted(m["by_category"].items(), key=lambda x: -x[1]):
            text += f"  • {cat}: {cur}{amt:,.2f}\n"
        text += (
            f"\n═══ WEEKLY REPORT ═══\n"
            f"Period: {w['start_date']} to {w['end_date']}\n"
            f"Total: {cur}{w['total']:,.2f} ({w['count']} transactions)\n"
        )
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", text)


class MainApp(ctk.CTk):
    """Main application window with sidebar navigation."""

    def __init__(self, user):
        super().__init__()
        self.user = user
        settings = get_user_settings(user["id"])
        self.theme = settings.get("theme", "dark")
        self.currency = settings.get("currency_symbol", "₹")

        self.title("Daily Expense Tracker")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        ctk.set_appearance_mode(self.theme)
        ctk.set_default_color_theme("blue")

        self._center_window()
        self._build_layout()
        self.show_page("dashboard")

        # Check budget on startup
        self.after(500, self._check_budget_alert)

    def _center_window(self):
        self.update_idletasks()
        w, h = 1200, 750
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="💰 Expense\nTracker",
            font=ctk.CTkFont(size=20, weight="bold"), justify="center",
        ).pack(pady=(24, 8), padx=16)
        ctk.CTkLabel(
            self.sidebar, text=self.user["username"],
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(pady=(0, 20))

        self.nav_buttons = {}
        for key, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                height=40, fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[key] = btn

        ctk.CTkButton(
            self.sidebar, text="🚪 Logout", height=40,
            fg_color="#c0392b", hover_color="#a93226",
            command=self._logout,
        ).pack(side="bottom", fill="x", padx=12, pady=20)

        # Content area
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Pages
        self.pages = {
            "dashboard": DashboardPage(self.content, self),
            "expenses": ExpensesPage(self.content, self),
            "income": IncomePage(self.content, self),
            "savings": SavingsPage(self.content, self),
            "goals": GoalsPage(self.content, self),
            "analytics": AnalyticsPage(self.content, self),
            "reports": ReportsPage(self.content, self),
            "settings": SettingsPage(self.content, self),
        }

    def show_page(self, name):
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color=("#3498db", "#2980b9"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        for page in self.pages.values():
            page.grid_forget()

        page = self.pages[name]
        page.grid(row=0, column=0, sticky="nsew")
        if hasattr(page, "refresh"):
            page.refresh()

    def apply_theme(self, theme):
        self.theme = theme
        ctk.set_appearance_mode(theme)
        self.refresh_all()

    def refresh_all(self):
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                page.refresh()

    def _check_budget_alert(self):
        from expense_manager import is_budget_exceeded, get_budget
        exceeded, over = is_budget_exceeded(self.user["id"])
        budget = get_budget(self.user["id"])
        if exceeded and budget > 0:
            messagebox.showwarning(
                "Budget Alert",
                f"⚠️ You have exceeded your monthly budget by {self.currency}{over:,.2f}!",
            )

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            start_app()


def start_app():
    """Initialize database and launch auth → main app flow."""
    init_database()
    create_sample_data()

    def on_login(user):
        app = MainApp(user)
        app.mainloop()

    auth = AuthWindow(on_login_success=on_login)
    auth.mainloop()


if __name__ == "__main__":
    start_app()
