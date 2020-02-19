#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE ---------------------------------------------
#
# python-3         http://www.python.org
#
# ----- PREFIX VARIABELEN ----------------------------------------------
#
#  le_     line edit
#  lbl_    label
#  sa_     scrollarea
#  cbx_    combobox
#  te_     text edit
#  de_     datum edit
#  pb_     push button
#  cb_     checkbox
#  bg_     button group
#
# ----- MET DANK AAN ---------------------------------------------------
#
# https://qgis.org/pyqgis/3.4/index.html
# http://qgis.sourceforge.net/qgis_api/html/index.html
# http://doc.qt.io/qt-5/
# https://pythonspot.com/pyqt5/
# https://srinikom.github.io/pyside-docs/PySide/QtGui/QButtonGroup.html
#
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__      = 'Plugin voor QGis om metadata aan te maken volgens het Nederlandse ISO profiel 19119 2.0.0'
__rights__   = 'Jan van Sambeek'
__author__   = 'Jan van Sambeek'
__license__  = 'GNU Lesser General Public License, version 3 (LGPL-3.0)'
__date__     = ['06-2019']
__version__  = '0.9.5'

# ----- IMPORT LIBRARIES -----------------------------------------------

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .ME_19119_200_ui import Ui_ME_19119_200
from PIL import Image
from io import BytesIO
from lxml import etree

import os, requests

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

# ----- ME_19119_200 ---------------------------------------------------

class ME_19119_200(QDialog):
  def __init__(self, parent):
    QDialog.__init__(self)
    # Set up the user interface from Designer.
    self.parent = parent
    self.iface = parent.iface
    # roep de gui aan
    self.ui = Ui_ME_19119_200()
    self.ui.setupUi(self)
    # scheidingsteken
    self.sep = ';'    
    # bepaal de start dir en de naam van de file
    self.start_dir, self.start_file = os.path.split(os.path.abspath(__file__))
    # ~ # maak een object van de configuratie data
    # ~ cfg = Config(self.parent.start_dir+os.sep+self.start_file.split('.')[0]+'.cfg')
    # ~ # lees de verschillende lijst tags uit
    # ~ self.eigenlijsten = cfg.get_dict()
    # ~ # haal de geonovum codelijsten op
    # ~ GN_Codes = Config(self.parent.start_dir+os.sep+'Codelijsten_19115_200.cfg')
    # ~ self.codelijsten = GN_Codes.get_dict()
    # ~ # maak lege dictionaries om alle aangevinkte (trefwoorden) op te slaan
    # ~ self.trefwoorden_dict = {}
    # ~ self.checkbox_dict = {}
    # ~ # lees de contact gegevens uit contact_gegevens.csv
    # ~ csv_bestand = self.eigenlijsten["dirs"]["csv_dir"]+os.sep+"Metadata_Master.csv" 
    # ~ # maak een lege dictionarie
    # ~ self.csv_dict = {}
    # ~ # als de csv bestaat
    # ~ if os.path.isfile(csv_bestand):
      # ~ # maak een object van de csv data open de file en lees de regels
      # ~ with open(csv_bestand, 'r') as csvfile: csv_regels = csvfile.readlines()
      # ~ # genereer een list uit de lines
      # ~ csv_list = [csv_regel.strip().split(self.sep) for csv_regel in csv_regels]
      # ~ # vul de dictionarie met keys in kleine letters
      # ~ for csv in csv_list[1:]: self.csv_dict[csv[0].lower()] = csv
    # ~ # maak anders een leeg csv bestand met header
    # ~ else:
      # ~ with open(csv_bestand, 'w') as csvfile: 
        # ~ csvfile.writelines('email;contactpersoon;organisatie;adres;postcode;plaats;provincie;land;tel;fax;url')
    # ~ # bepaal de xml naam
    # ~ self.bepaal_xml_naam()
    # ~ # lees de xml uit als deze bestaat
    # ~ if os.path.isfile(self.xml_map+os.sep+os.path.splitext(self.xml_naam)[0]+'.xml'): self.leesXML()
    # ~ # lees de srid uit
    # ~ srid = self.iface.activeLayer().crs().postgisSrid()
    # ~ # als er geen srid is maak de srid en extent leeg
    # ~ if not srid:
      # ~ srid = ''
      # ~ srid_naam = ''
      # ~ xMin = ''
      # ~ yMin = ''
      # ~ xMax = ''
      # ~ yMax = ''
    # ~ # als de srid gelijk is aan WGS84 lees de extent uit
    # ~ elif self.iface.activeLayer().crs().postgisSrid() == 4326:
      # ~ srid = str(srid)
      # ~ srid_naam = self.iface.activeLayer().crs().description()
      # ~ xMin = '%9.4f\n' %(self.iface.activeLayer().extent().xMinimum())
      # ~ yMin = '%9.4f\n' %(self.iface.activeLayer().extent().yMinimum())
      # ~ xMax = '%9.4f\n' %(self.iface.activeLayer().extent().xMaximum())
      # ~ yMax = '%9.4f\n' %(self.iface.activeLayer().extent().yMaximum())
    # ~ # anders zet de extent om naar WGS84
    # ~ # ter info EPSG 28992 xMin=3.2, yMin=50.75, xMax=7.22, yMax=53.7
    # ~ else: 
      # ~ transform = QgsCoordinateTransform(QgsCoordinateReferenceSystem(srid), QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())           
      # ~ wgsExtent = transform.transformBoundingBox(self.iface.activeLayer().extent())
      # ~ srid = str(srid)
      # ~ srid_naam = self.iface.activeLayer().crs().description()
      # ~ xMin = '%9.4f\n' %(wgsExtent.xMinimum())
      # ~ yMin = '%9.4f\n' %(wgsExtent.yMinimum())
      # ~ xMax = '%9.4f\n' %(wgsExtent.xMaximum())
      # ~ yMax = '%9.4f\n' %(wgsExtent.yMaximum())

    # ~ # PushButton "pb_Opslaan" voor de controle en opslag van de data : zet een tooltip en als er op de button geklikt wordt
    # ~ self.ui.pb_Opslaan.setToolTip(self.eigenlijsten["ToolTips"]["pb_Opslaan"])
    # ~ self.ui.pb_Opslaan.clicked.connect(self.schrijfXML)

    # ~ # Identificatie algemeen
    # ~ # zet diverse tooltips
    # ~ self.ui.le_TitelBron.setToolTip(self.eigenlijsten["ToolTips"]["le_TitelBron"])
    # ~ self.ui.le_AlternatieveTitel.setToolTip(self.eigenlijsten["ToolTips"]["le_AlternatieveTitel"])
    # ~ self.ui.le_Versie.setToolTip(self.eigenlijsten["ToolTips"]["le_Versie"])
    # ~ self.ui.le_uuid.setToolTip(self.eigenlijsten["ToolTips"]["le_uuid"])
    # ~ self.ui.te_Samenvatting.setToolTip(self.eigenlijsten["ToolTips"]["te_Samenvatting"])
    # ~ self.ui.le_Serienaamnummer.setToolTip(self.eigenlijsten["ToolTips"]["le_Serienaamnummer"])
    # ~ self.ui.de_Creatiedatum.setToolTip(self.codelijsten["A.1 Codelijst CI_DateTypeCode"][0][1])
    # ~ self.ui.de_Publicatiedatum.setToolTip(self.codelijsten["A.1 Codelijst CI_DateTypeCode"][1][1])   
    # ~ self.ui.de_Revisiedatum.setToolTip(self.codelijsten["A.1 Codelijst CI_DateTypeCode"][2][1])  
    # ~ # vul de alternative titel met de bestandsnaam
    # ~ if not self.ui.le_AlternatieveTitel.text() and self.xml_naam: self.ui.le_AlternatieveTitel.setText(os.path.splitext(self.xml_naam)[0])
    # ~ # PushButton "pb_uuid" voor een nieuwe uuid: zet een tooltip en als er op de button geklikt wordt
    # ~ self.ui.pb_uuid.setToolTip(self.eigenlijsten["ToolTips"]["pb_uuid"])
    # ~ self.ui.pb_uuid.clicked.connect(self.verander_uuid)
    # ~ self.ui.pb_aanpassen_uuid.setToolTip(self.eigenlijsten["ToolTips"]["pb_aanpassen_uuid"])
    # ~ # zet de uuid op read only
    # ~ self.ui.le_uuid.setReadOnly(True)
    # ~ # zet read only uit
    # ~ self.ui.pb_aanpassen_uuid.clicked.connect(self.aanpassen_uuid)
    # ~ # als 'le_uuid' leeg is maak dan een uuid aan
    # ~ if not self.ui.le_uuid.text(): self.ui.le_uuid.setText(self.eigenlijsten['Voorkeuren']['le_uuid_prefix']+'/'+str(uuid.uuid4()))
    # ~ # Combobox "cbx_Status" 
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de codelijst A.9 Codelijst MD_ProgressCode en bepaal het item waarmee gestart wordt
    # ~ addItemLijst = [self.codelijsten["A.9 Codelijst MD_ProgressCode"][index][0] for index in range(len(self.codelijsten["A.9 Codelijst MD_ProgressCode"]))]
    # ~ self.ui.cbx_Status.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Status"])
    # ~ self.ui.cbx_Status.addItems(addItemLijst)
    # ~ # haal de index voor de status uit de xml
    # ~ if hasattr(self, 'status') and self.status in addItemLijst:
      # ~ self.ui.cbx_Status.setCurrentIndex(addItemLijst.index(self.status))  
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Status"] in addItemLijst:
      # ~ self.ui.cbx_Status.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Status"]))
    # ~ # Combobox "cbx_Ruimtelijke_schema" 
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de codelijst A.12 Codelijst MD_SpatialRepresentationTypeCode en bepaal het item waarmee gestart wordt
    # ~ addItemLijst = [self.codelijsten["A.12 Codelijst MD_SpatialRepresentationTypeCode"][index][0] for index in range(len(self.codelijsten["A.12 Codelijst MD_SpatialRepresentationTypeCode"]))]
    # ~ self.ui.cbx_Ruimtelijke_schema.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Ruimtelijke_schema"])
    # ~ self.ui.cbx_Ruimtelijke_schema.addItems(addItemLijst)
    # ~ # self.ruimtelijkSchema bestaat bepaal de index
    # ~ if hasattr(self, 'ruimtelijkSchema') and self.ruimtelijkSchema in addItemLijst: 
      # ~ self.ui.cbx_Ruimtelijke_schema.setCurrentIndex(addItemLijst.index(self.ruimtelijkSchema))
    # ~ # lees het type uit van de actieve laag: 0 = vector; 1 = grid/raster
    # ~ elif self.iface.activeLayer().type() == 0:
      # ~ self.ui.cbx_Ruimtelijke_schema.setCurrentIndex(addItemLijst.index("vector"))
    # ~ elif self.iface.activeLayer().type() == 1:
      # ~ self.ui.cbx_Ruimtelijke_schema.setCurrentIndex(addItemLijst.index("grid"))
    # ~ # zet het cbx_Ruimtelijke_schema op de voorkeur van ME_19115_200.cfg 
    # ~ elif self.iface.activeLayer().type() != 0 and self.iface.activeLayer().type() == 1 and self.eigenlijsten["Voorkeuren"]["cbx_Ruimtelijke_schema"] in addItemLijst:
      # ~ self.ui.cbx_Ruimtelijke_schema.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Ruimtelijke_schema"]))
    # ~ # Combobox "cbx_Taal_bron"
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de codelijst A.17 Codelijst Talen (ISO 639-2) en bepaal het item waarmee gestart wordt
    # ~ addItemLijst = sorted([self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"][index][0] for index in range(len(self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"]))])
    # ~ self.ui.cbx_Taal_bron.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Taal_bron"])
    # ~ self.ui.cbx_Taal_bron.addItems(addItemLijst)
    # ~ # haal de index voor de bronTaal uit de xml
    # ~ if hasattr(self, 'bronTaal') and self.bronTaal in addItemLijst: 
      # ~ self.ui.cbx_Taal_bron.setCurrentIndex(addItemLijst.index(self.bronTaal))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Taal_bron"] in addItemLijst:
      # ~ self.ui.cbx_Taal_bron.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Taal_bron"]))
    # ~ # Combobox "cbx_Karakterset_bron"
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de codelijst A.5 Codelijst MD_CharacterSetCode en bepaal het item waarmee gestart wordt
    # ~ addItemLijst = [self.codelijsten["A.5 Codelijst MD_CharacterSetCode"][index][0] for index in range(len(self.codelijsten["A.5 Codelijst MD_CharacterSetCode"]))]
    # ~ self.ui.cbx_Karakterset_bron.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Karakterset_bron"])
    # ~ self.ui.cbx_Karakterset_bron.addItems(addItemLijst)
    # ~ # haal de index voor de bronKarakterset uit de xml
    # ~ if hasattr(self, 'bronKarakterset') and self.bronKarakterset in addItemLijst: 
      # ~ self.ui.cbx_Karakterset_bron.setCurrentIndex(addItemLijst.index(self.bronKarakterset))
    # ~ # kijk of de data van het type vector is, lees de karakterset van de bron (verwijder eventuele streepjes) en geef deze als voorkeur
    # ~ elif self.iface.activeLayer().type() == 0 and self.iface.activeLayer().dataProvider().encoding().lower().replace("-", "") in addItemLijst:
      # ~ self.ui.cbx_Karakterset_bron.setCurrentIndex(addItemLijst.index(self.iface.activeLayer().dataProvider().encoding().lower().replace("-", "")))
    # ~ # geef anders de voorkeur uit ME_19115_200.cfg
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Karakterset_bron"] in addItemLijst:
      # ~ self.ui.cbx_Karakterset_bron.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Karakterset_bron"]))

    # ~ # Identificatie thema's
    # ~ # plaats Checkboxen "cb_Onderwerpen_*" in QScrollArea "sa_Onderwerpen"
    # ~ # geef de naam voor de checkbox en maak een list aan in de dictionary
    # ~ checkbox_naam = 'onderwerpen'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_Onderwerpen = QtWidgets.QButtonGroup()
    # ~ self.bg_Onderwerpen.setExclusive(False)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_Onderwerpen.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Onderwerpen.exclusive()}    
    # ~ # vul de checkboxen met codelijst A.13 Codelijst MD_TopicCategoryCode en lees de tooltips uit A.13 Codelijst MD_TopicCategoryCode
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.13 Codelijst MD_TopicCategoryCode"])):
      # ~ exec("cb_Onderwerpen_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Onderwerpen_%s.setText(self.codelijsten['A.13 Codelijst MD_TopicCategoryCode'][%s][0])" %(num, num))
      # ~ exec("cb_Onderwerpen_%s.setToolTip(self.codelijsten['A.13 Codelijst MD_TopicCategoryCode'][%s][1])" %(num, num))
      # ~ exec("if cb_Onderwerpen_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Onderwerpen_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Onderwerpen.addButton(cb_Onderwerpen_%s, %s)" %(num, num))
      # ~ exec("chkBoxLayout.addWidget(cb_Onderwerpen_%s)" %(num))
    # ~ # als er op een checkbox wordt geklikt
    # ~ self.bg_Onderwerpen.buttonClicked[QAbstractButton].connect(self.changed_checkbox)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(30,15,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Onderwerpen.setWidget(widget)
    # ~ # Combobox "cbx_Thesaurus"
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de eigenlijst Voorkeuren
    # ~ addItemLijst = [*self.eigenlijsten["Thesaurussen"].keys()]
    # ~ self.ui.cbx_Thesaurus.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Thesaurus"])
    # ~ self.ui.cbx_Thesaurus.addItems(addItemLijst)
    # ~ if self.eigenlijsten["Voorkeuren"]["cbx_Thesaurus"] in addItemLijst:
      # ~ self.ui.cbx_Thesaurus.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Thesaurus"]))
    # ~ # als de trefwoorden dictionary nog leeg is vul deze met lege lists    
    # ~ if len(self.trefwoorden_dict) == 0:
      # ~ # maak een lege list in self.checkbox_dict als de thesaurus nog niet aanwezig is 
      # ~ for item in addItemLijst:
        # ~ if item not in self.trefwoorden_dict.keys(): self.trefwoorden_dict[item] = []
    # ~ # als er iets veranderd ga naar ThesaurusChanged
    # ~ self.ui.cbx_Thesaurus.currentIndexChanged.connect(self.ThesaurusChanged)  
    # ~ # plaats Checkboxen "cb_Trefwoorden_*" in QScrollArea "sa_Trefwoorden"  
    # ~ # vul de checkboxen met eigenlijst Thesaurussen en lees de tooltips uit eigenlijst Thesaurussen
    # ~ # maak een button group voor de checkboxen. er kunnen meerdere checkboxen aangevinkt worden. 
    # ~ self.bg_Trefwoorden = QtWidgets.QButtonGroup()
    # ~ self.bg_Trefwoorden.setExclusive(False)
    # ~ # voeg alle trefwoorden toe van de actieve thesaurus
    # ~ addItemLijst = self.eigenlijsten["Thesaurussen"][self.ui.cbx_Thesaurus.currentText()][1]
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(addItemLijst)):
      # ~ exec("cb_Trefwoorden_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Trefwoorden_%s.setText(addItemLijst[%s])" %(num, num))
      # ~ exec("cb_Trefwoorden_%s.setText(addItemLijst[%s])" %(num, num))
      # ~ exec("if self.ui.cbx_Thesaurus.currentText() in self.trefwoorden_dict.keys() and cb_Trefwoorden_%s.text() in self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()]:\n cb_Trefwoorden_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Trefwoorden.addButton(cb_Trefwoorden_%s, %s)" %(num, num))
      # ~ exec("chkBoxLayout.addWidget(cb_Trefwoorden_%s)" %(num))
    # ~ # als er op een checkbox wordt geklikt
    # ~ self.bg_Trefwoorden.buttonClicked[QAbstractButton].connect(self.changed_trefwoorden)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(30,15,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Trefwoorden.setWidget(widget)    

    # ~ # Identificatie beperkingen
    # ~ # zet diverse tooltips
    # ~ self.ui.lbl_Gebruiksbeperkingen.setToolTip(self.eigenlijsten["ToolTips"]["lbl_Gebruiksbeperkingen"])
    # ~ self.ui.lbl_toegangsrestricties.setToolTip(self.eigenlijsten["ToolTips"]["lbl_toegangsrestricties"])
    # ~ self.ui.lbl_gebruiksrestricties.setToolTip(self.eigenlijsten["ToolTips"]["lbl_gebruiksrestricties"])
    # ~ self.ui.lbl_Veiligheidsrestricties.setToolTip(self.eigenlijsten["ToolTips"]["lbl_Veiligheidsrestricties"])
    # ~ self.ui.lbl_Toelichting_veiligheidsrestricties.setToolTip(self.eigenlijsten["ToolTips"]["lbl_Toelichting_veiligheidsrestricties"])
    # ~ self.ui.le_veiligheidsrestricties.setToolTip(self.eigenlijsten["ToolTips"]["le_veiligheidsrestricties"])
    # ~ # geef de naam voor de checkbox en maak een list aan in de dictionary
    # ~ checkbox_naam = 'gebruiksbeperkingen'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_Gebruiksbeperkingen = QtWidgets.QButtonGroup()
    # ~ self.bg_Gebruiksbeperkingen.setExclusive(False)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_Gebruiksbeperkingen.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Gebruiksbeperkingen.exclusive()}
    # ~ # vul de checkboxen met
    # ~ addItemLijst = self.eigenlijsten["Gebruiksbeperkingen"]
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(addItemLijst)):
      # ~ exec("cb_Gebruiksbeperkingen_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Gebruiksbeperkingen_%s.setText(addItemLijst[%s][0])" %(num, num))
      # ~ exec("if cb_Gebruiksbeperkingen_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Gebruiksbeperkingen_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Gebruiksbeperkingen.addButton(cb_Gebruiksbeperkingen_%s, %s)" %(num, num))
      # ~ exec("chkBoxLayout.addWidget(cb_Gebruiksbeperkingen_%s)" %(num))
    # ~ # als er op een checkbox wordt geklikt
    # ~ self.bg_Gebruiksbeperkingen.buttonClicked[QAbstractButton].connect(self.changed_checkbox)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Gebruiksbeperkingen.setWidget(widget)
    # ~ # plaats Checkboxen "cb_Gebruiksrestricties_*" in QScrollArea "sa_Gebruiksrestricties"
    # ~ # geef de naam voor de checkbox en maak een list aan in de dictionary
    # ~ checkbox_naam = 'gebruiksrestricties'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # maak een buttongroep aan, waar een checkbox aangevinkt kunnen worden 
    # ~ self.bg_Gebruiksrestricties = QtWidgets.QButtonGroup()
    # ~ self.bg_Gebruiksrestricties.setExclusive(False)
    # ~ # geen deze variabelen mee voor de functie self.changed_checkbox
    # ~ self.bg_Gebruiksrestricties.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Gebruiksrestricties.exclusive()}
    # ~ # vul de checkboxen met codelijst A.10 Codelijst MD_RestrictionCode en lees de tooltips uit A.10 Codelijst MD_RestrictionCode
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.10 Codelijst MD_RestrictionCode"])):
      # ~ exec("cb_Gebruiksrestricties_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Gebruiksrestricties_%s.setText(self.codelijsten['A.10 Codelijst MD_RestrictionCode'][%s][0])" %(num, num))
      # ~ exec("cb_Gebruiksrestricties_%s.setToolTip(self.codelijsten['A.10 Codelijst MD_RestrictionCode'][%s][1])" %(num, num))
      # ~ exec("if cb_Gebruiksrestricties_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Gebruiksrestricties_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Gebruiksrestricties.addButton(cb_Gebruiksrestricties_%s, %s)" %(num, num))
      # ~ exec("chkBoxLayout.addWidget(cb_Gebruiksrestricties_%s)" %(num))
    # ~ # als er op een checkbox wordt geklikt
    # ~ self.bg_Gebruiksrestricties.buttonClicked[QAbstractButton].connect(self.changed_checkbox)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Gebruiksrestricties.setWidget(widget)
    # ~ # plaats Checkboxen "cb_Toegangsrestricties_*" in QScrollArea "sa_Toegangsrestricties"
    # ~ checkbox_naam = 'toegangsrestricties'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # als checkbox_naam nog leeg is plaats dan de voorkeur
    # ~ if len(self.checkbox_dict[checkbox_naam]) == 0: self.checkbox_dict[checkbox_naam] = [self.eigenlijsten["Voorkeuren"]["cb_Toegangsrestricties"]]
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_Toegangsrestricties = QtWidgets.QButtonGroup()
    # ~ self.bg_Toegangsrestricties.setExclusive(False)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_Toegangsrestricties.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Toegangsrestricties.exclusive()}    
    # ~ # vul de checkboxen met codelijst A.10 Codelijst MD_RestrictionCode en lees de tooltips uit A.10 Codelijst MD_RestrictionCode
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.10 Codelijst MD_RestrictionCode"])):
      # ~ exec("cb_Toegangsrestricties_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Toegangsrestricties_%s.setText(self.codelijsten['A.10 Codelijst MD_RestrictionCode'][%s][0])" %(num, num))
      # ~ exec("cb_Toegangsrestricties_%s.setToolTip(self.codelijsten['A.10 Codelijst MD_RestrictionCode'][%s][1])" %(num, num))
      # ~ exec("if cb_Toegangsrestricties_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Toegangsrestricties_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Toegangsrestricties.addButton(cb_Toegangsrestricties_%s, %s)" %(num, num+1))
      # ~ exec("chkBoxLayout.addWidget(cb_Toegangsrestricties_%s)" %(num))
    # ~ self.bg_Toegangsrestricties.buttonClicked[QtWidgets.QAbstractButton].connect(self.changed_checkbox)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Toegangsrestricties.setWidget(widget)
    # ~ # plaats Checkboxen "cb_veiligheidsrestricties_*" in QScrollArea "sa_veiligheidsrestricties"
    # ~ # vul de checkboxen met codelijst A.6 Codelijst MD_ClassificationCode en lees de tooltips uit A.6 Codelijst MD_ClassificationCode
    # ~ checkbox_naam = 'veiligheidsrestricties'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_veiligheidsrestricties = QtWidgets.QButtonGroup()
    # ~ self.bg_veiligheidsrestricties.setExclusive(True)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_veiligheidsrestricties.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_veiligheidsrestricties.exclusive()}     
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.6 Codelijst MD_ClassificationCode"])):
      # ~ exec("cb_veiligheidsrestricties_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_veiligheidsrestricties_%s.setText(self.codelijsten['A.6 Codelijst MD_ClassificationCode'][%s][0])" %(num, num))
      # ~ exec("cb_veiligheidsrestricties_%s.setToolTip(self.codelijsten['A.6 Codelijst MD_ClassificationCode'][%s][1])" %(num, num))
      # ~ exec("if cb_veiligheidsrestricties_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_veiligheidsrestricties_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_veiligheidsrestricties.addButton(cb_veiligheidsrestricties_%s, %s)" %(num, num+1))
      # ~ exec("chkBoxLayout.addWidget(cb_veiligheidsrestricties_%s)" %(num))
    # ~ self.bg_veiligheidsrestricties.buttonClicked[QtWidgets.QAbstractButton].connect(self.changed_checkbox)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_veiligheidsrestricties.setWidget(widget)        

    # ~ # Identificatie overige beperkingen
    # ~ # variabelen: sa_Data_licenties; sa_Publieke_toegang; sa_Gebruiks_condities
    # ~ # zet diverse tooltips
    # ~ self.ui.lbl_Overige_beperkingen.setToolTip(self.eigenlijsten["ToolTips"]["lbl_Overige_beperkingen"])
    # ~ # plaats Checkboxen "cb_Data_licenties_*" in QScrollArea "sa_Data_licenties"
    # ~ checkbox_naam = 'datalicenties'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # als checkbox_naam nog leeg is plaats dan de voorkeur
    # ~ if len(self.checkbox_dict[checkbox_naam]) == 0: self.checkbox_dict[checkbox_naam] = [self.eigenlijsten["Voorkeuren"]["cb_Data_licenties"]]
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_Data_licenties = QtWidgets.QButtonGroup()
    # ~ self.bg_Data_licenties.setExclusive(True)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_Data_licenties.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Data_licenties.exclusive()}    
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.20 Codelijst data licenties"])):
      # ~ exec("cb_Data_licenties_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Data_licenties_%s.setText(self.codelijsten['A.20 Codelijst data licenties'][%s][1])" %(num, num))
      # ~ exec("cb_Data_licenties_%s.setToolTip(self.codelijsten['A.20 Codelijst data licenties'][%s][2])" %(num, num))
      # ~ exec("if cb_Data_licenties_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Data_licenties_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Data_licenties.addButton(cb_Data_licenties_%s, %s)" %(num, num+1))
      # ~ exec("chkBoxLayout.addWidget(cb_Data_licenties_%s)" %(num))
    # ~ self.bg_Data_licenties.buttonClicked[QtWidgets.QAbstractButton].connect(self.changed_checkbox)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Data_licenties.setWidget(widget)
    # ~ # plaats Checkboxen "cb_Gebruiks_condities_*" in QScrollArea "sa_Gebruiks_condities"
    # ~ # vul de checkboxen met
    # ~ checkbox_naam = 'gebruikscondities'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_Gebruiks_condities = QtWidgets.QButtonGroup()
    # ~ self.bg_Gebruiks_condities.setExclusive(True)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_Gebruiks_condities.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Gebruiks_condities.exclusive()}
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.15 Codelijst INSPIRE ConditionsApplyingToAccessAndUse"])):
      # ~ exec("cb_Gebruiks_condities_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Gebruiks_condities_%s.setText(self.codelijsten['A.15 Codelijst INSPIRE ConditionsApplyingToAccessAndUse'][%s][1])" %(num, num))
      # ~ exec("cb_Gebruiks_condities_%s.setToolTip(self.codelijsten['A.15 Codelijst INSPIRE ConditionsApplyingToAccessAndUse'][%s][2])" %(num, num))
      # ~ exec("if cb_Gebruiks_condities_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Gebruiks_condities_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Gebruiks_condities.addButton(cb_Gebruiks_condities_%s, %s)" %(num, num+1))
      # ~ exec("chkBoxLayout.addWidget(cb_Gebruiks_condities_%s)" %(num))
    # ~ self.bg_Gebruiks_condities.buttonClicked[QtWidgets.QAbstractButton].connect(self.changed_checkbox)
    # ~ self.bg_Gebruiks_condities.setExclusive(True)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Gebruiks_condities.setWidget(widget)
    # ~ # plaats Checkboxen "cb_Publieke_toegang_*" in QScrollArea "sa_Publieke_toegang"
    # ~ checkbox_naam = 'publieketoegang'
    # ~ if checkbox_naam not in self.checkbox_dict.keys(): self.checkbox_dict[checkbox_naam] = []
    # ~ # maak een buttongroep aan, waar meerdere checkboxen aangevinkt kunnen worden 
    # ~ self.bg_Publieke_toegang = QtWidgets.QButtonGroup()
    # ~ self.bg_Publieke_toegang.setExclusive(True)
    # ~ # geen deze variabele mee voor de functie self.changed_checkbox
    # ~ self.bg_Publieke_toegang.argumenten = {'naam': checkbox_naam, 'exclusief': self.bg_Publieke_toegang.exclusive()}
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(self.codelijsten["A.16 Codelijst INSPIRE LimitationsOnPublicAccess"])):
      # ~ exec("cb_Publieke_toegang_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Publieke_toegang_%s.setText(self.codelijsten['A.16 Codelijst INSPIRE LimitationsOnPublicAccess'][%s][1])" %(num, num))
      # ~ exec("cb_Publieke_toegang_%s.setToolTip(self.codelijsten['A.16 Codelijst INSPIRE LimitationsOnPublicAccess'][%s][2])" %(num, num))
      # ~ exec("if cb_Publieke_toegang_%s.text() in self.checkbox_dict[checkbox_naam]:\n cb_Publieke_toegang_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Publieke_toegang.addButton(cb_Publieke_toegang_%s, %s)" %(num, num+1))
      # ~ exec("chkBoxLayout.addWidget(cb_Publieke_toegang_%s)" %(num))
    # ~ self.bg_Publieke_toegang.buttonClicked[QtWidgets.QAbstractButton].connect(self.changed_checkbox)
    # ~ self.bg_Publieke_toegang.setExclusive(True)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(10,10,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Publieke_toegang.setWidget(widget)
    
    # ~ # Identificatie beheer
    # ~ # zet diverse tooltips
    # ~ self.ui.de_Datum_herziening.setToolTip(self.eigenlijsten['ToolTips']['de_Datum_herziening'])
    # ~ self.ui.cbx_Herzieningsfrequentie.setToolTip(self.eigenlijsten['ToolTips']['cbx_Herzieningsfrequentie'])
    # ~ self.ui.te_Doel_vervaardiging.setToolTip(self.eigenlijsten["ToolTips"]["te_Doel_vervaardiging"])
    # ~ self.ui.le_Toepassingsschaal_01.setToolTip(self.eigenlijsten["ToolTips"]["le_Toepassingsschaal"])
    # ~ self.ui.le_Toepassingsschaal_02.setToolTip(self.eigenlijsten["ToolTips"]["le_Toepassingsschaal"])    
    # ~ self.ui.le_Resolutie_01.setToolTip(self.eigenlijsten["ToolTips"]["le_Resolutie"])
    # ~ self.ui.le_Resolutie_02.setToolTip(self.eigenlijsten["ToolTips"]["le_Resolutie"])    
    # ~ self.ui.le_Aanvullende_informatie.setToolTip(self.eigenlijsten["ToolTips"]["le_Aanvullende_informatie"])
    # ~ self.ui.le_gerelateerde_dataset_1.setToolTip(self.eigenlijsten['ToolTips']['le_gerelateerde_dataset'])
    # ~ self.ui.de_gd_Datum_1.setToolTip(self.eigenlijsten['ToolTips']['de_gd_Creatiedatum'])
    # ~ self.ui.cbx_gd_Datumtype_1.setToolTip(self.eigenlijsten["ToolTips"]["cbx_gd_Datumtype"])
    # ~ # lees de datum van de herziening uit de xml
    # ~ if hasattr(self, 'datumHerziening') and self.datumHerziening is not None: 
      # ~ self.ui.de_Datum_herziening.setDate(QtCore.QDate.fromString(self.datumHerziening, "yyyy-MM-dd"))
    # ~ # Combobox "cbx_Herzieningsfrequentie"    
    # ~ # vul combobox cbx_Herzieningsfrequentie met de codelijst A.7 Codelijst MD_MaintenanceFrequencyCode
    # ~ addItemLijst = [self.codelijsten["A.7 Codelijst MD_MaintenanceFrequencyCode"][index][0] for index in range(len(self.codelijsten["A.7 Codelijst MD_MaintenanceFrequencyCode"]))]
    # ~ self.ui.cbx_Herzieningsfrequentie.addItems(addItemLijst)
    # ~ # haal de index voor de herzieningsfrequentie uit de xml
    # ~ if hasattr(self, 'herzieningsFrequentie') and self.herzieningsFrequentie in addItemLijst: 
      # ~ self.ui.cbx_Herzieningsfrequentie.setCurrentIndex(addItemLijst.index(self.herzieningsFrequentie)) 
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Herzieningsfrequentie"] in addItemLijst:
      # ~ self.ui.cbx_Herzieningsfrequentie.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Herzieningsfrequentie"]))
    # ~ # LineEdit "le_gerelateerde_dataset"
    # ~ # zet de create datum van de eerste gerelateerde datasets op vandaag; als op enter gedrukt wordt start dan self.vulaan_gerelateerde_dataset
    # ~ self.ui.le_gerelateerde_dataset_1.returnPressed.connect(self.vulaan_gerelateerde_dataset)
    # ~ # vul de huidige datum
    # ~ if str(self.ui.de_gd_Datum_1.date().toPyDate()) == '2000-01-01': 
      # ~ self.ui.de_gd_Datum_1.setDate(QtCore.QDate.currentDate())
    # ~ # Combobox "cbx_gd_Datumtype_1" 
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de codelijst A.1 Codelijst CI_DateTypeCode en bepaal het item waarmee gestart wordt
    # ~ addItemLijst = [self.codelijsten["A.1 Codelijst CI_DateTypeCode"][index][0] for index in range(len(self.codelijsten["A.1 Codelijst CI_DateTypeCode"]))]
    # ~ self.ui.cbx_gd_Datumtype_1.addItems(addItemLijst)
    # ~ if hasattr(self, 'gerelateerdeDatumType_1') and self.gerelateerdeDatumType_1 in addItemLijst: 
      # ~ self.ui.cbx_gd_Datumtype_1.setCurrentIndex(addItemLijst.index(self.gerelateerdeDatumType_1)) 
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_gd_Datumtype"] in addItemLijst: 
      # ~ self.ui.cbx_gd_Datumtype_1.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_gd_Datumtype"]))
    # ~ # Vul de overige objecten van de gerelateerde dataset en zet ze op hidden
    # ~ for num in range(2, 7):
      # ~ exec_tekst = """self.ui.le_gerelateerde_dataset_%s.setHidden(True); self.ui.de_gd_Datum_%s.setHidden(True); \
        # ~ self.ui.cbx_gd_Datumtype_%s.addItems(addItemLijst); self.ui.cbx_gd_Datumtype_%s.setHidden(True); \
        # ~ self.ui.le_gerelateerde_dataset_%s.returnPressed.connect(self.vulaan_gerelateerde_dataset)""" %(num, num, num, num, num)
      # ~ exec(exec_tekst)
      # ~ exec('if hasattr(self, "gerelateerdeDatumType_%s"): \n self.ui.cbx_gd_Datumtype_%s.setCurrentIndex(addItemLijst.index(self.gerelateerdeDatumType_%s))' %(num, num, num))
      # ~ exec_tekst = """if not hasattr(self, "gerelateerdeDatumType_%s") and self.eigenlijsten["Voorkeuren"]["cbx_gd_Datumtype"] in addItemLijst: \
        # ~ self.ui.cbx_gd_Datumtype_%s.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_gd_Datumtype']))""" %(num, num)
      # ~ exec(exec_tekst)
      # ~ exec('if str(self.ui.de_gd_Datum_%s.date().toPyDate()) == "2000-01-01": \n self.ui.de_gd_Datum_%s.setDate(QtCore.QDate.currentDate())' %(num, num))
    # ~ # vul aan uit de xml
    # ~ self.vulaan_gerelateerde_dataset()
      
    # ~ # kwaliteit algemeen
    # ~ # zet de diverse tooltips
    # ~ self.ui.le_topologische_samenhang_waarde.setToolTip(self.eigenlijsten["ToolTips"]["le_topologische_samenhang_waarde"])
    # ~ self.ui.te_beschrijving_herkomst.setToolTip(self.eigenlijsten["ToolTips"]["te_beschrijving_herkomst"])
    # ~ self.ui.te_nauwkeurigheid.setToolTip(self.eigenlijsten["ToolTips"]["te_nauwkeurigheid"])
    # ~ self.ui.te_Compleetheid.setToolTip(self.eigenlijsten["ToolTips"]["te_Compleetheid"])
    # ~ self.ui.le_Features.setToolTip(self.eigenlijsten['ToolTips']['le_features'])
    # ~ self.ui.le_verklaring.setToolTip(self.eigenlijsten['ToolTips']['le_verklaring'])
    # ~ self.ui.le_specificatie.setToolTip(self.eigenlijsten['ToolTips']['le_specificatie'])
    # ~ self.ui.de_specificatie_datum.setToolTip(self.eigenlijsten['ToolTips']['de_specificatie_datum'])
    # ~ self.ui.le_alternatieve_specificatie.setToolTip(self.eigenlijsten['ToolTips']['le_alternatieve_specificatie'])
    # ~ # Combobox "cbx_kwaliteitsbeschrijving"
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de eigenlijst Voorkeuren
    # ~ addItemLijst = [self.codelijsten["A.11 Codelijst MD_ScopeCode"][index][0] for index in range(len(self.codelijsten["A.11 Codelijst MD_ScopeCode"]))]
    # ~ self.ui.cbx_kwaliteitsbeschrijving.setToolTip(self.eigenlijsten["ToolTips"]["cbx_kwaliteitsbeschrijving"])
    # ~ self.ui.cbx_kwaliteitsbeschrijving.addItems(addItemLijst)
    # ~ # haal de index voor het niveau kwaliteit beschrijving uit de xml
    # ~ if hasattr(self, 'niveauKwaliteit'):
      # ~ self.ui.cbx_kwaliteitsbeschrijving.setCurrentIndex(addItemLijst.index(self.niveauKwaliteit))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_kwaliteitsbeschrijving"] in addItemLijst:
      # ~ self.ui.cbx_kwaliteitsbeschrijving.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_kwaliteitsbeschrijving"]))
    # ~ # Combobox "cbx_Conformiteitsindicatie"
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de eigenlijst Voorkeuren
    # ~ addItemLijst = [self.eigenlijsten["cbx_Conformiteitsindicatie"][index][0] for index in range(len(self.eigenlijsten["cbx_Conformiteitsindicatie"]))]
    # ~ self.ui.cbx_Conformiteitsindicatie.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Conformiteitsindicatie"])
    # ~ self.ui.cbx_Conformiteitsindicatie.addItems(addItemLijst)
    # ~ # haal de index voor het niveau kwaliteit beschrijving uit de xml
    # ~ if hasattr(self, 'conformiteitIndicatie'):
      # ~ row_num = [index for index, row in enumerate(self.eigenlijsten["cbx_Conformiteitsindicatie"]) if self.conformiteitIndicatie in row][0]
      # ~ self.ui.cbx_Conformiteitsindicatie.setCurrentIndex(row_num)
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Conformiteitsindicatie"] in addItemLijst:
      # ~ self.ui.cbx_Conformiteitsindicatie.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Conformiteitsindicatie"]))
    # ~ # Combobox "cbx_specificatie_datum"
    # ~ # vul de itemlijst van de combobox, zet een tooltip, vul de combobox met de eigenlijst Voorkeuren
    # ~ addItemLijst = [self.codelijsten["A.1 Codelijst CI_DateTypeCode"][index][0] for index in range(len(self.codelijsten["A.1 Codelijst CI_DateTypeCode"]))]
    # ~ self.ui.cbx_specificatie_datum.setToolTip(self.eigenlijsten["ToolTips"]["cbx_specificatie_datum"])
    # ~ self.ui.cbx_specificatie_datum.addItems(addItemLijst)
    # ~ # haal de specificatie type datum uit de xml
    # ~ if hasattr(self, 'specificatieTypeDatum') and self.specificatieTypeDatum in addItemLijst: 
      # ~ self.ui.cbx_specificatie_datum.setCurrentIndex(addItemLijst.index(self.specificatieTypeDatum))
    # ~ # pak anders de voorkeurs index    
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_specificatie_datum"] in addItemLijst:
      # ~ self.ui.cbx_specificatie_datum.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_specificatie_datum"]))
    # ~ # vul dateEdit de_specificatie_datum met huidige datum
    # ~ if str(self.ui.de_specificatie_datum.date().toPyDate()) == '2000-01-01': self.ui.de_specificatie_datum.setDate(QtCore.QDate.currentDate())

    # ~ # kwaliteit bewerking
    # ~ # TextEdit "te_beschrijving_bewerking"
    # ~ self.ui.te_beschrijving_bewerking_1.setToolTip(self.eigenlijsten['ToolTips']['te_beschrijving_bewerking'])
    # ~ self.ui.de_kwaliteit_bewerking_1.setToolTip(self.eigenlijsten['ToolTips']['de_kwaliteit_bewerking'])
    # ~ self.ui.cbx_bewerking_organisatie_1.setToolTip(self.eigenlijsten['ToolTips']['cbx_bewerking_organisatie'])
    # ~ self.ui.cbx_rol_organisatie_1.setToolTip(self.eigenlijsten['ToolTips']['cbx_rol_organisatie'])
    # ~ # maak een organisatie lijst met unique organisaties uit de csv lijst
    # ~ organisatie_lijst = []
    # ~ [organisatie_lijst.append(self.csv_dict[item][2]) for item in self.csv_dict.keys() if self.csv_dict[item][2] not in organisatie_lijst]
    # ~ # maak een lijst van de code rollen    
    # ~ addItemLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
    # ~ for num in range(1, 9):
      # ~ exec("self.ui.de_kwaliteit_bewerking_%s.setDate(QtCore.QDate.currentDate())" %(num))
      # ~ exec("if hasattr(self, 'datumUB_%s'): self.ui.de_kwaliteit_bewerking_%s.setDateTime(QtCore.QDateTime.fromString(self.datumUB_%s, 'yyyy-MM-ddThh:mm:ss'))" %(num, num, num))
      # ~ exec("self.ui.cbx_bewerking_organisatie_%s.addItems(organisatie_lijst)" %(num))
      # ~ exec_tekst = """if hasattr(self, 'producentBD_%s') and self.producentBD_%s in organisatie_lijst: \
        # ~ self.ui.cbx_bewerking_organisatie_%s.setCurrentIndex(organisatie_lijst.index(self.producentBD_%s))""" %(num, num, num, num) 
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if not hasattr(self, 'producentBD_%s') and self.eigenlijsten['Voorkeuren']['cbx_bewerking_organisatie'] in organisatie_lijst: \
        # ~ self.ui.cbx_bewerking_organisatie_%s.setCurrentIndex(organisatie_lijst.index(self.eigenlijsten['Voorkeuren']['cbx_bewerking_organisatie']))""" %(num, num)
      # ~ exec(exec_tekst)
      # ~ exec("self.ui.cbx_rol_organisatie_%s.addItems(addItemLijst)" %(num))
      # ~ exec_tekst = """if hasattr(self, 'rolPBD_%s') and self.rolPBD_%s in addItemLijst: 
        # ~ self.ui.cbx_rol_organisatie_%s.setCurrentIndex(addItemLijst.index(self.rolPBD_%s))""" %(num, num, num, num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if not hasattr(self, 'rolPBD_%s') and self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron"] in addItemLijst: \
        # ~ self.ui.cbx_rol_organisatie_%s.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_Rol_bron']))""" %(num, num)
      # ~ exec(exec_tekst)
     
    # ~ # kwaliteit bron
    # ~ # zet de diverse tooltips
    # ~ self.ui.te_beschrijving_bron_1.setToolTip(self.eigenlijsten['ToolTips']['te_beschrijving_bron'])
    # ~ self.ui.cbx_methode_bron_1.setToolTip(self.eigenlijsten['ToolTips']['cbx_methode_bron'])
    # ~ self.ui.de_datum_bron_1.setToolTip(self.eigenlijsten['ToolTips']['de_datum_bron'])
    # ~ self.ui.cbx_organisatie_bron_1.setToolTip(self.eigenlijsten['ToolTips']['cbx_organisatie_bron'])
    # ~ self.ui.cbx_rol_bron_organisatie_1.setToolTip(self.eigenlijsten['ToolTips']['cbx_rol_bron_organisatie'])    
    # ~ addItemLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
    # ~ for num in range(1, 9):
      # ~ exec("self.ui.de_datum_bron_%s.setDate(QtCore.QDate.currentDate())" %(num))
      # ~ exec("self.ui.cbx_methode_bron_%s.addItems(self.eigenlijsten['Inwinningsmethode'])" %(num))
      # ~ exec("self.ui.cbx_rol_bron_organisatie_%s.addItems(addItemLijst)" %(num))
      # ~ exec("self.ui.cbx_organisatie_bron_%s.addItems(organisatie_lijst)" %(num))
      # ~ exec_tekst = """if hasattr(self, 'inwinningsmethode_%s') and self.inwinningsmethode_%s in self.eigenlijsten['Inwinningsmethode']: \
        # ~ self.ui.cbx_methode_bron_%s.setCurrentIndex(self.eigenlijsten['Inwinningsmethode'].index(self.inwinningsmethode_%s))""" %(num, num, num, num) 
      # ~ exec(exec_tekst)
      # ~ exec("if hasattr(self, 'datumBrondata_%s'): self.ui.de_datum_bron_%s.setDateTime(QtCore.QDateTime.fromString(self.datumBrondata_%s, 'yyyy-MM-ddThh:mm:ss'))" %(num, num, num))
      # ~ exec_tekst = """if self.eigenlijsten['Voorkeuren']['cbx_organisatie_bron'] in organisatie_lijst: \
        # ~ self.ui.cbx_organisatie_bron_%s.setCurrentIndex(organisatie_lijst.index(self.eigenlijsten['Voorkeuren']['cbx_organisatie_bron']))""" %(num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if hasattr(self, 'inwinnendeOrganisatie_%s') and self.inwinnendeOrganisatie_%s in organisatie_lijst: \
        # ~ self.ui.cbx_organisatie_bron_%s.setCurrentIndex(organisatie_lijst.index(self.inwinnendeOrganisatie_%s))""" %(num, num, num, num) 
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if self.eigenlijsten["Voorkeuren"]["cbx_rol_bron_organisatie"] in addItemLijst: \
        # ~ self.ui.cbx_rol_bron_organisatie_%s.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_rol_bron_organisatie']))""" %(num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if hasattr(self, 'rolInwinOrg_%s') and self.rolInwinOrg_%s in addItemLijst: \
        # ~ self.ui.cbx_rol_bron_organisatie_%s.setCurrentIndex(addItemLijst.index(self.rolInwinOrg_%s))""" %(num, num, num, num) 
      # ~ exec(exec_tekst)

    # ~ # Dekking
    # ~ # zet diverse tooltips
    # ~ self.ui.le_naam_geo_gebied.setToolTip(self.eigenlijsten["ToolTips"]["le_naam_geo_gebied"])
    # ~ self.ui.de_temp_dekking_van.setToolTip(self.eigenlijsten["ToolTips"]["de_temp_dekking_van"])
    # ~ self.ui.de_temp_dekking_tot.setToolTip(self.eigenlijsten["ToolTips"]["de_temp_dekking_tot"])
    # ~ self.ui.te_temporele_dekking.setToolTip(self.eigenlijsten["ToolTips"]["te_temporele_dekking"])
    # ~ self.ui.le_horizontaal_referentiesysteem.setToolTip(self.eigenlijsten["ToolTips"]["le_horizontaal_referentiesysteem"])
    # ~ self.ui.le_horizontaal_Verantwoordelijk_organisatie.setToolTip(self.eigenlijsten["ToolTips"]["le_horizontaal_Verantwoordelijk_organisatie"])
    # ~ self.ui.cbx_verticaal_referentiesysteem.setToolTip(self.eigenlijsten["ToolTips"]["cbx_verticaal_referentiesysteem"])
    # ~ self.ui.le_verticaal_Verantwoordelijk_organisatie.setToolTip(self.eigenlijsten["ToolTips"]["le_verticaal_Verantwoordelijk_organisatie"])
    # ~ # zet dekkings voorkeuren
    # ~ if not self.ui.le_min_X.text(): self.ui.le_min_X.setText(xMin)
    # ~ if not self.ui.le_max_X.text(): self.ui.le_max_X.setText(xMax)
    # ~ if not self.ui.le_min_Y.text(): self.ui.le_min_Y.setText(yMin)
    # ~ if not self.ui.le_max_Y.text(): self.ui.le_max_Y.setText(yMax)
    # ~ if not self.ui.le_horizontaal_referentiesysteem.text(): self.ui.le_horizontaal_referentiesysteem.setText(srid+'  "'+srid_naam+'"') 
    # ~ if not self.ui.le_horizontaal_Verantwoordelijk_organisatie.text(): self.ui.le_horizontaal_Verantwoordelijk_organisatie.setText("EPSG")
    # ~ if not self.ui.le_naam_geo_gebied.text(): self.ui.le_naam_geo_gebied.setText(self.eigenlijsten["Voorkeuren"]["le_naam_geo_gebied"])
    # ~ # zet de verticale dekkingen op hidden
    # ~ self.ui.lbl_verticale_dekking.setHidden(True)
    # ~ self.ui.fr_verticale_dekking.setHidden(True)
    # ~ self.ui.lbl_max_Z.setHidden(True)
    # ~ self.ui.le_max_Z.setHidden(True)
    # ~ self.ui.lbl_min_Z.setHidden(True)
    # ~ self.ui.le_min_Z.setHidden(True)
    # ~ # Combobox "cbx_verticaal_referentiesysteem"
    # ~ # vul combobox cbx_verticaal_referentiesysteem met de self.eigenlijsten EPSG
    # ~ addItemLijst = [str(self.eigenlijsten["EPSG"][index][0])+'  "'+self.eigenlijsten["EPSG"][index][1]+'"' for index in range(len(self.eigenlijsten["EPSG"]))]
    # ~ addItemLijst.append("")
    # ~ self.ui.cbx_verticaal_referentiesysteem.addItems(addItemLijst)
    # ~ # haal de index voor het vericaal referentie systeem uit de xml
    # ~ if hasattr(self, 'verticaal_referentiesysteem'):
      # ~ # vul de item lijst met alleen het srid nummer      
      # ~ addItemLijst = [str(self.eigenlijsten["EPSG"][index][0]) for index in range(len(self.eigenlijsten["EPSG"]))]
      # ~ addItemLijst.append("")
      # ~ self.ui.cbx_verticaal_referentiesysteem.clear()
      # ~ self.ui.cbx_verticaal_referentiesysteem.addItems(addItemLijst)
      # ~ self.ui.cbx_verticaal_referentiesysteem.setCurrentIndex(addItemLijst.index(self.verticaal_referentiesysteem))
      # ~ # wijzig de aanvullende gegevens
      # ~ self.item_verticaal_referentiesysteem(addItemLijst.index(self.verticaal_referentiesysteem))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_verticaal_referentiesysteem"] in addItemLijst:
      # ~ self.ui.cbx_verticaal_referentiesysteem.setCurrentIndex(addItemLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_verticaal_referentiesysteem"]))
    # ~ # als cbx_verticaal_referentiesysteem wordt gewijzigd voer dan item_verticaal_referentiesysteem uit
    # ~ self.ui.cbx_verticaal_referentiesysteem.activated.connect(self.item_verticaal_referentiesysteem)
    # ~ # PushButton "pb_Voorbeeld"
    # ~ # verander het pad naar de image folder voor de pushbutton icon, zet een tooltip, zet het icon en als er op de button geklikt wordt    
    # ~ icon = QtGui.QIcon()
    # ~ icon.addPixmap(QtGui.QPixmap(parent.start_dir+"/images/folder.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    # ~ self.ui.pb_Voorbeeld.setToolTip(self.eigenlijsten["ToolTips"]["pb_Voorbeeld"])
    # ~ self.ui.pb_Voorbeeld.setIcon(icon)
    # ~ self.ui.pb_Voorbeeld.clicked.connect(self.zoek_voorbeeld)
    # ~ # LineEdit "le_Voorbeeld"
    # ~ # plaats een tooltip en voer als op enter gedrukt wordt vul_image uit
    # ~ self.ui.le_Voorbeeld.setToolTip(self.eigenlijsten["ToolTips"]["le_Voorbeeld"])
    # ~ self.ui.le_Voorbeeld.returnPressed.connect(self.vul_image)

    # ~ # Contact gegevens Bron, metadata en distributie
    # ~ # Contact gegevens Bron
    # ~ # als self.ContGegBron nog niet bestaat maak dan een lege list
    # ~ if not hasattr(self, 'ContGegBron'): self.ContGegBron = []
    # ~ # maak de structuur van de bron contact gegevens plus één lege extra
    # ~ for num in range(len(self.ContGegBron)+1): 
      # ~ self.structuur_contactgegevens(num+1, 'bron')
      # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
      # ~ exec('self.ui.le_Email_bron_%s.returnPressed.connect(self.aanpassen_bron_contactgegevens)' %(num+1))
    # ~ # vul de bron contact gevens   
    # ~ for num in range(len(self.ContGegBron)): self.vul_bron_contactgegevens(num+1)    
    # ~ # Contact gegevens Metadata
    # ~ # als self.ContGegMetadata nog niet bestaat maak dan een lege list
    # ~ if not hasattr(self, 'ContGegMetadata'): self.ContGegMetadata = []
    # ~ # maak de structuur van de metadata contact gegevens plus één lege extra
    # ~ for num in range(len(self.ContGegMetadata)+1): 
      # ~ self.structuur_contactgegevens(num+1, 'metadata')
      # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
      # ~ exec('self.ui.le_Email_metadata_%s.returnPressed.connect(self.aanpassen_metadata_contactgegevens)' %(num+1))
    # ~ # vul de metadata contact gevens   
    # ~ for num in range(len(self.ContGegMetadata)): self.vul_metadata_contactgegevens(num+1)
    # ~ # Contact gegevens Distributie
    # ~ # als self.ContGegDistributie nog niet bestaat maak dan een lege list
    # ~ if not hasattr(self, 'ContGegDistributie'): self.ContGegDistributie = []
    # ~ # maak de structuur van de distributie contact gegevens plus één lege extra
    # ~ for num in range(len(self.ContGegDistributie)+1): 
      # ~ self.structuur_contactgegevens(num+1, 'distributie')
      # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
      # ~ exec('self.ui.le_Email_distributie_%s.returnPressed.connect(self.aanpassen_distributie_contactgegevens)' %(num+1))
    # ~ # vul de distributie contact gevens   
    # ~ for num in range(len(self.ContGegDistributie)): self.vul_distributie_contactgegevens(num+1)

    # ~ # Contact gegevens beheer
    # ~ # zet diverse tooltips
    # ~ self.ui.cbx_beheer_email.setToolTip(self.eigenlijsten["ToolTips"]["cbx_beheer_email"])
    # ~ self.ui.le_beheer_contactpersoon.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_contactpersoon"])
    # ~ self.ui.le_beheer_organisatie.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_organisatie"])
    # ~ self.ui.le_beheer_adres.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_adres"])
    # ~ self.ui.le_beheer_postcode.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_postcode"])
    # ~ self.ui.le_beheer_plaats.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_plaats"])
    # ~ self.ui.le_beheer_provincie.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_provincie"])
    # ~ self.ui.le_beheer_land.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_land"])
    # ~ self.ui.le_beheer_telefoon.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_telefoon"])
    # ~ self.ui.le_beheer_fax.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_fax"])
    # ~ self.ui.le_beheer_email.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_email"])
    # ~ self.ui.le_beheer_URL.setToolTip(self.eigenlijsten["ToolTips"]["le_beheer_URL"])
    # ~ # vul de combobox beheer email
    # ~ contactbeheerlijst = ['nieuw']
    # ~ contactbeheerlijst.extend(self.csv_dict.keys())
    # ~ self.ui.cbx_beheer_email.addItems(contactbeheerlijst)
    # ~ # als een ander item uit de combobox wordt gekozen
    # ~ self.ui.cbx_beheer_email.currentIndexChanged.connect(self.beheer_email_change)
    # ~ # als er op oplaan contacten wordt gedrukt
    # ~ self.ui.pb_opslaan_contact_gegevens.clicked.connect(self.opslag_contactgegevens)

    # ~ # Algemeen Metadata
    # ~ # zet diverse tooltips
    # ~ self.ui.le_Metadata_stand_versie.setToolTip(self.eigenlijsten["ToolTips"]["le_Metadata_stand_versie"])
    # ~ self.ui.le_Metadata_stand_naam.setToolTip(self.eigenlijsten["ToolTips"]["le_Metadata_stand_naam"])
    # ~ self.ui.cbx_taal_metadata.setToolTip(self.eigenlijsten["ToolTips"]["cbx_taal_metadata"])
    # ~ self.ui.cbx_Metadata_karakterset.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Metadata_karakterset"])
    # ~ self.ui.le_Metadata_uuid.setToolTip(self.eigenlijsten["ToolTips"]["le_Metadata_uuid"])
    # ~ self.ui.pb_aanpassen_metadata_uuid.setToolTip(self.eigenlijsten["ToolTips"]["pb_aanpassen_uuid"])
    # ~ self.ui.pb_Metadata_uuid.setToolTip(self.eigenlijsten["ToolTips"]["pb_Metadata_uuid"])
    # ~ self.ui.de_Wijzigingsdatum.setToolTip(self.eigenlijsten["ToolTips"]["de_Wijzigingsdatum"])
    # ~ self.ui.cbx_hierarchieniveau.setToolTip(self.eigenlijsten["ToolTips"]["cbx_hierarchieniveau"])
    # ~ self.ui.le_hierachieniveau_naam.setToolTip(self.eigenlijsten["ToolTips"]["le_hierachieniveau_naam"])
    # ~ # zet de metadata standaarden 'vast'en vul ze
    # ~ self.ui.le_Metadata_stand_versie.setReadOnly(True)
    # ~ self.ui.le_Metadata_stand_versie.setText(self.eigenlijsten["Voorkeuren"]["le_Metadata_stand_versie"])
    # ~ self.ui.le_Metadata_stand_naam.setReadOnly(True)
    # ~ self.ui.le_Metadata_stand_naam.setText(self.eigenlijsten["Voorkeuren"]["le_Metadata_stand_naam"])
    # ~ # vul de combobox 'cbx_taal_metadata' en geef de voorkeur aan
    # ~ addItemLijst = [self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"][index][0] for index in range(len(self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"]))]
    # ~ self.ui.cbx_taal_metadata.addItems(addItemLijst)
    # ~ # haal de index voor de metadata taal uit de xml
    # ~ if hasattr(self, 'metadataTaal') and self.metadataTaal in addItemLijst:
      # ~ self.ui.cbx_taal_metadata.setCurrentIndex(addItemLijst.index(self.metadataTaal))  
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_taal_metadata"] in addItemLijst:
      # ~ self.ui.cbx_taal_metadata.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_taal_metadata']))
    # ~ # vul de combobox 'cbx_Metadata_karakterset' en geef de voorkeur aan
    # ~ addItemLijst = [self.codelijsten["A.5 Codelijst MD_CharacterSetCode"][index][0] for index in range(len(self.codelijsten["A.5 Codelijst MD_CharacterSetCode"]))]
    # ~ self.ui.cbx_Metadata_karakterset.addItems(addItemLijst)
    # ~ # haal de index voor de matadata karakterset uit de xml
    # ~ if hasattr(self, 'metadataKarakterSet') and self.metadataKarakterSet in addItemLijst:
      # ~ self.ui.cbx_Metadata_karakterset.setCurrentIndex(addItemLijst.index(self.metadataKarakterSet))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Metadata_karakterset"] in addItemLijst:
      # ~ self.ui.cbx_Metadata_karakterset.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_Metadata_karakterset']))    
    # ~ # zet de metadata uuid op read only
    # ~ self.ui.le_Metadata_uuid.setReadOnly(True)
    # ~ # zet read only uit
    # ~ self.ui.pb_aanpassen_metadata_uuid.clicked.connect(self.aanpassen_metadata_uuid)
    # ~ # als 'le_Metadata_uuid' leeg is maak dan een uuid aan
    # ~ if not self.ui.le_Metadata_uuid.text(): self.ui.le_Metadata_uuid.setText(str(uuid.uuid4()))  
    # ~ # als PushButton "pb_Metadata_uuid" nieuwe uuid wordt ingedrukt
    # ~ self.ui.pb_Metadata_uuid.clicked.connect(self.verander_metadata_uuid)  
    # ~ # als het object datumStamp bestaat vul de wijzingingsdatum met deze waarde anders met vandaag
    # ~ if hasattr(self, 'datumStamp'): self.ui.de_Wijzigingsdatum.setDate(QtCore.QDate.fromString(self.datumStamp, "yyyy-MM-dd"))
    # ~ else: self.ui.de_Wijzigingsdatum.setDate(QtCore.QDate.currentDate())
    # ~ # vul de combobox 'cbx_hierarchieniveau' en geef de voorkeur aan
    # ~ addItemLijst = [self.codelijsten["A.11 Codelijst MD_ScopeCode"][index][0] for index in range(len(self.codelijsten["A.11 Codelijst MD_ScopeCode"]))]
    # ~ self.ui.cbx_hierarchieniveau.addItems(addItemLijst)
    # ~ # haal de index voor de matadata karakterset uit de xml
    # ~ if hasattr(self, 'hierarchieniveau') and self.hierarchieniveau in addItemLijst:
      # ~ self.ui.cbx_hierarchieniveau.setCurrentIndex(addItemLijst.index(self.hierarchieniveau))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_hierarchieniveau"] in addItemLijst:
      # ~ self.ui.cbx_hierarchieniveau.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_hierarchieniveau']))

    # ~ # Algemeen Distributie
    # ~ # zet diverse tooltips
    # ~ self.ui.le_URL_1.setToolTip(self.eigenlijsten["ToolTips"]["le_URL"])
    # ~ self.ui.cbx_protocol_1.setToolTip(self.eigenlijsten["ToolTips"]["cbx_protocol"])
    # ~ self.ui.le_naam_1.setToolTip(self.eigenlijsten["ToolTips"]["le_naam"])
    # ~ self.ui.cbx_omschrijving_1.setToolTip(self.eigenlijsten["ToolTips"]["cbx_omschrijving"])
    # ~ self.ui.cbx_functie_1.setToolTip(self.eigenlijsten["ToolTips"]["cbx_functie"])
    # ~ self.ui.le_orderprocedure.setToolTip(self.eigenlijsten["ToolTips"]["le_orderprocedure"])
    # ~ self.ui.le_prijsinformatie.setToolTip(self.eigenlijsten["ToolTips"]["le_prijsinformatie"])
    # ~ self.ui.le_doorlooptijd.setToolTip(self.eigenlijsten["ToolTips"]["le_doorlooptijd"])
    # ~ self.ui.le_leveringseenheid.setToolTip(self.eigenlijsten["ToolTips"]["le_leveringseenheid"])
    # ~ self.ui.le_bestandsgrootte.setToolTip(self.eigenlijsten["ToolTips"]["le_bestandsgrootte"])
    # ~ self.ui.cbx_Naam_medium.setToolTip(self.eigenlijsten["ToolTips"]["cbx_Naam_medium"])        
    # ~ self.ui.le_Naam_dist_formaat_1.setToolTip(self.eigenlijsten["ToolTips"]["le_Naam_dist_formaat"])
    # ~ self.ui.le_Versie_formaat_1.setToolTip(self.eigenlijsten["ToolTips"]["le_Versie_formaat"])
    # ~ self.ui.le_specificatie_formaat_1.setToolTip(self.eigenlijsten["ToolTips"]["le_specificatie_formaat"])    
    # ~ # vul de combobox Naam medium en geef de voorkeur aan
    # ~ addItemLijst = [self.codelijsten["A.8 Codelijst MD_MediumNameCode"][index][0] for index in range(len(self.codelijsten["A.8 Codelijst MD_MediumNameCode"]))]
    # ~ self.ui.cbx_Naam_medium.addItems(addItemLijst)
    # ~ # als de naam van het medium  uit de xml is uitgelezen
    # ~ if hasattr(self, 'naamMedium') and self.naamMedium in addItemLijst: 
      # ~ self.ui.cbx_Naam_medium.setCurrentIndex(addItemLijst.index(self.naamMedium))
    # ~ # neem anders de voorkeur
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Naam_medium"] in addItemLijst:
      # ~ self.ui.cbx_Naam_medium.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_Naam_medium']))
    # ~ # vul de combobox protocol_1 en geef de voorkeur aan 
    # ~ addItemLijst = [self.codelijsten["A.18 Codelijst Protocol"][index][1] for index in range(len(self.codelijsten["A.18 Codelijst Protocol"]))]
    # ~ self.ui.cbx_protocol_1.addItems(addItemLijst)
    # ~ # als het onlineProtocol uit de xml is uitgelezen
    # ~ if hasattr(self, 'onlineProtocol_1'): 
      # ~ self.ui.cbx_protocol_1.setCurrentIndex(addItemLijst.index(self.onlineProtocol_1))
    # ~ # neem anders de voorkeur
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_protocol"] in addItemLijst:
      # ~ self.ui.cbx_protocol_1.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_protocol']))
    # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
    # ~ self.ui.le_URL_1.returnPressed.connect(self.vulaan_URL_gegevens)
    # ~ # als in de Naam distributie formaat op enter wordt gedrukt start dan de functie vulaan_naam_distributie_gegevens
    # ~ self.ui.le_Naam_dist_formaat_1.returnPressed.connect(self.vulaan_naam_distributie_gegevens)
    # ~ # vul de combobox cbx_omschrijving en geef de voorkeur aan 
    # ~ addItemLijst_omschrijving = [self.codelijsten["A.14 Codelijst INSPIRE OnLineDescriptionCode"][index][1] for index in range(len(self.codelijsten["A.14 Codelijst INSPIRE OnLineDescriptionCode"]))]
    # ~ self.ui.cbx_omschrijving_1.addItems(addItemLijst_omschrijving)
    # ~ # als het onlineOmschrijving uit de xml is uitgelezen
    # ~ if hasattr(self, 'onlineOmschrijving_1'): 
      # ~ self.ui.cbx_omschrijving_1.setCurrentIndex(addItemLijst_omschrijving.index(self.onlineOmschrijving_1))
    # ~ # neem anders de voorkeur
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_omschrijving"] in addItemLijst_omschrijving:    
      # ~ self.ui.cbx_omschrijving_1.setCurrentIndex(addItemLijst_omschrijving.index(self.eigenlijsten['Voorkeuren']['cbx_omschrijving']))
    # ~ # vul de combox cbx_functie en geef de voorkeur aan
    # ~ functieLijst = [self.codelijsten["A.2 Codelijst CI_OnLineFunctionCode"][index][0] for index in range(len(self.codelijsten["A.2 Codelijst CI_OnLineFunctionCode"]))]
    # ~ self.ui.cbx_functie_1.addItems(functieLijst)
    # ~ # als het onlineFunctie uit de xml is uitgelezen
    # ~ if hasattr(self, 'onlineFunctie_1'): 
      # ~ self.ui.cbx_functie_1.setCurrentIndex(functieLijst.index(self.onlineFunctie_1))
    # ~ # neem anders de voorkeur
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_functie"] in functieLijst:
      # ~ self.ui.cbx_functie_1.setCurrentIndex(functieLijst.index(self.eigenlijsten['Voorkeuren']['cbx_functie']))
    # ~ for num in range(2, 6):
      # ~ exec("self.ui.le_URL_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.cbx_protocol_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.le_naam_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.cbx_omschrijving_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.cbx_functie_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.le_Naam_dist_formaat_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.le_Versie_formaat_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.le_specificatie_formaat_%s.setHidden(True)" %(num))
      # ~ exec("self.ui.cbx_protocol_%s.addItems(addItemLijst)" %(num))
      # ~ exec("self.ui.cbx_omschrijving_%s.addItems(addItemLijst_omschrijving)" %(num))
      # ~ exec("self.ui.cbx_functie_%s.addItems(functieLijst)" %(num))
      # ~ exec("self.ui.le_URL_%s.returnPressed.connect(self.vulaan_URL_gegevens)" %(num))
      # ~ exec("self.ui.le_Naam_dist_formaat_%s.returnPressed.connect(self.vulaan_naam_distributie_gegevens)" %(num))
      # ~ exec_tekst = """if hasattr(self, 'onlineProtocol_%s'): \
      # ~ self.ui.cbx_protocol_%s.setCurrentIndex(addItemLijst.index(self.onlineProtocol_%s))""" %(num, num, num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if not hasattr(self, 'onlineProtocol_%s') and self.eigenlijsten["Voorkeuren"]["cbx_protocol"] in addItemLijst: \
        # ~ self.ui.cbx_protocol_%s.setCurrentIndex(addItemLijst.index(self.eigenlijsten['Voorkeuren']['cbx_protocol']))""" %(num, num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if hasattr(self, 'onlineOmschrijving_%s'): \
      # ~ self.ui.cbx_omschrijving_%s.setCurrentIndex(addItemLijst_omschrijving.index(self.onlineOmschrijving_%s))""" %(num, num, num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if not hasattr(self, 'onlineOmschrijving_%s') and self.eigenlijsten['Voorkeuren']['cbx_omschrijving'] in addItemLijst_omschrijving: \
        # ~ self.ui.cbx_omschrijving_%s.setCurrentIndex(addItemLijst_omschrijving.index(self.eigenlijsten['Voorkeuren']['cbx_omschrijving']))""" %(num, num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if hasattr(self, 'onlineFunctie_%s'): \
      # ~ self.ui.cbx_functie_%s.setCurrentIndex(functieLijst.index(self.onlineFunctie_%s))""" %(num, num, num)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if not hasattr(self, 'onlineFunctie_%s') and self.eigenlijsten['Voorkeuren']['cbx_functie'] in functieLijst: \
        # ~ self.ui.cbx_functie_%s.setCurrentIndex(functieLijst.index(self.eigenlijsten['Voorkeuren']['cbx_functie']))""" %(num, num)
      # ~ exec(exec_tekst)
    # ~ # vul aan uit de xml
    # ~ self.vulaan_URL_gegevens()
    # ~ self.vulaan_naam_distributie_gegevens()

    # ~ # Algemeen Attribuutgegevens
    # ~ # Verberg het tabblad als het geen vecor bestand is
    # ~ # https://stackoverflow.com/questions/34377663/how-to-hide-a-tab-in-qtabwidget-and-show-it-when-a-button-is-pressed
    # ~ if self.ui.cbx_Ruimtelijke_schema.currentText() != 'vector': self.ui.tab_9.setEnabled(False)
    # ~ # zet diverse tooltips
    # ~ self.ui.cbx_feature_types.setToolTip(self.eigenlijsten["ToolTips"]["cbx_feature_types"])
    # ~ self.ui.de_attribuutgegevens_datum.setToolTip(self.eigenlijsten["ToolTips"]["de_attribuutgegevens_datum"])
    # ~ self.ui.cbx_datum_type_attribuutgegevens.setToolTip(self.eigenlijsten["ToolTips"]["cbx_datum_type_attribuutgegevens"])
    # ~ self.ui.le_titel_attribuutgegevens.setToolTip(self.eigenlijsten["ToolTips"]["le_titel_attribuutgegevens"])
    # ~ self.ui.le_uuid_attribuutgegevens.setToolTip(self.eigenlijsten["ToolTips"]["le_uuid_attribuutgegevens"])
    # ~ self.ui.pb_aanpassen_uuid_attribuutgegevens.setToolTip(self.eigenlijsten["ToolTips"]["pb_aanpassen_uuid_attribuutgegevens"])
    # ~ self.ui.pb_uuid_attribuutgegevens.setToolTip(self.eigenlijsten["ToolTips"]["pb_uuid_attribuutgegevens"])
    # ~ # als het een vector laag is
    # ~ if self.iface.activeLayer().type() == 0:  
      # ~ # vul de combobox 'cbx_feature_types'
      # ~ FeatureTypesLijst = self.eigenlijsten["FeatureTypes ISO 19103"]
      # ~ self.ui.cbx_feature_types.addItems(FeatureTypesLijst)
      # ~ # haal de index voor het feature type uit de xml
      # ~ if hasattr(self, 'featureTypes') and self.featureTypes in FeatureTypesLijst: 
        # ~ self.ui.cbx_feature_types.setCurrentIndex(FeatureTypesLijst.index(self.featureTypes))
      # ~ # als het geometrie type nummer kleiner is als de lengte van de "FeatureTypes ISO 19103", zet dan het geometrie type nummer als voorkeur
      # ~ elif self.iface.activeLayer().wkbType()-1 < len(FeatureTypesLijst): self.ui.cbx_feature_types.setCurrentIndex(self.iface.activeLayer().wkbType()-1)
      # ~ # cbx_datum_type_attribuutgegevens
      # ~ # vul de itemlijst van de combobox met de codelijst A.1 Codelijst CI_DateTypeCode
      # ~ DatumTypeAttrLijst = [self.codelijsten["A.1 Codelijst CI_DateTypeCode"][index][0] for index in range(len(self.codelijsten["A.1 Codelijst CI_DateTypeCode"]))]
      # ~ self.ui.cbx_datum_type_attribuutgegevens.addItems(DatumTypeAttrLijst)
      # ~ if hasattr(self, 'featurecatalogTypeDatum') and self.featurecatalogTypeDatum in DatumTypeAttrLijst: 
        # ~ self.ui.cbx_datum_type_attribuutgegevens.setCurrentIndex(DatumTypeAttrLijst.index(self.featurecatalogTypeDatum))
      # ~ # le_titel_attribuutgegevens
      # ~ if not self.ui.le_titel_attribuutgegevens.text() and self.xml_naam: self.ui.le_titel_attribuutgegevens.setText(os.path.splitext(self.xml_naam)[0])
      # ~ # PushButton 'pb_uuid_attribuutgegevens' voor een nieuwe uuid
      # ~ self.ui.pb_uuid_attribuutgegevens.clicked.connect(self.verander_attribuutgegevens_uuid)
      # ~ # zet 'le_uuid_attribuutgegevens' uuid op read only
      # ~ self.ui.le_uuid_attribuutgegevens.setReadOnly(True)
      # ~ # zet 'pb_aanpassen_uuid_attribuutgegevens'read only uit
      # ~ self.ui.pb_aanpassen_uuid_attribuutgegevens.clicked.connect(self.aanpassen_attribuutgegevens_uuid)
      # ~ # als 'le_uuid_attribuutgegevens' leeg is maak dan een attribuutgegevens uuid aan
      # ~ if not self.ui.le_uuid_attribuutgegevens.text(): self.ui.le_uuid_attribuutgegevens.setText(self.eigenlijsten['Voorkeuren']['le_uuid_attribuutgegevens_prefix']+'/'+str(uuid.uuid4()))
    # ~ # geef anders lege velden
    # ~ else:
      # ~ self.ui.cbx_feature_types.addItems([''])
      # ~ self.ui.cbx_datum_type_attribuutgegevens.addItems([''])
      # ~ self.ui.le_titel_attribuutgegevens.setText('')
      # ~ self.ui.le_uuid_attribuutgegevens.setText('')

  # ~ def bepaal_xml_naam(self):
    # ~ """
    # ~ Bepaal welk pad en welke naam de xml krijgt
    # ~ """
    # ~ # genereer de opslag directorie en de xml naam    
    # ~ # lees de bron gegevens van de actieve laag uit
    # ~ bron_gegevens = self.iface.activeLayer().dataProvider().dataSourceUri()
    # ~ # als het een vector laag is
    # ~ if self.iface.activeLayer().type() == 0:
      # ~ # lees uit wat voor opslag type het is
      # ~ opslag_type = self.iface.activeLayer().dataProvider().storageType().lower()
      # ~ # als het een shape file is
      # ~ if 'shapefile' in opslag_type:
        # ~ if '|' in bron_gegevens:
          # ~ self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
        # ~ else: self.xml_map, self.xml_naam = os.path.split(bron_gegevens)
      # ~ # als het een dxf is
      # ~ elif 'dxf' in opslag_type:
        # ~ if '|' in bron_gegevens:
          # ~ self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
        # ~ else: self.xml_map, self.xml_naam = os.path.split(bron_gegevens)
      # ~ # als het een gdb is
      # ~ elif 'filegdb' in opslag_type:
        # ~ QtWidgets.QMessageBox.warning(None, 'Bestands info', 'Gebruik de geostandaarden, zie:\n"https://www.forumstandaardisatie.nl/standaard/geo-standaarden"')
        # ~ self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
        # ~ self.xml_naam = os.path.splitext(self.xml_naam)[0]
        # ~ laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split('|') if '=' in item}
        # ~ self.xml_naam += '+'+laag_geg['layername']        
      # ~ # als het een sqlite of geopackage is
      # ~ elif 'sqlite' in opslag_type or 'gpkg' in opslag_type:
        # ~ if '|' in bron_gegevens and 'layername' in bron_gegevens:
          # ~ self.xml_map, self.xml_naam = os.path.split(bron_gegevens.split('|')[0])
          # ~ self.xml_naam = os.path.splitext(self.xml_naam)[0]
          # ~ laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split('|') if '=' in item}
          # ~ self.xml_naam += '+'+laag_geg['layername']
        # ~ elif 'dbname' in bron_gegevens and 'table' in bron_gegevens:
          # ~ laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split(' ') if '=' in item}
          # ~ self.xml_map, self.xml_naam = os.path.split(laag_geg['dbname'])
          # ~ self.xml_naam = os.path.splitext(self.xml_naam)[0]
          # ~ self.xml_naam += '+'+laag_geg['table']
      # ~ # als het een database is
      # ~ elif ('oracle' in opslag_type or 'postgis' in opslag_type) and 'table' in bron_gegevens:
        # ~ self.xml_map = self.eigenlijsten['dirs']['xml_dir']
        # ~ laag_geg = {item.split('=')[0]: item.split('=')[1].replace('"', '').replace("'", "") for item in bron_gegevens.split(' ') if '=' in item}
        # ~ self.xml_naam = laag_geg['table']
      # ~ # onbekende laag, schrijf naar de home directorie
      # ~ else: 
        # ~ self.xml_map = os.path.expanduser("~")
        # ~ self.xml_naam = self.start_file.split('.')[0]
    # ~ # als het een raster laag is
    # ~ elif self.iface.activeLayer().type() == 1: self.xml_map, self.xml_naam = os.path.split(bron_gegevens)

  # ~ def ThesaurusChanged(self):
    # ~ """
    # ~ Als de thesaurus wordt aangepast, pas de trefwoorden aan de actieve thesaurus inclusief aangevinkte trefwoorden
    # ~ """
    # ~ # maak een nieuwe button group voor de checkboxen    
    # ~ self.bg_Trefwoorden = QtWidgets.QButtonGroup()
    # ~ self.bg_Trefwoorden.setExclusive(False)
    # ~ addItemLijst = self.eigenlijsten["Thesaurussen"][self.ui.cbx_Thesaurus.currentText()][1]
    # ~ chkBoxLayout = QtWidgets.QVBoxLayout(self)
    # ~ for num in range(len(addItemLijst)):
      # ~ exec("cb_Trefwoorden_%s = QtWidgets.QCheckBox(self)" %(num))
      # ~ exec("cb_Trefwoorden_%s.setText(addItemLijst[%s])" %(num, num))
      # ~ exec("if cb_Trefwoorden_%s.text() in self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()]:\n cb_Trefwoorden_%s.setChecked(True)" %(num, num))
      # ~ exec("self.bg_Trefwoorden.addButton(cb_Trefwoorden_%s, %s)" %(num, num))
      # ~ exec("chkBoxLayout.addWidget(cb_Trefwoorden_%s)" %(num))
    # ~ # als er op een checkbox wordt geklikt
    # ~ self.bg_Trefwoorden.buttonClicked[QAbstractButton].connect(self.changed_trefwoorden)
    # ~ chkBoxLayout.addStretch(1) 
    # ~ chkBoxLayout.setMargin(0);
    # ~ chkBoxLayout.setContentsMargins(30,15,10,10)
    # ~ chkBoxLayout.setSpacing(0) 
    # ~ widget = QtWidgets.QWidget()  
    # ~ widget.setLayout(chkBoxLayout)
    # ~ self.ui.sa_Trefwoorden.setWidget(widget)
    
  # ~ def zoek_voorbeeld(self):
    # ~ #
    # ~ bestandsnaam = QtWidgets.QFileDialog.getOpenFileName(self, "Voorbeeld Image", "", filter="*.png *.jpg *.jpeg")[0]
    # ~ if bestandsnaam: 
      # ~ self.ui.le_Voorbeeld.setText(bestandsnaam)
      # ~ self.vul_image()

  # ~ def vul_image(self):
    # ~ #
    # ~ bestandsnaam = self.ui.le_Voorbeeld.text().strip()   
    # ~ if bestandsnaam.startswith("http://") or bestandsnaam.startswith("https://"):
      # ~ try: 
        # ~ response = requests.get(bestandsnaam, verify=False, timeout=20)
        # ~ im = Image.open(BytesIO(response.content))
        # ~ bestandsnaam = "%s%s/URLimage.jpg" %(tempfile.gettempdir(), os.sep)
        # ~ im.save(bestandsnaam)
      # ~ except: bestandsnaam = None
    # ~ if bestandsnaam:
      # ~ breedte = self.ui.lbl_dekking.frameGeometry().width()
      # ~ hoogte = self.ui.lbl_dekking.frameGeometry().height()
      # ~ image = QtGui.QPixmap(bestandsnaam)
      # ~ self.ui.lbl_dekking.setPixmap(image.scaled(breedte-10, hoogte-10, QtCore.Qt.KeepAspectRatio))
      # ~ self.ui.lbl_dekking.setAlignment(QtCore.Qt.AlignCenter)
      # ~ self.ui.lbl_dekking.update()

  # ~ def item_verticaal_referentiesysteem(self, index):
    # ~ #
    # ~ if self.ui.cbx_verticaal_referentiesysteem.itemText(index)!= "":
      # ~ self.ui.le_verticaal_Verantwoordelijk_organisatie.setText("EPSG")
      # ~ self.ui.lbl_verticale_dekking.show()
      # ~ self.ui.fr_verticale_dekking.show()
      # ~ self.ui.lbl_max_Z.show()
      # ~ self.ui.le_max_Z.show()
      # ~ self.ui.lbl_min_Z.show()
      # ~ self.ui.le_min_Z.show()
    # ~ else:
      # ~ self.ui.le_verticaal_Verantwoordelijk_organisatie.setText("")
      # ~ self.ui.lbl_verticale_dekking.setHidden(True)
      # ~ self.ui.fr_verticale_dekking.setHidden(True)
      # ~ self.ui.lbl_max_Z.setHidden(True)
      # ~ self.ui.le_max_Z.setHidden(True)
      # ~ self.ui.lbl_min_Z.setHidden(True)
      # ~ self.ui.le_min_Z.setHidden(True)
      
  # ~ def verander_uuid(self):
    # ~ #
    # ~ msgbox = QtWidgets.QMessageBox.warning(None, "LET OP !!!", "Er wordt een nieuwe UUID gegenereerd?", QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
    # ~ if msgbox == QtWidgets.QMessageBox.Ok: self.ui.le_uuid.setText(self.eigenlijsten['Voorkeuren']['le_uuid_prefix']+'/'+str(uuid.uuid4()))

  # ~ def aanpassen_uuid(self):
    # ~ #
    # ~ msgbox = QtWidgets.QMessageBox.warning(None, "LET OP !!!", "De UUID kan aangepast worden?", QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
    # ~ if msgbox == QtWidgets.QMessageBox.Ok: self.ui.le_uuid.setReadOnly(False)
    
  # ~ def verander_metadata_uuid(self):
    # ~ #
    # ~ msgbox = QtWidgets.QMessageBox.warning(None, "LET OP !!!", "Er wordt een nieuwe Metadata UUID gegenereerd?", QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
    # ~ if msgbox == QtWidgets.QMessageBox.Ok: self.ui.le_Metadata_uuid.setText(str(uuid.uuid4()))

  # ~ def aanpassen_metadata_uuid(self):
    # ~ #
    # ~ msgbox = QtWidgets.QMessageBox.warning(None, "LET OP !!!", "De Metadata UUID kan aangepast worden", QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
    # ~ if msgbox == QtWidgets.QMessageBox.Ok: self.ui.le_Metadata_uuid.setReadOnly(False)

  # ~ def verander_attribuutgegevens_uuid(self):
    # ~ #
    # ~ message = "Er wordt een nieuwe Attribuutgegevens UUID gegenereerd?"
    # ~ msgbox = QtWidgets.QMessageBox.warning(None, "LET OP !!!", message, QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
    # ~ if msgbox == QtWidgets.QMessageBox.Ok: self.ui.le_uuid_attribuutgegevens.setText(self.eigenlijsten['Voorkeuren']['le_uuid_attribuutgegevens_prefix']+'/'+str(uuid.uuid4()))

  # ~ def aanpassen_attribuutgegevens_uuid(self):
    # ~ #
    # ~ message = "De attribuutgegevens UUID kan aangepast worden?"
    # ~ msgbox = QtWidgets.QMessageBox.warning(None, "LET OP !!!", message, QtWidgets.QMessageBox.Cancel|QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)
    # ~ if msgbox == QtWidgets.QMessageBox.Ok: self.ui.le_uuid_attribuutgegevens.setReadOnly(False)

  # ~ def changed_trefwoorden(self,cb_num):
    # ~ """
    # ~ Vul de list in de trefwoorden dictionary aan met de aangevinkte checkbox of verwijder de niet meer aangevinkte checkbox
    # ~ """
    # ~ # als cb_num aangevinkt is en cb_num komt niet voor in self.trefwoorden_dict, voeg hem dan toe aan de list in de dictionarie
    # ~ if cb_num.isChecked() == True and cb_num.text() not in self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()]:
      # ~ self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()].append(cb_num.text())
    # ~ # verwijder anders de cb_num uit de list in de dictionarie
    # ~ elif cb_num.isChecked() == False and cb_num.text() in self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()]: 
      # ~ del self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()][self.trefwoorden_dict[self.ui.cbx_Thesaurus.currentText()].index(cb_num.text())]

  # ~ def changed_checkbox(self,cb_num):
    # ~ """
    # ~ Vul de list in de checkbox dictionary aan met de aangevinkte checkbox of verwijder de niet meer aangevinkte checkbox
    # ~ """
    # ~ naam = self.sender().argumenten['naam']
    # ~ exclusief = self.sender().argumenten['exclusief']
    # ~ # als het exclusief is maak dan de list leeg
    # ~ if exclusief: self.checkbox_dict[naam] = []
    # ~ # als cb_num aangevinkt is en cb_num komt niet voor in self.checkbox_dict, voeg hem dan toe aan de list in de dictionarie
    # ~ if cb_num.isChecked() == True and cb_num.text() not in self.checkbox_dict[naam]:
      # ~ self.checkbox_dict[naam].append(cb_num.text())
    # ~ # verwijder anders de cb_num uit de list in de dictionarie
    # ~ elif cb_num.isChecked() == False and cb_num.text() in self.checkbox_dict[naam]: 
      # ~ del self.checkbox_dict[naam][self.checkbox_dict[naam].index(cb_num.text())]

  # ~ def vulaan_gerelateerde_dataset(self):
    # ~ #
    # ~ for num in range(2, 7): 
      # ~ exec_tekst = """if self.ui.le_gerelateerde_dataset_%s.text() != '': \
      # ~ self.ui.lbl_gd_Datumtype.setHidden(False); \
      # ~ self.ui.lbl_gd_Datum.setHidden(False); \
      # ~ self.ui.le_gerelateerde_dataset_%s.setHidden(False); \
      # ~ self.ui.cbx_gd_Datumtype_%s.setHidden(False); \
      # ~ self.ui.de_gd_Datum_%s.setHidden(False)"""%(num-1, num, num-1, num-1)
      # ~ exec(exec_tekst)
      # ~ exec_tekst = """if self.ui.le_gerelateerde_dataset_%s.text() != '' and num == 6: \
      # ~ self.ui.cbx_gd_Datumtype_%s.setHidden(False); \
      # ~ self.ui.de_gd_Datum_%s.setHidden(False)""" %(num, num, num)
      # ~ exec(exec_tekst)

  # ~ def vulaan_URL_gegevens(self):
    # ~ for num in range(2, 6):
      # ~ exec_tekst = """if self.ui.le_URL_%s.text().strip() != '': \
        # ~ self.ui.le_URL_%s.setHidden(False); \
        # ~ self.ui.cbx_protocol_%s.setHidden(False); \
        # ~ self.ui.cbx_omschrijving_%s.setHidden(False); \
        # ~ self.ui.cbx_functie_%s.setHidden(False); \
        # ~ self.ui.le_naam_%s.setHidden(False)"""  %(num-1, num, num, num, num, num)   
      # ~ exec(exec_tekst)

  # ~ def vulaan_naam_distributie_gegevens(self):
    # ~ for num in range(2, 6):
      # ~ exec_tekst = """if self.ui.le_Naam_dist_formaat_%s.text().strip() != '': \
        # ~ self.ui.le_Naam_dist_formaat_%s.setHidden(False); \
        # ~ self.ui.le_Versie_formaat_%s.setHidden(False); \
        # ~ self.ui.le_specificatie_formaat_%s.setHidden(False)""" %(num-1, num, num, num)
      # ~ exec(exec_tekst)  

  # ~ def structuur_contactgegevens(self, num, naam):
    # ~ """
    # ~ maak een lege structuur van de  contact gegevens
    # ~ """
    # ~ scrollWidget = {'bron': [13, '_3'], 'metadata': [11, '_2'], 'distributie': [8, '']}
    # ~ exec('self.ui.le_Email_%s_%s = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents_%s)' %(naam,num, scrollWidget[naam][0]))
    # ~ sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    # ~ sizePolicy.setHorizontalStretch(0)
    # ~ sizePolicy.setVerticalStretch(0)
    # ~ exec('sizePolicy.setHeightForWidth(self.ui.le_Email_%s_%s.sizePolicy().hasHeightForWidth())' %(naam, num))
    # ~ exec('self.ui.le_Email_%s_%s.setSizePolicy(sizePolicy)' %(naam, num))
    # ~ exec('self.ui.le_Email_%s_%s.setMinimumSize(QtCore.QSize(200, 25))' %(naam, num))
    # ~ exec('self.ui.le_Email_%s_%s.setObjectName("le_Email_%s_%s")' %(naam, num, naam, num))
    # ~ exec('self.ui.gridLayout%s.addWidget(self.ui.le_Email_%s_%s, %s, 0, 1, 1)' %(scrollWidget[naam][1], naam, num, num))
    # ~ exec('self.ui.cbx_Rol_%s_%s = QtWidgets.QComboBox(self.ui.scrollAreaWidgetContents_%s)' %(naam, num, scrollWidget[naam][0]))
    # ~ exec('self.ui.cbx_Rol_%s_%s.setEnabled(True)' %(naam, num))
    # ~ sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
    # ~ sizePolicy.setHorizontalStretch(0)
    # ~ sizePolicy.setVerticalStretch(0)
    # ~ exec('sizePolicy.setHeightForWidth(self.ui.cbx_Rol_%s_%s.sizePolicy().hasHeightForWidth())' %(naam, num))
    # ~ exec('self.ui.cbx_Rol_%s_%s.setSizePolicy(sizePolicy)' %(naam, num))
    # ~ exec('self.ui.cbx_Rol_%s_%s.setMinimumSize(QtCore.QSize(90, 25))' %(naam, num))
    # ~ exec('self.ui.cbx_Rol_%s_%s.setObjectName("cbx_Rol_%s_%s")' %(naam, num, naam, num))
    # ~ exec('self.ui.gridLayout%s.addWidget(self.ui.cbx_Rol_%s_%s, %s, 1, 1, 1)' %(scrollWidget[naam][1], naam, num, num))
    # ~ exec('self.ui.le_%s_naam_%s = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents_%s)' %(naam, num, scrollWidget[naam][0]))
    # ~ sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    # ~ sizePolicy.setHorizontalStretch(0)
    # ~ sizePolicy.setVerticalStretch(0)
    # ~ exec('sizePolicy.setHeightForWidth(self.ui.le_%s_naam_%s.sizePolicy().hasHeightForWidth())' %(naam, num))
    # ~ exec('self.ui.le_%s_naam_%s.setSizePolicy(sizePolicy)' %(naam, num))
    # ~ exec('self.ui.le_%s_naam_%s.setMinimumSize(QtCore.QSize(200, 25))' %(naam, num))
    # ~ exec('self.ui.le_%s_naam_%s.setObjectName("le_%s_naam_%s")' %(naam, num, naam, num))
    # ~ exec('self.ui.gridLayout%s.addWidget(self.ui.le_%s_naam_%s, %s, 2, 1, 1)' %(scrollWidget[naam][1], naam, num, num))
    # ~ exec('self.ui.le_%s_website_%s = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents_%s)'%(naam, num, scrollWidget[naam][0]))
    # ~ sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    # ~ sizePolicy.setHorizontalStretch(0)
    # ~ sizePolicy.setVerticalStretch(0)
    # ~ exec('sizePolicy.setHeightForWidth(self.ui.le_%s_website_%s.sizePolicy().hasHeightForWidth())' %(naam, num))
    # ~ exec('self.ui.le_%s_website_%s.setSizePolicy(sizePolicy)' %(naam, num))
    # ~ exec('self.ui.le_%s_website_%s.setMinimumSize(QtCore.QSize(200, 25))' %(naam, num))
    # ~ exec('self.ui.le_%s_website_%s.setObjectName("le_%s_website_%s")' %(naam, num, naam, num))
    # ~ exec('self.ui.gridLayout%s.addWidget(self.ui.le_%s_website_%s, %s, 3, 1, 1)' %(scrollWidget[naam][1], naam, num, num))
    # ~ exec('self.ui.le_%s_contactpersoon_%s = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents_%s)' %(naam, num, scrollWidget[naam][0]))
    # ~ sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    # ~ sizePolicy.setHorizontalStretch(0)
    # ~ sizePolicy.setVerticalStretch(0)
    # ~ exec('sizePolicy.setHeightForWidth(self.ui.le_%s_contactpersoon_%s.sizePolicy().hasHeightForWidth())' %(naam, num))
    # ~ exec('self.ui.le_%s_contactpersoon_%s.setSizePolicy(sizePolicy)' %(naam, num))
    # ~ exec('self.ui.le_%s_contactpersoon_%s.setMinimumSize(QtCore.QSize(200, 25))' %(naam, num))
    # ~ exec('self.ui.le_%s_contactpersoon_%s.setObjectName("le_%s_contactpersoon_%s")' %(naam, num, naam, num))
    # ~ exec('self.ui.gridLayout%s.addWidget(self.ui.le_%s_contactpersoon_%s, %s, 4, 1, 1)' %(scrollWidget[naam][1], naam, num, num))
    # ~ exec('self.ui.cbx_Rol_%s_contactpersoon_%s = QtWidgets.QComboBox(self.ui.scrollAreaWidgetContents_%s)' %(naam, num, scrollWidget[naam][0]))
    # ~ exec('self.ui.cbx_Rol_%s_contactpersoon_%s.setMinimumSize(QtCore.QSize(120, 25))' %(naam, num))
    # ~ exec('self.ui.cbx_Rol_%s_contactpersoon_%s.setObjectName("cbx_Rol_%s_contactpersoon_%s")' %(naam, num, naam, num))
    # ~ exec('self.ui.gridLayout%s.addWidget(self.ui.cbx_Rol_%s_contactpersoon_%s, %s, 5, 1, 1)' %(scrollWidget[naam][1], naam, num, num))
    # ~ # zet diverse tooltips
    # ~ exec('self.ui.le_Email_%s_%s.setToolTip(self.eigenlijsten["ToolTips"]["le_organisatie_email"])' %(naam, num))
    # ~ exec('self.ui.cbx_Rol_%s_%s.setToolTip(self.eigenlijsten["ToolTips"]["cbx_organisatie_rol"])' %(naam, num))
    # ~ exec('self.ui.le_%s_naam_%s.setToolTip(self.eigenlijsten["ToolTips"]["le_organisatie_naam"])' %(naam, num))
    # ~ exec('self.ui.le_%s_website_%s.setToolTip(self.eigenlijsten["ToolTips"]["le_organisatie_website"])' %(naam, num))
    # ~ exec('self.ui.le_%s_contactpersoon_%s.setToolTip(self.eigenlijsten["ToolTips"]["le_contactpersoon_naam"])' %(naam, num))
    # ~ exec('self.ui.cbx_Rol_%s_contactpersoon_%s.setToolTip(self.eigenlijsten["ToolTips"]["cbx_contactpersoon_rol"])' %(naam, num))    

  # ~ def vul_bron_contactgegevens(self, num):
    # ~ """
    # ~ vul de bron contact gegevens
    # ~ variabelen: le_Email_bron_; cbx_Rol_bron_; le_bron_naam_; le_bron_website_; 
                # ~ le_bron_contactpersoon_; cbx_Rol_bron_contactpersoon_
    # ~ """
    # ~ # vul het email adres
    # ~ if self.ContGegBron[num-1][0]: exec('self.ui.le_Email_bron_%s.setText(self.ContGegBron[num-1][0])' %(num))
    # ~ # vul de combobox 'cbx_Rol_bron_' en geef de voorkeur aan
    # ~ A3CodeLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
    # ~ exec('self.ui.cbx_Rol_bron_%s.clear()' %(num))
    # ~ exec('self.ui.cbx_Rol_bron_%s.addItems(A3CodeLijst)' %(num))
    # ~ # haal de rol van de distributie organisatie uit de xml
    # ~ if self.ContGegBron[num-1][1] and self.ContGegBron[num-1][1] in A3CodeLijst:
      # ~ exec('self.ui.cbx_Rol_bron_%s.setCurrentIndex(A3CodeLijst.index(self.ContGegBron[num-1][1]))' %(num))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron"] in A3CodeLijst:
      # ~ exec('self.ui.cbx_Rol_bron_%s.setCurrentIndex(A3CodeLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron"]))' %(num)) 
    # ~ # haal de naam van de bron organisatie uit de xml
    # ~ if self.ContGegBron[num-1][2]: exec('self.ui.le_bron_naam_%s.setText(self.ContGegBron[%s-1][2])' %(num, num))
    # ~ # haal de URL van de distributie organisatie uit de xml
    # ~ if self.ContGegBron[num-1][3]: exec('self.ui.le_bron_website_%s.setText(self.ContGegBron[%s-1][3])' %(num, num))
    # ~ # haal de naam van de contact persoon uit de xml
    # ~ if self.ContGegBron[num-1][4]: exec('self.ui.le_bron_contactpersoon_%s.setText(self.ContGegBron[%s-1][4])' %(num, num))
    # ~ # vul de combobox 'Rol_bron_contactpersoon_'en geef de voorkeur aan
    # ~ exec('self.ui.cbx_Rol_bron_contactpersoon_%s.clear()' %(num))
    # ~ exec('self.ui.cbx_Rol_bron_contactpersoon_%s.addItems(self.eigenlijsten["Rollen"])' %(num))
    # ~ if self.ContGegBron[num-1][5] and self.ContGegBron[num-1][5] in self.eigenlijsten["Rollen"]:
      # ~ exec('self.ui.cbx_Rol_bron_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.ContGegBron[%s-1][5]))' %(num, num))
    # ~ elif self.eigenlijsten['Voorkeuren']['cbx_Rol_bron_contactpersoon'] in self.eigenlijsten['Rollen']:
      # ~ exec('self.ui.cbx_Rol_bron_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron_contactpersoon"]))' %(num))

  # ~ def vul_metadata_contactgegevens(self, num):
    # ~ """
    # ~ vul de metadata contact gegevens
    # ~ variabelen: le_Email_metadata_; cbx_Rol_metadata_; le_metadata_naam_; le_metadata_website_; 
                # ~ le_metadata_contactpersoon_; cbx_Rol_metadata_contactpersoon_
    # ~ """
    # ~ # vul het email adres
    # ~ if self.ContGegMetadata[num-1][0]: exec('self.ui.le_Email_metadata_%s.setText(self.ContGegMetadata[num-1][0])' %(num))
    # ~ # vul de combobox 'cbx_Rol_metadata_' en geef de voorkeur aan
    # ~ A3CodeLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
    # ~ exec('self.ui.cbx_Rol_metadata_%s.clear()' %(num))
    # ~ exec('self.ui.cbx_Rol_metadata_%s.addItems(A3CodeLijst)' %(num))
    # ~ # haal de rol van de metadata organisatie uit de xml
    # ~ if self.ContGegMetadata[num-1][1] and self.ContGegMetadata[num-1][1] in A3CodeLijst:
      # ~ exec('self.ui.cbx_Rol_metadata_%s.setCurrentIndex(A3CodeLijst.index(self.ContGegMetadata[num-1][1]))' %(num))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie"] in A3CodeLijst:
      # ~ exec('self.ui.cbx_Rol_metadata_%s.setCurrentIndex(A3CodeLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_metadata"]))' %(num)) 
    # ~ # haal de naam van de metadata organisatie uit de xml
    # ~ if self.ContGegMetadata[num-1][2]: exec('self.ui.le_metadata_naam_%s.setText(self.ContGegMetadata[%s-1][2])' %(num, num))
    # ~ # haal de URL van de metadata organisatie uit de xml
    # ~ if self.ContGegMetadata[num-1][3]: exec('self.ui.le_metadata_website_%s.setText(self.ContGegMetadata[%s-1][3])' %(num, num))
    # ~ # haal de naam van de contact persoon uit de xml
    # ~ if self.ContGegMetadata[num-1][4]: exec('self.ui.le_metadata_contactpersoon_%s.setText(self.ContGegMetadata[%s-1][4])' %(num, num))
    # ~ # vul de combobox 'Rol_metadata_contactpersoon_'en geef de voorkeur aan
    # ~ exec('self.ui.cbx_Rol_metadata_contactpersoon_%s.clear()' %(num))
    # ~ exec('self.ui.cbx_Rol_metadata_contactpersoon_%s.addItems(self.eigenlijsten["Rollen"])' %(num))
    # ~ if self.ContGegMetadata[num-1][5] and self.ContGegMetadata[num-1][5] in self.eigenlijsten["Rollen"]:
      # ~ exec('self.ui.cbx_Rol_metadata_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.ContGegMetadata[%s-1][5]))' %(num, num))
    # ~ elif self.eigenlijsten['Voorkeuren']['cbx_Rol_metadata_contactpersoon'] in self.eigenlijsten['Rollen']:
      # ~ exec('self.ui.cbx_Rol_metadata_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_metadata_contactpersoon"]))' %(num))
    
  # ~ def vul_distributie_contactgegevens(self, num):
    # ~ """
    # ~ vul de distributie contact gegevens
    # ~ variabelen: le_Email_distributie_; cbx_Rol_distributie_; le_distributie_naam_; le_distributie_website_; 
                # ~ le_distributie_contactpersoon_; cbx_Rol_distributie_contactpersoon_
    # ~ """
    # ~ # vul het email adres
    # ~ if self.ContGegDistributie[num-1][0]: exec('self.ui.le_Email_distributie_%s.setText(self.ContGegDistributie[num-1][0])' %(num))
    # ~ # vul de combobox 'cbx_Rol_distributie_' en geef de voorkeur aan
    # ~ A3CodeLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
    # ~ exec('self.ui.cbx_Rol_distributie_%s.clear()' %(num))
    # ~ exec('self.ui.cbx_Rol_distributie_%s.addItems(A3CodeLijst)' %(num))
    # ~ # haal de rol van de distributie organisatie uit de xml
    # ~ if self.ContGegDistributie[num-1][1] and self.ContGegDistributie[num-1][1] in A3CodeLijst:
      # ~ exec('self.ui.cbx_Rol_distributie_%s.setCurrentIndex(A3CodeLijst.index(self.ContGegDistributie[num-1][1]))' %(num))
    # ~ # pak anders de voorkeurs index
    # ~ elif self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie"] in A3CodeLijst:
      # ~ exec('self.ui.cbx_Rol_distributie_%s.setCurrentIndex(A3CodeLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie"]))' %(num)) 
    # ~ # haal de naam van de distributie organisatie uit de xml
    # ~ if self.ContGegDistributie[num-1][2]: exec('self.ui.le_distributie_naam_%s.setText(self.ContGegDistributie[%s-1][2])' %(num, num))
    # ~ # haal de URL van de distributie organisatie uit de xml
    # ~ if self.ContGegDistributie[num-1][3]: exec('self.ui.le_distributie_website_%s.setText(self.ContGegDistributie[%s-1][3])' %(num, num))
    # ~ # haal de naam van de contact persoon uit de xml
    # ~ if self.ContGegDistributie[num-1][4]: exec('self.ui.le_distributie_contactpersoon_%s.setText(self.ContGegDistributie[%s-1][4])' %(num, num))
    # ~ # vul de combobox 'Rol_distributie_contactpersoon_'en geef de voorkeur aan
    # ~ exec('self.ui.cbx_Rol_distributie_contactpersoon_%s.clear()' %(num))
    # ~ exec('self.ui.cbx_Rol_distributie_contactpersoon_%s.addItems(self.eigenlijsten["Rollen"])' %(num))
    # ~ if self.ContGegDistributie[num-1][5] and self.ContGegDistributie[num-1][5] in self.eigenlijsten["Rollen"]:
      # ~ exec('self.ui.cbx_Rol_distributie_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.ContGegDistributie[%s-1][5]))' %(num, num))
    # ~ elif self.eigenlijsten['Voorkeuren']['cbx_Rol_distributie_contactpersoon'] in self.eigenlijsten['Rollen']:
      # ~ exec('self.ui.cbx_Rol_distributie_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie_contactpersoon"]))' %(num))

  # ~ def aanpassen_bron_contactgegevens(self):
    # ~ """
    # ~ """
    # ~ # lees de lengte van de list plus één extra
    # ~ lenContGegBron = len(self.ContGegBron)+1
    # ~ # lees de aangepaste gegevens uit
    # ~ for num in range(lenContGegBron):
      # ~ num += 1
      # ~ # als er zich een email adres in de keys van contacten bevind lees dan de gegevens uit het csv bestand
      # ~ exec("""if self.ui.le_Email_bron_%s.text().lower().strip() in self.csv_dict.keys() and not self.ui.le_bron_naam_%s.text() \
      # ~ and not self.ui.le_bron_website_%s.text() and not self.ui.le_bron_contactpersoon_%s.text(): \
      # ~ self.ui.le_bron_naam_%s.setText(self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][2]); \
      # ~ self.ui.le_bron_contactpersoon_%s.setText(self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][1]); \
      # ~ self.ui.le_bron_website_%s.setText(self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][10]); \
      # ~ """ %(num, num, num, num, num, num, num, num, num, num))
      # ~ # als het laatste veld is
      # ~ if num == lenContGegBron:
        # ~ # vul de combobox 'cbx_Rol_bron_' en geef de voorkeur aan
        # ~ A3CodeLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
        # ~ exec('if self.ui.le_Email_bron_%s.text(): self.ui.cbx_Rol_bron_%s.addItems(A3CodeLijst)' %(num, num))
        # ~ # vul de combobox 'Rol_bron_contactpersoon_'en geef de voorkeur aan
        # ~ exec('if self.ui.le_Email_bron_%s.text(): self.ui.cbx_Rol_bron_contactpersoon_%s.addItems(self.eigenlijsten["Rollen"])' %(num, num))
        # ~ exec("""if self.ui.le_Email_bron_%s.text() and self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron"] in A3CodeLijst: \
          # ~ self.ui.cbx_Rol_bron_%s.setCurrentIndex(A3CodeLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron"]))""" %(num, num)) 
        # ~ exec("""if self.ui.le_Email_bron_%s.text() and self.eigenlijsten['Voorkeuren']['cbx_Rol_bron_contactpersoon'] in self.eigenlijsten['Rollen']: \
          # ~ self.ui.cbx_Rol_bron_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_bron_contactpersoon"])); \
          # ~ """ %(num, num))
        # ~ exec("""if self.ui.le_Email_bron_%s.text(): \
          # ~ ContGegBron = []; \
          # ~ ContGegBron.append(self.ui.le_Email_bron_%s.text()); \
          # ~ ContGegBron.append(self.ui.cbx_Rol_bron_%s.currentText()); \
          # ~ ContGegBron.append(self.ui.le_bron_naam_%s.text()); \
          # ~ ContGegBron.append(self.ui.le_bron_website_%s.text()); \
          # ~ ContGegBron.append(self.ui.le_bron_contactpersoon_%s.text()); \
          # ~ ContGegBron.append(self.ui.cbx_Rol_bron_contactpersoon_%s.currentText()); \
          # ~ self.ContGegBron.append(ContGegBron)""" %(num, num, num, num, num, num, num))
      # ~ else:
        # ~ # lees de self.ContGegBron list opnieuw in
        # ~ exec('self.ContGegBron[%s-1][0] = self.ui.le_Email_bron_%s.text()' %(num, num))
        # ~ exec('self.ContGegBron[%s-1][1] = self.ui.cbx_Rol_bron_%s.currentText()' %(num, num))
        # ~ exec('self.ContGegBron[%s-1][2] = self.ui.le_bron_naam_%s.text()' %(num, num))
        # ~ exec('self.ContGegBron[%s-1][3] = self.ui.le_bron_website_%s.text()' %(num, num))
        # ~ exec('self.ContGegBron[%s-1][4] = self.ui.le_bron_contactpersoon_%s.text()' %(num, num))
        # ~ exec('self.ContGegBron[%s-1][5] = self.ui.cbx_Rol_bron_contactpersoon_%s.currentText()' %(num, num))
    # ~ # pas eventueel de structuur aan
    # ~ if lenContGegBron == len(self.ContGegBron):
      # ~ self.structuur_contactgegevens(lenContGegBron+1, 'bron')
      # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
      # ~ exec('self.ui.le_Email_bron_%s.returnPressed.connect(self.aanpassen_bron_contactgegevens)' %(lenContGegBron+1))
    # ~ # vul de bron contact gevens opnieuw 
    # ~ for num in range(len(self.ContGegBron)): self.vul_bron_contactgegevens(num+1)

  # ~ def aanpassen_metadata_contactgegevens(self):
    # ~ """
    # ~ """
    # ~ # lees de lengte van de list plus één extra
    # ~ lenContGegMetadata = len(self.ContGegMetadata)+1
    # ~ # lees de aangepaste gegevens uit
    # ~ for num in range(lenContGegMetadata):
      # ~ num += 1
      # ~ # als er zich een email adres in de keys van contacten bevind lees dan de gegevens uit het csv bestand
      # ~ exec("""if self.ui.le_Email_metadata_%s.text().lower().strip() in self.csv_dict.keys() and not self.ui.le_metadata_naam_%s.text() \
      # ~ and not self.ui.le_metadata_website_%s.text() and not self.ui.le_metadata_contactpersoon_%s.text(): \
      # ~ self.ui.le_metadata_naam_%s.setText(self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][2]); \
      # ~ self.ui.le_metadata_contactpersoon_%s.setText(self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][1]); \
      # ~ self.ui.le_metadata_website_%s.setText(self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][10]); \
      # ~ """ %(num, num, num, num, num, num, num, num, num, num))
      # ~ # als het laatste veld is
      # ~ if num == lenContGegMetadata:
        # ~ # vul de combobox 'cbx_Rol_metadata_' en geef de voorkeur aan
        # ~ A3CodeLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
        # ~ exec('if self.ui.le_Email_metadata_%s.text(): self.ui.cbx_Rol_metadata_%s.addItems(A3CodeLijst)' %(num, num))
        # ~ # vul de combobox 'Rol_metadata_contactpersoon_'en geef de voorkeur aan
        # ~ exec('if self.ui.le_Email_metadata_%s.text(): self.ui.cbx_Rol_metadata_contactpersoon_%s.addItems(self.eigenlijsten["Rollen"])' %(num, num))
        # ~ exec("""if self.ui.le_Email_metadata_%s.text() and self.eigenlijsten["Voorkeuren"]["cbx_Rol_metadata"] in A3CodeLijst: \
          # ~ self.ui.cbx_Rol_metadata_%s.setCurrentIndex(A3CodeLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_metadata"]))""" %(num, num)) 
        # ~ exec("""if self.ui.le_Email_metadata_%s.text() and self.eigenlijsten['Voorkeuren']['cbx_Rol_metadata_contactpersoon'] in self.eigenlijsten['Rollen']: \
          # ~ self.ui.cbx_Rol_metadata_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_metadata_contactpersoon"])); \
          # ~ """ %(num, num))
        # ~ exec("""if self.ui.le_Email_metadata_%s.text(): \
          # ~ ContGegMetadata = []; \
          # ~ ContGegMetadata.append(self.ui.le_Email_metadata_%s.text()); \
          # ~ ContGegMetadata.append(self.ui.cbx_Rol_metadata_%s.currentText()); \
          # ~ ContGegMetadata.append(self.ui.le_metadata_naam_%s.text()); \
          # ~ ContGegMetadata.append(self.ui.le_metadata_website_%s.text()); \
          # ~ ContGegMetadata.append(self.ui.le_metadata_contactpersoon_%s.text()); \
          # ~ ContGegMetadata.append(self.ui.cbx_Rol_metadata_contactpersoon_%s.currentText()); \
          # ~ self.ContGegMetadata.append(ContGegMetadata)""" %(num, num, num, num, num, num, num))
      # ~ else:
        # ~ # lees de self.ContGegMetadata list opnieuw in
        # ~ exec('self.ContGegMetadata[%s-1][0] = self.ui.le_Email_metadata_%s.text()' %(num, num))
        # ~ exec('self.ContGegMetadata[%s-1][1] = self.ui.cbx_Rol_metadata_%s.currentText()' %(num, num))
        # ~ exec('self.ContGegMetadata[%s-1][2] = self.ui.le_metadata_naam_%s.text()' %(num, num))
        # ~ exec('self.ContGegMetadata[%s-1][3] = self.ui.le_metadata_website_%s.text()' %(num, num))
        # ~ exec('self.ContGegMetadata[%s-1][4] = self.ui.le_metadata_contactpersoon_%s.text()' %(num, num))
        # ~ exec('self.ContGegMetadata[%s-1][5] = self.ui.cbx_Rol_metadata_contactpersoon_%s.currentText()' %(num, num))
    # ~ # pas eventueel de structuur aan
    # ~ if lenContGegMetadata == len(self.ContGegMetadata):
      # ~ self.structuur_contactgegevens(lenContGegMetadata+1, 'metadata')
      # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
      # ~ exec('self.ui.le_Email_metadata_%s.returnPressed.connect(self.aanpassen_metadata_contactgegevens)' %(lenContGegMetadata+1))
    # ~ # vul de metadata contact gevens opnieuw 
    # ~ for num in range(len(self.ContGegMetadata)): self.vul_metadata_contactgegevens(num+1)

  # ~ def aanpassen_distributie_contactgegevens(self):
    # ~ """
    # ~ """
    # ~ # lees de lengte van de list plus één extra
    # ~ lenContGegDistributie = len(self.ContGegDistributie)+1
    # ~ # lees de aangepaste gegevens uit
    # ~ for num in range(lenContGegDistributie):
      # ~ num += 1
      # ~ # als er zich een email adres in de keys van contacten bevind lees dan de gegevens uit het csv bestand
      # ~ exec("""if self.ui.le_Email_distributie_%s.text().lower().strip() in self.csv_dict.keys() and not self.ui.le_distributie_naam_%s.text() \
      # ~ and not self.ui.le_distributie_website_%s.text() and not self.ui.le_distributie_contactpersoon_%s.text(): \
      # ~ self.ui.le_distributie_naam_%s.setText(self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][2]); \
      # ~ self.ui.le_distributie_contactpersoon_%s.setText(self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][1]); \
      # ~ self.ui.le_distributie_website_%s.setText(self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][10]); \
      # ~ """ %(num, num, num, num, num, num, num, num, num, num))
      # ~ # als het laatste veld is
      # ~ if num == lenContGegDistributie:
        # ~ # vul de combobox 'cbx_Rol_distributie_' en geef de voorkeur aan
        # ~ A3CodeLijst = [self.codelijsten["A.3 Codelijst CI_RoleCode"][index][0] for index in range(len(self.codelijsten["A.3 Codelijst CI_RoleCode"]))]
        # ~ exec('if self.ui.le_Email_distributie_%s.text(): self.ui.cbx_Rol_distributie_%s.addItems(A3CodeLijst)' %(num, num))
        # ~ # vul de combobox 'Rol_distributie_contactpersoon_'en geef de voorkeur aan
        # ~ exec('if self.ui.le_Email_distributie_%s.text(): self.ui.cbx_Rol_distributie_contactpersoon_%s.addItems(self.eigenlijsten["Rollen"])' %(num, num))
        # ~ exec("""if self.ui.le_Email_distributie_%s.text() and self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie"] in A3CodeLijst: \
          # ~ self.ui.cbx_Rol_distributie_%s.setCurrentIndex(A3CodeLijst.index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie"]))""" %(num, num)) 
        # ~ exec("""if self.ui.le_Email_distributie_%s.text() and self.eigenlijsten['Voorkeuren']['cbx_Rol_distributie_contactpersoon'] in self.eigenlijsten['Rollen']: \
          # ~ self.ui.cbx_Rol_distributie_contactpersoon_%s.setCurrentIndex(self.eigenlijsten["Rollen"].index(self.eigenlijsten["Voorkeuren"]["cbx_Rol_distributie_contactpersoon"])); \
          # ~ """ %(num, num))
        # ~ exec("""if self.ui.le_Email_distributie_%s.text(): \
          # ~ ContGegDistributie = []; \
          # ~ ContGegDistributie.append(self.ui.le_Email_distributie_%s.text()); \
          # ~ ContGegDistributie.append(self.ui.cbx_Rol_distributie_%s.currentText()); \
          # ~ ContGegDistributie.append(self.ui.le_distributie_naam_%s.text()); \
          # ~ ContGegDistributie.append(self.ui.le_distributie_website_%s.text()); \
          # ~ ContGegDistributie.append(self.ui.le_distributie_contactpersoon_%s.text()); \
          # ~ ContGegDistributie.append(self.ui.cbx_Rol_distributie_contactpersoon_%s.currentText()); \
          # ~ self.ContGegDistributie.append(ContGegDistributie)""" %(num, num, num, num, num, num, num))
      # ~ else:
        # ~ # lees de self.ContGegDistributie list opnieuw in
        # ~ exec('self.ContGegDistributie[%s-1][0] = self.ui.le_Email_distributie_%s.text()' %(num, num))
        # ~ exec('self.ContGegDistributie[%s-1][1] = self.ui.cbx_Rol_distributie_%s.currentText()' %(num, num))
        # ~ exec('self.ContGegDistributie[%s-1][2] = self.ui.le_distributie_naam_%s.text()' %(num, num))
        # ~ exec('self.ContGegDistributie[%s-1][3] = self.ui.le_distributie_website_%s.text()' %(num, num))
        # ~ exec('self.ContGegDistributie[%s-1][4] = self.ui.le_distributie_contactpersoon_%s.text()' %(num, num))
        # ~ exec('self.ContGegDistributie[%s-1][5] = self.ui.cbx_Rol_distributie_contactpersoon_%s.currentText()' %(num, num))
    # ~ # pas eventueel de structuur aan
    # ~ if lenContGegDistributie == len(self.ContGegDistributie):
      # ~ self.structuur_contactgegevens(lenContGegDistributie+1, 'distributie')
      # ~ # als in de URL op enter wordt gedrukt start dan de functie vulaan_URL_gegevens
      # ~ exec('self.ui.le_Email_distributie_%s.returnPressed.connect(self.aanpassen_distributie_contactgegevens)' %(lenContGegDistributie+1))
    # ~ # vul de distributie contact gevens opnieuw 
    # ~ for num in range(len(self.ContGegDistributie)): self.vul_distributie_contactgegevens(num+1)

  # ~ def beheer_email_change(self, index):
    # ~ # als er iets aan de combobox gewijzigd is verander dan de inhoud
    # ~ if index >= 1:
      # ~ self.ui.le_beheer_contactpersoon.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][1]))
      # ~ self.ui.le_beheer_organisatie.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][2]))
      # ~ self.ui.le_beheer_adres.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][3]))
      # ~ self.ui.le_beheer_postcode.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][4]))
      # ~ self.ui.le_beheer_plaats.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][5]))
      # ~ self.ui.le_beheer_provincie.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][6]))
      # ~ self.ui.le_beheer_land.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][7]))
      # ~ self.ui.le_beheer_telefoon.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][8]))
      # ~ self.ui.le_beheer_fax.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][9]))
      # ~ self.ui.le_beheer_email.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][0]))
      # ~ self.ui.le_beheer_URL.setText("%s" %(self.csv_dict[list(self.csv_dict.keys())[index-1]][10]))
    # ~ # bij een nieuwe, maak alles leeg
    # ~ else:
      # ~ self.ui.le_beheer_contactpersoon.setText("")
      # ~ self.ui.le_beheer_organisatie.setText("")
      # ~ self.ui.le_beheer_adres.setText("")
      # ~ self.ui.le_beheer_postcode.setText("")
      # ~ self.ui.le_beheer_plaats.setText("")
      # ~ self.ui.le_beheer_provincie.setText("")
      # ~ self.ui.le_beheer_land.setText("")
      # ~ self.ui.le_beheer_telefoon.setText("")
      # ~ self.ui.le_beheer_fax.setText("")
      # ~ self.ui.le_beheer_email.setText("")
      # ~ self.ui.le_beheer_URL.setText("")

  # ~ def opslag_contactgegevens(self):
    # ~ # sla de contact gegevens op in het contact_gegevens.csv bestand
    # ~ csv_bestand = self.eigenlijsten["dirs"]["csv_dir"]+os.sep+"Metadata_Master.csv" 
    # ~ # open de contact gegevens
    # ~ with open(csv_bestand, 'r') as csvfile: csv_regels = csvfile.readlines()
    # ~ # bepaal de te vervangen regel
    # ~ regel = '%s;' %(self.ui.le_beheer_email.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_contactpersoon.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_organisatie.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_adres.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_postcode.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_plaats.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_provincie.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_land.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_telefoon.text())
    # ~ regel += '%s;' %(self.ui.le_beheer_fax.text())
    # ~ regel += '%s' %(self.ui.le_beheer_URL.text())
    # ~ # voeg de nieuwe toe
    # ~ if self.ui.cbx_beheer_email.currentText() == 'nieuw': csv_regels.append(regel+'\n')
    # ~ # of vervang de bestaande
    # ~ else: 
      # ~ QtWidgets.QMessageBox.warning(None, None, "%s" %(regel)) 
      # ~ csv_regels[list(self.csv_dict.keys()).index(self.ui.cbx_beheer_email.currentText())+1] = regel+'\n'
    # ~ # schrijf het bestand weg
    # ~ with open(csv_bestand, 'w') as csvfile: 
      # ~ for csv_regel in csv_regels: csvfile.writelines(csv_regel)
    # ~ # open de contact gegevens en vul de verschillende variabelen opnieuw
    # ~ with open(csv_bestand, 'r') as csvfile: csv_regels = csvfile.readlines()
    # ~ # maak een lege dictionarie
    # ~ self.csv_dict = {}
    # ~ # genereer een list uit de lines
    # ~ csv_list = [csv_regel.strip().split(self.sep) for csv_regel in csv_regels]
    # ~ # vul de dictionarie met keys in kleine letters
    # ~ for csv in csv_list[1:]: self.csv_dict[csv[0].lower()] = csv
    # ~ # vul de combobox beheer email
    # ~ contactbeheerlijst = ['nieuw']
    # ~ contactbeheerlijst.extend(self.csv_dict.keys())
    # ~ self.ui.cbx_beheer_email.clear()
    # ~ self.ui.cbx_beheer_email.addItems(contactbeheerlijst)

  # ~ def leesXML(self):
    # ~ """
    # ~ Lees de xml met metadata uit en plaats de gegevens in de Metadata Editor
    
    # ~ https://sites.google.com/site/bmaupinwiki/home/programming/python/python-xml-lxml
    # ~ """ 
    # ~ # plak .xml achter de xml_naam
    # ~ self.xml_naam = os.path.splitext(self.xml_naam)[0]+'.xml'
    # ~ # lees de namespaces    
    # ~ namespaces = self.eigenlijsten["namespaces"]
    # ~ gmd = namespaces['gmd']
    # ~ gco = namespaces['gco']
    # ~ gmx = namespaces['gmx']
    # ~ gml = namespaces['gml']
    # ~ xlink = namespaces['xlink']
    # ~ # als de xml bestaat
    # ~ if os.path.isfile(self.xml_map+os.sep+self.xml_naam):
      # ~ # parse de xml
      # ~ xmldoc = etree.parse(self.xml_map+os.sep+self.xml_naam)
      # ~ # lees de metadata indentifier
      # ~ metadataUUID = xmldoc.findtext('//{%s}fileIdentifier/{%s}CharacterString' %(gmd, gco))
      # ~ # als de metadata UUID bestaat vul dan self.ui.le_Metadata_uuid
      # ~ if metadataUUID: self.ui.le_Metadata_uuid.setText(metadataUUID)
      # ~ # lees de taal van de metadata
      # ~ self.metadataTaal = xmldoc.findtext('//{%s}language/{%s}LanguageCode' %(gmd, gmd))
      # ~ # zet de uitgelezen waarde om naar een leesbare uit de codelijst
      # ~ self.metadataTaal = [item[0] for item in self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"] if item[1] == self.metadataTaal][0]
      # ~ # lees de karakterset van de metadata uit de xml
      # ~ self.metadataKarakterSet = xmldoc.find('//{%s}characterSet/{%s}MD_CharacterSetCode'%(gmd, gmd)).get('codeListValue')
      # ~ # lees het hiërarchieniveau uit de xml
      # ~ self.hierarchieniveau = xmldoc.find('//{%s}hierarchyLevel/{%s}MD_ScopeCode' %(gmd, gmd)).get('codeListValue')
      # ~ # lees het hiërarchieniveau naam uit de xml
      # ~ hierarchieniveaunaam = xmldoc.findtext('//{%s}hierarchyLevelname/{%s}CharacterString' %(gmd, gco))
      # ~ # als de hierarchieniveaunaam bestaat vul dan self.ui.le_hierachieniveau_naam
      # ~ if hierarchieniveaunaam: self.ui.le_hierachieniveau_naam.setText(hierarchieniveaunaam)
      # ~ # verantwoordelijke organisatie metadata e-mail
      # ~ self.ContGegMetadata = []
      # ~ metadataEmails = xmldoc.findall('//{%s}contact/{%s}CI_ResponsibleParty/{%s}contactInfo/{%s}CI_Contact/{%s}address/{%s}CI_Address/{%s}electronicMailAddress/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ metadataEmails = [metadataEmail.text for metadataEmail in metadataEmails]
      # ~ for teller, metadataEmail in list(enumerate(metadataEmails, start=1)):
        # ~ ContGegMetadata = []
        # ~ ContGegMetadata.append(metadataEmail)
        # ~ # verantwoordelijke organisatie metadata rol
        # ~ rolOrganisatie = xmldoc.find('//{%s}contact[%s]/{%s}CI_ResponsibleParty/{%s}role/{%s}CI_RoleCode' %(gmd, teller, gmd, gmd, gmd)).get('codeListValue')
        # ~ if rolOrganisatie: ContGegMetadata.append(rolOrganisatie)
        # ~ else: ContGegMetadata.append(None)
        # ~ # verantwoordelijke organisatie metadata
        # ~ naamOrganisatieMetadata = xmldoc.findtext('//{%s}contact[%s]/{%s}CI_ResponsibleParty/{%s}organisationName/{%s}CharacterString' %(gmd, teller, gmd, gmd, gco))
        # ~ if naamOrganisatieMetadata: ContGegMetadata.append(naamOrganisatieMetadata)
        # ~ else: ContGegMetadata.append(None)
        # ~ # verantwoordelijke organisatie metadata URL
        # ~ URLOrganisatieMetadata = xmldoc.findtext('//{%s}contact[%s]/{%s}CI_ResponsibleParty/{%s}contactInfo/{%s}CI_Contact/{%s}onlineResource/{%s}CI_OnlineResource/{%s}linkage/{%s}URL' %(gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
        # ~ if URLOrganisatieMetadata: ContGegMetadata.append(URLOrganisatieMetadata)
        # ~ else: ContGegMetadata.append(None)
        # ~ # naam contactpersoon metadata
        # ~ naamContactMetadata = xmldoc.findtext('//{%s}contact[%s]/{%s}CI_ResponsibleParty/{%s}individualName/{%s}CharacterString' %(gmd, teller, gmd, gmd, gco))
        # ~ if naamContactMetadata: ContGegMetadata.append(naamContactMetadata)
        # ~ else: ContGegMetadata.append(None)
        # ~ # rol contactpersoon metadata
        # ~ rolContactMetadata = xmldoc.findtext('//{%s}contact[%s]/{%s}CI_ResponsibleParty/{%s}positionName/{%s}CharacterString' %(gmd, teller, gmd, gmd, gco))
        # ~ if rolContactMetadata: ContGegMetadata.append(rolContactMetadata)
        # ~ else: ContGegMetadata.append(None)
        # ~ self.ContGegMetadata.append(ContGegMetadata)
      # ~ # lees de datumStamp uit
      # ~ self.datumStamp = xmldoc.findtext('//{%s}dateStamp/{%s}Date' %(gmd, gco))
      # ~ # lees de ruimtelijke referentie systemen
      # ~ rrs = xmldoc.findall('//{%s}referenceSystemInfo/{%s}MD_ReferenceSystem/{%s}referenceSystemIdentifier/{%s}RS_Identifier/{%s}code/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ # maak een leesbare list (alleen epsg codes) van de uitkomst
      # ~ rrs_list = [item.text.split('/')[-1] for item in rrs]
      # ~ # als de lengte van de list groter als 1 is vul self.ui.le_horizontaal_referentiesysteem
      # ~ if len(rrs_list) >= 1: self.ui.le_horizontaal_referentiesysteem.setText(rrs_list[0])
      # ~ # als de lengte van de list 2 is vul dan self.verticaal_referentiesysteem
      # ~ if len(rrs_list) == 2: self.verticaal_referentiesysteem = rrs_list[1]
      # ~ # lees de titel van de bron
      # ~ titelbron = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}title/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ # als de titel van de bron bestaat vul self.ui.le_TitelBron
      # ~ if titelbron: self.ui.le_TitelBron.setText(titelbron)
      # ~ # als de alternative titel bestaat vul dan self.ui.le_AlternatieveTitel
      # ~ alternatieveTitel = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}alternateTitle/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if alternatieveTitel: self.ui.le_AlternatieveTitel.setText(alternatieveTitel)
      # ~ # lees de bron datums uit
      # ~ bron_datums = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}date/{%s}Date' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ bron_datums_list = [item.text for item in bron_datums]
      # ~ # lees het bron datum type uit
      # ~ bron_datum_types = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}dateType/{%s}CI_DateTypeCode' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ bron_datum_types_list = [item.get('codeListValue') for item in bron_datum_types]
      # ~ # maak van de list een dictionairy
      # ~ bron_datums_dict = dict(zip(bron_datum_types_list, bron_datums_list)) 
      # ~ # vul de creatie datum
      # ~ if 'creation' in bron_datums_dict.keys():
        # ~ creatie = bron_datums_dict['creation'].split('-')
        # ~ self.ui.de_Creatiedatum.setDate(QtCore.QDate(int(creatie[0]), int(creatie[1]), int(creatie[-1])))
      # ~ # vul de publicatie datum
      # ~ if 'publication' in bron_datums_dict.keys(): 
        # ~ publicatie = bron_datums_dict['publication'].split('-')
        # ~ self.ui.de_Publicatiedatum.setDate(QtCore.QDate(int(publicatie[0]), int(publicatie[1]), int(publicatie[-1])))
      # ~ # vul de revisie datum
      # ~ if 'revision' in bron_datums_dict.keys():
        # ~ revisie = bron_datums_dict['revision'].split('-')
        # ~ self.ui.de_Revisiedatum.setDate(QtCore.QDate(int(revisie[0]), int(revisie[1]), int(revisie[-1])))
      # ~ # vul het versie nummer
      # ~ versienummer = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}edition/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if versienummer: self.ui.le_Versie.setText(versienummer)
      # ~ # vul de bron UUID
      # ~ bronUUID = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}identifier/{%s}MD_Identifier/{%s}code/{%s}CharacterString'%(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if bronUUID: self.ui.le_uuid.setText(bronUUID)
      # ~ # vul de serie/afgeleide data set
      # ~ afgeleideDataset = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}citation/{%s}CI_Citation/{%s}series/{%s}CI_Series/{%s}name/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if afgeleideDataset: self.ui.le_Serienaamnummer.setText(afgeleideDataset)
      # ~ # vul de samenvatting
      # ~ samenvatting = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}abstract/{%s}CharacterString' %(gmd, gmd, gmd, gco))
      # ~ if samenvatting: self.ui.te_Samenvatting.setText(samenvatting)
      # ~ # vul doel van vervaardiging
      # ~ doelVervaardiging = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}purpose/{%s}CharacterString' %(gmd, gmd, gmd, gco))
      # ~ if doelVervaardiging: self.ui.te_Doel_vervaardiging.setText(doelVervaardiging)
      # ~ # lees de status
      # ~ self.status = xmldoc.find('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}status/{%s}MD_ProgressCode' %(gmd, gmd, gmd, gmd)).get('codeListValue')
      # ~ # verantwoordelijke organisatie bron e-mail
      # ~ self.ContGegBron = []
      # ~ bronEmails = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}pointOfContact/{%s}CI_ResponsibleParty/{%s}contactInfo/{%s}CI_Contact/{%s}address/{%s}CI_Address/{%s}electronicMailAddress/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ bronEmails = [bronEmail.text for bronEmail in bronEmails]
      # ~ for teller, bronEmail in list(enumerate(bronEmails, start=1)):
        # ~ ContGegBron = []
        # ~ ContGegBron.append(bronEmail)
        # ~ # verantwoordelijke bron organisatie rol
        # ~ rolBronOrganisatie = xmldoc.find('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}pointOfContact[%s]/{%s}CI_ResponsibleParty/{%s}role/{%s}CI_RoleCode' %(gmd, gmd, gmd, teller, gmd, gmd, gmd)).get('codeListValue')
        # ~ if rolBronOrganisatie: ContGegBron.append(rolBronOrganisatie)
        # ~ else: ContGegBron.append(None)
        # ~ # verantwoordelijke organisatie bron
        # ~ naamOrganisatieBron = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}pointOfContact[%s]/{%s}CI_ResponsibleParty/{%s}organisationName/{%s}CharacterString' %(gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if naamOrganisatieBron: ContGegBron.append(naamOrganisatieBron)
        # ~ else: ContGegBron.append(None)
        # ~ # verantwoordelijke organisatie bron URL
        # ~ URLOrganisatieBron = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}pointOfContact[%s]/{%s}CI_ResponsibleParty/{%s}contactInfo/{%s}CI_Contact/{%s}onlineResource/{%s}CI_OnlineResource/{%s}linkage/{%s}URL' %(gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
        # ~ if URLOrganisatieBron: ContGegBron.append(URLOrganisatieBron)
        # ~ else: ContGegBron.append(None)
        # ~ # naam contactpersoon bron
        # ~ naamContactBron = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}pointOfContact[%s]/{%s}CI_ResponsibleParty/{%s}individualName/{%s}CharacterString' %(gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if naamContactBron: ContGegBron.append(naamContactBron)
        # ~ else: ContGegBron.append(None)
        # ~ # rol contactpersoon bron
        # ~ rolContactBron = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}pointOfContact[%s]/{%s}CI_ResponsibleParty/{%s}positionName/{%s}CharacterString' %(gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if rolContactBron: ContGegBron.append(rolContactBron)
        # ~ else: ContGegBron.append(None)
        # ~ self.ContGegBron.append(ContGegBron)
      # ~ # herzieningsfrequentie
      # ~ self.herzieningsFrequentie = xmldoc.find('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceMaintenance/{%s}MD_MaintenanceInformation/{%s}maintenanceAndUpdateFrequency/{%s}MD_MaintenanceFrequencyCode' %(gmd, gmd, gmd, gmd, gmd, gmd)).get('codeListValue')
      # ~ # datum volgende herziening
      # ~ self.datumHerziening = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceMaintenance/{%s}MD_MaintenanceInformation/{%s}dateOfNextUpdate/{%s}Date' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ # voorbeeld; als het voorbeeld bestaat vul dan het image
      # ~ voorbeeld = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}graphicOverview/{%s}MD_BrowseGraphic/{%s}fileName/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if voorbeeld: 
        # ~ self.ui.le_Voorbeeld.setText(voorbeeld)
        # ~ self.vul_image()
      # ~ # vul de thesaurus gegevens uit de xml de datum en datum type worden uit ME_19115_200.cfg gelezen
      # ~ thesaurusnamen = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}descriptiveKeywords/{%s}MD_Keywords/{%s}thesaurusName/{%s}CI_Citation/{%s}title/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ thesaurusnamen = [naam.text for naam in thesaurusnamen]
      # ~ for teller, thesaurusnaam in list(enumerate(thesaurusnamen, start=1)):
        # ~ trefwoorden = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}descriptiveKeywords[%s]/{%s}MD_Keywords/{%s}keyword/{%s}CharacterString' %(gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ self.trefwoorden_dict[thesaurusnaam] = [trefwoord.text for trefwoord in trefwoorden]
      # ~ # gebruiksbeperkingen
      # ~ gebruiksbeperkingen = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceConstraints/{%s}MD_Constraints/{%s}useLimitation/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ self.checkbox_dict['gebruiksbeperkingen'] = [gebruiksbeperking.text for gebruiksbeperking in gebruiksbeperkingen]
      # ~ # toegangsrestricties
      # ~ toegangsrestricties = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceConstraints/{%s}MD_LegalConstraints/{%s}accessConstraints/{%s}MD_RestrictionCode' %(gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ self.checkbox_dict['toegangsrestricties'] = [toegangsrestrictie.get('codeListValue') for toegangsrestrictie in toegangsrestricties]
      # ~ # gebruiksrestricties
      # ~ gebruiksrestricties = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceConstraints/{%s}MD_LegalConstraints/{%s}useConstraints/{%s}MD_RestrictionCode' %(gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ self.checkbox_dict['gebruiksrestricties'] = [gebruiksrestrictie.get('codeListValue') for gebruiksrestrictie in gebruiksrestricties]
      # ~ # overige beperkingen 
      # ~ overigeBeperkingen = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceConstraints/{%s}MD_LegalConstraints/{%s}otherConstraints/{%s}Anchor'  %(gmd, gmd, gmd, gmd, gmd, gmx))
      # ~ overigeBeperkingen = [overigeBeperking.get('{%s}href' %(xlink)) for overigeBeperking in overigeBeperkingen]
      # ~ # overige beperkingen 'datalicenties'
      # ~ self.checkbox_dict['datalicenties'] = [licentie[1] for licentie in self.codelijsten['A.20 Codelijst data licenties'] if licentie[0] in overigeBeperkingen]
      # ~ # overige beperkingen 'gebruikscondities'
      # ~ self.checkbox_dict['gebruikscondities'] = [conditie[1] for conditie in self.codelijsten['A.15 Codelijst INSPIRE ConditionsApplyingToAccessAndUse'] if conditie[0] in overigeBeperkingen]
      # ~ # overige beperkingen 'publieketoegang'
      # ~ self.checkbox_dict['publieketoegang'] = [toegang[1] for toegang in self.codelijsten['A.16 Codelijst INSPIRE LimitationsOnPublicAccess'] if toegang[0] in overigeBeperkingen]
      # ~ # veiligheidsrestricties
      # ~ veiligheidsrestricties = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceConstraints/{%s}MD_SecurityConstraints/{%s}classification/{%s}MD_ClassificationCode'  %(gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ self.checkbox_dict['veiligheidsrestricties'] = [veiligheidsrestrictie.get('codeListValue') for veiligheidsrestrictie in veiligheidsrestricties]
      # ~ # toelichting veiligheidsrestricties
      # ~ toelichtingVR = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}resourceConstraints/{%s}MD_SecurityConstraints/{%s}userNote/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if toelichtingVR: self.ui.le_veiligheidsrestricties.setText(toelichtingVR)
      # ~ # naam gerelateerde dataset
      # ~ gerelateerdeTitels = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}aggregationInfo/{%s}MD_AggregateInformation/{%s}aggregateDataSetName/{%s}CI_Citation/{%s}title/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ gerelateerdeTitels = [gerelateerdeTitel.text for gerelateerdeTitel in gerelateerdeTitels]
      # ~ for teller, gerelateerdeTitel in list(enumerate(gerelateerdeTitels, start=1)):
        # ~ exec('self.ui.le_gerelateerde_dataset_%s.setText("%s")' %(teller, gerelateerdeTitel))
        # ~ # datum gerelateerde dataset
        # ~ gerelateerdeDatum = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}aggregationInfo[%s]/{%s}MD_AggregateInformation/{%s}aggregateDataSetName/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}date/{%s}Date' %(gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gco))
        # ~ if gerelateerdeDatum and gerelateerdeDatum is not None:
          # ~ grd_list = gerelateerdeDatum.split('-')
          # ~ exec('self.ui.de_gd_Datum_%s.setDate(QtCore.QDate(int("%s"), int("%s"), int("%s")))' %(teller, grd_list[0], grd_list[1], grd_list[-1]))      
        # ~ # datum type gerelateerde dataset
        # ~ gerelateerdeDatumType = xmldoc.find('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}aggregationInfo[%s]/{%s}MD_AggregateInformation/{%s}aggregateDataSetName/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}dateType/{%s}CI_DateTypeCode' %(gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gmd)).get('codeListValue')
        # ~ if gerelateerdeDatumType and gerelateerdeDatumType is not None: 
          # ~ exec('self.gerelateerdeDatumType_%s = "%s"' %(teller, gerelateerdeDatumType))
      # ~ # ruimtelijk schema
      # ~ self.ruimtelijkSchema = xmldoc.find('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}spatialRepresentationType/{%s}MD_SpatialRepresentationTypeCode' %(gmd, gmd, gmd, gmd,)).get('codeListValue')
      # ~ # toepassingsschaal
      # ~ toepassingsschalen = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}spatialResolution/{%s}MD_Resolution/{%s}equivalentScale/{%s}MD_RepresentativeFraction/{%s}denominator/{%s}Integer' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ toepassingsschalen = [toepassingsschaal.text for toepassingsschaal in toepassingsschalen]
      # ~ if len(toepassingsschalen) >= 1: self.ui.le_Toepassingsschaal_01.setText(toepassingsschalen[0])
      # ~ if len(toepassingsschalen) >= 2: self.ui.le_Toepassingsschaal_02.setText(toepassingsschalen[1])
      # ~ # resolutie
      # ~ resoluties = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}spatialResolution/{%s}MD_Resolution/{%s}distance/{%s}Distance' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ resoluties = [resolutie.text for resolutie in resoluties]
      # ~ if len(resoluties) >= 1: self.ui.le_Resolutie_01.setText(resoluties[0])
      # ~ if len(resoluties) >= 2: self.ui.le_Resolutie_02.setText(resoluties[1])
      # ~ # taal van de bron
      # ~ bronTaal = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}language/{%s}LanguageCode' %(gmd, gmd, gmd, gmd))
      # ~ self.bronTaal = [item[0] for item in self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"] if item[1] == bronTaal][0]
      # ~ # karakterset van de bron
      # ~ self.bronKarakterset = xmldoc.find('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}characterSet/{%s}MD_CharacterSetCode' %(gmd, gmd, gmd, gmd)).get('codeListValue')
      # ~ # onderwerpen
      # ~ onderwerpen = xmldoc.findall('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}topicCategory/{%s}MD_TopicCategoryCode' %(gmd, gmd, gmd, gmd))
      # ~ self.checkbox_dict['onderwerpen'] = [onderwerp.text for onderwerp in onderwerpen]
      # ~ # beschrijving temporele dekking
      # ~ temporeleDekking = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}description/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if temporeleDekking: self.ui.te_temporele_dekking.setText(temporeleDekking)
      # ~ # lees de bounding box uit
      # ~ min_X = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}geographicElement/{%s}EX_GeographicBoundingBox/{%s}westBoundLongitude/{%s}Decimal' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ self.ui.le_min_X.setText(min_X)
      # ~ max_X = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}geographicElement/{%s}EX_GeographicBoundingBox/{%s}eastBoundLongitude/{%s}Decimal' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ self.ui.le_max_X.setText(max_X)
      # ~ min_Y = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}geographicElement/{%s}EX_GeographicBoundingBox/{%s}southBoundLatitude/{%s}Decimal' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ self.ui.le_min_Y.setText(min_Y)
      # ~ max_Y = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}geographicElement/{%s}EX_GeographicBoundingBox/{%s}northBoundLatitude/{%s}Decimal' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ self.ui.le_max_Y.setText(max_Y)
      # ~ # geografisch gebied
      # ~ geografischGebied = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}geographicElement/{%s}EX_GeographicDescription/{%s}geographicIdentifier/{%s}MD_Identifier/{%s}code/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if geografischGebied: self.ui.le_naam_geo_gebied.setText(geografischGebied)
      # ~ # temporele dekking datums
      # ~ temporeleDatum_01 = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}temporalElement/{%s}EX_TemporalExtent/{%s}extent/{%s}TimePeriod/{%s}begin/{%s}TimeInstant/{%s}timePosition' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gml, gml, gml, gml))
      # ~ if temporeleDatum_01: self.ui.de_temp_dekking_van.setDate(QtCore.QDate.fromString(temporeleDatum_01, "yyyy-MM-dd"))
      # ~ temporeleDatum_02 = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}temporalElement/{%s}EX_TemporalExtent/{%s}extent/{%s}TimePeriod/{%s}end/{%s}TimeInstant/{%s}timePosition' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gml, gml, gml, gml))
      # ~ if temporeleDatum_02:self.ui.de_temp_dekking_tot.setDate(QtCore.QDate.fromString(temporeleDatum_02, "yyyy-MM-dd"))
      # ~ # minimum Z-coördinaat
      # ~ min_Z = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}verticalElement/{%s}EX_VerticalExtent/{%s}minimumValue/{%s}Real' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if min_Z: self.ui.le_min_Z.setText(min_Z)
      # ~ # maximum Z-coördinaat
      # ~ max_Z = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}extent/{%s}EX_Extent/{%s}verticalElement/{%s}EX_VerticalExtent/{%s}maximumValue/{%s}Real' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if max_Z: self.ui.le_max_Z.setText(max_Z)
      # ~ # aanvullende informatie
      # ~ aanvullendeInfo = xmldoc.findtext('//{%s}identificationInfo/{%s}MD_DataIdentification/{%s}supplementalInformation/{%s}CharacterString' %(gmd, gmd, gmd, gco))
      # ~ if aanvullendeInfo: self.ui.le_Aanvullende_informatie.setText(aanvullendeInfo)
      # ~ # feature types
      # ~ self.featureTypes = xmldoc.findtext('//{%s}contentInfo/{%s}MD_FeatureCatalogueDescription/{%s}featureTypes/{%s}LocalName' %(gmd, gmd, gmd, gco))
      # ~ # featurecatalog Titel
      # ~ featurecatalogTitel =  xmldoc.findtext('//{%s}contentInfo/{%s}MD_FeatureCatalogueDescription/{%s}featureCatalogueCitation/{%s}CI_Citation/{%s}title/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if featurecatalogTitel: self.ui.le_titel_attribuutgegevens.setText(featurecatalogTitel)
      # ~ # featurecatalog datum
      # ~ featurecatalogDatum =  xmldoc.findtext('//{%s}contentInfo/{%s}MD_FeatureCatalogueDescription/{%s}featureCatalogueCitation/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}date/{%s}Date' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if featurecatalogDatum: self.ui.de_attribuutgegevens_datum.setDate(QtCore.QDate.fromString(featurecatalogDatum, "yyyy-MM-dd"))
       # ~ # featurecatalog type datum
      # ~ featurecatalogTypeDatum = xmldoc.find('//{%s}contentInfo/{%s}MD_FeatureCatalogueDescription/{%s}featureCatalogueCitation/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}date/{%s}dateType/{%s}CI_DateTypeCode' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ if featurecatalogTypeDatum: self.featurecatalogTypeDatum = featurecatalogTypeDatum.get('codeListValue')
      # ~ # featurecatalog UUID
      # ~ featurecatalogUUID =  xmldoc.findtext('//{%s}contentInfo/{%s}MD_FeatureCatalogueDescription/{%s}featureCatalogueCitation/{%s}CI_Citation/{%s}identifier/{%s}MD_Identifier/{%s}code/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if featurecatalogUUID: self.ui.le_uuid_attribuutgegevens.setText(featurecatalogUUID)
      # ~ # distributie formaat
      # ~ distributieFormaten = xmldoc.findall('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributionFormat/{%s}MD_Format/{%s}name/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ distributieFormaten = [distributieFormaat.text for distributieFormaat in distributieFormaten]
      # ~ # loop door de distributie formaten
      # ~ for teller, distributieFormaat in list(enumerate(distributieFormaten, start=1)):
        # ~ exec('self.ui.le_Naam_dist_formaat_%s.setText("%s")' %(teller, distributieFormaat))
        # ~ # versie distributie formaat
        # ~ versieDistFormat = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributionFormat/{%s}MD_Format[%s]/{%s}version/{%s}CharacterString' %(gmd, gmd, gmd, gmd, teller, gmd, gco))
        # ~ if versieDistFormat: exec('self.ui.le_Versie_formaat_%s.setText("%s")' %(teller, versieDistFormat))
        # ~ # specificatie distibutie formaat
        # ~ specsDistFormat = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributionFormat/{%s}MD_Format[%s]/{%s}specification/{%s}CharacterString' %(gmd, gmd, gmd, gmd, teller, gmd, gco))
        # ~ if specsDistFormat: exec('self.ui.le_specificatie_formaat_%s.setText("%s")' %(teller, specsDistFormat))
      # ~ # verantwoordelijke organisatie distributie e-mail
      # ~ self.ContGegDistributie = []
      # ~ distEmails = xmldoc.findall('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributorContact/{%s}CI_ResponsibleParty/{%s}contactInfo/{%s}CI_Contact/{%s}address/{%s}CI_Address/{%s}electronicMailAddress/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ distEmails = [distEmail.text for distEmail in distEmails]
      # ~ for teller, distEmail in list(enumerate(distEmails, start=1)):
        # ~ ContGegDistributie = []
        # ~ ContGegDistributie.append(distEmail)
        # ~ # verantwoordelijke distributie organisatie rol
        # ~ rolOrgDist = xmldoc.find('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributorContact[%s]/{%s}CI_ResponsibleParty/{%s}role/{%s}CI_RoleCode' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd)).get('codeListValue')
        # ~ if rolOrgDist: ContGegDistributie.append(rolOrgDist)
        # ~ else: ContGegDistributie.append(None)
        # ~ # verantwoordelijke organisatie distributie
        # ~ naamOrgDist = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributorContact[%s]/{%s}CI_ResponsibleParty/{%s}organisationName/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if naamOrgDist: ContGegDistributie.append(naamOrgDist)
        # ~ else: ContGegDistributie.append(None)
        # ~ # verantwoordelijke organisatie distributie URL
        # ~ URLOrgDist = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributorContact[%s]/{%s}CI_ResponsibleParty/{%s}contactInfo/{%s}CI_Contact/{%s}onlineResource/{%s}CI_OnlineResource/{%s}linkage/{%s}URL' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
        # ~ if URLOrgDist: ContGegDistributie.append(URLOrgDist)
        # ~ else: ContGegDistributie.append(None)
        # ~ # naam contactpersoon distributie
        # ~ naamContDist = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributorContact[%s]/{%s}CI_ResponsibleParty/{%s}individualName/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if naamContDist: ContGegDistributie.append(naamContDist)
        # ~ else: ContGegDistributie.append(None)
        # ~ # rol contactpersoon distributie
        # ~ rolContDist = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributorContact[%s]/{%s}CI_ResponsibleParty/{%s}positionName/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if rolContDist: ContGegDistributie.append(rolContDist)
        # ~ else: ContGegDistributie.append(None)
        # ~ self.ContGegDistributie.append(ContGegDistributie)
      # ~ # prijs informatie
      # ~ prijsinformatie = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributionOrderProcess/{%s}MD_StandardOrderProcess/{%s}fees/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if prijsinformatie: self.ui.le_prijsinformatie.setText(prijsinformatie)
      # ~ # orderprocedure
      # ~ orderprocedure = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributionOrderProcess/{%s}MD_StandardOrderProcess/{%s}orderingInstructions/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if orderprocedure: self.ui.le_orderprocedure.setText(orderprocedure)
      # ~ # doorlooptijd orderprocedure
      # ~ doorlooptijd = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}distributor/{%s}MD_Distributor/{%s}distributionOrderProcess/{%s}MD_StandardOrderProcess/{%s}turnaround/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if doorlooptijd: self.ui.le_doorlooptijd.setText(doorlooptijd)
      # ~ # leverings eenheid
      # ~ leveringsEenheid = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}unitsOfDistribution/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if leveringsEenheid: self.ui.le_leveringseenheid.setText(leveringsEenheid)
      # ~ # bestands grootte
      # ~ bestandsGrootte = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}transferSize/{%s}Real' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if bestandsGrootte: self.ui.le_bestandsgrootte.setText(bestandsGrootte)
      # ~ # online toegang
      # ~ # URL
      # ~ onlineURLs = xmldoc.findall('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}onLine/{%s}CI_OnlineResource/{%s}linkage/{%s}URL' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ onlineURLs = [onlineURL.text for onlineURL in onlineURLs]
      # ~ for teller, onlineURL in list(enumerate(onlineURLs, start=1)):
        # ~ exec('self.ui.le_URL_%s.setText("%s")' %(teller, onlineURL))
        # ~ # protocol
        # ~ onlineProtocol = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}onLine[%s]/{%s}CI_OnlineResource/{%s}protocol/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if onlineProtocol: exec('self.onlineProtocol_%s = onlineProtocol' %(teller))
        # ~ # naam
        # ~ onlineNaam = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}onLine[%s]/{%s}CI_OnlineResource/{%s}name/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if onlineNaam: exec('self.ui.le_naam_%s.setText("%s")' %(teller, onlineNaam))
        # ~ # omschrijving
        # ~ onlineOmschrijving = xmldoc.findtext('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}onLine[%s]/{%s}CI_OnlineResource/{%s}description/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if onlineOmschrijving: exec('self.onlineOmschrijving_%s = onlineOmschrijving' %(teller))
        # ~ # functie
        # ~ onlineFunctie = xmldoc.find('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}onLine[%s]/{%s}CI_OnlineResource/{%s}function/{%s}CI_OnLineFunctionCode' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd)).get('codeListValue')
        # ~ if onlineFunctie: exec('self.onlineFunctie_%s = onlineFunctie' %(teller))
      # ~ # naam medium
      # ~ naamMedium = xmldoc.find('//{%s}distributionInfo/{%s}MD_Distribution/{%s}transferOptions/{%s}MD_DigitalTransferOptions/{%s}offLine/{%s}MD_Medium/{%s}name/{%s}MD_MediumNameCode' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ if naamMedium: self.naamMedium = naamMedium.get('codeListValue')
      # ~ # niveau kwaliteitsbeschrijving
      # ~ self.niveauKwaliteit = xmldoc.find('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}scope/{%s}DQ_Scope/{%s}level/{%s}MD_ScopeCode' %(gmd, gmd, gmd, gmd, gmd, gmd)).get('codeListValue')
      # ~ # features
      # ~ features = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}scope/{%s}DQ_Scope/{%s}levelDescription/{%s}MD_ScopeDescription/{%s}features/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if features: self.ui.le_Features.setText(features)
      # ~ # specificatie
      # ~ specificatie = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_DomainConsistency/{%s}result/{%s}DQ_ConformanceResult/{%s}specification/{%s}CI_Citation/{%s}title/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if specificatie: self.ui.le_specificatie.setText(specificatie)
      # ~ # alternatieven titel
      # ~ alternatieveTitel = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_DomainConsistency/{%s}result/{%s}DQ_ConformanceResult/{%s}specification/{%s}CI_Citation/{%s}alternateTitle/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if alternatieveTitel: self.ui.le_alternatieve_specificatie.setText(alternatieveTitel)
      # ~ # specificatie datum
      # ~ specificatieDatum = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_DomainConsistency/{%s}result/{%s}DQ_ConformanceResult/{%s}specification/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}date/{%s}Date' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if specificatieDatum: self.ui.de_specificatie_datum.setDate(QtCore.QDate.fromString(specificatieDatum, "yyyy-MM-dd"))
      # ~ # specificatie type datum
      # ~ specificatieTypeDatum = xmldoc.find('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_DomainConsistency/{%s}result/{%s}DQ_ConformanceResult/{%s}specification/{%s}CI_Citation/{%s}date/{%s}CI_Date/{%s}dateType/{%s}CI_DateTypeCode' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd, gmd))
      # ~ if specificatieTypeDatum: self.specificatieTypeDatum = specificatieTypeDatum.get('codeListValue')
      # ~ # verklaring
      # ~ verklaring = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_DomainConsistency/{%s}result/{%s}DQ_ConformanceResult/{%s}explanation/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if verklaring: self.ui.le_verklaring.setText(verklaring)
      # ~ # conformiteit indicatie      
      # ~ conformiteitIndicatie = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_DomainConsistency/{%s}result/{%s}DQ_ConformanceResult/{%s}pass/{%s}Boolean' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if conformiteitIndicatie: self.conformiteitIndicatie = conformiteitIndicatie
      # ~ # compleetheid
      # ~ compleetheid = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_CompletenessOmission/{%s}result/{%s}DQ_QuantitativeResult/{%s}value/{%s}Record' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if compleetheid: self.ui.te_Compleetheid.setText(compleetheid)
      # ~ # waarde topologische samenhang
      # ~ waardeTopo = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_TopologicalConsistency/{%s}result/{%s}DQ_QuantitativeResult/{%s}value/{%s}Record' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if waardeTopo: self.ui.le_topologische_samenhang_waarde.setText(waardeTopo)
      # ~ # geometrische nauwkeurigheid
      # ~ geoNauwkeurigheid = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}report/{%s}DQ_AbsoluteExternalPositionalAccuracy/{%s}result/{%s}DQ_QuantitativeResult/{%s}value/{%s}Record' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if geoNauwkeurigheid: self.ui.te_nauwkeurigheid.setText(geoNauwkeurigheid)
      # ~ # algemene beschrijving herkomst
      # ~ beschrijvingHerkomst = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}statement/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gco))
      # ~ if beschrijvingHerkomst: self.ui.te_beschrijving_herkomst.setText(beschrijvingHerkomst)
      # ~ # beschrijving uitgevoerde bewerking
      # ~ BUBewerkingen = xmldoc.findall('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}processStep/{%s}LI_ProcessStep/{%s}description/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ BUBewerkingen = [BUBewerking.text for BUBewerking in BUBewerkingen]
      # ~ for teller, BUBewerking in list(enumerate(BUBewerkingen, start=1)): 
        # ~ exec('self.ui.te_beschrijving_bewerking_%s.setText("%s")' %(teller, BUBewerking))
        # ~ # datum uitgevoerde bewerking
        # ~ datumUB = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}processStep[%s]/{%s}LI_ProcessStep/{%s}dateTime/{%s}DateTime' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gco))
        # ~ if datumUB: exec('self.datumUB_%s = datumUB' %(teller))
        # ~ # producent beschreven dataset
        # ~ producentBD = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}processStep[%s]/{%s}LI_ProcessStep/{%s}processor/{%s}CI_ResponsibleParty/{%s}organisationName/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gco))
        # ~ if producentBD: exec('self.producentBD_%s = producentBD' %(teller))
        # ~ # rol producent beschreven dataset
        # ~ rolPBD = xmldoc.find('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}processStep[%s]/{%s}LI_ProcessStep/{%s}processor/{%s}CI_ResponsibleParty/{%s}role/{%s}CI_RoleCode' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd)).get('codeListValue')
        # ~ if rolPBD: exec('self.rolPBD_%s = rolPBD' %(teller))
      # ~ # beschrijving brondata
      # ~ brondataBeschrijvingen = xmldoc.findall('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}source/{%s}LI_Source/{%s}description/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, gmd, gmd, gco))
      # ~ brondataBeschrijvingen = [brondataBeschrijving.text for brondataBeschrijving in brondataBeschrijvingen]
      # ~ for teller, brondataBeschrijving in list(enumerate(brondataBeschrijvingen, start=1)): 
        # ~ exec('self.ui.te_beschrijving_bron_%s.setText("%s")' %(teller, brondataBeschrijving))
        # ~ # inwinningsmethode
        # ~ inwinningsmethode = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}source[%s]/{%s}LI_Source/{%s}sourceStep/{%s}LI_ProcessStep/{%s}description/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gco))
        # ~ if inwinningsmethode: exec('self.inwinningsmethode_%s = inwinningsmethode' %(teller))
        # ~ # datum inwinning brondata
        # ~ datumBrondata = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}source[%s]/{%s}LI_Source/{%s}sourceStep/{%s}LI_ProcessStep/{%s}dateTime/{%s}DateTime' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gco))
        # ~ if datumBrondata: exec('self.datumBrondata_%s = datumBrondata' %(teller))
        # ~ # inwinnende organisatie
        # ~ inwinnendeOrganisatie = xmldoc.findtext('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}source[%s]/{%s}LI_Source/{%s}sourceStep/{%s}LI_ProcessStep/{%s}processor/{%s}CI_ResponsibleParty/{%s}organisationName/{%s}CharacterString' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gco))
        # ~ if inwinnendeOrganisatie: exec('self.inwinnendeOrganisatie_%s = inwinnendeOrganisatie' %(teller))
        # ~ # rol inwinnende organisatie
        # ~ rolInwinOrg = xmldoc.find('//{%s}dataQualityInfo/{%s}DQ_DataQuality/{%s}lineage/{%s}LI_Lineage/{%s}source[%s]/{%s}LI_Source/{%s}sourceStep/{%s}LI_ProcessStep/{%s}processor/{%s}CI_ResponsibleParty/{%s}role/{%s}CI_RoleCode' %(gmd, gmd, gmd, gmd, gmd, teller, gmd, gmd, gmd, gmd, gmd, gmd, gmd)).get('codeListValue')
        # ~ if rolInwinOrg: exec('self.rolInwinOrg_%s = rolInwinOrg' %(teller))

  # ~ def schrijfXML(self):
    # ~ """
    # ~ Sla de ingevulde dat op in een metadata xml
    # ~ """
    # ~ # als het object self.xml_map niet bestaat gebruik dan de home directorie    
    # ~ if not hasattr(self,'xml_map'): self.xml_map = os.path.expanduser('~')
    # ~ # als self.xml_naam niet bestaat gebruik dan de metadata uuid
    # ~ if not hasattr(self,'xml_naam'): 
      # ~ if self.ui.le_Metadata_uuid.text(): self.xml_naam = self.ui.le_Metadata_uuid.text()
      # ~ # maak anders een uuid
      # ~ else: self.xml_naam = str(uuid.uuid4())
    # ~ # plak .xml achter de xml_naam
    # ~ self.xml_naam = os.path.splitext(self.xml_naam)[0]+'.xml'
    # ~ # lees de namespaces    
    # ~ namespaces = self.eigenlijsten["namespaces"]
    # ~ # xsd invoegen
    # ~ schemalocation = etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'schemaLocation')
    # ~ # bepaal het root element
    # ~ root = etree.Element('MD_Metadata', {schemalocation: 'http://www.isotc211.org/2005/gmd http://schemas.opengis.net/iso/19139/20060504/gmd/gmd.xsd'}, nsmap=namespaces)
    # ~ # zet de metadata identifier in de xml    
    # ~ if self.ui.le_Metadata_uuid.text():
      # ~ metadataIdentifier = etree.SubElement(root, 'fileIdentifier')
      # ~ le_Metadata_uuid = etree.SubElement(metadataIdentifier, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_Metadata_uuid.text = self.ui.le_Metadata_uuid.text()
    # ~ # zet de taal van de metadata in de xml
    # ~ if self.ui.cbx_taal_metadata.currentText():
      # ~ metadata_taal = [item[1] for item in self.codelijsten["A.17 Codelijst Talen (ISO 639-2)"] if item[0] == self.ui.cbx_taal_metadata.currentText()][0]
      # ~ language = etree.SubElement(root, 'language')
      # ~ cbx_taal_metadata = etree.SubElement(language, 'LanguageCode', codeList='http://www.loc.gov/standards/iso639-2/', codeListValue='%s' %(metadata_taal))
      # ~ cbx_taal_metadata.text = metadata_taal
    # ~ # zet de karakterset van de metadata in de xml
    # ~ if self.ui.cbx_Metadata_karakterset.currentText():
      # ~ characterMetadata = etree.SubElement(root, 'characterSet')
      # ~ cbx_Metadata_karakterset = etree.SubElement(characterMetadata, 'MD_CharacterSetCode', codeList='./resources/codeList.xml#MD_CharacterSetCode', codeListValue='%s' %(self.ui.cbx_Metadata_karakterset.currentText()))
    # ~ # zet de dataset in de xml
    # ~ if self.ui.cbx_hierarchieniveau.currentText():
      # ~ scope = [item[0] for item in self.codelijsten["A.11 Codelijst MD_ScopeCode"] if item[0] == self.ui.cbx_hierarchieniveau.currentText()][0]
      # ~ hierarchyniveau = etree.SubElement(root, 'hierarchyLevel')
      # ~ cbx_hierarchieniveau = etree.SubElement(hierarchyniveau, 'MD_ScopeCode', codeList='./resources/codeList.xml#MD_ScopeCode', codeListValue='%s' %(scope))
      # ~ cbx_hierarchieniveau.text = scope
    # ~ # zet hierarchieniveau naam in de xml
    # ~ if self.ui.le_hierachieniveau_naam.text():
      # ~ hierarchieniveaunaam = etree.SubElement(root, 'hierarchyLevelname')
      # ~ le_hierachieniveau_naam = etree.SubElement(hierarchieniveaunaam, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_hierachieniveau_naam.text = self.ui.le_hierachieniveau_naam.text()
    # ~ # contact gegevens van de metadata
    # ~ for num in range(1, len(self.ContGegMetadata)+1):
      # ~ # plaats naam, organisatie en rol van de contactpersoon
      # ~ exec_tekst = """if self.ui.le_Email_metadata_%s.text(): \
        # ~ tag350 = etree.SubElement(root, 'contact'); \
        # ~ tag351 = etree.SubElement(tag350, 'CI_ResponsibleParty'); \
        # ~ tag352 = etree.SubElement(tag351, 'individualName'); \
        # ~ individuelenaam = etree.SubElement(tag352, '{%s}CharacterString'); \
        # ~ individuelenaam.text = self.ui.le_metadata_contactpersoon_%s.text(); \
        # ~ tag353 = etree.SubElement(tag351, 'organisationName'); \
        # ~ organisatienaam = etree.SubElement(tag353, '{%s}CharacterString'); \
        # ~ organisatienaam.text = self.ui.le_metadata_naam_%s.text(); \
        # ~ tag354 = etree.SubElement(tag351, 'positionName'); \
        # ~ rolcontactpersoon = etree.SubElement(tag354, '{%s}CharacterString'); \
        # ~ rolcontactpersoon.text = self.ui.cbx_Rol_metadata_contactpersoon_%s.currentText(); \
        # ~ """ %(num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num)
      # ~ exec(exec_tekst)
      # ~ # zoek de contact gegevens uit het csv bestand
      # ~ exec_tekst = """if self.ui.le_Email_metadata_%s.text() and self.ui.le_Email_metadata_%s.text().lower().strip() in self.csv_dict.keys(): \
        # ~ tag355 = etree.SubElement(tag351, 'contactInfo'); \
        # ~ tag356 = etree.SubElement(tag355, 'CI_Contact'); \
        # ~ tag357 = etree.SubElement(tag356, 'phone'); \
        # ~ tag358 = etree.SubElement(tag357, 'CI_Telephone'); \
        # ~ tag359 = etree.SubElement(tag358, 'voice'); \
        # ~ telefoon = etree.SubElement(tag359, '{%s}CharacterString'); \
        # ~ telefoon.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][8]; \
        # ~ tag360 = etree.SubElement(tag358, 'facsimile'); \
        # ~ fax = etree.SubElement(tag360, '{%s}CharacterString'); \
        # ~ fax.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][9]; \
        # ~ tag361 = etree.SubElement(tag356, 'address'); \
        # ~ tag362 = etree.SubElement(tag361, 'CI_Address'); \
        # ~ tag363 = etree.SubElement(tag362, 'deliveryPoint'); \
        # ~ adres = etree.SubElement(tag363, '{%s}CharacterString'); \
        # ~ adres.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][3]; \
        # ~ tag364 = etree.SubElement(tag362, 'city'); \
        # ~ plaats = etree.SubElement(tag364, '{%s}CharacterString'); \
        # ~ plaats.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][5]; \
        # ~ tag365 = etree.SubElement(tag362, 'administrativeArea'); \
        # ~ provincie = etree.SubElement(tag365, '{%s}CharacterString'); \
        # ~ provincie.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][6]; \
        # ~ tag366 = etree.SubElement(tag362, 'postalCode'); \
        # ~ postcode = etree.SubElement(tag366, '{%s}CharacterString'); \
        # ~ postcode.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][4]; \
        # ~ tag367 = etree.SubElement(tag362, 'country'); \
        # ~ land = etree.SubElement(tag367, '{%s}CharacterString'); \
        # ~ land.text = self.csv_dict[self.ui.le_Email_metadata_%s.text().lower().strip()][7]; \
        # ~ tag368 = etree.SubElement(tag362, 'electronicMailAddress'); \
        # ~ email = etree.SubElement(tag368, '{%s}CharacterString'); \
        # ~ email.text = self.ui.le_Email_metadata_%s.text(); \
        # ~ tag369 = etree.SubElement(tag356, 'onlineResource'); \
        # ~ tag370 = etree.SubElement(tag369, 'CI_OnlineResource'); \
        # ~ tag371 = etree.SubElement(tag370, 'linkage'); \
        # ~ url = etree.SubElement(tag371, 'URL'); \
        # ~ url.text = self.ui.le_metadata_website_%s.text(); \
        # ~ tag372 = etree.SubElement(tag351, 'role'); \
        # ~ rolmetadata = etree.SubElement(tag372, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', \
        # ~ codeListValue=self.ui.cbx_Rol_metadata_%s.currentText()); \
        # ~ """ %(num, num, namespaces['gco'],num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], \
        # ~ num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, num, num)
      # ~ exec(exec_tekst)
      # ~ # als de contact gegevens niet in het csv bestand staan
      # ~ exec_tekst = """if self.ui.le_Email_metadata_%s.text() and not self.ui.le_Email_metadata_%s.text().lower().strip() in self.csv_dict.keys(): \
        # ~ tag355 = etree.SubElement(tag351, 'contactInfo'); \
        # ~ tag356 = etree.SubElement(tag355, 'CI_Contact'); \
        # ~ tag361 = etree.SubElement(tag356, 'address'); \
        # ~ tag362 = etree.SubElement(tag361, 'CI_Address'); \
        # ~ tag368 = etree.SubElement(tag362, 'electronicMailAddress'); \
        # ~ email = etree.SubElement(tag368, '{%s}CharacterString'); \
        # ~ email.text = self.ui.le_Email_metadata_%s.text(); \
        # ~ tag369 = etree.SubElement(tag356, 'onlineResource'); \
        # ~ tag370 = etree.SubElement(tag369, 'CI_OnlineResource'); \
        # ~ tag371 = etree.SubElement(tag370, 'linkage'); \
        # ~ url = etree.SubElement(tag371, 'URL'); \
        # ~ url.text = self.ui.le_metadata_website_%s.text(); \
        # ~ tag372 = etree.SubElement(tag351, 'role'); \
        # ~ rolmetadata = etree.SubElement(tag372, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', \
        # ~ codeListValue=self.ui.cbx_Rol_metadata_%s.currentText()); \
        # ~ """ %(num, num, namespaces['gco'], num, num, num)
      # ~ exec(exec_tekst)
    # ~ # datestamp
    # ~ if not str(self.ui.de_Wijzigingsdatum.date().toPyDate()) == '2000-01-01': 
      # ~ datestamp = etree.SubElement(root, 'dateStamp')
      # ~ de_Wijzigingsdatum = etree.SubElement(datestamp, '{%s}Date' %(namespaces['gco']))
      # ~ de_Wijzigingsdatum.text = str(self.ui.de_Wijzigingsdatum.date().toPyDate())
    # ~ # metadata standaard naam
    # ~ if self.ui.le_Metadata_stand_naam.text(): 
      # ~ metadatanaam = etree.SubElement(root, 'metadataStandardName')
      # ~ le_Metadata_stand_naam = etree.SubElement(metadatanaam, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_Metadata_stand_naam.text = self.ui.le_Metadata_stand_naam.text()
    # ~ # metadata standaard versie
    # ~ if self.ui.le_Metadata_stand_versie.text(): 
      # ~ metadataversie = etree.SubElement(root, 'metadataStandardVersion')
      # ~ le_Metadata_stand_versie = etree.SubElement(metadataversie, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_Metadata_stand_versie.text = self.ui.le_Metadata_stand_versie.text()
    # ~ # horizontaal ruimtelijk referentie systeem
    # ~ if self.ui.le_horizontaal_referentiesysteem.text():
      # ~ rfSystem0 = etree.SubElement(root, 'referenceSystemInfo')
      # ~ rfSystem1 = etree.SubElement(rfSystem0, 'MD_ReferenceSystem')
      # ~ rfSystem2 = etree.SubElement(rfSystem1, 'referenceSystemIdentifier')
      # ~ rfSystem3 = etree.SubElement(rfSystem2, 'RS_Identifier')
      # ~ rfSystem4 = etree.SubElement(rfSystem3, 'code')
      # ~ le_horizontaal_referentiesysteem = etree.SubElement(rfSystem4, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_horizontaal_referentiesysteem.text = 'http://www.opengis.net/def/crs/EPSG/0/%s' %(self.ui.le_horizontaal_referentiesysteem.text().split()[0])
      # ~ if self.ui.le_horizontaal_Verantwoordelijk_organisatie.text():
        # ~ rfSystem6 = etree.SubElement(rfSystem3, 'codeSpace')
        # ~ le_horizontaal_Verantwoordelijk_organisatie = etree.SubElement(rfSystem6, '{%s}CharacterString' %(namespaces['gco']))
        # ~ le_horizontaal_Verantwoordelijk_organisatie.text = self.ui.le_horizontaal_Verantwoordelijk_organisatie.text()
    # ~ # vertikaal ruimtelijk referentie systeem
    # ~ if self.ui.cbx_verticaal_referentiesysteem.currentText():
      # ~ rfSystem0 = etree.SubElement(root, 'referenceSystemInfo')
      # ~ rfSystem1 = etree.SubElement(rfSystem0, 'MD_ReferenceSystem')
      # ~ rfSystem2 = etree.SubElement(rfSystem1, 'referenceSystemIdentifier')
      # ~ rfSystem3 = etree.SubElement(rfSystem2, 'RS_Identifier')
      # ~ rfSystem4 = etree.SubElement(rfSystem3, 'code')
      # ~ cbx_verticaal_referentiesysteem = etree.SubElement(rfSystem4, '{%s}CharacterString' %(namespaces['gco']))
      # ~ cbx_verticaal_referentiesysteem.text = 'http://www.opengis.net/def/crs/EPSG/0/%s' %(self.ui.cbx_verticaal_referentiesysteem.currentText().split()[0])
      # ~ if self.ui.le_verticaal_Verantwoordelijk_organisatie.text():
        # ~ rfSystem7 = etree.SubElement(rfSystem3, 'codeSpace')
        # ~ le_verticaal_Verantwoordelijk_organisatie = etree.SubElement(rfSystem7, '{%s}CharacterString' %(namespaces['gco']))
        # ~ le_verticaal_Verantwoordelijk_organisatie.text = self.ui.le_verticaal_Verantwoordelijk_organisatie.text()      
    # ~ # indentification info
    # ~ tag0 = etree.SubElement(root, 'identificationInfo')
    # ~ # self titel_uuid
    # ~ if not hasattr(self,'titel_uuid') or not self.titel_uuid: self.titel_uuid = str(uuid.uuid4())
    # ~ tag1 = etree.SubElement(tag0, 'MD_DataIdentification') #, id='%s' %(self.titel_uuid))
    # ~ tag2 = etree.SubElement(tag1, 'citation')
    # ~ tag3 = etree.SubElement(tag2, 'CI_Citation')
    # ~ # titel van de bron
    # ~ if self.ui.le_TitelBron.text():
      # ~ tag4 = etree.SubElement(tag3, 'title')
      # ~ le_TitelBron = etree.SubElement(tag4, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_TitelBron.text = self.ui.le_TitelBron.text()
    # ~ # alternative titel
    # ~ if self.ui.le_AlternatieveTitel.text():
      # ~ tag5 = etree.SubElement(tag3, 'alternateTitle')
      # ~ le_AlternatieveTitel = etree.SubElement(tag5, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_AlternatieveTitel.text = self.ui.le_AlternatieveTitel.text()
    # ~ # aanmaak datum van de bron
    # ~ if not str(self.ui.de_Creatiedatum.date().toPyDate()) == '2000-01-01': 
      # ~ tag6 = etree.SubElement(tag3, 'date')
      # ~ tag7 = etree.SubElement(tag6, 'CI_Date')
      # ~ tag8 = etree.SubElement(tag7, 'date')
      # ~ de_Creatiedatum = etree.SubElement(tag8, '{%s}Date' %(namespaces['gco']))
      # ~ de_Creatiedatum.text = str(self.ui.de_Creatiedatum.date().toPyDate())
      # ~ tag9 = etree.SubElement(tag7, 'dateType')
      # ~ lbl_Creatiedatum = etree.SubElement(tag9, 'CI_DateTypeCode',  codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue='creation')
    # ~ # publicatie datum van de bron      
    # ~ if not str(self.ui.de_Publicatiedatum.date().toPyDate()) == '2000-01-01': 
      # ~ tag6 = etree.SubElement(tag3, 'date')
      # ~ tag7 = etree.SubElement(tag6, 'CI_Date')
      # ~ tag8 = etree.SubElement(tag7, 'date')
      # ~ de_Publicatiedatum = etree.SubElement(tag8, '{%s}Date' %(namespaces['gco']))
      # ~ de_Publicatiedatum.text = str(self.ui.de_Publicatiedatum.date().toPyDate())
      # ~ tag9 = etree.SubElement(tag7, 'dateType')
      # ~ lbl_Publicatiedatum = etree.SubElement(tag9, 'CI_DateTypeCode',  codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue='publication')      
    # ~ # revisie datum van de bron
    # ~ if not str(self.ui.de_Revisiedatum.date().toPyDate()) == '2000-01-01': 
      # ~ tag6 = etree.SubElement(tag3, 'date')
      # ~ tag7 = etree.SubElement(tag6, 'CI_Date')
      # ~ tag8 = etree.SubElement(tag7, 'date')
      # ~ de_Revisiedatum = etree.SubElement(tag8, '{%s}Date' %(namespaces['gco']))
      # ~ de_Revisiedatum.text = str(self.ui.de_Revisiedatum.date().toPyDate())
      # ~ tag9 = etree.SubElement(tag7, 'dateType')
      # ~ lbl_Revisiedatum = etree.SubElement(tag9, 'CI_DateTypeCode',  codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue='revision')   
    # ~ # versie nummer of naam
    # ~ if self.ui.le_Versie.text():
      # ~ tag10 = etree.SubElement(tag3, 'edition')
      # ~ le_Versie = etree.SubElement(tag10, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_Versie.text = self.ui.le_Versie.text()
    # ~ # uuid van de bron
    # ~ if self.ui.le_uuid.text():
      # ~ tag301 = etree.SubElement(tag3, 'identifier')
      # ~ tag302 = etree.SubElement(tag301, 'MD_Identifier')
      # ~ tag303 = etree.SubElement(tag302, 'code')
      # ~ bronuuid = etree.SubElement(tag303, '{%s}CharacterString' %(namespaces['gco']))
      # ~ bronuuid.text = self.ui.le_uuid.text()
    # ~ # serie of afgeleide dataset
    # ~ if self.ui.le_Serienaamnummer.text():
      # ~ tag13 = etree.SubElement(tag3, 'series')
      # ~ tag14 = etree.SubElement(tag13, 'CI_Series')
      # ~ tag15 = etree.SubElement(tag14, 'name')
      # ~ le_Serienaamnummer = etree.SubElement(tag15, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_Serienaamnummer.text = self.ui.le_Serienaamnummer.text()
    # ~ # samenvatting
    # ~ if self.ui.te_Samenvatting.toPlainText():
      # ~ tag16 = etree.SubElement(tag1, 'abstract')
      # ~ te_Samenvatting = etree.SubElement(tag16, '{%s}CharacterString' %(namespaces['gco']))
      # ~ te_Samenvatting.text = self.ui.te_Samenvatting.toPlainText()
    # ~ # doel van de vervaardiging    
    # ~ if self.ui.te_Doel_vervaardiging.toPlainText():
      # ~ tag17 = etree.SubElement(tag1, 'purpose')
      # ~ te_Doel_vervaardiging = etree.SubElement(tag17, '{%s}CharacterString' %(namespaces['gco']))
      # ~ te_Doel_vervaardiging.text = self.ui.te_Doel_vervaardiging.toPlainText()
    # ~ # status
    # ~ if self.ui.cbx_Status.currentText():
      # ~ tag18 = etree.SubElement(tag1, 'status')
      # ~ cbx_Status = etree.SubElement(tag18, 'MD_ProgressCode', codeList='./resources/codeList.xml#MD_ProgressCode',  codeListValue='%s' %(self.ui.cbx_Status.currentText()))
    # ~ # contact gegevens van de bron
    # ~ for num in range(1, len(self.ContGegBron)+1):
      # ~ # plaats naam, organisatie en rol van de contactpersoon
      # ~ exec_tekst = """if self.ui.le_Email_bron_%s.text(): \
        # ~ tag400 = etree.SubElement(tag1, 'pointOfContact'); \
        # ~ tag401 = etree.SubElement(tag400, 'CI_ResponsibleParty'); \
        # ~ tag402 = etree.SubElement(tag401, 'individualName'); \
        # ~ individuelenaam = etree.SubElement(tag402, '{%s}CharacterString'); \
        # ~ individuelenaam.text = self.ui.le_bron_contactpersoon_%s.text(); \
        # ~ tag403 = etree.SubElement(tag401, 'organisationName'); \
        # ~ organisatienaam = etree.SubElement(tag403, '{%s}CharacterString'); \
        # ~ organisatienaam.text = self.ui.le_bron_naam_%s.text(); \
        # ~ tag404 = etree.SubElement(tag401, 'positionName'); \
        # ~ rolcontactpersoon = etree.SubElement(tag404, '{%s}CharacterString'); \
        # ~ rolcontactpersoon.text = self.ui.cbx_Rol_bron_contactpersoon_%s.currentText(); \
        # ~ """ %(num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num)
      # ~ exec(exec_tekst)
      # ~ # zoek de contact gegevens uit het csv bestand
      # ~ exec_tekst = """if self.ui.le_Email_bron_%s.text() and self.ui.le_Email_bron_%s.text().lower().strip() in self.csv_dict.keys(): \
        # ~ tag405 = etree.SubElement(tag401, 'contactInfo'); \
        # ~ tag406 = etree.SubElement(tag405, 'CI_Contact'); \
        # ~ tag407 = etree.SubElement(tag406, 'phone'); \
        # ~ tag408 = etree.SubElement(tag407, 'CI_Telephone'); \
        # ~ tag409 = etree.SubElement(tag408, 'voice'); \
        # ~ telefoon = etree.SubElement(tag409, '{%s}CharacterString'); \
        # ~ telefoon.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][8]; \
        # ~ tag410 = etree.SubElement(tag408, 'facsimile'); \
        # ~ fax = etree.SubElement(tag410, '{%s}CharacterString'); \
        # ~ fax.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][9]; \
        # ~ tag411 = etree.SubElement(tag406, 'address'); \
        # ~ tag412 = etree.SubElement(tag411, 'CI_Address'); \
        # ~ tag413 = etree.SubElement(tag412, 'deliveryPoint'); \
        # ~ adres = etree.SubElement(tag413, '{%s}CharacterString'); \
        # ~ adres.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][3]; \
        # ~ tag414 = etree.SubElement(tag412, 'city'); \
        # ~ plaats = etree.SubElement(tag414, '{%s}CharacterString'); \
        # ~ plaats.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][5]; \
        # ~ tag415 = etree.SubElement(tag412, 'administrativeArea'); \
        # ~ provincie = etree.SubElement(tag415, '{%s}CharacterString'); \
        # ~ provincie.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][6]; \
        # ~ tag416 = etree.SubElement(tag412, 'postalCode'); \
        # ~ postcode = etree.SubElement(tag416, '{%s}CharacterString'); \
        # ~ postcode.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][4]; \
        # ~ tag417 = etree.SubElement(tag412, 'country'); \
        # ~ land = etree.SubElement(tag417, '{%s}CharacterString'); \
        # ~ land.text = self.csv_dict[self.ui.le_Email_bron_%s.text().lower().strip()][7]; \
        # ~ tag418 = etree.SubElement(tag412, 'electronicMailAddress'); \
        # ~ email = etree.SubElement(tag418, '{%s}CharacterString'); \
        # ~ email.text = self.ui.le_Email_bron_%s.text(); \
        # ~ tag419 = etree.SubElement(tag406, 'onlineResource'); \
        # ~ tag420 = etree.SubElement(tag419, 'CI_OnlineResource'); \
        # ~ tag421 = etree.SubElement(tag420, 'linkage'); \
        # ~ url = etree.SubElement(tag421, 'URL'); \
        # ~ url.text = self.ui.le_bron_website_%s.text(); \
        # ~ tag422 = etree.SubElement(tag401, 'role'); \
        # ~ rolmetadata = etree.SubElement(tag422, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', \
        # ~ codeListValue=self.ui.cbx_Rol_bron_%s.currentText()); \
        # ~ """ %(num, num, namespaces['gco'],num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], \
        # ~ num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, num, num)
      # ~ exec(exec_tekst)
      # ~ # als de contact gegevens niet in het csv bestand staan
      # ~ exec_tekst = """if self.ui.le_Email_bron_%s.text() and not self.ui.le_Email_bron_%s.text().lower().strip() in self.csv_dict.keys(): \
        # ~ tag405 = etree.SubElement(tag401, 'contactInfo'); \
        # ~ tag406 = etree.SubElement(tag405, 'CI_Contact'); \
        # ~ tag411 = etree.SubElement(tag406, 'address'); \
        # ~ tag412 = etree.SubElement(tag411, 'CI_Address'); \
        # ~ tag418 = etree.SubElement(tag412, 'electronicMailAddress'); \
        # ~ email = etree.SubElement(tag418, '{%s}CharacterString'); \
        # ~ email.text = self.ui.le_Email_bron_%s.text(); \
        # ~ tag419 = etree.SubElement(tag406, 'onlineResource'); \
        # ~ tag420 = etree.SubElement(tag419, 'CI_OnlineResource'); \
        # ~ tag421 = etree.SubElement(tag420, 'linkage'); \
        # ~ url = etree.SubElement(tag421, 'URL'); \
        # ~ url.text = self.ui.le_bron_website_%s.text(); \
        # ~ tag422 = etree.SubElement(tag401, 'role'); \
        # ~ rolmetadata = etree.SubElement(tag422, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', \
        # ~ codeListValue=self.ui.cbx_Rol_bron_%s.currentText()); \
        # ~ """ %(num, num, namespaces['gco'], num, num, num)
      # ~ exec(exec_tekst)
    # ~ # herzienings frequentie
    # ~ if self.ui.cbx_Herzieningsfrequentie.currentText():
      # ~ tag19 = etree.SubElement(tag1, 'resourceMaintenance')
      # ~ tag20 = etree.SubElement(tag19, 'MD_MaintenanceInformation')
      # ~ tag21 = etree.SubElement(tag20, 'maintenanceAndUpdateFrequency')
      # ~ cbx_Herzieningsfrequentie = etree.SubElement(tag21, 'MD_MaintenanceFrequencyCode', codeList='./resources/codeList.xml#MD_MaintenanceFrequencyCode',  codeListValue='%s' %(self.ui.cbx_Herzieningsfrequentie.currentText()))
    # ~ # datum volgende herziening
    # ~ if not str(self.ui.de_Datum_herziening.date().toPyDate()) == '2000-01-01': 
      # ~ tag22 = etree.SubElement(tag20, 'dateOfNextUpdate')
      # ~ de_Datum_herziening = etree.SubElement(tag22, '{%s}Date' %(namespaces['gco']))
      # ~ de_Datum_herziening.text = str(self.ui.de_Datum_herziening.date().toPyDate())
    # ~ # voorbeeld image
    # ~ if self.ui.le_Voorbeeld.text():
      # ~ tag23 = etree.SubElement(tag1, 'graphicOverview')
      # ~ tag24 = etree.SubElement(tag23, 'MD_BrowseGraphic')
      # ~ tag25 = etree.SubElement(tag24, 'fileName')
      # ~ le_Voorbeeld = etree.SubElement(tag25, '{%s}CharacterString' %(namespaces['gco']))
      # ~ le_Voorbeeld.text = self.ui.le_Voorbeeld.text()
    # ~ # loop door de thesaurussen
    # ~ for thesaurus in self.eigenlijsten["Thesaurussen"].keys():
      # ~ # als de list in de dict is gevuld loop dan door de trefwoorden
      # ~ if thesaurus in self.trefwoorden_dict.keys() and self.trefwoorden_dict[thesaurus]:
        # ~ tag26 = etree.SubElement(tag1, 'descriptiveKeywords')
        # ~ tag27 = etree.SubElement(tag26, 'MD_Keywords')
        # ~ # loop door de gesorteerde aangevinkte trefwoorden
        # ~ for trefwoord in sorted(self.trefwoorden_dict[thesaurus]):
          # ~ tag28 = etree.SubElement(tag27, 'keyword')
          # ~ trfwrd = etree.SubElement(tag28, '{%s}CharacterString' %(namespaces['gco']))
          # ~ trfwrd.text = trefwoord
        # ~ tag29 = etree.SubElement(tag27, 'thesaurusName')
        # ~ tag30 = etree.SubElement(tag29, 'CI_Citation')
        # ~ tag31 = etree.SubElement(tag30, 'title')
        # ~ thesaurusname = etree.SubElement(tag31, '{%s}CharacterString' %(namespaces['gco']))
        # ~ thesaurusname.text = thesaurus
        # ~ tag32 = etree.SubElement(tag30, 'date')
        # ~ tag33 = etree.SubElement(tag32, 'CI_Date')
        # ~ tag34 = etree.SubElement(tag33, 'date')
        # ~ thesaurusdatum = etree.SubElement(tag34, '{%s}Date' %(namespaces['gco']))
        # ~ thesaurusdatum.text = str(self.eigenlijsten["Thesaurussen"][thesaurus][0][0])
        # ~ tag35 = etree.SubElement(tag33, 'dateType')
        # ~ thesaurusdatumType = etree.SubElement(tag35, 'CI_DateTypeCode', codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue='publication')
    # ~ # gebruiksbeperkingen
    # ~ if 'gebruiksbeperkingen' in self.checkbox_dict.keys() and self.checkbox_dict['gebruiksbeperkingen']:
      # ~ tag36 = etree.SubElement(tag1, 'resourceConstraints')
      # ~ tag37 = etree.SubElement(tag36, 'MD_Constraints')
      # ~ for gebruiksbeperking in self.checkbox_dict['gebruiksbeperkingen']:
        # ~ tag38 = etree.SubElement(tag37, 'useLimitation')
        # ~ gebruiksbeperkingen = etree.SubElement(tag38, '{%s}CharacterString' %(namespaces['gco']))
        # ~ gebruiksbeperkingen.text = gebruiksbeperking
    # ~ # loop door de checkbox_dict als er een list gevuld is maak dan de MD_LegalConstraints aan
    # ~ dummy = False
    # ~ for sleutel in self.checkbox_dict.keys():
      # ~ if sleutel in ['toegangsrestricties', 'gebruiksrestricties', 'datalicenties', 'gebruikscondities', 'publieketoegang']: dummy = True
    # ~ if dummy:
      # ~ tag36 = etree.SubElement(tag1, 'resourceConstraints')
      # ~ tag39 = etree.SubElement(tag36, 'MD_LegalConstraints')
    # ~ # toegangsrestricties
    # ~ if 'toegangsrestricties' in self.checkbox_dict.keys() and self.checkbox_dict['toegangsrestricties']:
      # ~ for toegangsrestrictie in self.checkbox_dict['toegangsrestricties']:
        # ~ tag40 = etree.SubElement(tag39, 'accessConstraints')
        # ~ toegangsrestricties =  etree.SubElement(tag40,  'MD_RestrictionCode', \
        # ~ codeList='./resources/codeList.xml#MD_RestrictionCode', codeListValue='%s' %(toegangsrestrictie))
    # ~ # gebruiksrestricties
    # ~ if 'gebruiksrestricties' in self.checkbox_dict.keys() and self.checkbox_dict['gebruiksrestricties']:
      # ~ for gebruiksrestrictie in self.checkbox_dict['gebruiksrestricties']:
        # ~ tag40 = etree.SubElement(tag39, 'useConstraints')
        # ~ gebruiksrestricties =  etree.SubElement(tag40,  'MD_RestrictionCode', \
        # ~ codeList='./resources/codeList.xml#MD_RestrictionCode', codeListValue='%s' %(gebruiksrestrictie))
    # ~ # overige restricties
    # ~ # datalicenties
    # ~ if 'datalicenties' in self.checkbox_dict.keys() and self.checkbox_dict['datalicenties']:
      # ~ tag41 = etree.SubElement(tag39, 'otherConstraints')
      # ~ datalicentie = [licenties for licenties in self.codelijsten['A.20 Codelijst data licenties'] if licenties[1] == self.checkbox_dict['datalicenties'][0]][0]
      # ~ datalicenties = etree.SubElement(tag41, '{%s}Anchor' %(namespaces['gmx']))
      # ~ datalicenties.set('{%s}href' %(namespaces['xlink']), datalicentie[0])
      # ~ datalicenties.text = datalicentie[2]
    # ~ # gebruikscondities
    # ~ if 'gebruikscondities' in self.checkbox_dict.keys() and self.checkbox_dict['gebruikscondities']:
      # ~ tag41 = etree.SubElement(tag39, 'otherConstraints')
      # ~ gebruiksconditie = [licenties for licenties in self.codelijsten['A.15 Codelijst INSPIRE ConditionsApplyingToAccessAndUse'] if licenties[1] == self.checkbox_dict['gebruikscondities'][0]][0]
      # ~ gebruikscondities = etree.SubElement(tag41, '{%s}Anchor' %(namespaces['gmx']))
      # ~ gebruikscondities.set('{%s}href' %(namespaces['xlink']), gebruiksconditie[0])
      # ~ gebruikscondities.text = gebruiksconditie[2]
    # ~ # publieketoegang
    # ~ if 'publieketoegang' in self.checkbox_dict.keys() and self.checkbox_dict['publieketoegang']:
      # ~ tag41 = etree.SubElement(tag39, 'otherConstraints')
      # ~ toegang = [licenties for licenties in self.codelijsten['A.16 Codelijst INSPIRE LimitationsOnPublicAccess'] if licenties[1] == self.checkbox_dict['publieketoegang'][0]][0]
      # ~ publieketoegang = etree.SubElement(tag41, '{%s}Anchor' %(namespaces['gmx']))
      # ~ publieketoegang.set('{%s}href' %(namespaces['xlink']), toegang[0])
      # ~ publieketoegang.text = toegang[2]
    # ~ # veiligheids restricties
    # ~ if 'veiligheidsrestricties' in self.checkbox_dict.keys() and self.checkbox_dict['veiligheidsrestricties']:
      # ~ tag42 = etree.SubElement(tag1, 'resourceConstraints')
      # ~ tag43 = etree.SubElement(tag42, 'MD_SecurityConstraints')
      # ~ tag44 = etree.SubElement(tag43, 'classification')
      # ~ veiligheidsrestrictie = etree.SubElement(tag44, 'MD_ClassificationCode', codeList='./resources/codeList.xml#MD_ClassificationCode', codeListValue='%s' %(self.checkbox_dict['veiligheidsrestricties'][0]))
      # ~ # toelichting
      # ~ if self.ui.le_veiligheidsrestricties.text():
        # ~ tag45 = etree.SubElement(tag43, 'userNote')
        # ~ toelichting = etree.SubElement(tag45, '{%s}CharacterString' %(namespaces['gco']))
        # ~ toelichting.text = self.ui.le_veiligheidsrestricties.text()
    # ~ # naam gerelateerde dataset
    # ~ for num in range(1, 7):
      # ~ exec_tekst = """if self.ui.le_gerelateerde_dataset_%s.text(): \
        # ~ tag46 = etree.SubElement(tag1, 'aggregationInfo'); \
        # ~ tag47 = etree.SubElement(tag46, 'MD_AggregateInformation'); \
        # ~ tag48 = etree.SubElement(tag47, 'aggregateDataSetName'); \
        # ~ tag49 = etree.SubElement(tag48, 'CI_Citation'); \
        # ~ tag50 = etree.SubElement(tag49, 'title'); \
        # ~ titel_dataset = etree.SubElement(tag50, '{%s}CharacterString'); \
        # ~ titel_dataset.text = self.ui.le_gerelateerde_dataset_%s.text(); \
        # ~ tag51 = etree.SubElement(tag49, 'date'); \
        # ~ tag52 = etree.SubElement(tag51, 'CI_Date'); \
        # ~ tag53 = etree.SubElement(tag52, 'date'); \
        # ~ gd_datum = etree.SubElement(tag53, '{%s}Date'); \
        # ~ gd_datum.text = str(self.ui.de_gd_Datum_%s.date().toPyDate()); \
        # ~ tag54 = etree.SubElement(tag52, 'dateType'); \
        # ~ gb_datum_type = etree.SubElement(tag54, 'CI_DateTypeCode', codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue=self.ui.cbx_gd_Datumtype_%s.currentText()); \
        # ~ tag55 = etree.SubElement(tag47, 'associationType'); \
        # ~ type_relatie = etree.SubElement(tag55, 'DS_AssociationTypeCode', codeList='./resources/codeList.xml#DS_AssociationTypeCode', codeListValue='crossReference')
        # ~ """ %(num, namespaces['gco'], num, namespaces['gco'], num, num)
      # ~ exec(exec_tekst)
    # ~ # ruimtelijk schema
    # ~ if self.ui.cbx_Ruimtelijke_schema.currentText():
      # ~ tag56 = etree.SubElement(tag1, 'spatialRepresentationType')
      # ~ ruimtelijkschema = etree.SubElement(tag56, 'MD_SpatialRepresentationTypeCode', codeList='./resources/codeList.xml#MD_SpatialRepresentationTypeCode', codeListValue='%s' %(self.ui.cbx_Ruimtelijke_schema.currentText()))
    # ~ # toepassings schaal
    # ~ for num in range(1, 3):
      # ~ exec_tekst = """if self.ui.le_Toepassingsschaal_0%s.text(): \
        # ~ tag57 = etree.SubElement(tag1, 'spatialResolution'); \
        # ~ tag58 = etree.SubElement(tag57, 'MD_Resolution'); \
        # ~ tag59 = etree.SubElement(tag58, 'equivalentScale'); \
        # ~ tag60 = etree.SubElement(tag59, 'MD_RepresentativeFraction'); \
        # ~ tag61 = etree.SubElement(tag60, 'denominator'); \
        # ~ toepassingsschaal = etree.SubElement(tag61, '{%s}Integer'); \
        # ~ toepassingsschaal.text = self.ui.le_Toepassingsschaal_0%s.text(); \
        # ~ """ %(num, namespaces['gco'], num)
      # ~ exec(exec_tekst)
    # ~ # resolutie
    # ~ for num in range(1, 3):
      # ~ exec_tekst = """if self.ui.le_Resolutie_0%s.text():\
        # ~ tag57 = etree.SubElement(tag1, 'spatialResolution'); \
        # ~ tag58 = etree.SubElement(tag57, 'MD_Resolution'); \
        # ~ tag62 = etree.SubElement(tag58, 'distance'); \
        # ~ resolutie = etree.SubElement(tag62, '{%s}Distance', uom='meters'); \
        # ~ resolutie.text = self.ui.le_Resolutie_0%s.text().replace(',', '.'); \
        # ~ """ %(num, namespaces['gco'], num)               
      # ~ exec(exec_tekst)
    # ~ # taal van de bron
    # ~ if self.ui.cbx_Taal_bron.currentText():
      # ~ tag63 = etree.SubElement(tag1, 'language')
      # ~ taal = [talen for talen in self.codelijsten['A.17 Codelijst Talen (ISO 639-2)'] if talen[0] == self.ui.cbx_Taal_bron.currentText()][0][1]
      # ~ taalbron = etree.SubElement(tag63, 'LanguageCode', codeList='http://www.loc.gov/standards/iso639-2/', codeListValue='%s' %(taal))
      # ~ taalbron.text = taal
    # ~ # karakterset van de bron
    # ~ if self.ui.cbx_Karakterset_bron.currentText():
      # ~ tag64 = etree.SubElement(tag1, 'characterSet')
      # ~ karaktersetbron = etree.SubElement(tag64, 'MD_CharacterSetCode', codeList='./resources/codeList.xml#MD_CharacterSetCode', codeListValue='%s' %(self.ui.cbx_Karakterset_bron.currentText()))
    # ~ # onderwerpen
    # ~ if 'onderwerpen' in self.checkbox_dict.keys() and self.checkbox_dict['onderwerpen']:
      # ~ for item in self.checkbox_dict['onderwerpen']:
        # ~ tag65 = etree.SubElement(tag1, 'topicCategory')
        # ~ onderwerp = etree.SubElement(tag65, 'MD_TopicCategoryCode')
        # ~ onderwerp.text = item
    # ~ # beschrijving temporele dekking
    # ~ if self.ui.te_temporele_dekking.toPlainText():
      # ~ tag66 = etree.SubElement(tag1, 'extent')
      # ~ tag67 = etree.SubElement(tag66, 'EX_Extent')
      # ~ tag68 = etree.SubElement(tag67, 'description')
      # ~ beschrijvingtemporeledekking = etree.SubElement(tag68, '{%s}CharacterString' %(namespaces['gco']))
      # ~ beschrijvingtemporeledekking.text = self.ui.te_temporele_dekking.toPlainText()
    # ~ else:
      # ~ tag66 = etree.SubElement(tag1, 'extent')
      # ~ tag67 = etree.SubElement(tag66, 'EX_Extent')
    # ~ tag68 = etree.SubElement(tag67, 'geographicElement')
    # ~ tag69 = etree.SubElement(tag68, 'EX_GeographicBoundingBox')
    # ~ # west coordinaat
    # ~ if self.ui.le_min_X.text():
      # ~ tag70 = etree.SubElement(tag69, 'westBoundLongitude')
      # ~ westcoordinaat = etree.SubElement(tag70, '{%s}Decimal' %(namespaces['gco']))
      # ~ westcoordinaat.text = self.ui.le_min_X.text().strip()
    # ~ # oost coordinaat
    # ~ if self.ui.le_max_X.text():
      # ~ tag71 = etree.SubElement(tag69, 'eastBoundLongitude')
      # ~ oostcoordinaat = etree.SubElement(tag71, '{%s}Decimal' %(namespaces['gco']))
      # ~ oostcoordinaat.text = self.ui.le_max_X.text().strip()
    # ~ # zuid coordinaat
    # ~ if self.ui.le_min_Y.text(): 
      # ~ tag72 = etree.SubElement(tag69, 'southBoundLatitude')
      # ~ zuidcoordinaat = etree.SubElement(tag72, '{%s}Decimal' %(namespaces['gco']))
      # ~ zuidcoordinaat.text = self.ui.le_min_Y.text().strip()
    # ~ # noord coordinaat
    # ~ if self.ui.le_max_Y.text(): 
      # ~ tag73 = etree.SubElement(tag69, 'northBoundLatitude')
      # ~ noordcoordinaat = etree.SubElement(tag73, '{%s}Decimal' %(namespaces['gco']))
      # ~ noordcoordinaat.text = self.ui.le_max_Y.text().strip()
    # ~ # identifier geografisch gebied
    # ~ if self.ui.le_naam_geo_gebied.text():
      # ~ tag74 = etree.SubElement(tag67, 'geographicElement')
      # ~ tag75 = etree.SubElement(tag74, 'EX_GeographicDescription')
      # ~ tag76 = etree.SubElement(tag75, 'geographicIdentifier')
      # ~ tag77 = etree.SubElement(tag76, 'MD_Identifier')
      # ~ tag78 = etree.SubElement(tag77, 'code')
      # ~ geografischgebied = etree.SubElement(tag78, '{%s}CharacterString' %(namespaces['gco']))
      # ~ geografischgebied.text = self.ui.le_naam_geo_gebied.text()
    # ~ # temporele dekking
    # ~ if not str(self.ui.de_temp_dekking_van.date().toPyDate()) == '2000-01-01':
     # ~ tag79 = etree.SubElement(tag67, 'temporalElement')
     # ~ tag80 = etree.SubElement(tag79, 'EX_TemporalExtent')
     # ~ tag81 = etree.SubElement(tag80, 'extent')
     # ~ tag82 = etree.SubElement(tag81, '{%s}TimePeriod' %(namespaces['gml']))
     # ~ tag82.set('{%s}id' %(namespaces['gml']), 'tp1')
     # ~ tag83 = etree.SubElement(tag82, '{%s}begin' %(namespaces['gml']))
     # ~ tag84 = etree.SubElement(tag83, '{%s}TimeInstant' %(namespaces['gml']))
     # ~ tag84.set('{%s}id' %(namespaces['gml']), 'ti1')
     # ~ temporeledekking1 = etree.SubElement(tag84, '{%s}timePosition' %(namespaces['gml']))
     # ~ temporeledekking1.text = str(self.ui.de_temp_dekking_van.date().toPyDate())
     # ~ if not str(self.ui.de_temp_dekking_tot.date().toPyDate()) == '2000-01-01':
       # ~ tag85 = etree.SubElement(tag82, '{%s}end' %(namespaces['gml']))
       # ~ tag851 = etree.SubElement(tag85, '{%s}TimeInstant' %(namespaces['gml']))
       # ~ tag851.set('{%s}id' %(namespaces['gml']), 'ti2')
       # ~ temporeledekking2 = etree.SubElement(tag851, '{%s}timePosition' %(namespaces['gml']))
       # ~ temporeledekking2.text = str(self.ui.de_temp_dekking_tot.date().toPyDate())
    # ~ # verticale coordinaten
    # ~ if self.ui.le_min_Z.text() and self.ui.le_max_Z.text():
      # ~ tag86 = etree.SubElement(tag67, 'verticalElement')
      # ~ tag87 = etree.SubElement(tag86, 'EX_VerticalExtent')
      # ~ tag88 = etree.SubElement(tag87, 'minimumValue')
      # ~ zmincoordinaat = etree.SubElement(tag88, '{%s}Real' %(namespaces['gco']))
      # ~ zmincoordinaat.text = self.ui.le_min_Z.text().strip()
      # ~ tag89 = etree.SubElement(tag87, 'maximumValue')
      # ~ zmaxcoordinaat = etree.SubElement(tag89, '{%s}Real' %(namespaces['gco']))
      # ~ zmaxcoordinaat.text = self.ui.le_max_Z.text().strip()
      # ~ verticalCRS = etree.SubElement(tag87, 'verticalCRS')
    # ~ # aanvullende informatie
    # ~ if self.ui.le_Aanvullende_informatie.text():
      # ~ tag90 = etree.SubElement(tag1, 'supplementalInformation')
      # ~ aanvullendeinformatie = etree.SubElement(tag90, '{%s}CharacterString' %(namespaces['gco']))
      # ~ aanvullendeinformatie.text = self.ui.le_Aanvullende_informatie.text()
    # ~ # feature gegevens
    # ~ if self.ui.le_titel_attribuutgegevens.text():
      # ~ # feature catalog inbegrepen bij dataset
      # ~ tag310 = etree.SubElement(root, 'contentInfo')
      # ~ tag311 = etree.SubElement(tag310, 'MD_FeatureCatalogueDescription')
      # ~ tag312 = etree.SubElement(tag311, 'includedWithDataset')
      # ~ fcinbegrepen = etree.SubElement(tag312, '{%s}Boolean' %(namespaces['gco']))
      # ~ fcinbegrepen.text = 'true'
      # ~ # feature type
      # ~ tag313 = etree.SubElement(tag311, 'featureTypes')
      # ~ featuretype = etree.SubElement(tag313,'{%s}LocalName' %(namespaces['gco']))
      # ~ featuretype.text = self.ui.cbx_feature_types.currentText()
      # ~ # feature catalog titel
      # ~ tag314 = etree.SubElement(tag311, 'featureCatalogueCitation')
      # ~ tag315 = etree.SubElement(tag314, 'CI_Citation')
      # ~ tag316 = etree.SubElement(tag315, 'title')
      # ~ fctitel = etree.SubElement(tag316,'{%s}CharacterString' %(namespaces['gco']))
      # ~ fctitel.text = self.ui.le_titel_attribuutgegevens.text()
      # ~ # feature catalog datum type
      # ~ tag317 = etree.SubElement(tag315, 'date')
      # ~ tag318 = etree.SubElement(tag317, 'CI_Date')
      # ~ tag319 = etree.SubElement(tag318, 'date')
      # ~ fcdatum = etree.SubElement(tag319, '{%s}Date' %(namespaces['gco']))
      # ~ fcdatum.text = str(self.ui.de_attribuutgegevens_datum.date().toPyDate())
      # ~ tag320 = etree.SubElement(tag318, 'dateType')
      # ~ fcdatumtype = etree.SubElement(tag320, 'CI_DateTypeCode',  codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue='%s' %(self.ui.cbx_datum_type_attribuutgegevens.currentText()))
      # ~ # feature catalog uuid
      # ~ tag321 = etree.SubElement(tag315, 'identifier')
      # ~ tag322 = etree.SubElement(tag321, 'MD_Identifier')
      # ~ tag323 = etree.SubElement(tag322, 'code')
      # ~ fcuuid = etree.SubElement(tag323, '{%s}CharacterString' %(namespaces['gco']))
      # ~ fcuuid.text = self.ui.le_uuid_attribuutgegevens.text()
    # ~ # distributie
    # ~ tag91 = etree.SubElement(root, 'distributionInfo')
    # ~ tag92 = etree.SubElement(tag91, 'MD_Distribution')
    # ~ # distributie formaat
    # ~ if self.ui.le_Naam_dist_formaat_1.text(): 
      # ~ tag93 = etree.SubElement(tag92, 'distributionFormat')
      # ~ for num in range(1, 6):
        # ~ exec_tekst = """if self.ui.le_Naam_dist_formaat_%s.text(): \
          # ~ tag94 = etree.SubElement(tag93, 'MD_Format'); \
          # ~ tag95 = etree.SubElement(tag94, 'name'); \
          # ~ distributieformaat = etree.SubElement(tag95, '{%s}CharacterString'); \
          # ~ distributieformaat.text = self.ui.le_Naam_dist_formaat_%s.text()""" %(num, namespaces['gco'], num)
        # ~ exec(exec_tekst)
        # ~ exec_tekst = """if self.ui.le_Versie_formaat_%s.text(): \
          # ~ tag96 = etree.SubElement(tag94, 'version'); \
          # ~ distributieversie = etree.SubElement(tag96, '{%s}CharacterString'); \
          # ~ distributieversie.text = self.ui.le_Versie_formaat_%s.text()""" %(num, namespaces['gco'], num)
        # ~ exec(exec_tekst)
        # ~ exec_tekst = """if self.ui.le_specificatie_formaat_%s.text(): \
          # ~ tag97 = etree.SubElement(tag94, 'specification'); \
          # ~ distributiespecificatie = etree.SubElement(tag97, '{%s}CharacterString'); \
          # ~ distributiespecificatie.text = self.ui.le_specificatie_formaat_%s.text()""" %(num, namespaces['gco'], num)
        # ~ exec(exec_tekst)
    # ~ # gegevens van de distributeur
    # ~ tag448 = etree.SubElement(tag92, 'distributor')
    # ~ tag449 = etree.SubElement(tag448, 'MD_Distributor')
    # ~ # vul de contact gevevens van de distributeur
    # ~ for num in range(1, len(self.ContGegDistributie)+1):
      # ~ # plaats naam, organisatie en rol van de contactpersoon
      # ~ exec_tekst = """if self.ui.le_Email_distributie_%s.text(): \
        # ~ tag450 = etree.SubElement(tag449, 'distributorContact'); \
        # ~ tag451 = etree.SubElement(tag450, 'CI_ResponsibleParty'); \
        # ~ tag452 = etree.SubElement(tag451, 'individualName'); \
        # ~ individuelenaam = etree.SubElement(tag452, '{%s}CharacterString'); \
        # ~ individuelenaam.text = self.ui.le_distributie_contactpersoon_%s.text(); \
        # ~ tag453 = etree.SubElement(tag451, 'organisationName'); \
        # ~ organisatienaam = etree.SubElement(tag453, '{%s}CharacterString'); \
        # ~ organisatienaam.text = self.ui.le_distributie_naam_%s.text(); \
        # ~ tag454 = etree.SubElement(tag451, 'positionName'); \
        # ~ rolcontactpersoon = etree.SubElement(tag454, '{%s}CharacterString'); \
        # ~ rolcontactpersoon.text = self.ui.cbx_Rol_distributie_contactpersoon_%s.currentText(); \
        # ~ """ %(num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num)
      # ~ exec(exec_tekst)
      # ~ # zoek de contact gegevens uit het csv bestand
      # ~ exec_tekst = """if self.ui.le_Email_distributie_%s.text() and self.ui.le_Email_distributie_%s.text().lower().strip() in self.csv_dict.keys(): \
        # ~ tag455 = etree.SubElement(tag451, 'contactInfo'); \
        # ~ tag456 = etree.SubElement(tag455, 'CI_Contact'); \
        # ~ tag457 = etree.SubElement(tag456, 'phone'); \
        # ~ tag458 = etree.SubElement(tag457, 'CI_Telephone'); \
        # ~ tag459 = etree.SubElement(tag458, 'voice'); \
        # ~ telefoon = etree.SubElement(tag459, '{%s}CharacterString'); \
        # ~ telefoon.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][8]; \
        # ~ tag460 = etree.SubElement(tag458, 'facsimile'); \
        # ~ fax = etree.SubElement(tag460, '{%s}CharacterString'); \
        # ~ fax.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][9]; \
        # ~ tag461 = etree.SubElement(tag456, 'address'); \
        # ~ tag462 = etree.SubElement(tag461, 'CI_Address'); \
        # ~ tag463 = etree.SubElement(tag462, 'deliveryPoint'); \
        # ~ adres = etree.SubElement(tag463, '{%s}CharacterString'); \
        # ~ adres.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][3]; \
        # ~ tag464 = etree.SubElement(tag462, 'city'); \
        # ~ plaats = etree.SubElement(tag464, '{%s}CharacterString'); \
        # ~ plaats.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][5]; \
        # ~ tag465 = etree.SubElement(tag462, 'administrativeArea'); \
        # ~ provincie = etree.SubElement(tag465, '{%s}CharacterString'); \
        # ~ provincie.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][6]; \
        # ~ tag466 = etree.SubElement(tag462, 'postalCode'); \
        # ~ postcode = etree.SubElement(tag466, '{%s}CharacterString'); \
        # ~ postcode.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][4]; \
        # ~ tag467 = etree.SubElement(tag462, 'country'); \
        # ~ land = etree.SubElement(tag467, '{%s}CharacterString'); \
        # ~ land.text = self.csv_dict[self.ui.le_Email_distributie_%s.text().lower().strip()][7]; \
        # ~ tag468 = etree.SubElement(tag462, 'electronicMailAddress'); \
        # ~ email = etree.SubElement(tag468, '{%s}CharacterString'); \
        # ~ email.text = self.ui.le_Email_distributie_%s.text(); \
        # ~ tag469 = etree.SubElement(tag456, 'onlineResource'); \
        # ~ tag470 = etree.SubElement(tag469, 'CI_OnlineResource'); \
        # ~ tag471 = etree.SubElement(tag470, 'linkage'); \
        # ~ url = etree.SubElement(tag471, 'URL'); \
        # ~ url.text = self.ui.le_distributie_website_%s.text(); \
        # ~ tag472 = etree.SubElement(tag451, 'role'); \
        # ~ rolmetadata = etree.SubElement(tag472, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', \
        # ~ codeListValue=self.ui.cbx_Rol_distributie_%s.currentText()); \
        # ~ """ %(num, num, namespaces['gco'],num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], \
        # ~ num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, num, num)
      # ~ exec(exec_tekst)
      # ~ # als de contact gegevens niet in het csv bestand staan
      # ~ exec_tekst = """if self.ui.le_Email_distributie_%s.text() and not self.ui.le_Email_distributie_%s.text().lower().strip() in self.csv_dict.keys(): \
        # ~ tag455 = etree.SubElement(tag451, 'contactInfo'); \
        # ~ tag456 = etree.SubElement(tag455, 'CI_Contact'); \
        # ~ tag461 = etree.SubElement(tag456, 'address'); \
        # ~ tag462 = etree.SubElement(tag461, 'CI_Address'); \
        # ~ tag468 = etree.SubElement(tag462, 'electronicMailAddress'); \
        # ~ email = etree.SubElement(tag468, '{%s}CharacterString'); \
        # ~ email.text = self.ui.le_Email_distributie_%s.text(); \
        # ~ tag469 = etree.SubElement(tag456, 'onlineResource'); \
        # ~ tag470 = etree.SubElement(tag469, 'CI_OnlineResource'); \
        # ~ tag471 = etree.SubElement(tag470, 'linkage'); \
        # ~ url = etree.SubElement(tag471, 'URL'); \
        # ~ url.text = self.ui.le_distributie_website_%s.text(); \
        # ~ tag472 = etree.SubElement(tag451, 'role'); \
        # ~ rolmetadata = etree.SubElement(tag422, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', \
        # ~ codeListValue=self.ui.cbx_Rol_distributie_%s.currentText()); \
        # ~ """ %(num, num, namespaces['gco'], num, num, num)
      # ~ exec(exec_tekst)
    # ~ # prijs info, oderprocedure, doorlooptijd, leveringseenheid en bestandsgrootte
    # ~ if self.ui.le_prijsinformatie.text() or self.ui.le_orderprocedure.text() or self.ui.le_doorlooptijd.text() \
      # ~ or self.ui.le_leveringseenheid.text() or self.ui.le_bestandsgrootte.text():
      # ~ tag101 = etree.SubElement(tag449, 'distributionOrderProcess')
      # ~ tag102 = etree.SubElement(tag101, 'MD_StandardOrderProcess')
      # ~ # prijs informatie
      # ~ if self.ui.le_prijsinformatie.text():
        # ~ tag103 = etree.SubElement(tag102, 'fees')
        # ~ prijsinfo = etree.SubElement(tag103, '{%s}CharacterString' %(namespaces['gco']))
        # ~ prijsinfo.text = self.ui.le_prijsinformatie.text()
      # ~ # orderprocedure
      # ~ if self.ui.le_orderprocedure.text():
        # ~ tag104 = etree.SubElement(tag102, 'orderingInstructions')
        # ~ prijsinfo = etree.SubElement(tag104, '{%s}CharacterString' %(namespaces['gco']))
        # ~ prijsinfo.text = self.ui.le_orderprocedure.text()
      # ~ # doorlooptijd  
      # ~ if self.ui.le_doorlooptijd.text():
        # ~ tag105 = etree.SubElement(tag102, 'turnaround')
        # ~ prijsinfo = etree.SubElement(tag105, '{%s}CharacterString' %(namespaces['gco']))
        # ~ prijsinfo.text = self.ui.le_doorlooptijd.text()
      # ~ if self.ui.le_leveringseenheid.text() or self.ui.le_bestandsgrootte.text():
        # ~ tag106 = etree.SubElement(tag92, 'transferOptions')
        # ~ tag107 = etree.SubElement(tag106, 'MD_DigitalTransferOptions')
        # ~ # leverings eenheid
        # ~ if self.ui.le_leveringseenheid.text():
          # ~ tag108 = etree.SubElement(tag107, 'unitsOfDistribution')
          # ~ leveringseenheid = etree.SubElement(tag108, '{%s}CharacterString' %(namespaces['gco']))
          # ~ leveringseenheid.text = self.ui.le_leveringseenheid.text()
        # ~ # bestandsgrootte
        # ~ if self.ui.le_bestandsgrootte.text():
          # ~ tag109 = etree.SubElement(tag107, 'transferSize')
          # ~ bestandsgrootte = etree.SubElement(tag109, '{%s}Real' %(namespaces['gco']))
          # ~ bestandsgrootte.text = self.ui.le_bestandsgrootte.text()
    # ~ # online toegang
    # ~ if self.ui.le_URL_1.text() or self.ui.cbx_protocol_1.currentText() or self.ui.le_naam_1.text() or self.ui.cbx_omschrijving_1.currentText() or self.ui.cbx_functie_1.currentText(): 
      # ~ tag110 = etree.SubElement(tag92, 'transferOptions')
      # ~ tag111 = etree.SubElement(tag110, 'MD_DigitalTransferOptions')
      # ~ for num in range(1, 6):
        # ~ # URL
        # ~ exec_tekst = """if self.ui.le_URL_%s.text(): \
          # ~ tag112 = etree.SubElement(tag111, 'onLine'); \
          # ~ tag113 = etree.SubElement(tag112, 'CI_OnlineResource'); \
          # ~ tag114 = etree.SubElement(tag113, 'linkage'); \
          # ~ onlineURL = etree.SubElement(tag114, 'URL'); \
          # ~ onlineURL.text = self.ui.le_URL_%s.text()""" %(num, num)
        # ~ exec(exec_tekst)
        # ~ # protocol
        # ~ exec_tekst = """if self.ui.le_URL_%s.text() and self.ui.cbx_protocol_%s.currentText(): \
          # ~ tag115 = etree.SubElement(tag113, 'protocol'); \
          # ~ onlineProtocol = etree.SubElement(tag115, '{%s}CharacterString'); \
          # ~ onlineProtocol.text = self.ui.cbx_protocol_%s.currentText()""" %(num, num, namespaces['gco'], num)
        # ~ exec(exec_tekst)
        # ~ # naam
        # ~ exec_tekst = """if self.ui.le_URL_%s.text() and self.ui.le_naam_%s.text(): \
          # ~ tag116 = etree.SubElement(tag113, 'name'); \
          # ~ onlineNaam = etree.SubElement(tag116, '{%s}CharacterString'); \
          # ~ onlineNaam.text = self.ui.le_naam_%s.text()""" %(num, num, namespaces['gco'], num)
        # ~ exec(exec_tekst)  
        # ~ # omschrijving
        # ~ exec_tekst = """if self.ui.le_URL_%s.text() and self.ui.cbx_omschrijving_%s.currentText(): \
          # ~ tag117 = etree.SubElement(tag113, 'description'); \
          # ~ onlineNaam = etree.SubElement(tag117, '{%s}CharacterString'); \
          # ~ onlineNaam.text = self.ui.cbx_omschrijving_%s.currentText()""" %(num, num, namespaces['gco'], num)
        # ~ exec(exec_tekst)
        # ~ # functie
        # ~ exec_tekst = """if self.ui.le_URL_%s.text() and self.ui.cbx_functie_%s.currentText(): \
          # ~ tag118 = etree.SubElement(tag113, 'function'); \
          # ~ onlineNaam = etree.SubElement(tag118, 'CI_OnLineFunctionCode', codeList='./resources/codeList.xml#CI_OnLineFunctionCode', codeListValue=self.ui.cbx_functie_%s.currentText()); \
          # ~ """ %(num, num, num)
        # ~ exec(exec_tekst)
    # ~ # offLine toegang
    # ~ if self.ui.cbx_Naam_medium.currentText():
      # ~ tag119 = etree.SubElement(tag111, 'offLine')
      # ~ tag120 = etree.SubElement(tag119, 'MD_Medium')
      # ~ tag121 = etree.SubElement(tag120, 'name')
      # ~ medium = etree.SubElement(tag121, 'MD_MediumNameCode', codeList='./resources/codeList.xml#MD_MediumNameCode', codeListValue='%s' %(self.ui.cbx_Naam_medium.currentText()))
    # ~ # data kwaliteit
    # ~ tag122 = etree.SubElement(root, 'dataQualityInfo')
    # ~ tag123 = etree.SubElement(tag122, 'DQ_DataQuality')
    # ~ # kwaliteitsbeschrijving
    # ~ if self.ui.cbx_kwaliteitsbeschrijving.currentText() or self.ui.le_Features.text():
      # ~ tag124 = etree.SubElement(tag123, 'scope')
      # ~ tag125 = etree.SubElement(tag124, 'DQ_Scope')
      # ~ if self.ui.cbx_kwaliteitsbeschrijving.currentText():
        # ~ tag126 = etree.SubElement(tag125, 'level')
        # ~ kwaliteitsbechrijving = etree.SubElement(tag126, 'MD_ScopeCode', codeList='./resources/codeList.xml#MD_ScopeCode', codeListValue='%s' %(self.ui.cbx_kwaliteitsbeschrijving.currentText()))
      # ~ # features
      # ~ if self.ui.le_Features.text():
        # ~ tag127 = etree.SubElement(tag125, 'levelDescription')
        # ~ tag128 = etree.SubElement(tag127, 'MD_ScopeDescription')
        # ~ features = etree.SubElement(tag128, 'features')
        # ~ features.set('{%s}title' %(namespaces['xlink']), self.ui.le_Features.text())
    # ~ # (altenatieve)specificatie
    # ~ if self.ui.le_specificatie.text() or self.ui.le_alternatieve_specificatie.text():
      # ~ tag130 = etree.SubElement(tag123, 'report')
      # ~ tag131 = etree.SubElement(tag130, 'DQ_DomainConsistency')
      # ~ tag132 = etree.SubElement(tag131, 'result')
      # ~ tag133 = etree.SubElement(tag132, 'DQ_ConformanceResult')
      # ~ tag134 = etree.SubElement(tag133, 'specification')
      # ~ tag135 = etree.SubElement(tag134, 'CI_Citation')
      # ~ # specificatie
      # ~ if self.ui.le_specificatie.text():
        # ~ tag136 = etree.SubElement(tag135, 'title')
        # ~ titel = etree.SubElement(tag136,  '{%s}CharacterString' %(namespaces['gco']))
        # ~ titel.text = self.ui.le_specificatie.text()
      # ~ # alternatieve titel
      # ~ if self.ui.le_alternatieve_specificatie.text():
        # ~ tag137 = etree.SubElement(tag135, 'alternateTitle')
        # ~ alternatievetitel = etree.SubElement(tag137,  '{%s}CharacterString' %(namespaces['gco']))
        # ~ alternatievetitel.text = self.ui.le_alternatieve_specificatie.text()
      # ~ # datum specificatie en type
      # ~ if not str(self.ui.de_specificatie_datum.date().toPyDate()) == '2000-01-01':
        # ~ tag138 = etree.SubElement(tag135, 'date')
        # ~ tag139 = etree.SubElement(tag138, 'CI_Date')
        # ~ tag140 = etree.SubElement(tag139, 'date')
        # ~ datumspecificatie = etree.SubElement(tag140, '{%s}Date' %(namespaces['gco']))
        # ~ datumspecificatie.text = str(self.ui.de_specificatie_datum.date().toPyDate())
        # ~ tag141 = etree.SubElement(tag139, 'dateType')
        # ~ specificatieType = etree.SubElement(tag141, 'CI_DateTypeCode',  codeList='./resources/codeList.xml#CI_DateTypeCode', codeListValue='%s' %(self.ui.cbx_specificatie_datum.currentText()))
      # ~ # verklaring
      # ~ if self.ui.le_verklaring.text():
        # ~ tag142 = etree.SubElement(tag133, 'explanation')
        # ~ verklaring = etree.SubElement(tag142, '{%s}CharacterString' %(namespaces['gco']))
        # ~ verklaring.text = self.ui.le_verklaring.text()
      # ~ # indicatie
      # ~ if self.ui.cbx_Conformiteitsindicatie.currentText():
        # ~ tag143 = etree.SubElement(tag133, 'pass')
        # ~ indicatie = etree.SubElement(tag143, '{%s}Boolean' %(namespaces['gco']))
        # ~ indicatie.text = [item for item in self.eigenlijsten["cbx_Conformiteitsindicatie"] if item[0] == self.ui.cbx_Conformiteitsindicatie.currentText()][0][1]
    # ~ # type waarde en compleetheid
    # ~ if self.ui.te_Compleetheid.toPlainText():
      # ~ tag144 = etree.SubElement(tag123, 'report')
      # ~ tag145 = etree.SubElement(tag144, 'DQ_CompletenessOmission')
      # ~ tag146 = etree.SubElement(tag145, 'result')
      # ~ tag147 = etree.SubElement(tag146, 'DQ_QuantitativeResult')
      # ~ typewaarde = etree.SubElement(tag147, 'valueUnit')
      # ~ typewaarde.set('{%s}nilReason' %(namespaces['gco']), 'inapplicable' )
      # ~ tag148 = etree.SubElement(tag147, 'value')
      # ~ compleetheid = etree.SubElement(tag148, '{%s}Record' %(namespaces['gco']))
      # ~ compleetheid.text = self.ui.te_Compleetheid.toPlainText()
    # ~ # eenheid topologische samenhang
    # ~ if self.ui.le_topologische_samenhang_waarde.text():
      # ~ tag149 = etree.SubElement(tag123, 'report')
      # ~ tag150 = etree.SubElement(tag149, 'DQ_TopologicalConsistency')
      # ~ tag151 = etree.SubElement(tag150, 'result')
      # ~ tag152 = etree.SubElement(tag151, 'DQ_QuantitativeResult')
      # ~ samenhang = etree.SubElement(tag152, 'valueUnit')
      # ~ samenhang.set('{%s}href' %(namespaces['xlink']), 'http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/uom/gmxUom.xml#m' )
      # ~ tag153 = etree.SubElement(tag152, 'value')
      # ~ samenhang_waarde = etree.SubElement(tag153, '{%s}Record' %(namespaces['gco']))
      # ~ samenhang_waarde.text = self.ui.le_topologische_samenhang_waarde.text().replace(',','.')
    # ~ # geometrische nauwkeurigheid
    # ~ if self.ui.te_nauwkeurigheid.toPlainText():
      # ~ tag154 = etree.SubElement(tag123, 'report')
      # ~ tag155 = etree.SubElement(tag154, 'DQ_AbsoluteExternalPositionalAccuracy')
      # ~ tag156 = etree.SubElement(tag155, 'result')
      # ~ tag157 = etree.SubElement(tag156, 'DQ_QuantitativeResult')
      # ~ typegeom = etree.SubElement(tag157, 'valueUnit')
      # ~ typegeom.set('{%s}nilReason' %(namespaces['gco']), 'inapplicable' )
      # ~ tag158 = etree.SubElement(tag157, 'value')
      # ~ geomnauwkeurigheid = etree.SubElement(tag158, '{%s}Record' %(namespaces['gco']))
      # ~ geomnauwkeurigheid.text = self.ui.te_nauwkeurigheid.toPlainText()
    # ~ # verwerken beschrijving herkomst, kwaliteit bewerkingen en kwaliteit bron
    # ~ if self.ui.te_beschrijving_herkomst.toPlainText() or self.ui.te_beschrijving_bewerking_1.toPlainText() or self.ui.te_beschrijving_bron_1.toPlainText():
      # ~ tag159 = etree.SubElement(tag123, 'lineage')
      # ~ tag160 = etree.SubElement(tag159, 'LI_Lineage')
      # ~ # beschrijving herkomst
      # ~ if self.ui.te_beschrijving_herkomst.toPlainText():
        # ~ tag161 = etree.SubElement(tag160, 'statement')
        # ~ beschrijvingherkomst = etree.SubElement(tag161, '{%s}CharacterString' %(namespaces['gco']))
        # ~ beschrijvingherkomst.text = self.ui.te_beschrijving_herkomst.toPlainText()
      # ~ # kwaliteit bewerkingen
      # ~ if self.ui.te_beschrijving_bewerking_1.toPlainText():
        # ~ for num in range(1, 9):
          # ~ exec_tekst = """if self.ui.te_beschrijving_bewerking_%s.toPlainText(): \
            # ~ tag162 = etree.SubElement(tag160, 'processStep'); \
            # ~ tag163 = etree.SubElement(tag162, 'LI_ProcessStep') ;\
            # ~ tag164 = etree.SubElement(tag163, 'description'); \
            # ~ beschrijvingbewerking = etree.SubElement(tag164, '{%s}CharacterString'); \
            # ~ beschrijvingbewerking.text = self.ui.te_beschrijving_bewerking_%s.toPlainText(); \
            # ~ tag165 = etree.SubElement(tag163, 'dateTime'); \
            # ~ datumbewerking = etree.SubElement(tag165, '{%s}DateTime'); \
            # ~ datumbewerking.text = self.ui.de_kwaliteit_bewerking_%s.dateTime().toString(Qt.ISODate); \
            # ~ tag166 = etree.SubElement(tag163, 'processor'); \
            # ~ tag167 = etree.SubElement(tag166, 'CI_ResponsibleParty'); \
            # ~ tag168 = etree.SubElement(tag167, 'organisationName'); \
            # ~ producentdataset = etree.SubElement(tag168, '{%s}CharacterString'); \
            # ~ producentdataset.text = self.ui.cbx_bewerking_organisatie_%s.currentText(); \
            # ~ tag169 = etree.SubElement(tag167, 'role'); \
            # ~ rolproducentdataset = etree.SubElement(tag169, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', codeListValue=self.ui.cbx_rol_organisatie_%s.currentText()); \
            # ~ """ %(num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, num)
          # ~ exec(exec_tekst)
      # ~ # kwaliteit bron
      # ~ if self.ui.te_beschrijving_bron_1.toPlainText():
       # ~ for num in range(1, 9):
         # ~ exec_tekst = """if self.ui.te_beschrijving_bron_%s.toPlainText(): \
           # ~ tag170 = etree.SubElement(tag160, 'source'); \
           # ~ tag171 = etree.SubElement(tag170, 'LI_Source'); \
           # ~ tag172 = etree.SubElement(tag171, 'description'); \
           # ~ beschrijvingbron = etree.SubElement(tag172, '{%s}CharacterString'); \
           # ~ beschrijvingbron.text = self.ui.te_beschrijving_bron_%s.toPlainText(); \
           # ~ tag173 = etree.SubElement(tag171, 'sourceStep'); \
           # ~ tag174 = etree.SubElement(tag173, 'LI_ProcessStep'); \
           # ~ tag175 = etree.SubElement(tag174, 'description'); \
           # ~ inwinningsmethode = etree.SubElement(tag175, '{%s}CharacterString'); \
           # ~ inwinningsmethode.text = self.ui.cbx_methode_bron_%s.currentText(); \
           # ~ tag176 = etree.SubElement(tag174, 'dateTime'); \
           # ~ datuminwinningbron = etree.SubElement(tag176, '{%s}DateTime'); \
           # ~ datuminwinningbron.text = self.ui.de_datum_bron_%s.dateTime().toString(Qt.ISODate); \
           # ~ tag177 = etree.SubElement(tag174, 'processor'); \
           # ~ tag178 = etree.SubElement(tag177, 'CI_ResponsibleParty'); \
           # ~ tag179 = etree.SubElement(tag178, 'organisationName'); \
           # ~ producentbron = etree.SubElement(tag179, '{%s}CharacterString'); \
           # ~ producentbron.text = self.ui.cbx_organisatie_bron_%s.currentText(); \
           # ~ tag180 = etree.SubElement(tag178, 'role'); \
           # ~ producentrol = etree.SubElement(tag180, 'CI_RoleCode', codeList='./resources/codeList.xml#CI_RoleCode', codeListValue=self.ui.cbx_rol_bron_organisatie_%s.currentText()); \
           # ~ """ %(num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, namespaces['gco'], num, num)
         # ~ exec(exec_tekst)
    # ~ # schrijf alles weg
    # ~ etree.ElementTree(root).write(self.xml_map+os.sep+self.xml_naam, pretty_print=True, xml_declaration=True, encoding='utf-8')
    # ~ # geef een melding dat de xml is opgeslagen    
    # ~ QtWidgets.QMessageBox.warning(None, "", "%s%s%s is opgeslagen" %(self.xml_map, os.sep, self.xml_naam))
