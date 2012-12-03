"""
/***************************************************************************
Name		     : Raster Processing Suite
Description          : Perform raster math calculations 
Date                 : 05/10/2010
copyright            : (C) 2010 Tom Holderness & Newcastle University
email                : tom.holderness@ncl.ac.uk 
license		     : Relseased under Simplified BSD license (see LICENSE.txt)
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
def name(): 
  return "Raster Processing Suite [beta]" 
def description():
  return "Perform raster math calculations"
def version(): 
  return "0.9.3" 
def qgisMinimumVersion():
  return "1.5.0"
def classFactory(iface): 
  # load Template class from file Template
  from raster_processing_suite import RasterProcessingSuite
  return RasterProcessingSuite(iface)
