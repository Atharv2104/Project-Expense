[app]

# Expense Tracker - Android APK (KivyMD)
title = Expense Tracker
package.name = expensetracker
package.domain = org.expensetracker

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
source.include_patterns = database/*,assets/*,mobile/*
source.exclude_dirs = venv,.git,__pycache__,.buildozer,bin,.cursor

version = 1.0.0

# KivyMD mobile entry point
source.main = mobile/main.py

requirements = python3,kivy==2.3.1,kivymd==1.2.0,reportlab,pillow,android

orientation = portrait
fullscreen = 0

# Android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# App icon (optional - add assets/icon.png 512x512)
# icon.filename = %(source.dir)s/assets/icon.png

# Presplash (optional)
# presplash.filename = %(source.dir)s/assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
