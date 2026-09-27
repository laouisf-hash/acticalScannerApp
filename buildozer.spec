[app]

# (str) Title of your application
title = TacticalScannerApp

# (str) Package name
package.name = tacticalscannerapp

# (str) Package domain (needed for android packaging)
package.domain = org.tactical

# (list) Source files to include (let it include all)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
requirements = python3, kivy, requests, plyer

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = CAMERA, INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (bool) If True, then skip permission checks for android
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
