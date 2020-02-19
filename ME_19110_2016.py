#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE ---------------------------------------------
#
# python-3         http://www.python.org
#
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__      = 'Plugin voor QGis om metadata aan te maken volgens het ISO profiel 19110 2016'
__rights__   = 'Jan van Sambeek'
__author__   = 'Jan van Sambeek'
__license__  = 'GNU Lesser General Public License, version 3 (LGPL-3.0)'
__date__     = ['03-2019']
__version__  = '0.8'

# ----- IMPORT LIBRARIES -----------------------------------------------

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .ME_19110_2016_ui import Ui_ME_19110_2016
from lxml import etree

import os, uuid

# ----- CONFIG CLASS ---------------------------------------------------

class Config:
  """
  Lees config bestand en haal key's op
  Schrijf dictionarie naar config
  """
  def __init__(self, conf_bestand):
    """
    ini config object
    """
    self.conf_bestand = conf_bestand
    self.conf = None

  def get(self, key, default = None):
    """
    Lees values uit config bestand
    """    
    if not self.conf: self.load()
    if self.conf and (key in self.conf): return self.conf[key]
    return default

  def get_dict(self, default = None):
    """
    Geef de complete dictionarie
    """    
    if not self.conf: self.load()
    if self.conf: return self.conf
    return default

  def set(self, key, value):
    """
    Voeg keys en values toe aan config 
    """    
    if not self.conf: self.load()
    self.conf[key] = value
    self.save()

  def load(self):
    """
    Laad het config bestand
    Als het niet bestaat maak een lege config
    """    
    try: self.conf = eval(open(self.conf_bestand, 'r').read())
    except: self.conf = {}

  def save(self):
    """
    Schijf dictionarie naar config bestand
    """    
    open(self.conf_bestand, 'w').write(repr(self.conf))

# ----- ME_19110_2016 --------------------------------------------------

class ME_19110_2016(QDialog):
  def __init__(self, parent):
    """
    """
    QDialog.__init__(self)
    # haal gegevens op uit de ouder
    self.parent = parent
    self.iface = parent.iface
    # lees de interface in
    self.ui = Ui_ME_19110_2016()
    self.ui.setupUi(self)
    # let op: vanaf QGis 3.8  https://qgis.org/pyqgis/master/core/QgsMapLayerType.html
    qgis_versie = int(Qgis.QGIS_VERSION[:5].replace('.', ''))
    if qgis_versie >= 380: self.laagType = [QgsMapLayerType.VectorLayer, QgsMapLayerType.RasterLayer, QgsMapLayerType.PluginLayer, QgsMapLayerType.MeshLayer]
    else: self.laagType = [0, 1, 2, 3]
    # lees de start directorie en bestanduit
    self.start_dir, self.start_file = os.path.split(os.path.abspath(__file__))
    # maak een object van de configuratie data
    cfg = Config(parent.start_dir+os.sep+self.start_file.split('.')[0]+'.cfg')
    # lees het configuratie bestand uit
    self.config = cfg.get_dict()
    xml_dir = self.config["dirs"]["xml_dir"]
    self.xml_dir = xml_dir.replace('%USERNAME%', os.getenv('USERNAME'))
    # bepaal de xml naam
    self.bepaal_xml_naam()
    # lees de xml bestaat lees hem dan uit
    if os.path.isfile(self.xml_map+os.sep+os.path.splitext(self.xml_naam)[0] + '_19110.xml'): self.leesXML()
    # loop door de verschillende velden maak een lineedit en textedit, vul de lineedit      
    for teller, veldnaam in enumerate(self.iface.activeLayer().fields().names(), start=1):
        # lineedit
        exec('self.ui.lineEdit_%s = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents)' %(teller))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        exec('sizePolicy.setHeightForWidth(self.ui.lineEdit_%s.sizePolicy().hasHeightForWidth())' %(teller))
        exec('self.ui.lineEdit_%s.setSizePolicy(sizePolicy)' %(teller))
        exec('self.ui.lineEdit_%s.setMinimumSize(QtCore.QSize(300, 0))' %(teller))
        exec('self.ui.lineEdit_%s.setSizeIncrement(QtCore.QSize(0, 0))' %(teller))
        exec('self.ui.lineEdit_%s.setObjectName("lineEdit_%s")' %(teller, teller))
        exec('self.ui.formLayout.setWidget(%s, QtWidgets.QFormLayout.LabelRole, self.ui.lineEdit_%s)' %(teller, teller))
        exec("self.ui.lineEdit_%s.setText('%s')" %(teller, veldnaam))
        exec('self.ui.lineEdit_%s.setReadOnly(True)' %(teller))
        # textedit
        exec('self.ui.textEdit_%s = QtWidgets.QTextEdit(self.ui.scrollAreaWidgetContents)' %(teller))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        exec('sizePolicy.setHeightForWidth(self.ui.textEdit_%s.sizePolicy().hasHeightForWidth())' %(teller))
        exec('self.ui.textEdit_%s.setSizePolicy(sizePolicy)' %(teller))
        exec('self.ui.textEdit_%s.setMinimumSize(QtCore.QSize(500, 25))' %(teller))
        exec('self.ui.textEdit_%s.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)' %(teller))
        exec('self.ui.textEdit_%s.setCursorWidth(2)' %(teller))
        exec('self.ui.textEdit_%s.setObjectName("textEdit_%s")' %(teller, teller))
        exec('self.ui.textEdit_%s.setToolTip(self.config["ToolTips"]["te_omschrijving"])' %(teller))
        exec('self.ui.formLayout.setWidget(%s, QtWidgets.QFormLayout.FieldRole, self.ui.textEdit_%s)' %(teller, teller))
        # vul textedit als self.definitionlist bestaat
        exec('if hasattr(self, "definitionList") and self.definitionList[%s]: \n self.ui.textEdit_%s.setText(self.definitionList[%s])' %(teller-1, teller, teller-1))
    # PushButton "pb_Opslaan" voor de opslag van de attribuut gegevens: zet een tooltip en als er op de button geklikt wordt
    self.ui.pb_Opslaan.setToolTip(self.config["ToolTips"]["pb_Opslaan"])
    self.ui.pb_Opslaan.clicked.connect(self.schrijfXML)

  def bepaal_xml_naam(self):
    """
    Bepaal welk pad en welke naam de xml krijgt
    """
    # genereer de opslag directorie en de xml naam    
    # lees de bron gegevens van de actieve laag uit
    bron_gegevens = self.iface.activeLayer().dataProvider().dataSourceUri()
    # als het een vector laag is
    if self.iface.activeLayer().type() == self.laagType[0]:
      # lees uit wat voor opslag type het is
      opslag_type = self.iface.activeLayer().dataProvider().storageType().lower()
      # als het een shape file is
      if 'shapefile' in opslag_type:
        if '|' in bron_gegevens:
          self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
        else: self.xml_map, self.xml_naam = os.path.split(bron_gegevens)
      # als het een dxf is
      elif 'dxf' in opslag_type:
        if '|' in bron_gegevens:
          self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
        else: self.xml_map, self.xml_naam = os.path.split(bron_gegevens)
      # als het een gdb is
      elif 'filegdb' in opslag_type:
        QtWidgets.QMessageBox.warning(None, 'Bestands info', 'Gebruik de geostandaarden, zie:\n"https://www.forumstandaardisatie.nl/standaard/geo-standaarden"')
        self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
        self.xml_naam = os.path.splitext(self.xml_naam)[0]
        laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split('|') if '=' in item}
        self.xml_naam += '+'+laag_geg['layername']        
      # als het een sqlite of geopackage is
      elif 'sqlite' in opslag_type or 'gpkg' in opslag_type:
        if '|' in bron_gegevens and 'layername' in bron_gegevens:
          self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
          self.xml_naam = os.path.splitext(self.xml_naam)[0]
          laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split('|') if '=' in item}
          self.xml_naam += '+'+laag_geg['layername']
        elif 'dbname' in bron_gegevens and 'table' in bron_gegevens:
          laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split(' ') if '=' in item}
          self.xml_map, self.xml_naam = os.path.split(laag_geg['dbname'])
          self.xml_naam = os.path.splitext(self.xml_naam)[0]
          self.xml_naam += '+'+laag_geg['table']
      # als het een database is
      elif ('oracle' in opslag_type or 'postgis' in opslag_type) and 'table' in bron_gegevens:
        self.xml_map = self.xml_dir
        laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split(' ') if '=' in item}
        self.xml_naam = laag_geg['table']
      # onbekende laag, schrijf naar de home directorie
      else: 
        self.xml_map = os.path.expanduser("~")
        self.xml_naam = self.start_file.split('.')[0]
    # als het een raster laag is
    elif self.iface.activeLayer().type() == self.laagType[1]: self.xml_map, self.xml_naam = os.path.split(bron_gegevens)

  def leesXML(self):
    """
    Lees de xml met ISO 19110 data uit en plaats de gegevens in de Metadata Editor
    https://sites.google.com/site/bmaupinwiki/home/programming/python/python-xml-lxml
    """
    # lees de namespaces
    namespaces = self.config["namespaces"]
    gco = namespaces['gco']
    gfc = namespaces['gfc']
    # maak een list om de definitions te vullen
    self.definitionList = [None] * len(self.iface.activeLayer().fields())
    # parse de xml
    xmldoc = etree.parse(self.xml_map+os.sep+os.path.splitext(self.xml_naam)[0] + '_19110.xml')
    # lees de memberName
    memberNames = xmldoc.findall('//{%s}featureType/{%s}FC_FeatureType/{%s}carrierOfCharacteristics/{%s}FC_FeatureAttribute/{%s}memberName/{%s}LocalName' %(gfc, gfc, gfc, gfc, gfc, gco))
    for teller, memberName in list(enumerate(memberNames, start=1)):
      # lees de definition
      definition = xmldoc.findtext('//{%s}featureType/{%s}FC_FeatureType/{%s}carrierOfCharacteristics[%s]/{%s}FC_FeatureAttribute/{%s}definition/{%s}CharacterString' %(gfc, gfc, gfc, teller, gfc, gfc, gco))
      # zoek de index in de veldnamen en plaats de definitie op de goede plaats
      if memberName.text in self.iface.activeLayer().fields().names():
        self.definitionList[self.iface.activeLayer().fields().names().index(memberName.text)] = definition

  def schrijfXML(self):
    """
    Sla de ingevulde dat op in een metadata xml
    """
    # als het object self.xml_map niet bestaat gebruik dan de home directorie en de metadata uuid
    if not hasattr(self,'xml_naam'): 
      self.xml_map = os.path.expanduser('~')
      self.xml_naam = str(uuid.uuid4())
    # feature catalogue name
    attributeNaam = os.path.splitext(self.xml_naam)[0]
    # plak "_19110.xml" achter de attributeNaam
    xml_naam = attributeNaam + '_19110.xml'
    # lees de namespaces    
    namespaces = self.config["namespaces"]
    gco = namespaces['gco']
    gmd = namespaces['gmd']
    # lees feature catalogue UUID uit 19115 xml
    if os.path.isfile(self.xml_map+os.sep+attributeNaam + '.xml'): 
      # parse de xml
      xmldoc = etree.parse(self.xml_map+os.sep+attributeNaam + '.xml')
      fcUUID = xmldoc.findtext('//{%s}contentInfo/{%s}MD_FeatureCatalogueDescription/{%s}featureCatalogueCitation/{%s}CI_Citation/{%s}identifier/{%s}MD_Identifier/{%s}code/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
    # maak hem anders aan
    else: fcUUID = str(uuid.uuid4())
    # xsd invoegen
    schemalocation = etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'schemaLocation')
    # bepaal het root element
    root = etree.Element('FC_FeatureCatalogue', {schemalocation: 'http://www.isotc211.org/2005/gfc http://www.isotc211.org/2005/gfc/gfc.xsd'}, nsmap=namespaces)
    name = etree.SubElement(root, '{%s}name' %(namespaces['gmx']))
    CharacterString_1 = etree.SubElement(name, '{%s}CharacterString' %(namespaces['gco']))
    CharacterString_1.text = attributeNaam
    scope = etree.SubElement(root, '{%s}scope' %(namespaces['gmx']))
    scope.set('{%s}nilReason' %(namespaces['gco']), 'unknown')
    versionNumber = etree.SubElement(root, '{%s}versionNumber' %(namespaces['gmx']))
    versionNumber.set('{%s}nilReason' %(namespaces['gco']), 'unknown')
    versionDate = etree.SubElement(root, '{%s}versionDate' %(namespaces['gmx']))
    versionDate.set('{%s}nilReason' %(namespaces['gco']), 'unknown')
    language = etree.SubElement(root, '{%s}language' %(namespaces['gmx']))
    CharacterString_2 = etree.SubElement(language, '{%s}CharacterString' %(namespaces['gco']))
    CharacterString_2.text = 'dut'
    characterSet = etree.SubElement(root, '{%s}characterSet' %(namespaces['gmx']))
    MD_CharacterSetCode =  etree.SubElement(characterSet, '{%s}MD_CharacterSetCode' %(namespaces['gmd']))
    MD_CharacterSetCode.set('codeList', 'http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#MD_CharacterSetCode')
    MD_CharacterSetCode.set('codeListValue', 'utf8')
    producer = etree.SubElement(root, 'producer')
    producer.set('{%s}arcrole' %(namespaces['xlink']), 'pointOfContact')
    producer.set('{%s}title' %(namespaces['xlink']), '%s' %(self.config["organisatie"]))
    featureType = etree.SubElement(root, 'featureType')
    FC_FeatureType = etree.SubElement(featureType, 'FC_FeatureType')
    typeName = etree.SubElement(FC_FeatureType, 'typeName')
    LocalName_20 = etree.SubElement(typeName, '{%s}LocalName' %(namespaces['gco']))
    LocalName_20.text = attributeNaam
    definition = etree.SubElement(FC_FeatureType, 'definition')
    CharacterString_20 = etree.SubElement(definition, '{%s}CharacterString' %(namespaces['gco']))
    CharacterString_20.text = 'Feature Class'
    isAbstract = etree.SubElement(FC_FeatureType, 'isAbstract')
    Boolean = etree.SubElement(isAbstract, '{%s}Boolean' %(namespaces['gco']))
    Boolean.text = 'false'
    aliases = etree.SubElement(FC_FeatureType, 'aliases')
    LocalName_21 = etree.SubElement(aliases, '{%s}LocalName' %(namespaces['gco']))
    LocalName_21.text = attributeNaam
    featureCatalogue = etree.SubElement(FC_FeatureType, 'featureCatalogue')
    featureCatalogue.set('uuidref', '%s' %(fcUUID))
    # loop door de verschillende velden 
    for teller, veld in enumerate(self.iface.activeLayer().fields(), start=1):
      num = teller*100+teller
      exec("tag_%s = etree.SubElement(FC_FeatureType, 'carrierOfCharacteristics')" %(num+1))
      exec("tag_%s = etree.SubElement(tag_%s, 'FC_FeatureAttribute')" %(num+2, num+1))
      exec("tag_%s = etree.SubElement(tag_%s, 'featureType')" %(num+3, num+2))
      exec("tag_%s = etree.SubElement(tag_%s, 'memberName')" %(num+4, num+2))
      exec("tag_%s = etree.SubElement(tag_%s, '{%s}LocalName'); tag_%s.text = '%s'" %(num+5, num+4, namespaces['gco'], num+5, veld.name()))
      exec("tag_%s = etree.SubElement(tag_%s, 'definition')" %(num+6, num+2))
      exec("tag_%s = etree.SubElement(tag_%s, '{%s}CharacterString'); tag_%s.text = self.ui.textEdit_%s.toPlainText()" %(num+7, num+6, namespaces['gco'], num+7, teller))
      exec("tag_%s = etree.SubElement(tag_%s, 'cardinality')" %(num+8, num+2))
      exec("tag_%s.set('{%s}nilReason', 'unknown')"  %(num+8, namespaces['gco']))
      exec("tag_%s = etree.SubElement(tag_%s, 'code')" %(num+9, num+2))
      exec("tag_%s = etree.SubElement(tag_%s, '{%s}CharacterString'); tag_%s.text = '%s'" %(num+10, num+9, namespaces['gco'], num+10, veld.name()))
      exec("tag_%s = etree.SubElement(tag_%s, 'valueType')" %(num+11, num+2))
      exec("tag_%s = etree.SubElement(tag_%s, '{%s}TypeName')" %(num+12, num+11, namespaces['gco']))
      exec("tag_%s = etree.SubElement(tag_%s, '{%s}aName')" %(num+13, num+12, namespaces['gco']))
      exec("tag_%s = etree.SubElement(tag_%s, '{%s}CharacterString'); tag_%s.text = '%s'" %(num+14, num+13, namespaces['gco'], num+14, veld.typeName()))
    # schrijf alles weg
    etree.ElementTree(root).write(self.xml_map+os.sep+xml_naam, pretty_print=True, xml_declaration=True, encoding='utf-8')
    # geef een melding dat de xml is opgeslagen    
    QtWidgets.QMessageBox.warning(None, "", "%s%s%s is opgeslagen" %(self.xml_map, os.sep, xml_naam))

# ----------------------------------------------------------------------
