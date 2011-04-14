#!/usr/bin/env python
import os
import string
import plistlib
import urllib
import urlparse

BASE_PATH=''

from bottle import route, run, request, response, static_file, HTTPError

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
	if (icon_512_url):
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

def install_page(name):
	install_url = 'itms-services://?'
	manifest_url = _base_url()+name+'/manifest'
	manifest_url = manifest_url.replace('//','/')
	namevals = 'action=download-manifest&url='+manifest_url

	install_url += namevals

	return '<a href="%s"><h1>install</h1></a>'%(install_url)

def install_manifest(name):
	name = urllib.unquote(name)

	if not os.path.exists(name):
		return HTTPError(code=404)

	if not os.path.islink(name) and not os.path.isdir(name):
		return HTTPError(code=404, output='not a directory')

	class Ctx(object):
		pass

	ctx = Ctx()

	ctx.base_url = _base_url()+name
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

				if _easy_match(fname, "no_gloss"):
					ctx.icon_gloss = False
			elif ext == '.plist':
				if _easy_match(fname, 'info'):
					ctx.info_plist = os.path.join(dirname, fname)

	os.path.walk(name, _skywalker, None)

	plist = plistlib.readPlist(ctx.info_plist)

	meta = make_meta(plist['CFBundleIdentifier'], plist['CFBundleVersion'], name)
	assets = make_assets(ctx.ipa_url, ctx.icon_url, ctx.icon_512_url, ctx.icon_gloss)
	manifest = make_manifest(meta, assets)

	response.content_type = "application/xml"
	return manifest

@route(BASE_PATH+'/:name/:action')
@route(BASE_PATH+'/:name')
@route(BASE_PATH+'/:name/')
def index(name=None, action=None):
	print name, action
	if not name:
		return HTTPError(code=404)

	if action == 'manifest':
		return install_manifest(name)
	elif action == 'install' or not action:
		return install_page(name)
	elif action:
		print action
		return static_file(action, root=name+'/')
	else:
		return HTTPError(code=404)


import bottle
bottle.debug(True)

run(host='10.54.85.13', port=8080, reloader=True)