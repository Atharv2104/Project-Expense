# Build Android APK (Mobile App)

The **desktop app** (`python main.py`) uses CustomTkinter and **cannot** run on phones.

The **mobile app** (`mobile/main.py`) uses **KivyMD** and builds a real **Android APK**.

Both apps share the same backend: `database.py`, `expense_manager.py`, `auth_core.py`.

---

## Quick test on PC (before building APK)

```powershell
cd d:\atharv\project\expense
pip install -r requirements-mobile.txt
python database.py
python mobile/main.py
```

Login: `demo` / `demo123`

---

## Build APK (Android)

APK builds require **Linux** (or **WSL2** on Windows). Buildozer does not run natively on Windows.

### Option A: WSL2 (Windows — recommended)

1. Install [WSL2 Ubuntu](https://learn.microsoft.com/en-us/windows/wsl/install)
2. Open Ubuntu terminal:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
  pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake \
  libffi-dev libssl-dev

pip install buildozer cython
pip install -r requirements-mobile.txt

cd /mnt/d/atharv/project/expense
buildozer android debug
```

3. APK output:
   ```
   bin/expensetracker-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
   ```

4. Copy APK to your phone and install (enable **Install from unknown sources**).

### Option B: Google Colab / Linux VM

Upload the project folder, install buildozer, run `buildozer android debug`, download the APK from `bin/`.

### Release APK (signed)

```bash
buildozer android release
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore my.keystore bin/*.apk alias_name
```

---

## Install on phone

1. Transfer `bin/*-debug.apk` to the phone (USB, Google Drive, etc.)
2. Open the APK file → Allow install
3. Open **Expense Tracker**
4. Use demo account or register

---

## Mobile features

| Feature | Mobile app |
|---------|------------|
| Login / Register | ✅ |
| Dashboard & budget alert | ✅ |
| Add / edit / delete expenses | ✅ |
| Category & Small/Big type | ✅ |
| Income & savings | ✅ |
| Goals progress | ✅ |
| Budget setting | ✅ |
| Dark / light mode | ✅ |
| Export CSV | ✅ |
| Charts (full matplotlib) | Desktop only |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `buildozer: command not found` | `pip install buildozer` |
| Build fails on Windows | Use WSL2 Ubuntu |
| App crashes on open | Run `python database.py` once; check logcat: `adb logcat` |
| Storage permission | Grant storage permission in Android settings |

---

## Project layout

```
expense/
├── main.py              ← Desktop (Windows/Mac/Linux)
├── mobile/main.py       ← Mobile (Android APK)
├── buildozer.spec       ← APK build config
├── BUILD_APK.md         ← This guide
└── database/            ← SQLite (shared logic)
```
