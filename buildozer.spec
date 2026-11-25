[app]
title = الكودرهن
package.name = kodrhan
package.domain = org.abera
source.dir = .
source.include_exts = py,png,jpg,kv,json,txt
version = 1.0
requirements = python3,kivy,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 35
android.minapi = 23
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = 1
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
