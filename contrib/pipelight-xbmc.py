#!/usr/bin/python

# Written by slackner
#
# Test for example with:
# python pipelight-xbmc.py "http://www.lovefilm.de/film/?token=%3Fu%3D%252Fcatalog%252Ftitle%252F326573%26m%3DGET"


import sys
import os
import tempfile
import shutil
from PyQt4 import QtCore, QtGui, QtWebKit

MOZILLA_PLUGINDIR = "/usr/lib/mozilla/plugins"
PIPELIGHT_LIBDIR  = "/usr/lib/pipelight"
PIPELIGHT_LIBRARY = "libpipelight.so"

class MainWindow(QtGui.QMainWindow):
	def __init__(self, page):
		QtGui.QMainWindow.__init__(self)
		self.setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(0, 0, 0).name())

		self.container = X11Container()
		self.setCentralWidget(self.container)

		os.putenv("PIPELIGHT_X11WINDOW", str(self.container.winId()))

		self.is_embedded 	= False
		self.browser 		= None
		self.browser_page   = page

		self.loadBrowser()
		#timer = QtCore.QTimer()
		#timer.singleShot(100, self.loadBrowser)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Escape:
			self.close()

	def loadBrowser(self):
		self.browser 		= Browser(self.browser_page)

		timer = QtCore.QTimer()
		timer.singleShot(10000, self.checkIfEmbedded)

	def checkIfEmbedded(self):
		if not self.is_embedded:
			print "Timeout reached and no Silverlight application embedded yet!"
			self.close()

	def close(self):
		os.unsetenv("PIPELIGHT_X11WINDOW")

		# Set to empty string to let Silverlight unload the page properly
		if self.browser is not None:
			self.browser.setHtml(QtCore.QString(""))
			self.browser = None

			timer = QtCore.QTimer()
			timer.singleShot(100, self.close)
			return

		QtGui.QMainWindow.close(self)

class X11Container(QtGui.QX11EmbedContainer):
	def __init__(self):
		QtGui.QX11EmbedContainer.__init__(self)
		QtCore.QObject.connect(self, QtCore.SIGNAL('clientIsEmbedded()'), self.clientIsEmbedded)
		QtCore.QObject.connect(self, QtCore.SIGNAL('clientClose()'), self.clientClose)

	def keyPressEvent(self, event):
		self.window().keyPressEvent(event)

	def clientIsEmbedded(self):
		print "*CLIENT EMBEDDED*"
		self.window().is_embedded = True

	def clientClose(self):
		print "*CLIENT CLOSED*"
		self.window().close()

class WebPage(QtWebKit.QWebPage):
	def userAgentForUrl(self, url):
		return "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20120427 Firefox/15.0a1"

class Browser(QtWebKit.QWebView):
	def __init__(self, page):
		QtWebKit.QWebView.__init__(self)
		self.resize(800,600)

		self.setPage(WebPage())
		self.settings().setAttribute(QtWebKit.QWebSettings.PluginsEnabled, True)
		self.settings().setAttribute(QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)
		QtCore.QObject.connect(self, QtCore.SIGNAL('loadFinished(bool)'), self.loadFinished)
		self.load(QtCore.QUrl(page))

	def loadFinished(self, ok):
		pass

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print "Usage: ./pipelight-xbmc.py WEBPAGE"
		exit(1)

	page = sys.argv[1]

	if not os.path.exists("%s/%s" % (PIPELIGHT_LIBDIR, PIPELIGHT_LIBRARY)):
		print "It looks like pipelight is not installed! Unable to find '%s'." % PIPELIGHT_LIBRARY
		exit(1)

	enabled_systemwide = os.path.exists("%s/%s" % (MOZILLA_PLUGINDIR, PIPELIGHT_LIBRARY))
	plugin_tempdir = None

	try:

		# Pipelight not enabled systemwide, create a temporary plugin dir
		if not enabled_systemwide:
			plugin_tempdir = tempfile.mkdtemp()
			os.symlink("%s/%s" % (PIPELIGHT_LIBDIR, PIPELIGHT_LIBRARY), "%s/%s" % (plugin_tempdir, PIPELIGHT_LIBRARY))
			os.putenv("MOZ_PLUGIN_PATH", plugin_tempdir)

		# Show the Silverlight plugin in a QtGui window
		app = QtGui.QApplication([]) #(sys.argv) ?
		app.setAttribute(QtCore.Qt.AA_NativeWindows, True)
		mainWindow = MainWindow(page)
		mainWindow.showFullScreen()
		app.exec_()

	finally:

		# Delete the temporary plugin dir
		if plugin_tempdir is not None:
			try:
				shutil.rmtree(plugin_tempdir)
			except OSError as e:
				if e.errno != 2:
					raise
