"""
reports.py - Export expense reports to CSV and PDF formats.
"""

import csv
import os
from datetime import datetime
from tkinter import filedialog, messagebox

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from expense_manager import (
    search_expenses,
    get_monthly_summary,
    get_weekly_summary,
    get_total_income,
    get_budget,
)


def export_to_csv(user_id, expenses=None, filepath=None, currency="₹"):
    """
    Export expenses list to CSV file.
    Returns (success, message or filepath).
    """
    if expenses is None:
        expenses = search_expenses(user_id)

    if not expenses:
        return False, "No expenses to export."

    if not filepath:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
        )
    if not filepath:
        return False, "Export cancelled."

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Date", "Title", "Category", "Type", f"Amount ({currency})",
                "Notes", "Created At",
            ])
            for e in expenses:
                writer.writerow([
                    e["id"], e["date"], e["title"], e["category"],
                    e["expense_type"], e["amount"], e.get("notes", ""),
                    e.get("created_at", ""),
                ])
            total = sum(e["amount"] for e in expenses)
            writer.writerow([])
            writer.writerow(["", "", "", "", "TOTAL", total, "", ""])
        return True, filepath
    except OSError as e:
        return False, f"Failed to write CSV: {e}"


def export_summary_pdf(user_id, month=None, year=None, filepath=None, currency="₹"):
    """
    Export monthly summary report as PDF.
    """
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    summary = get_monthly_summary(user_id, month, year)
    expenses = search_expenses(
        user_id,
        date_from=summary["start_date"],
        date_to=summary["end_date"],
    )
    budget = get_budget(user_id, month, year)
    income = get_total_income(user_id, summary["start_date"], summary["end_date"])

    if not filepath:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"expense_report_{year}_{month:02d}.pdf",
        )
    if not filepath:
        return False, "Export cancelled."

    try:
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"], fontSize=18, spaceAfter=20,
        )
        elements = []

        month_name = datetime(year, month, 1).strftime("%B %Y")
        elements.append(Paragraph(f"Expense Report — {month_name}", title_style))
        elements.append(Spacer(1, 12))

        # Summary table
        summary_data = [
            ["Metric", f"Amount ({currency})"],
            ["Total Expenses", f"{summary['total']:,.2f}"],
            ["Small Expenses", f"{summary['small']:,.2f}"],
            ["Big Expenses", f"{summary['big']:,.2f}"],
            ["Total Income", f"{income:,.2f}"],
            ["Monthly Budget", f"{budget:,.2f}"],
            ["Remaining Budget", f"{budget - summary['total']:,.2f}"],
            ["Net Balance", f"{income - summary['total']:,.2f}"],
        ]
        t = Table(summary_data, colWidths=[3 * inch, 2.5 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 24))

        # Category breakdown
        if summary["by_category"]:
            elements.append(Paragraph("Category Breakdown", styles["Heading2"]))
            elements.append(Spacer(1, 8))
            cat_data = [["Category", f"Amount ({currency})"]]
            for cat, amt in sorted(summary["by_category"].items(), key=lambda x: -x[1]):
                cat_data.append([cat, f"{amt:,.2f}"])
            ct = Table(cat_data, colWidths=[3 * inch, 2.5 * inch])
            ct.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2ecc71")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]))
            elements.append(ct)
            elements.append(Spacer(1, 24))

        # Expense details
        if expenses:
            elements.append(Paragraph("Expense Details", styles["Heading2"]))
            elements.append(Spacer(1, 8))
            detail_data = [["Date", "Title", "Category", "Type", "Amount"]]
            for e in expenses[:50]:  # Limit rows for PDF size
                detail_data.append([
                    e["date"], e["title"][:25], e["category"],
                    e["expense_type"], f"{e['amount']:,.2f}",
                ])
            if len(expenses) > 50:
                detail_data.append(["...", f"({len(expenses) - 50} more rows)", "", "", ""])

            dt = Table(detail_data, colWidths=[1 * inch, 2 * inch, 1.2 * inch, 0.8 * inch, 1 * inch])
            dt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#9b59b6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
            ]))
            elements.append(dt)

        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"],
        ))

        doc.build(elements)
        return True, filepath
    except Exception as e:
        return False, f"Failed to create PDF: {e}"


def show_export_dialog(parent, user_id, currency="₹"):
    """Simple dialog to choose CSV or PDF export."""
    from customtkinter import CTkToplevel, CTkLabel, CTkButton

    dialog = CTkToplevel(parent)
    dialog.title("Export Report")
    dialog.geometry("360x260")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.update_idletasks()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    px, py = parent.winfo_rootx(), parent.winfo_rooty()
    w, h = 360, 260
    dialog.geometry(f"{w}x{h}+{px + max((pw - w) // 2, 0)}+{py + max((ph - h) // 2, 0)}")

    CTkLabel(dialog, text="Choose export format", font=("Segoe UI", 16, "bold")).pack(pady=20)

    def do_csv():
        ok, msg = export_to_csv(user_id, currency=currency)
        if ok:
            messagebox.showinfo("Export", f"CSV saved to:\n{msg}")
        else:
            messagebox.showwarning("Export", msg)
        dialog.destroy()

    def do_pdf():
        ok, msg = export_summary_pdf(user_id, currency=currency)
        if ok:
            messagebox.showinfo("Export", f"PDF saved to:\n{msg}")
        else:
            messagebox.showwarning("Export", msg)
        dialog.destroy()

    CTkButton(dialog, text="📄 Export as CSV", command=do_csv, width=240, height=40).pack(pady=8)
    CTkButton(dialog, text="📑 Export as PDF", command=do_pdf, width=240, height=40).pack(pady=8)
    CTkButton(dialog, text="Cancel", command=dialog.destroy, width=240, fg_color="gray").pack(pady=8)
