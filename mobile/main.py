"""
mobile/main.py - Android/iOS mobile app (KivyMD).
Build APK: see BUILD_APK.md and buildozer.spec in project root.

Run on PC for testing:  python mobile/main.py
"""

import os
import sys

# Project root on path (database, expense_manager, auth_core)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from kivy.utils import platform
from kivy.metrics import dp
from kivy.clock import Clock

# Android: store DB in app-private storage
if platform == "android":
    try:
        from android.permissions import request_permissions, Permission
        from android.storage import app_storage_path

        request_permissions([
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
        ])
        os.environ["EXPENSE_DB_DIR"] = os.path.join(app_storage_path(), "database")
    except ImportError:
        pass

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.snackbar import Snackbar

from database import init_database, create_sample_data
from auth_core import login_user, register_user, get_user_settings, update_user_settings
from expense_manager import (
    CATEGORIES, EXPENSE_TYPES,
    add_expense, update_expense, delete_expense, search_expenses, get_expense,
    get_analytics, get_monthly_summary, get_weekly_summary,
    set_budget, get_budget, is_budget_exceeded,
    add_income, get_income_list, delete_income,
    add_savings, get_savings_list, delete_savings, get_savings_balance,
    add_goal, get_goals, update_goal_progress, delete_goal,
)
from reports import export_to_csv


class AppState:
    """Global session state."""
    user = None
    currency = "₹"
    theme = "Dark"


state = AppState()


def fmt(amount):
    return f"{state.currency}{amount:,.2f}"


def snack(text, duration=2.5):
    Snackbar(text=text, duration=duration).open()


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        layout = MDBoxLayout(orientation="vertical", padding=dp(24), spacing=dp(12))
        layout.add_widget(MDLabel(
            text="[b]💰 Expense Tracker[/b]", markup=True,
            halign="center", font_style="H4", size_hint_y=None, height=dp(56),
        ))
        layout.add_widget(MDLabel(
            text="Track daily spending on your phone",
            halign="center", theme_text_color="Secondary",
            size_hint_y=None, height=dp(32),
        ))
        self.username = MDTextField(hint_text="Username", mode="rectangle", size_hint_y=None, height=dp(56))
        self.password = MDTextField(hint_text="Password", mode="rectangle", password=True,
                                    size_hint_y=None, height=dp(56))
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(MDRaisedButton(
            text="SIGN IN", size_hint_y=None, height=dp(48),
            pos_hint={"center_x": 0.5}, on_release=self.do_login,
        ))
        layout.add_widget(MDFlatButton(
            text="Create account", pos_hint={"center_x": 0.5},
            on_release=lambda x: setattr(self.manager, "current", "register"),
        ))
        layout.add_widget(MDLabel(
            text="Demo: demo / demo123", halign="center",
            theme_text_color="Hint", size_hint_y=None, height=dp(28),
        ))
        self.add_widget(layout)

    def do_login(self, *_):
        u = self.username.text.strip()
        p = self.password.text
        if not u or not p:
            snack("Enter username and password")
            return
        ok, result = login_user(u, p)
        if ok:
            state.user = result
            settings = get_user_settings(result["id"])
            state.currency = settings.get("currency_symbol", "₹")
            state.theme = settings.get("theme", "dark").capitalize()
            MDApp.get_running_app().apply_theme(state.theme)
            self.manager.current = "home"
            Clock.schedule_once(lambda dt: self.manager.get_screen("home").refresh_all(), 0.2)
            exceeded, over = is_budget_exceeded(result["id"])
            if exceeded:
                snack(f"⚠ Budget exceeded by {fmt(over)}!", 4)
        else:
            snack(str(result))


class RegisterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "register"
        scroll = MDScrollView()
        layout = MDBoxLayout(orientation="vertical", padding=dp(24), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))
        layout.add_widget(MDLabel(text="Register", font_style="H5", size_hint_y=None, height=dp(40)))
        self.username = MDTextField(hint_text="Username", mode="rectangle", size_hint_y=None, height=dp(52))
        self.email = MDTextField(hint_text="Email", mode="rectangle", size_hint_y=None, height=dp(52))
        self.password = MDTextField(hint_text="Password", mode="rectangle", password=True,
                                    size_hint_y=None, height=dp(52))
        self.confirm = MDTextField(hint_text="Confirm password", mode="rectangle", password=True,
                                   size_hint_y=None, height=dp(52))
        for w in (self.username, self.email, self.password, self.confirm):
            layout.add_widget(w)
        layout.add_widget(MDRaisedButton(
            text="CREATE ACCOUNT", size_hint_y=None, height=dp(48),
            on_release=self.do_register,
        ))
        layout.add_widget(MDFlatButton(
            text="Back to login",
            on_release=lambda x: setattr(self.manager, "current", "login"),
        ))
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def do_register(self, *_):
        if self.password.text != self.confirm.text:
            snack("Passwords do not match")
            return
        ok, msg = register_user(
            self.username.text.strip(), self.email.text.strip(), self.password.text,
        )
        snack(msg, 3)
        if ok:
            self.manager.current = "login"


# ─── Stat card helper ─────────────────────────────────────────────────────────

def stat_card(title, value, color="#3498db"):
    card = MDCard(
        orientation="vertical", padding=dp(12), size_hint_y=None, height=dp(88),
        radius=[12], md_bg_color=(0.15, 0.15, 0.18, 1),
    )
    card.add_widget(MDLabel(text=title, theme_text_color="Secondary", font_style="Caption"))
    card.add_widget(MDLabel(
        text=value, theme_text_color="Custom", text_color=color,
        font_style="H6", bold=True,
    ))
    return card


# ─── Home (bottom navigation) ─────────────────────────────────────────────────

class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "home"
        root = MDBoxLayout(orientation="vertical")

        self.toolbar = MDTopAppBar(title="Dashboard", elevation=2)
        root.add_widget(self.toolbar)

        self.content = MDBoxLayout(orientation="vertical")
        root.add_widget(self.content)

        self.nav = MDBottomNavigation(panel_color=(0.12, 0.12, 0.14, 1))
        self.tab_dashboard = MDBottomNavigationItem(name="dash", text="Home", icon="view-dashboard")
        self.tab_expenses = MDBottomNavigationItem(name="exp", text="Expenses", icon="cash-minus")
        self.tab_finance = MDBottomNavigationItem(name="fin", text="Finance", icon="wallet")
        self.tab_more = MDBottomNavigationItem(name="more", text="More", icon="dots-horizontal")

        for tab in (self.tab_dashboard, self.tab_expenses, self.tab_finance, self.tab_more):
            self.nav.add_widget(tab)

        self._build_dashboard()
        self._build_expenses()
        self._build_finance()
        self._build_more()

        root.add_widget(self.nav)
        self.add_widget(root)

    def _scroll_page(self):
        scroll = MDScrollView()
        box = MDBoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        scroll.add_widget(box)
        return scroll, box

    def _build_dashboard(self):
        scroll, box = self._scroll_page()
        self.dash_box = box
        self.tab_dashboard.add_widget(scroll)

    def _build_expenses(self):
        scroll, box = self._scroll_page()
        self.exp_box = box
        row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        row.add_widget(MDRaisedButton(text="+ Add", size_hint_x=0.4, on_release=self.show_add_expense))
        row.add_widget(MDFlatButton(text="Export CSV", size_hint_x=0.6, on_release=self.export_csv))
        box.add_widget(row)
        self.exp_list = MDList()
        box.add_widget(self.exp_list)
        self.tab_expenses.add_widget(scroll)

    def _build_finance(self):
        scroll, box = self._scroll_page()
        self.fin_box = box
        self.tab_finance.add_widget(scroll)

    def _build_more(self):
        scroll, box = self._scroll_page()
        self.more_box = box
        box.add_widget(MDLabel(text="Settings", font_style="H6", size_hint_y=None, height=dp(36)))
        theme_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        theme_row.add_widget(MDLabel(text="Theme", size_hint_x=0.5))
        self.theme_btn = MDRaisedButton(
            text="Dark",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(40),
            on_release=self.toggle_theme,
        )
        theme_row.add_widget(self.theme_btn)
        box.add_widget(theme_row)
        self.budget_field = MDTextField(hint_text="Monthly budget", mode="rectangle",
                                        size_hint_y=None, height=dp(52))
        box.add_widget(self.budget_field)
        box.add_widget(MDRaisedButton(
            text="Save budget", size_hint_y=None, height=dp(44),
            on_release=self.save_budget,
        ))
        box.add_widget(MDRaisedButton(
            text="Logout", md_bg_color=(0.75, 0.2, 0.2, 1), size_hint_y=None, height=dp(44),
            on_release=self.logout,
        ))
        self.tab_more.add_widget(scroll)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_expenses()
        self.refresh_finance()
        self.toolbar.title = f"Hi, {state.user['username']}"
        if hasattr(self, "theme_btn"):
            self.theme_btn.text = state.theme
        budget = get_budget(state.user["id"])
        if budget > 0:
            self.budget_field.text = str(int(budget) if budget == int(budget) else budget)

    def refresh_dashboard(self):
        self.dash_box.clear_widgets()
        uid = state.user["id"]
        a = get_analytics(uid)
        w = get_weekly_summary(uid)

        if a["budget_exceeded"] and a["budget"] > 0:
            alert = MDCard(
                padding=dp(12), size_hint_y=None, height=dp(56),
                md_bg_color=(0.75, 0.2, 0.2, 1), radius=[10],
            )
            alert.add_widget(MDLabel(
                text=f"⚠ Over budget by {fmt(a['over_amount'])}",
                theme_text_color="Custom", text_color=(1, 1, 1, 1),
            ))
            self.dash_box.add_widget(alert)

        grid = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(96))
        grid.add_widget(stat_card("Total", fmt(a["monthly_total"]), "#e74c3c"))
        grid.add_widget(stat_card("Budget left", fmt(a["remaining_budget"]), "#2ecc71"))
        self.dash_box.add_widget(grid)

        grid2 = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(96))
        grid2.add_widget(stat_card("Small", fmt(a["small_total"]), "#f39c12"))
        grid2.add_widget(stat_card("Big", fmt(a["big_total"]), "#9b59b6"))
        self.dash_box.add_widget(grid2)

        grid3 = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(96))
        grid3.add_widget(stat_card("Income", fmt(a["income"]), "#3498db"))
        grid3.add_widget(stat_card("Savings", fmt(a["savings_balance"]), "#1abc9c"))
        self.dash_box.add_widget(grid3)

        self.dash_box.add_widget(MDLabel(
            text=f"Week total: {fmt(w['total'])}  •  {w['count']} transactions",
            size_hint_y=None, height=dp(32), theme_text_color="Secondary",
        ))

        self.dash_box.add_widget(MDLabel(
            text="By category", font_style="Subtitle1",
            size_hint_y=None, height=dp(32),
        ))
        total = a["monthly_total"] or 1
        for cat, amt in sorted(a["by_category"].items(), key=lambda x: -x[1]):
            card = MDCard(
                orientation="vertical", padding=dp(8), size_hint_y=None, height=dp(52),
                radius=[8],
            )
            row = MDBoxLayout()
            row.add_widget(MDLabel(text=cat, size_hint_x=0.35))
            row.add_widget(MDLabel(
                text=fmt(amt), halign="right", size_hint_x=0.35,
                theme_text_color="Primary",
            ))
            pct = amt / total
            from kivymd.uix.progressindicator import MDProgressBar
            card.add_widget(row)
            bar = MDProgressBar(value=pct, size_hint_y=None, height=dp(4))
            card.add_widget(bar)
            self.dash_box.add_widget(card)

    def refresh_expenses(self):
        self.exp_list.clear_widgets()
        for e in search_expenses(state.user["id"])[:80]:
            item = OneLineAvatarIconListItem(
                text=f"{e['title']}  •  {fmt(e['amount'])}",
                secondary_text=f"{e['date']}  |  {e['category']}  |  {e['expense_type']}",
                on_release=lambda x, ex=e: self.show_expense_menu(ex),
            )
            item.add_widget(IconLeftWidget(icon="receipt"))
            self.exp_list.add_widget(item)

    def refresh_finance(self):
        self.fin_box.clear_widgets()
        uid = state.user["id"]

        self.fin_box.add_widget(MDLabel(text="Income", font_style="H6",
                                       size_hint_y=None, height=dp(32)))
        inc_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.inc_title = MDTextField(hint_text="Title", size_hint_x=0.35, mode="rectangle")
        self.inc_amt = MDTextField(hint_text="Amount", size_hint_x=0.3, mode="rectangle")
        inc_row.add_widget(self.inc_title)
        inc_row.add_widget(self.inc_amt)
        inc_row.add_widget(MDRaisedButton(text="+", size_hint_x=0.15,
                                        on_release=self.add_income_click))
        self.fin_box.add_widget(inc_row)
        for i in get_income_list(uid)[:15]:
            self.fin_box.add_widget(MDLabel(
                text=f"• {i['date']} {i['title']}: {fmt(i['amount'])}",
                size_hint_y=None, height=dp(28), theme_text_color="Secondary",
            ))

        self.fin_box.add_widget(MDLabel(text="Savings", font_style="H6",
                                       size_hint_y=None, height=dp(36)))
        self.fin_box.add_widget(MDLabel(
            text=f"Balance: {fmt(get_savings_balance(uid))}",
            size_hint_y=None, height=dp(28), bold=True,
        ))
        sav_row = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        self.sav_title = MDTextField(hint_text="Title", size_hint_x=0.3, mode="rectangle")
        self.sav_amt = MDTextField(hint_text="Amount", size_hint_x=0.25, mode="rectangle")
        sav_row.add_widget(self.sav_title)
        sav_row.add_widget(self.sav_amt)
        sav_row.add_widget(MDRaisedButton(text="Dep", size_hint_x=0.2,
                                          on_release=lambda x: self.add_sav("Deposit")))
        sav_row.add_widget(MDRaisedButton(text="Wdr", size_hint_x=0.2,
                                          on_release=lambda x: self.add_sav("Withdrawal")))
        self.fin_box.add_widget(sav_row)

        self.fin_box.add_widget(MDLabel(text="Goals", font_style="H6",
                                       size_hint_y=None, height=dp(36)))
        for g in get_goals(uid):
            prog = g["current_amount"] / g["target_amount"] if g["target_amount"] else 0
            self.fin_box.add_widget(MDLabel(
                text=f"🎯 {g['title']}: {fmt(g['current_amount'])} / {fmt(g['target_amount'])}",
                size_hint_y=None, height=dp(36),
            ))
            from kivymd.uix.progressindicator import MDProgressBar
            self.fin_box.add_widget(MDProgressBar(value=min(prog, 1), size_hint_y=None, height=dp(6)))

    def show_expense_menu(self, expense):
        def edit(*_):
            self.dialog.dismiss()
            self.show_add_expense(expense=expense)

        def delete(*_):
            delete_expense(expense["id"], state.user["id"])
            self.dialog.dismiss()
            snack("Deleted")
            self.refresh_all()

        self.dialog = MDDialog(
            title=expense["title"],
            text=f"{expense['date']}\n{expense['category']} | {expense['expense_type']}\n{fmt(expense['amount'])}",
            buttons=[
                MDFlatButton(text="Edit", on_release=edit),
                MDFlatButton(text="Delete", on_release=delete),
            ],
        )
        self.dialog.open()

    def show_add_expense(self, expense=None, *_):
        from datetime import datetime
        fields = {}
        form = MDBoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        hints = [
            ("date", "Date YYYY-MM-DD", expense["date"] if expense else datetime.now().strftime("%Y-%m-%d")),
            ("title", "Title", expense["title"] if expense else ""),
            ("amount", "Amount", str(expense["amount"]) if expense else ""),
            ("notes", "Notes", expense.get("notes", "") if expense else ""),
        ]
        for key, hint, val in hints:
            f = MDTextField(hint_text=hint, text=val or "", mode="rectangle",
                            size_hint_y=None, height=dp(48))
            fields[key] = f
            form.add_widget(f)

        cat_btn = MDRaisedButton(text=f"Category: {expense['category'] if expense else CATEGORIES[0]}",
                                 size_hint_y=None, height=dp(40))
        type_btn = MDRaisedButton(text=f"Type: {expense['expense_type'] if expense else 'Small'}",
                                  size_hint_y=None, height=dp(40))
        sel_cat = [expense["category"] if expense else CATEGORIES[0]]
        sel_type = [expense["expense_type"] if expense else "Small"]

        def pick_cat(*_):
            menu = MDDropdownMenu(
                caller=cat_btn, items=[{"text": c} for c in CATEGORIES],
                width_mult=4,
            )
            def set_cat(item):
                sel_cat[0] = item.text
                cat_btn.text = f"Category: {item.text}"
                menu.dismiss()
            menu.callback = set_cat
            menu.open()

        def pick_type(*_):
            menu = MDDropdownMenu(
                caller=type_btn, items=[{"text": t} for t in EXPENSE_TYPES],
                width_mult=4,
            )
            def set_type(item):
                sel_type[0] = item.text
                type_btn.text = f"Type: {item.text}"
                menu.dismiss()
            menu.callback = set_type
            menu.open()

        cat_btn.bind(on_release=pick_cat)
        type_btn.bind(on_release=pick_type)
        form.add_widget(cat_btn)
        form.add_widget(type_btn)

        def save(*_):
            try:
                amount = float(fields["amount"].text)
            except ValueError:
                snack("Invalid amount")
                return
            title = fields["title"].text.strip()
            if not title:
                snack("Title required")
                return
            uid = state.user["id"]
            if expense:
                update_expense(
                    expense["id"], uid, fields["date"].text.strip(), title,
                    sel_cat[0], sel_type[0], amount, fields["notes"].text.strip(),
                )
            else:
                add_expense(
                    uid, fields["date"].text.strip(), title,
                    sel_cat[0], sel_type[0], amount, fields["notes"].text.strip(),
                )
            dlg.dismiss()
            snack("Saved")
            self.refresh_all()

        dlg = MDDialog(
            title="Edit expense" if expense else "Add expense",
            type="custom", content_cls=form,
            buttons=[MDRaisedButton(text="Save", on_release=save)],
        )
        dlg.open()

    def export_csv(self, *_):
        ok, msg = export_to_csv(state.user["id"], currency=state.currency)
        snack(f"Exported: {msg}" if ok else msg, 4)

    def add_income_click(self, *_):
        try:
            amount = float(self.inc_amt.text)
        except ValueError:
            snack("Invalid amount")
            return
        from datetime import datetime
        title = self.inc_title.text.strip() or "Income"
        add_income(state.user["id"], datetime.now().strftime("%Y-%m-%d"), title, amount)
        self.inc_title.text = ""
        self.inc_amt.text = ""
        snack("Income added")
        self.refresh_all()

    def add_sav(self, ttype, *_):
        try:
            amount = float(self.sav_amt.text)
        except ValueError:
            snack("Invalid amount")
            return
        from datetime import datetime
        title = self.sav_title.text.strip() or "Savings"
        add_savings(state.user["id"], datetime.now().strftime("%Y-%m-%d"), title, amount, ttype)
        self.sav_title.text = ""
        self.sav_amt.text = ""
        snack("Savings updated")
        self.refresh_all()

    def save_budget(self, *_):
        try:
            amount = float(self.budget_field.text)
        except ValueError:
            snack("Enter valid budget")
            return
        from datetime import datetime
        now = datetime.now()
        set_budget(state.user["id"], now.month, now.year, amount)
        snack(f"Budget set: {fmt(amount)}")
        self.refresh_all()

    def toggle_theme(self, *_):
        theme = "Light" if state.theme == "Dark" else "Dark"
        state.theme = theme
        self.theme_btn.text = theme
        update_user_settings(state.user["id"], theme=theme.lower())
        MDApp.get_running_app().apply_theme(theme)

    def logout(self, *_):
        state.user = None
        self.manager.current = "login"


class ExpenseTrackerApp(MDApp):
    def build(self):
        init_database()
        create_sample_data()
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        sm = MDScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(RegisterScreen())
        sm.add_widget(HomeScreen())
        return sm

    def apply_theme(self, theme):
        self.theme_cls.theme_style = theme


if __name__ == "__main__":
    ExpenseTrackerApp().run()
