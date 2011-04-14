#!/usr/bin/env python
import os, sys

d=os.path.dirname(__file__)
if d:
	os.chdir(d)
	sys.path.append(d)

import bottle
import icbm

application = bottle.default_app()
