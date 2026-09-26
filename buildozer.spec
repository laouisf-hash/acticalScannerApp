[app]
source.dir = .
version = 0.1
# (str) Title of your application
title = TacticalScannerApp

# (str) Package name
package.name = tacticalscannerapp

# (str) Package domain (needed for android packaging)
package.domain = org.tactical

# (list) Source files to include (let it include all)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# Zid el requirements mta3 l'application mta3ek houni (kima kivy, opencv, numpy, plyer...)
requirements = python3,kivy,opencv,numpy,plyer

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = CAMERA,INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
