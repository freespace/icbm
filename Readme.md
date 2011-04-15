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
