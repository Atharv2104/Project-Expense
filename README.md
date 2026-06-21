# Daily Life Expense Tracker

A professional Python desktop application to track daily expenses, manage budgets, monitor income and savings, and visualize spending with charts. Built with **CustomTkinter**, **SQLite**, and **Matplotlib**.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

### Core
- Add, edit, and delete daily expenses
- Categories: Food, Travel, Bills, Shopping, Medical, Education, Entertainment, Other
- Expense types: **Small** (tea, snacks, travel, recharge) and **Big** (rent, shopping, bills, medical, education)
- Search by date, category, type, or keyword
- Weekly and monthly summaries
- Total spending calculator

### Financial Management
- Monthly budget setting with **overspend alerts**
- Income tracker
- Savings tracker (deposits & withdrawals)
- Financial goal setting with progress bars

### Analytics & Reports
- Dashboard with key metrics
- Pie charts and bar graphs (Matplotlib)
- Spending trend line chart
- Export to **CSV** and **PDF**

### Security & UX
- Login / Register with password hashing (PBKDF2)
- Dark / Light mode toggle
- Sidebar navigation with modern UI
- Password change in settings

## Mobile APK (Android)

```powershell
pip install -r requirements-mobile.txt
python mobile/main.py
```

To build installable APK: read **[BUILD_APK.md](BUILD_APK.md)** (requires WSL2/Linux + `buildozer android debug`).

---

## Project Structure

```
expense/
├── main.py              # Desktop app entry point
├── mobile/main.py       # Android/mobile app entry point
├── buildozer.spec       # APK build configuration
├── BUILD_APK.md         # Step-by-step APK build guide
├── database.py          # SQLite schema & connection
├── auth_core.py         # Auth logic (shared desktop + mobile)
├── auth.py              # Desktop login window
├── dashboard.py         # Dashboard UI & stat cards
├── expense_manager.py   # CRUD & business logic
├── reports.py           # CSV/PDF export
├── charts.py            # Matplotlib chart helpers
├── settings.py          # Theme, budget, password settings
├── requirements.txt     # Python dependencies
├── assets/              # Icons & static assets
├── database/            # SQLite database files
└── README.md
```

## Desktop vs Mobile

| Platform | How to run | Technology |
|----------|------------|------------|
| **Windows / Mac / Linux** | `python main.py` | CustomTkinter |
| **Android phone (APK)** | See **[BUILD_APK.md](BUILD_APK.md)** | KivyMD + Buildozer |

> CustomTkinter cannot build APK files. The `mobile/` folder is a separate phone UI that reuses the same SQLite database and business logic.

---

## Installation (Desktop)

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone or download** the project folder.

2. **Open a terminal** in the project directory:
   ```bash
   cd expense
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database** (creates tables + sample data):
   ```bash
   python database.py
   ```

6. **Run the application**:
   ```bash
   python main.py
   ```

## Demo Account

After running `python database.py`, a sample account is created:

| Field    | Value    |
|----------|----------|
| Username | `demo`   |
| Password | `demo123`|

The demo account includes sample expenses, income, savings, and a financial goal.

## Usage Guide

### First Time Setup
1. Launch the app with `python main.py`
2. Click the **Register** tab to create your account
3. Log in with your credentials

### Adding Expenses
1. Go to **Expenses** in the sidebar
2. Click **+ Add Expense**
3. Fill in date, title, category, type (Small/Big), amount, and notes
4. Click **Add** (or **Save** when editing)

### Setting a Budget
1. Go to **Settings**
2. Enter your monthly budget amount
3. Click **Set Budget**
4. You'll receive an alert on startup if spending exceeds the budget

### Exporting Reports
1. Go to **Reports**
2. Click **Export CSV** or **Export PDF Report**
3. Choose a save location

### Theme
- Go to **Settings** → select **Dark Mode** or **Light Mode**

## Module Overview

| Module | Purpose |
|--------|---------|
| `database.py` | Creates SQLite tables, manages connections |
| `auth.py` | User registration, login, password security |
| `expense_manager.py` | All data operations (expenses, income, savings, goals) |
| `dashboard.py` | Main dashboard with cards and charts |
| `charts.py` | Pie, bar, and trend chart generation |
| `reports.py` | CSV and PDF report export |
| `settings.py` | User preferences and budget configuration |
| `main.py` | Application shell, pages, and navigation |

## Dependencies

| Package | Purpose |
|---------|---------|
| customtkinter | Modern Tkinter UI |
| matplotlib | Charts and graphs |
| reportlab | PDF report generation |
| Pillow | Image support for UI |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Database errors | Delete `database/expense_tracker.db` and run `python database.py` |
| Charts not showing | Ensure matplotlib is installed: `pip install matplotlib` |
| Login fails | Use demo account or register a new user |

## License

MIT License — free to use for learning and personal projects.

## Author

Built as a beginner-friendly yet feature-rich Python desktop project for personal finance tracking.
