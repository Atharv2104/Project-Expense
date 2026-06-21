"""
dashboard.py - Main dashboard view with summary cards, budget alerts, and charts.
"""

import customtkinter as ctk
from expense_manager import get_analytics, get_weekly_summary, get_monthly_summary, is_budget_exceeded
from charts import create_pie_chart, create_type_bar_chart


class StatCard(ctk.CTkFrame):
    """Reusable metric card for the dashboard."""

    def __init__(self, master, title, value="0", icon="📊", color="#3498db", **kwargs):
        super().__init__(master, corner_radius=12, fg_color=("gray90", "gray17"), **kwargs)
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=22)).pack(side="left")
        ctk.CTkLabel(
            top, text=title, font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(side="left", padx=(8, 0))

        self.value_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=color,
        )
        self.value_label.pack(anchor="w", padx=16, pady=(0, 14))

    def set_value(self, value, color=None):
        self.value_label.configure(text=value)
        if color:
            self.value_label.configure(text_color=color)


class DashboardPage(ctk.CTkScrollableFrame):
    """Dashboard with stats, budget alert, and charts."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(0, 16))
        ctk.CTkLabel(
            header, text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header, text=f"Welcome, {self.app.user['username']}! 👋",
            font=ctk.CTkFont(size=14), text_color="gray",
        ).pack(side="right", padx=8)

        # Budget alert banner (hidden by default)
        self.alert_frame = ctk.CTkFrame(self, fg_color="#c0392b", corner_radius=10)
        self.alert_label = ctk.CTkLabel(
            self.alert_frame, text="",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="white",
        )
        self.alert_label.pack(padx=16, pady=12)

        # Stat cards row
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=4, pady=8)
        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=1)

        self.card_total = StatCard(self.cards_frame, "Total Expenses", "₹0", "💸", "#e74c3c")
        self.card_total.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_small = StatCard(self.cards_frame, "Small Expenses", "₹0", "☕", "#f39c12")
        self.card_small.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_big = StatCard(self.cards_frame, "Big Expenses", "₹0", "🏠", "#9b59b6")
        self.card_big.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        self.card_budget = StatCard(self.cards_frame, "Remaining Budget", "₹0", "🎯", "#2ecc71")
        self.card_budget.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")

        # Second row
        self.cards_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame2.pack(fill="x", padx=4, pady=4)
        for i in range(4):
            self.cards_frame2.grid_columnconfigure(i, weight=1)

        self.card_income = StatCard(self.cards_frame2, "Monthly Income", "₹0", "💵", "#3498db")
        self.card_income.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_savings = StatCard(self.cards_frame2, "Savings Balance", "₹0", "🏦", "#1abc9c")
        self.card_savings.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_net = StatCard(self.cards_frame2, "Net Balance", "₹0", "📈", "#16a085")
        self.card_net.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        self.card_count = StatCard(self.cards_frame2, "Transactions", "0", "📋", "#7f8c8d")
        self.card_count.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")

        # Weekly / Monthly quick summary
        self.summary_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray90", "gray17"))
        self.summary_frame.pack(fill="x", padx=8, pady=12)
        ctk.CTkLabel(
            self.summary_frame, text="Quick Summary",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(12, 8))
        self.summary_text = ctk.CTkLabel(
            self.summary_frame, text="", justify="left",
            font=ctk.CTkFont(size=13), text_color="gray",
        )
        self.summary_text.pack(anchor="w", padx=16, pady=(0, 16))

        # Charts
        charts_label = ctk.CTkLabel(
            self, text="Visual Analytics",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        charts_label.pack(anchor="w", padx=12, pady=(8, 4))

        self.charts_container = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True, padx=4, pady=8)
        self.charts_container.grid_columnconfigure(0, weight=1)
        self.charts_container.grid_columnconfigure(1, weight=1)

        self.pie_frame = ctk.CTkFrame(self.charts_container, corner_radius=12, fg_color=("gray90", "gray17"))
        self.pie_frame.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(self.pie_frame, text="By Category", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=8)
        self.pie_chart_host = ctk.CTkFrame(self.pie_frame, fg_color="transparent")
        self.pie_chart_host.pack(fill="both", expand=True, padx=8, pady=8)

        self.bar_frame = ctk.CTkFrame(self.charts_container, corner_radius=12, fg_color=("gray90", "gray17"))
        self.bar_frame.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(self.bar_frame, text="Small vs Big", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=8)
        self.bar_chart_host = ctk.CTkFrame(self.bar_frame, fg_color="transparent")
        self.bar_chart_host.pack(fill="both", expand=True, padx=8, pady=8)

        self._pie_chart = None
        self._bar_chart = None

    def refresh(self):
        """Reload dashboard data from database."""
        cur = self.app.currency
        analytics = get_analytics(self.app.user["id"])
        weekly = get_weekly_summary(self.app.user["id"])
        monthly = get_monthly_summary(self.app.user["id"])

        def fmt(n):
            return f"{cur}{n:,.2f}"

        self.card_total.set_value(fmt(analytics["monthly_total"]))
        self.card_small.set_value(fmt(analytics["small_total"]))
        self.card_big.set_value(fmt(analytics["big_total"]))

        remaining = analytics["remaining_budget"]
        budget_color = "#2ecc71" if remaining >= 0 else "#e74c3c"
        self.card_budget.set_value(fmt(remaining), budget_color)

        self.card_income.set_value(fmt(analytics["income"]))
        self.card_savings.set_value(fmt(analytics["savings_balance"]))
        net_color = "#2ecc71" if analytics["net_balance"] >= 0 else "#e74c3c"
        self.card_net.set_value(fmt(analytics["net_balance"]), net_color)
        self.card_count.set_value(str(analytics["expense_count"]))

        # Budget alert
        if analytics["budget_exceeded"] and analytics["budget"] > 0:
            self.alert_label.configure(
                text=f"⚠️ Budget Exceeded! You are over by {fmt(analytics['over_amount'])} this month.",
            )
            self.alert_frame.pack(fill="x", padx=8, pady=(0, 12), before=self.cards_frame)
        else:
            self.alert_frame.pack_forget()

        # Summary text
        self.summary_text.configure(text=(
            f"Week ({weekly['start_date']} to {weekly['end_date']}): "
            f"{fmt(weekly['total'])} across {weekly['count']} transactions\n"
            f"Month ({monthly['start_date']} to {monthly['end_date']}): "
            f"{fmt(monthly['total'])} | Budget: {fmt(analytics['budget'])} | "
            f"Small: {fmt(monthly['small'])} | Big: {fmt(monthly['big'])}"
        ))

        # Refresh charts
        appearance = self.app.theme
        for w in self.pie_chart_host.winfo_children():
            w.destroy()
        for w in self.bar_chart_host.winfo_children():
            w.destroy()

        self._pie_chart = create_pie_chart(
            self.pie_chart_host, analytics["by_category"],
            title="Category Distribution", appearance=appearance,
        )
        self._bar_chart = create_type_bar_chart(
            self.bar_chart_host, analytics["small_total"], analytics["big_total"],
            appearance=appearance,
        )
