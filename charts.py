"""
charts.py - Matplotlib visualizations embedded in CustomTkinter frames.
"""

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


# Color palette for charts (works in dark and light themes)
COLORS = [
    "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#16a085", "#c0392b",
]


def _style_figure(fig, appearance="dark"):
    """Apply theme-appropriate styling to matplotlib figure."""
    bg = "#2b2b2b" if appearance == "dark" else "#f0f0f0"
    text_color = "#ffffff" if appearance == "dark" else "#333333"
    fig.patch.set_facecolor(bg)
    for ax in fig.axes:
        ax.set_facecolor(bg)
        ax.tick_params(colors=text_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
        ax.legend(facecolor=bg, edgecolor=text_color, labelcolor=text_color)
    return text_color


class ChartFrame(ctk.CTkFrame):
    """Reusable frame that hosts a matplotlib chart."""

    def __init__(self, master, width=5, height=4, dpi=100, **kwargs):
        super().__init__(master, **kwargs)
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

    def clear(self):
        self.fig.clear()

    def draw(self):
        self.canvas.draw()


def create_pie_chart(parent, data: dict, title="Spending by Category", appearance="dark"):
    """
    Create pie chart from {category: amount} dict.
    Returns ChartFrame instance.
    """
    frame = ChartFrame(parent, width=5, height=4)
    frame.clear()

    if not data or sum(data.values()) == 0:
        ax = frame.fig.add_subplot(111)
        _style_figure(frame.fig, appearance)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        frame.draw()
        return frame

    labels = list(data.keys())
    sizes = list(data.values())
    colors = COLORS[: len(labels)]

    ax = frame.fig.add_subplot(111)
    _style_figure(frame.fig, appearance)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.1f%%",
        colors=colors, startangle=90, textprops={"fontsize": 8},
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(7)
    ax.set_title(title, fontsize=11, pad=10)
    frame.fig.tight_layout()
    frame.draw()
    return frame


def create_bar_chart(parent, data: dict, title="Spending Comparison", appearance="dark",
                     xlabel="Category", ylabel="Amount"):
    """Create vertical bar chart."""
    frame = ChartFrame(parent, width=6, height=4)
    frame.clear()

    if not data:
        ax = frame.fig.add_subplot(111)
        _style_figure(frame.fig, appearance)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        frame.draw()
        return frame

    labels = list(data.keys())
    values = list(data.values())
    colors = COLORS[: len(labels)]

    ax = frame.fig.add_subplot(111)
    _style_figure(frame.fig, appearance)
    bars = ax.bar(labels, values, color=colors, edgecolor="none", linewidth=0.8)
    ax.set_title(title, fontsize=11, pad=10)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=35, ha="right", fontsize=8)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height(),
            f"{val:,.0f}", ha="center", va="bottom", fontsize=7,
        )
    frame.fig.tight_layout()
    frame.draw()
    return frame


def create_type_bar_chart(parent, small: float, big: float, title="Small vs Big Expenses",
                          appearance="dark"):
    """Bar chart comparing Small and Big expense totals."""
    return create_bar_chart(
        parent,
        {"Small": small, "Big": big},
        title=title,
        appearance=appearance,
        xlabel="Type",
        ylabel="Amount",
    )


def create_trend_chart(parent, dates: list, amounts: list, title="Daily Spending Trend",
                       appearance="dark"):
    """Line chart for spending over time."""
    frame = ChartFrame(parent, width=6, height=3.5)
    frame.clear()

    if not dates or not amounts:
        ax = frame.fig.add_subplot(111)
        _style_figure(frame.fig, appearance)
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        frame.draw()
        return frame

    ax = frame.fig.add_subplot(111)
    _style_figure(frame.fig, appearance)
    x = list(range(len(amounts)))
    ax.plot(x, amounts, color="#3498db", marker="o", markersize=4, linewidth=2)
    ax.fill_between(x, amounts, alpha=0.2, color="#3498db")
    ax.set_xticks(x)
    ax.set_xticklabels(dates)
    ax.set_title(title, fontsize=11, pad=10)
    ax.set_xlabel("Date", fontsize=9)
    ax.set_ylabel("Amount", fontsize=9)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=7)
    frame.fig.tight_layout()
    frame.draw()
    return frame
