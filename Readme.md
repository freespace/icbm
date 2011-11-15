Why
===

Why ICBM? Because I am silly, and I don't like creating the manifest plist and
webpage required for OTA distribution.

How
===

Suppose you have an app called AwesomeApp, you create the following directory
structure:

    AwesomeApp/
      awesomeapp.ipa 
      icon.png 
      icon_512.png 
      AwesomeApp-Info.plist 

Place it in the same directory as icbm.py and now the ICBM will generate 2
views:

    http://yoursite.com/webapp/root/AwesomeApp
    http://yoursite.com/webapp/root/AwesomeApp/manifest

The first generates a HTML page containing a link to install AwesomeApp, while
the second generates a manifest plist that iOS will use to download the
application.

File Identification
===================

The last ipa file encountered is assumed to be the application ipa. Simiarly
the last png file found is assumed to be the application icon, and the last
png file with '512' in the filename is assumed to be the full sized icon.
Finally, the last plist file containing 'info' is assumed to be the
application's info.plist, from which bundle ID and version is extracted.

Note that since `plistlib` can't read binary plists, the info plist should be
text version, normally called YourApp-Info.plist.

Sample info.plist

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.pictorii.${PRODUCT_NAME:rfc1034identifier}</string>
    <key>CFBundleVersion</key>
    <string>1.91</string>
</dict>
</plist>
```
Icons have the gloss applied by default. To stop this put 'no_gloss' in the
filename.

Sample WSGI Configuration
=========================
```
<VirtualHost *:80>
  ServerName icbm.blah.com
  WSGIDaemonProcess icbm user=www-data group=www-data processes=1 threads=5
  WSGIScriptAlias / /path/to/icbm/app.wsgi
  <Directory /path/to/icbm/>
      WSGIProcessGroup icbm
      WSGIApplicationGroup %{GLOBAL}
      Order deny,allow
      Allow from all
  </Directory>
</VirtualHost>
```
