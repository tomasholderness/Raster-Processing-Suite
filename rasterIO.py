''' Library of Geospatial raster functions to convert OSGEO.GDAL formats to/from Numpy masked arrays.

rasterIO
========

This library contains wrapper functions for GDAL Python I/O bindings, converting data to Numerical Python 
multi-dimensional array's in memory for processing. Subsequent, generated array's can be written to disk
in the standard Geospatial GeoTiff format.

Notes
-----
	Error checking - rasterIO contains minimal user-level error checking.

Supported Formats
-----------------
	Input: rasterIO supports reading any GDAL supported raster format
	Output: rasterIO generates GeoTiff files by default (this can be modified in the code).
		GeoTiffs are created with embedded binary header files containing geo information

Supported Datatypes
-------------------
	Raster IO supports Float32 and Int16 data types.
	The default datatype is Float32. Boolean datasets use Int16 datatypes.
	
NoDataValue
-----------
	If the input data has no recognisable NoDataValue (readable by GDAL) then the input NoDataValue
	is assumed to be  0. Note that this could result in loss of data. It is left to the user to define
	a suitable input NoDataValue.
	In accordance with GDAL the output data NoDataValue is 9999 or 9999.0

How to use documentation
------------------------
Documentation for module functions is provided as Python docstrings, accessible from an interactive Python terminal.
Within docstrings examples from an interactive Python console are identified using '>>>'. 
Further information is given to developers within the source code using '#' comment strings.
To view this text and a list of available functions call the Python in-built help command, specifying module name.


	>>> import rasterIO
	>>> help(rasterIO)
	...this text...
	
For help on a specific function call the Python in-built help command, specifying module.function.

	>>> import rasterIO
	>>> help(rasterIO.wkt2epsg)
		
		Help on function wkt2epsg in module rasterIO:

	wkt2epsg(wkt)
    		Accepts well known text of Projection/Coordinate Reference System and generates
    		EPSG code
	(END) 

How to access functions
-----------------------
To access functions, import the module to Python and call the desired function, assigning the output to a named variable.
Note that the primary input datatype (default) for all functions is either a Numpy array or a Numpy masked array. 
Within this module the term "raster" is used to signify a Numpy/Numpy masked array of raster values.
Use the rasterIO module to convert Numpy arrays to/from Geospatial raster data formats.

	>>> import rasterIO
	>>> band_number = 1
	>>> rasterdata = rasterIO.readrasterband(gdal_file_pointer, band_number)
	
	
Dependencies
------------
Python 2.5 or greater
Numerical python (Numpy) 1.2.1 or greater

License & Authors
-----------------
Copyright: Tom Holderness
Development team: Tom Holderness, Andrew Hardy, Nathan Forsythe
Released under the Simplified BSD License (see LICENSE.txt).
'''
__version__ = "1.0.1"
#!/usr/bin/env python
# raster.py - module of raster handling functions using GDAL and NUMPY
# T.Holderness 19/05/2010
#
# ChangeLog
# 02/08/2010 - TH - Added NoDataVal handling for both read and write.
# 04/08/2010 - TH - Added PCRS support using WKT from source image metadata
# 			New function wkt2epsg
# 04/08/2010 - TH - Moved UHII function to avhrr.py
# 18/08/2010 - TH - Moved all AVHRR specific functions to avhrr.py
# Functions moved: "ndvi" and "lst"
# 23/08/2010 - TH - Moved all statistical functions to rasterStats.py.v1
# 23/08/2010 - TH - Moved all processing functions to rasterProcs.py.v1
# 23/08/2010 - TH - Moved this file (remaining functions) to rasterIO.py.v1
# rasterIO.py.v1
# 06/09/2010 - TH - readrasterband - Added masking to NaN values.
# 05/11/2010 - TH - opengdalraster - Added exception, raising IOError if opening broken raster.
# 10/11/2010 - TH - Added exceptions, raising errors where appropriate.
# 10/11/2010 - TH - Marked this as version 1.0.1 - working.
import os, sys, struct
import numpy as np
import numpy.ma as ma
import osgeo.osr as osr
import osgeo.gdal as gdal
from osgeo.gdalconst import *
#
# function to open GDAL raster dataset
def opengdalraster(fname):
	'''Accepts gdal compatible file on disk and returns gdal pointer.'''
	dataset = gdal.Open( fname, GA_ReadOnly)
	if dataset != None:
		return dataset
	else: 
		raise IOError
		
# function to read raster image metadata
def readrastermeta(dataset):
	'''Accepts GDAL raster dataset and returns, gdal_driver, XSize, YSize, projection info(well known text), geotranslation data.'''
		# get GDAL driver
	driver_short = dataset.GetDriver().ShortName
	driver_long = dataset.GetDriver().LongName
		# get projection	
	proj_wkt = dataset.GetProjection()
		# get geotransforamtion parameters
	geotransform = dataset.GetGeoTransform()
		# geotransform[0] = top left x
		# geotransform[1] = w-e pixel resolution
		# geotransform[2] = rotation, 0 if image is "north up"
		# geotransform[3] = top left y
		# geotransform[4] = rotation, 0 if image is "north up"
		# geotransform[5] = n-s picel resolution
	XSize = dataset.RasterXSize
	YSize = dataset.RasterYSize
	
	return driver_short, XSize, YSize, proj_wkt, geotransform

# function to read a band from a dataset
def readrasterband(dataset, aband):
	'''Accepts GDAL raster dataset and band number, returns Numpy 2D-array.'''
	if dataset.RasterCount >= aband:		
		# Get one band
		band = dataset.GetRasterBand(aband)
		if band.GetNoDataValue() != None:
			NoDataVal = band.GetNoDataValue()
		else:
			NoDataVal = 0
			band.SetNoDataValue(NoDataVal)
			#print "Warning NoDataValue not found, assuming 0!".format(dataset,aband)
		# create blank array (full of 0's) to hold extracted data [note Y,X format]
		dt = np.dtype(np.float32)
		datarray = np.zeros( ( band.YSize,band.XSize ), dtype=dt )
			# create loop based on YAxis (i.e. num rows)
		for i in range(band.YSize):
			# read lines of band	
			scanline = band.ReadRaster( 0, i, band.XSize, 1, band.XSize, 1, GDT_Float32)
			# unpack from binary representation
			tuple_of_floats = struct.unpack('f' * band.XSize, scanline)
			# add tuple to image array line by line
			datarray[i,:] = tuple_of_floats	
		# apply mask for NoDataVal
		dataraster = ma.masked_values(datarray, NoDataVal)
		# apply mask for NaN values
		datarasterNaN = ma.masked_invalid(dataraster)
		# return array (raster)
		return datarasterNaN
	else:
		raise TypeError	

# create function to write GeoTiff raster from NumPy n-dimensional array
def writerasterband(myraster, outfile, format, aXSize, aYSize, geotrans, epsg):
	''' Accepts raster in Numpy 2D-array, outputfile string, format and geotranslation metadata and writes to file on disk'''
	# get noDataValue from matrix mask value
	# print myraster.fill_value
	if type(myraster) == np.ma.core.MaskedArray:
		NoDataVal = myraster.fill_value
	else:
		NoDataVal = 9999
	# get dtype of input array
	if myraster.dtype == 'int16':
		gdal_dtype = gdal.GDT_Int16
	else:
		gdal_dtype = gdal.GDT_Float32
	# get driver and driver properties	
	driver = gdal.GetDriverByName( format )
	metadata  = driver.GetMetadata()
	# check that specified driver has gdal create method and go create	
	if metadata.has_key(gdal.DCAP_CREATE) and metadata[gdal.DCAP_CREATE] =='YES':
		# Creare destination data-set
		#dst_ds = driver.Create( outfile, aXSize, aYSize, 1, gdal.GDT_Float32 )
		dst_ds = driver.Create( outfile, aXSize, aYSize, 1, gdal_dtype )
		# define "srs" as a home for coordinate system parameters
		srs = osr.SpatialReference()
		# import the standard OSGB36/BNG EPSG ProjCRS
		srs.ImportFromEPSG( epsg )
		# apply the geotransformation taken frok previosu image (Dundee = OSTN02 London localised?)
		dst_ds.SetGeoTransform( geotrans )
		# export these features to embedded well Known Text in the GeoTiff
		dst_ds.SetProjection( srs.ExportToWkt() )
		# write the raster band to file
		dst_ds.GetRasterBand(1).SetNoDataValue(NoDataVal)
		dst_ds.GetRasterBand(1).WriteArray ( myraster )
		dst_ds = None
	# catch error if no write method for format specified
	else:
		#print 'Error, GDAL %s driver does not support Create() method.' % outformat
		raise TypeError
#
# function to get Authority (e.g. EPSG) code from well known text
def wkt2epsg(wkt):
	'''
	Accepts well known text of Projection/Coordinate Reference System and generates
	EPSG code'''
	srs = osr.SpatialReference(wkt)
	if (srs.IsProjected()):
		try:
			return int(srs.GetAuthorityCode("PROJCS"))
		except TypeError:
			sys.stderr.write("Message from rasterIO.wkt2epsg:\t Projected EPSG code not found, wkt2epg will return EPSG of 0.\n")			
			return int(0)
		else:
			return int(0)	
	else:
		return int(srs.GetAuthorityCode("GEOGCS"))


	 
