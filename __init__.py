# -*- coding: utf-8 -*-

def classFactory(iface):
  from .Metadata_Editor import editor
  return editor(iface)
