#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE ---------------------------------------------
#
# python-3    http://www.python.org
#
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__     = 'Plugin voor QGis om metadata aan te maken'
__rights__  = 'Jan van Sambeek'
__author__  = 'Jan van Sambeek'
__date__    = ['10-2019']
__version__ = '1.0.0'

# ----- IMPORT LIBRARIES -----------------------------------------------

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *

from .ME_19115_200 import ME_19115_200
from .ME_19119_200 import ME_19119_200
from .ME_19110_2016 import ME_19110_2016

import os, sys

# ----- editor ---------------------------------------------------------

class editor:
  def __init__(self, iface):
    # save reference to the QGIS interface
    self.iface = iface
    # bepaal start directorie en bestand
    self.start_dir, self.start_file = os.path.split(os.path.abspath(__file__))
    # let op: vanaf QGis 3.8  https://qgis.org/pyqgis/master/core/QgsMapLayerType.html
    qgis_versie = int(Qgis.QGIS_VERSION[:5].replace('.', ''))
    if qgis_versie >= 380: self.laagType = [QgsMapLayerType.VectorLayer, QgsMapLayerType.RasterLayer, QgsMapLayerType.PluginLayer, QgsMapLayerType.MeshLayer]
    else: self.laagType = [0, 1, 2, 3]

  def initGui(self):
    # acties om ISO 19115 2.0.0 op te starten
    icon = QIcon("%s/images/19115.png" %(self.start_dir))
    self.ActionME_19115_200 = QAction(icon, "&ME 19115 2.0.0", self.iface.mainWindow())
    self.ActionME_19115_200.triggered.connect(self.RunME_19115_200)
    self.ActionME_19115_200.setCheckable(False)
    # add toolbar button and menu item
    self.iface.addToolBarIcon(self.ActionME_19115_200)
    self.iface.addPluginToMenu("&Metadata Editor", self.ActionME_19115_200)

    # acties om ISO 19119 2.0.0 op te starten
#    icon = QIcon("%s/images/19119.png" %(self.start_dir))
#    self.ActionME_19119_200 = QAction(icon, "&ME 19119 2.0.0", self.iface.mainWindow())
#    self.ActionME_19119_200.triggered.connect(self.RunME_19119_200)
#    self.ActionME_19119_200.setCheckable(False)
    # add toolbar button and menu item
#    self.iface.addToolBarIcon(self.ActionME_19119_200)
#    self.iface.addPluginToMenu("&Metadata Editor", self.ActionME_19119_200)    

    # acties om ISO 19110 2016 op te starten
    icon = QIcon("%s/images/19110.png" %(self.start_dir))
    self.ActionME_19110_2016 = QAction(icon, "&ME 19110 2016", self.iface.mainWindow())
    self.ActionME_19110_2016.triggered.connect(self.RunME_19110_2016)
    self.ActionME_19110_2016.setCheckable(False)
    # add toolbar button and menu item
    self.iface.addToolBarIcon(self.ActionME_19110_2016)
    self.iface.addPluginToMenu("&Metadata Editor", self.ActionME_19110_2016)

    # acties om de help op te starten
    icon = QIcon("%s/images/help.png" %(self.start_dir))
    self.AboutAction = QAction(icon, "Metadata Editor help", self.iface.mainWindow())
    self.AboutAction.triggered.connect(self.RunHelp)    
    self.AboutAction.setCheckable(False)
    # add toolbar button and menu item
    self.iface.addToolBarIcon(self.AboutAction)
    self.iface.addPluginToMenu("&Metadata Editor", self.AboutAction)

    # acties om about op te starten
    icon = QIcon("%s/images/about.png" %(self.start_dir))
    self.AboutAction = QAction(icon, "over Metadata Editor", self.iface.mainWindow())
    self.AboutAction.triggered.connect(self.RunAbout)    
    self.AboutAction.setCheckable(False)
    # add toolbar button and menu item
    self.iface.addToolBarIcon(self.AboutAction)
    self.iface.addPluginToMenu("&Metadata Editor", self.AboutAction)

  def unload(self):
    "Remove the plugin menu item and icon from QGIS GUI."
    self.iface.removePluginMenu("Metadata Editor", self.ActionME_19115_200)
    self.iface.removePluginVectorMenu("Metadata Editor", self.ActionME_19110_2016)
    self.iface.removePluginVectorMenu("Metadata Editor", self.AboutAction)
    self.iface.removeToolBarIcon(self.ActionME_19115_200)
    self.iface.removeToolBarIcon(self.ActionME_19110_2016)
    self.iface.removeToolBarIcon(self.AboutAction)

  def RunME_19115_200(self):
    # als er geen actieve laag is geef een popup
    if not self.iface.activeLayer():
      QtWidgets.QMessageBox.warning(None, "Laag Info", "Er is geen laag actief,\nselecteer een laag")      
    elif 'http' in self.iface.activeLayer().dataProvider().dataSourceUri() and '://' in self.iface.activeLayer().dataProvider().dataSourceUri():
      QtWidgets.QMessageBox.warning(None, "Laag Info", "Metadata Editor ISO 19115 versie 2.0.0\nis niet geschikt voor webservices\ngebruik ISO 19119.") 
    else:
      # create and show the dialog
      dlg = ME_19115_200(self)
      # show the dialog
      dlg.show()
      result = dlg.exec_()
      
  def RunME_19119_200(self):
    # als er geen actieve laag is geef een popup
    if not self.iface.activeLayer():
      QtWidgets.QMessageBox.warning(None, "Laag Info", "Er is geen laag actief,\nselecteer een laag")      
    elif 'http' not in self.iface.activeLayer().dataProvider().dataSourceUri() and '://' not in self.iface.activeLayer().dataProvider().dataSourceUri():
      QtWidgets.QMessageBox.warning(None, "Laag Info", "Metadata Editor ISO 19119 versie 2.0.0\nis niet geschikt voor data\ngebruik ISO 19115.") 
    else:
      # create and show the dialog
      dlg = ME_19119_200(self)
      # show the dialog
      dlg.show()
      result = dlg.exec_()      

  def RunME_19110_2016(self):
    # als er geen actieve laag is geef een popup
    if not self.iface.activeLayer():
      QtWidgets.QMessageBox.warning(None, "Laag Info", "Er is geen laag actief,\nselecteer een laag")      
    elif not self.iface.activeLayer().type() == self.laagType[0]:
      QtWidgets.QMessageBox.warning(None, "Laag Info", "De actieve laag is geen vector laag")
    elif 'url=' in self.iface.activeLayer().dataProvider().dataSourceUri():
      QtWidgets.QMessageBox.warning(None, "Laag Info", "Metadata Editor ISO 19110 2016\nis niet geschikt voor webservices\ngebruik ISO 19119.")
    else:
      # create and show the dialog
      dlg = ME_19110_2016(self)
      # show the dialog
      dlg.show()
      result = dlg.exec_()

  def RunHelp(self):
    """ Help menu """
    # open het help bestand
    if sys.platform == 'linux': os.system('firefox https://atlas.brabant.nl/metadata/Metadata_Editor/index.html')
    elif sys.platform == 'win32': os.startfile('"https://atlas.brabant.nl/metadata/Metadata_Editor/index.html"')
    return
    
  def RunAbout(self):
    infoString = """<table width="510">
    <tr><td colspan=\"2\"><b><font size="6">Metadata_Editor %s</font></b></td></tr>
    <tr><td></td></tr>
    <tr><td align="center"><IMG SRC="%s/images/PNB_logo.jpg" ALT="onbekend" WIDTH=16 HEIGHT=16></td></tr>
    <tr><td>Metadata_Editor is een programma voor het</td></tr>
    <tr><td>aanmaken van GEO metadata, die voldoet aan</td></tr>
    <tr><td>de door Geonovum vastgestelde normen</td></tr>
    <tr><td></td></tr>
    <tr><td>Het programma is te gebruiken in combinatie met <a href="https://github.com/provincies" target="_blank">Metadata_Master</a> voor het beheer van de metadata</td></tr>
    <tr><td></td></tr>
    <tr><td><font size="2">&copy; 2018    Jan van Sambeek</font></td></tr></table>""" %(__version__, self.start_dir)
    QMessageBox.information(self.iface.mainWindow(), "over Metadata Editor", infoString)

# ----------------------------------------------------------------------
