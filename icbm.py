#!/usr/bin/env python
import os
import string
import plistlib
import urllib
import urlparse
import time

BASE_PATH=''
HTML_TEMPLATE='install.html'
from bottle import route, run, request, response, static_file, HTTPError, template

def make_manifest(meta, assets):
    root = {}
    items = []
    items0 = {}
    items0['assets'] = assets
    items0['metadata'] = meta

    items.append(items0)
    root['items'] = items

    if 'writePlistToBytes' in plistlib.__all__:
        return plistlib.writePlistToBytes(root)
    else:
        return plistlib.writePlistToString(root)

def make_assets(ipa_url, icon_url, icon_512_url, icon_needs_shine=True):
    def _asset(kind, url, other=None):
        d = {'kind':kind, 'url':url}
        if other:
            d.update(other)
        return d
    assets = []

    assets.append(_asset('software-package', ipa_url))
    assets.append(_asset('full-size-image', icon_512_url, {'needs-shine':icon_needs_shine}))
    assets.append(_asset('display-image', icon_url, {'needs-shine':icon_needs_shine}))

    return assets

def make_meta(bundle_identifier, bundle_version, title):
    meta = {'bundle-identifier':bundle_identifier,
            'bundle-version':bundle_version,
            'kind':'software',
            'title':title}

    return meta

def _easy_match(haystack, needle):
    haystack = haystack.lower()
    haystack = haystack.translate(string.maketrans('',''), string.punctuation)

    return needle.lower() in haystack

def _base_url():
    p = urlparse.urlsplit(request.url)
    return p.scheme+'://'+p.netloc+'/'+BASE_PATH

def install_page(name, base_url = None, browser_check=True):
    if not base_url:
        base_url = _base_url()+name
    manifest_url = base_url+'/manifest.xml'
    install_url = 'itms-services://?action=download-manifest&url='+manifest_url

    browser_warning = False
    if browser_check:
        ua = request.headers.get('User-Agent')
        print 'user agent is', ua
        acceptable_uas = ['iPod', 'iPhone', 'iPad']
        browser_warning = not len(filter(lambda x: x in ua, acceptable_uas))

    return template(HTML_TEMPLATE, install_url=install_url, name=name,timestamp=time.ctime(), browser_warning = browser_warning)

def install_manifest(name, static=False, base_url=None, ipa_file=None, plist_file=None, icon_file=None, icon512_file=None, icon_gloss=True):
    class Ctx(object):
        pass

    ctx = Ctx()

    if static:
        ctx.base_url = base_url
        def _make_url(filepath):
            from os.path import basename
            url = ctx.base_url+'/'+urllib.quote(basename(filepath))
            return url

        ctx.ipa_url = _make_url(ipa_file)
        ctx.icon_512_url = _make_url(icon512_file)
        ctx.icon_url= _make_url(icon_file)
        ctx.info_plist = plist_file
        ctx.icon_gloss = icon_gloss

    else:
        ctx.base_url =_base_url()+name
        ctx.ipa_url = None
        ctx.icon_512_url = None
        ctx.icon_url= None
        ctx.info_plist = None
        ctx.icon_gloss = True

        def _skywalker(arg, dirname, fnames):
            for fname in fnames:
                ext = os.path.splitext(fname)[-1]
                url = ctx.base_url+'/'+urllib.quote(fname)
                # first .ipa we find, that's our application file
                if ext == '.ipa':
                    ctx.ipa_url = url
                elif ext == '.png':
                    if _easy_match(fname, '512'):
                        ctx.icon_512_url = url
                    else:
                        ctx.icon_url = url

                    if _easy_match(fname, 'no_gloss'):
                        ctx.icon_gloss = False
                elif ext == '.plist':
                    if _easy_match(fname, 'info'):
                        ctx.info_plist = os.path.join(dirname, fname)

            # ensure we only do a top level walk
            fnames[:]=[]

        os.path.walk(name, _skywalker, None)

        # $todo move this into install_page otherwise the 404 is invisible to
        # the user
        if not ctx.info_plist:
            return HTTPError(code=404, output='info plist not found')

        if not ctx.ipa_url:
            return HTTPError(code=404, output='ipa not found')

        if not ctx.icon_url:
            return HTTPError(code=404, output='icon not found')

        if not ctx.icon_512_url:
            return HTTPError(code=404, output='512 icon not found')

        response.content_type = "application/xml"

    plist = plistlib.readPlist(ctx.info_plist)

    meta = make_meta(plist['CFBundleIdentifier'], plist['CFBundleVersion'], name)
    assets = make_assets(ctx.ipa_url, ctx.icon_url, ctx.icon_512_url, ctx.icon_gloss)
    manifest = make_manifest(meta, assets)

    return manifest

@route(BASE_PATH+'/:name/:action')
@route(BASE_PATH+'/:name/')
@route(BASE_PATH+'/:name')
def index(name=None, action=None, path=None):
    if not name:
        return HTTPError(code=404)

    name = urllib.unquote(name)

    if not os.path.exists(name):
        return HTTPError(code=404)

    if not os.path.islink(name) and not os.path.isdir(name):
        return HTTPError(code=404, output='not a directory')

    if action == 'manifest.xml':
        return install_manifest(name)
    elif not action:
        return install_page(name)
    elif action:
        print 'action:', action
        return static_file(action, root=name+'/')
    else:
        return HTTPError(code=404)

from optmatch import OptionMatcher, optmatcher, optset
class ICBM(OptionMatcher):
    @optmatcher
    def run_static(self, staticFlag, baseURL, name, ipaFile, plistFile, iconFile, icon512File):
        index=open('index.html','w')
        with index:
            index.writelines(install_page(name, base_url = baseURL, browser_check=False))
        print 'wrote index.html'

        manifest=open('manifest.xml', 'w')
        with manifest:
            icon_gloss = not _easy_match(iconFile, 'no_gloss')
            manifest.writelines(install_manifest(   name,
                                                    static=True,
                                                    base_url=baseURL,
                                                    ipa_file = ipaFile,
                                                    plist_file = plistFile,
                                                    icon_file = iconFile,
                                                    icon512_file = icon512File,
                                                    icon_gloss = icon_gloss))
        print 'wrote manifest.xml'


    @optmatcher
    def run_bottle(self, host='localhost', port=8080):
        import bottle
        bottle.debug(True)
        run(host=host, port=port, reloader=True)

if __name__ == '__main__':
    import sys
    sys.exit(ICBM().process(sys.argv))
