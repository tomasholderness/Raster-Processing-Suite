"""
/***************************************************************************
Name		     : Raster Processing Suite
Description          : Perform raster math calculations 
Date                 : 05/10/2010
copyright            : (C) 2010 Tom Holderness & Newcastle University
contact              : http://www.students.ncl.ac.uk/tom.holderness 
license		     : Relseased under Simplified BSD license (see LICENSE.txt)
 ***************************************************************************/
"""
#
# 03/11/2010 - TH - Added support for opening layers in QGIS
# 05/11/2010 - TH - Changes in rasterIO catch IOErrors from broken raster images
#		- Also removed open file support. User must now open rasters in QGIS
#		- Added error catching for using rasters of different shape/size
#
# 0.9.1
# 10/11/2010 - TH - Changed all "string".format() references for backwards compatability with Python 2.5 (QGIS Windows version)
# 10/11/2010 - TH - This release marked as "0.9.1" in __init__ using rasterIO.py.v1.0.1
# 10/11/2010 - TH - Changed Date/Time stamp to be Python 2.5 compatible
# 10/11/2010 - TH - Fixed "Band #" bug.
#
# 0.9.2
# 23/11/2010 - TH - This released marked as "0.9.2" in __init__ using rasterIO.py.v1.0.1
# 23/11/2010 - TH - Created repository for plugin: http://www.students.ncl.ac.uk/tom.holderness/pyraster/qgis_repo.xml
# 23/11/2010 - TH - Fixed bug number 6 (User Validation) - un-caught TypeError if no raster in Equation Editor.
# 23/11/2010 - TH - Fixed bug number 6b (User Validation) - un-caught user input errors if 'checkBoxGenerateOutput.isChecked() == False:'
# 23/11/2010 - TH - Added SyntaxError catch for user validation of equation.
# 23/11/2010 - TH - Added AttributeError catch (raised from rasterIO.writerasterband when output file is broken [i.e. no write permission]).
# 23/11/2010 - TH - Tidied a few sys.stderr.write statements to be Python 2.5 compliant (removed '.format()' statements).
# 23/11/2010 - TH - Get version from resources.__version__
# 23/11/2010 - TH - Get rasterIO.version from raster.__version__
# 03/11/2010 - TH - Added test python output to tab_2
#
# 0.9.3 (05/12/2010)
# 04/12/2010 - TH - This released marked as "0.9.3" in __init__ using rasterIO.py.v1.0.1
# 04/12/2010 - TH - Erdas Imagine (.img) write support.
# 04/12/2010 - TH - Python script tab - execute, save, open, open templates of python scripts for raster processing.
# 04/12/2010 - TH - Templates from website, fixed a few formatting bugs in 'batch_raster_script.py'
# 04/12/2010 - TH - Help tab: basic information, links to website and license.
# 04/12/2010 - TH - Tidied a few code comments.
# 05/12/2010 - TH - Added 'Processing...' run status output to Information for Python script execution. 
# 05/12/2010 - TH - Fixed papercut - added tooltips to buttons in Python script tab.

# Import the PyQt libraries
from PyQt4 import QtCore, QtGui
# Import standard libraries 
import sys, os, string
from os.path import isfile
# Import QGIS core
from qgis.core import *
import qgis
# Initialize Qt resources from file resources.py
import resources
# Import the dialog
from rasterProcessor_ui import Ui_Form
# rasterIO and associates 
import rasterIO
import numpy.ma as ma
from datetime import datetime
import __init__ as initfile
version = initfile.version
rasterIO_version = rasterIO.__version__
# Classes for redicreting stdout, stderr.
class StdOutLog:
			
	def __init__(self, edit, out):
		"""
		http://www.riverbankcomputing.com/pipermail/pyqt/2009-February/022025.html
		"""
		self.edit = edit
		self.out = out
		

	def write(self, m):
	    	self.edit.setTextColor(QtCore.Qt.black)
		self.edit.insertPlainText( m )
		self.edit.moveCursor(QtGui.QTextCursor.End)
	
class StdErrLog:
			
	def __init__(self, edit, out):
		"""
		http://www.riverbankcomputing.com/pipermail/pyqt/2009-February/022025.html
		"""
		self.edit = edit
		self.out = out

	def write(self, m):
	    	self.edit.setTextColor(QtCore.Qt.red)
		self.edit.insertPlainText( m )
		self.edit.moveCursor(QtGui.QTextCursor.End)


class StartQT4(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)
		self.ui = Ui_Form ()
		self.ui.setupUi(self)
		sys.stdout = StdOutLog( self.ui.textInformation, sys.stdout)
		sys.stderr = StdErrLog( self.ui.textInformation, sys.stderr)		
		sys.stdout.write(str(datetime.now().strftime("%d-%m-%Y %H:%M\n")))
		#conect signals and slots
		QtCore.QObject.connect(self.ui.listWidget_Layers,QtCore.SIGNAL("itemClicked(QListWidgetItem*)"),self.get_band_list)
		QtCore.QObject.connect(self.ui.listWidget_Layers,QtCore.SIGNAL("itemChanged(QListWidgetItem*)"),self.get_band_list)	
		QtCore.QObject.connect(self.ui.btnLoad,QtCore.SIGNAL("pressed()"),self.load_band_status)
		QtCore.QObject.connect(self.ui.btnLoad,QtCore.SIGNAL("released()"),self.load_band)
		QtCore.QObject.connect(self.ui.btnRun,QtCore.SIGNAL("pressed()"),self.run_status)		
		QtCore.QObject.connect(self.ui.btnRun,QtCore.SIGNAL("released()"),self.run)
		QtCore.QObject.connect(self.ui.btnClear,QtCore.SIGNAL("pressed()"),self.clear_EqEdit)
		QtCore.QObject.connect(self.ui.btnSave,QtCore.SIGNAL("clicked()"),self.save_file_dialog)
		QtCore.QObject.connect(self.ui.checkBoxGenerateOutput,QtCore.SIGNAL("toggled(bool)"),self.disable_output)
		# Math operators
		QtCore.QObject.connect(self.ui.btnAddition,QtCore.SIGNAL("clicked()"),self.insertAdd)
		QtCore.QObject.connect(self.ui.btnSubtract,QtCore.SIGNAL("clicked()"),self.insertMinus)
		QtCore.QObject.connect(self.ui.btnDivide,QtCore.SIGNAL("clicked()"),self.insertDivide)
		QtCore.QObject.connect(self.ui.btnMultiply,QtCore.SIGNAL("clicked()"),self.insertMult)
		QtCore.QObject.connect(self.ui.btnSqRoot,QtCore.SIGNAL("clicked()"),self.insertRoot)
		QtCore.QObject.connect(self.ui.btnSquared,QtCore.SIGNAL("clicked()"),self.insertPower)
		QtCore.QObject.connect(self.ui.btnRBracket,QtCore.SIGNAL("clicked()"),self.insertRbracket)
		QtCore.QObject.connect(self.ui.btnLBracket,QtCore.SIGNAL("clicked()"),self.insertLbracket)		
		QtCore.QObject.connect(self.ui.btnMean,QtCore.SIGNAL("clicked()"),self.insertMean)
		QtCore.QObject.connect(self.ui.btnStDev,QtCore.SIGNAL("clicked()"),self.insertStDev)
		QtCore.QObject.connect(self.ui.btn0,QtCore.SIGNAL("clicked()"),self.insertZero)
		QtCore.QObject.connect(self.ui.btn1,QtCore.SIGNAL("clicked()"),self.insertOne)
		QtCore.QObject.connect(self.ui.btn2,QtCore.SIGNAL("clicked()"),self.insertTwo)
		QtCore.QObject.connect(self.ui.btn3,QtCore.SIGNAL("clicked()"),self.insertThree)
		QtCore.QObject.connect(self.ui.btn4,QtCore.SIGNAL("clicked()"),self.insertFour)
		QtCore.QObject.connect(self.ui.btn5,QtCore.SIGNAL("clicked()"),self.insertFive)
		QtCore.QObject.connect(self.ui.btn6,QtCore.SIGNAL("clicked()"),self.insertSix)
		QtCore.QObject.connect(self.ui.btn7,QtCore.SIGNAL("clicked()"),self.insertSeven)
		QtCore.QObject.connect(self.ui.btn8,QtCore.SIGNAL("clicked()"),self.insertEight)
		QtCore.QObject.connect(self.ui.btn9,QtCore.SIGNAL("clicked()"),self.insertNine)
		QtCore.QObject.connect(self.ui.btnPoint,QtCore.SIGNAL("clicked()"),self.insertPoint)
		# Tab_2 buttons (Python scripts)
		QtCore.QObject.connect(self.ui.btnClearScript,QtCore.SIGNAL("clicked()"),self.clear_Pyout)
		QtCore.QObject.connect(self.ui.btnRunScript,QtCore.SIGNAL("pressed()"),self.run_status)
		QtCore.QObject.connect(self.ui.btnRunScript,QtCore.SIGNAL("released()"),self.run_Pyout)
		QtCore.QObject.connect(self.ui.btnSaveScript,QtCore.SIGNAL("clicked()"),self.save_Pyout)
		QtCore.QObject.connect(self.ui.btnOpenScript,QtCore.SIGNAL("clicked()"),self.open_Pyout)
		QtCore.QObject.connect(self.ui.btnOpenTemplate,QtCore.SIGNAL("clicked()"),self.open_template)
		QtCore.QObject.connect(self.ui.btnViewLicense,QtCore.SIGNAL("clicked()"),self.print_license)
		# Get the rasters that have been loaded into QGIS
		self.add_band()
		# Add some text to PyOut
		#self.ui.textPyout.setTextColor(QtCore.Qt.blue)
		self.ui.textPyout.insertPlainText('#!/usr/bin/env python\n')
		self.ui.textPyout.insertPlainText('import rasterIO\n')
		self.ui.textPyout.insertPlainText('import numpy.ma as ma\n\n')
		#self.ui.textPyout.setTextColor(QtCore.Qt.black)
			
	# Add band function	
	def add_band(self):
		self.layermap = QgsMapLayerRegistry.instance().mapLayers()
		for (name, layer) in self.layermap.iteritems():
			if type(layer).__name__ == "QgsRasterLayer":
				raster =  layer.source()
				try:
					raster_str = str(raster)
					rasterIO.opengdalraster(raster_str)
					self.ui.listWidget_Layers.addItem(raster_str)
					self.ui.listWidget_Layers.setCurrentRow(0)
					self.get_band_list()
				except IOError:
					sys.stderr.write('IOError from file: ')
					sys.stderr.write(raster_str)
					sys.stderr.write('\n')
	def write(self,astring):
		self.ui.textInformation.append(astring)
	def exit(self):
		quit()
	def load_band_status(self):
		sys.stdout.write('Reading raster data...\n')
	# Math functions
	def insertStDev(self):
		self.ui.textEqEdit.insertPlainText(" ma.std( )")
		self.ui.textEqEdit.moveCursor(QtGui.QTextCursor.PreviousCharacter)
		#self.ui.statusbar.showMessage("Band standard deviation from Masked Array (ma) numerical library",4000)
	def insertRbracket(self):
		self.ui.textEqEdit.insertPlainText(") ")
	def insertLbracket(self):
		self.ui.textEqEdit.insertPlainText("( ")
	def insertRoot(self):
		self.ui.textEqEdit.insertPlainText("ma.sqrt( )")
		self.ui.textEqEdit.moveCursor(QtGui.QTextCursor.PreviousCharacter)
	def insertPower(self):
		self.ui.textEqEdit.insertPlainText("ma.power( ,2)")
		self.ui.textEqEdit.moveCursor(QtGui.QTextCursor.PreviousCharacter)
		self.ui.textEqEdit.moveCursor(QtGui.QTextCursor.PreviousCharacter)
		self.ui.textEqEdit.moveCursor(QtGui.QTextCursor.PreviousCharacter)
	def insertMean(self):
		self.ui.textEqEdit.insertPlainText(" ma.mean( )")
		self.ui.textEqEdit.moveCursor(QtGui.QTextCursor.PreviousCharacter)
	def insertAdd(self):
		self.ui.textEqEdit.insertPlainText("+ ")
	def insertMinus(self):
		self.ui.textEqEdit.insertPlainText("- ")
	def insertDivide(self):
		self.ui.textEqEdit.insertPlainText("/ ")
	def insertMult(self):
		self.ui.textEqEdit.insertPlainText("* ")
	def insertZero(self):
		self.ui.textEqEdit.insertPlainText("0")
	def insertOne(self):
		self.ui.textEqEdit.insertPlainText("1")
	def insertTwo(self):
		self.ui.textEqEdit.insertPlainText("2")
	def insertThree(self):
		self.ui.textEqEdit.insertPlainText("3")
	def insertFour(self):
		self.ui.textEqEdit.insertPlainText("4")
	def insertFive(self):
		self.ui.textEqEdit.insertPlainText("5")
	def insertSix(self):
		self.ui.textEqEdit.insertPlainText("6")
	def insertSeven(self):
		self.ui.textEqEdit.insertPlainText("7")
	def insertEight(self):
		self.ui.textEqEdit.insertPlainText("8")
	def insertNine(self):
		self.ui.textEqEdit.insertPlainText("9")	
	def insertPoint(self):
		self.ui.textEqEdit.insertPlainText(".")
	def disable_output(self):
		if self.ui.btnSave.isEnabled() == True:
			self.ui.btnSave.setEnabled(False)
			self.ui.lineOutfile.setEnabled(False)
			self.ui.comboFormats.setEnabled(False)
			self.ui.checkBoxQGIS.setEnabled(False)
			self.ui.labelSaveNewRaster.setEnabled(False)
		else:
			self.ui.btnSave.setEnabled(True)
			self.ui.lineOutfile.setEnabled(True)
			self.ui.comboFormats.setEnabled(True)
			self.ui.checkBoxQGIS.setEnabled(True)
			self.ui.labelSaveNewRaster.setEnabled(True)
	# Get a list of bands available in the raster	
	def get_band_list(self):
		if (self.ui.listWidget_Layers.count() > 0):
			fname = self.ui.listWidget_Layers.currentItem().text()
			fname_Str = str(fname)
			inraster = rasterIO.opengdalraster(fname_Str)
			numbands = inraster.RasterCount
			self.ui.comboBands.clear()
			self.ui.comboBands.addItem("Band #")		
			for i in range(1,numbands +1):
				self.ui.comboBands.addItem(str(i))
			self.ui.comboBands.setCurrentIndex(1)
	# Load the band into memory
	def load_band(self):
		file_count = self.ui.listWidget_Layers.count()		
		if file_count < 1:
			sys.stderr.write('Error: No input files, open a raster file first!\n')
		else:	
			if self.ui.comboBands.currentText() == 'Band #':
				sys.stderr.write('Select which band number to load.\n')
			else:
				band_num = int(self.ui.comboBands.currentText())
				fname = self.ui.listWidget_Layers.currentItem().text()
				fname_Str = str(fname)
				basename = os.path.basename(fname_Str)
				basename = os.path.splitext(basename)
				basename = basename[0]		
				cleaname_a = string.replace(basename, '.', '_') 
				cleaname = string.replace(cleaname_a, '-', '_')
				newname = cleaname+'_'+str(band_num)	
				rasterpointer = rasterIO.opengdalraster(fname_Str)
				global driver, XSize, YSize, proj, geotrans		
				global bandname
				bandname = newname
				globals()[bandname] = rasterIO.readrasterband(rasterpointer, band_num)
				driver, XSize, YSize, proj, geotrans = rasterIO.readrastermeta(rasterpointer)		
				self.ui.textEqEdit.insertPlainText(bandname+" ")
				sys.stdout.write("Loaded: ")
				sys.stdout.write(str(fname_Str))
				sys.stdout.write(", band: ")
				sys.stdout.write(str(band_num))
				sys.stdout.write("\n")
				self.ui.textPyout.insertPlainText('# open a file pointer\n')
				self.ui.textPyout.insertPlainText('rasterpointer = rasterIO.opengdalraster("%s")\n' %(fname_Str))
				self.ui.textPyout.insertPlainText('# read a raster band\n')
				self.ui.textPyout.insertPlainText('%s = rasterIO.readrasterband(rasterpointer, %i)\n' %(bandname, band_num))
				self.ui.textPyout.insertPlainText('# get file metadata: format, X, Y, projection, geo-parameters\n')
				self.ui.textPyout.insertPlainText('driver, XSize, YSize, proj, geotrans = rasterIO.readrastermeta(rasterpointer)\n\n')
	# print user information that process is running			
	def run_status(self):
		sys.stdout.write('Processing...\n')
	# execute process
	def run(self):
		# Get inputs
		outname = str(self.ui.lineOutfile.text())
		eqstring = str(self.ui.textEqEdit.toPlainText())
		# Basic user validation
		if (len(eqstring) < 1):
			sys.stderr.write('Error: No equation to process.\n')
		elif(self.ui.listWidget_Layers.count() < 1):
			sys.stderr.write('Error: No input files.\n')
		# Process to new file	
		else:	
			try:
				# Test if output box is checked
				if self.ui.checkBoxGenerateOutput.isChecked() == False:
					if (len(outname) < 1):
						sys.stderr.write('Error: No output filename specified.\n')
					else:
						newband = eval(eqstring)
						newband = ma.masked_values(newband, 9999.0)
						epsg = rasterIO.wkt2epsg(proj)
						# setup python dictionary of rgdal formats and drivers
						formats = {'GeoTiff (.tif)':'.tif','Erdas Imagine (.img)':'.img'}
						drivers = {'GeoTiff (.tif)':'GTiff','Erdas Imagine (.img)':'HFA'}
						out_ext = formats[str(self.ui.comboFormats.currentText())]
						driver = drivers[str(self.ui.comboFormats.currentText())]
						outfile = outname + out_ext
						#driver = 'GTiff'
						rasterIO.writerasterband(newband, outfile, driver, XSize, YSize, geotrans, epsg)
						sys.stdout.write('Process complete, created newfile ')
						sys.stdout.write(str(outfile))
						sys.stdout.write('\n')
						if self.ui.checkBoxQGIS.isEnabled() == True:
							qgis.utils.iface.addRasterLayer(outfile)
						self.ui.textPyout.insertPlainText('# create a new matrix from equation\n')
						self.ui.textPyout.insertPlainText('newband = %s\n' %(eqstring))
						self.ui.textPyout.insertPlainText('# get the epsg code from the projection\n')
						self.ui.textPyout.insertPlainText('epsg = rasterIO.wkt2epsg(proj)\n')
						self.ui.textPyout.insertPlainText('# set the gdal driver / output file type\n')
						self.ui.textPyout.insertPlainText('driver = "%s"\n' %(driver))
						self.ui.textPyout.insertPlainText('# specify the new output file\n')
						self.ui.textPyout.insertPlainText('outfile = "%s"\n' %(outfile))
						self.ui.textPyout.insertPlainText('# write the new matrix to the new file\n')
						self.ui.textPyout.insertPlainText('rasterIO.writerasterband(newband, outfile, driver, XSize, YSize, geotrans, epsg)\n\n')
						self.ui.textPyout.insertPlainText('# add the new file to qgis\n')
						self.ui.textPyout.insertPlainText('qgis.utils.iface.addRasterLayer(outfile)\n\n')
				else:
					outputstring = (str(eval(str(self.ui.textEqEdit.toPlainText())))) +'\n'
					self.ui.textInformation.setTextColor(QtGui.QColor(0,0,255))
					self.ui.textInformation.insertPlainText(outputstring)
					self.ui.textInformation.moveCursor(QtGui.QTextCursor.End)
					self.ui.textPyout.insertPlainText('# run without output file\n')
					self.ui.textPyout.insertPlainText('print %s\n\n' %(eqstring))
			except ValueError:
				sys.stderr.write('Error: Could not perform calculation. Are input rasters same shape and size? Is the output a matrix?\n')
			except TypeError:
				sys.stderr.write('Error: Could not perform calculation. Are input rasters loaded?\n')
			except SyntaxError:
				sys.stderr.write('Error: Could not perform calculation. Is the equation correct?\n')
			except AttributeError:
				sys.stderr.write('Error: Could not perform calculation. Is the output raster correct?\n')
	# Python script functions			
	def run_Pyout(self):
		try:
			commandstring = str(self.ui.textPyout.toPlainText())
			exec(commandstring)
		except:
			sys.stderr.write('Error: There was an error in the script.\n')
	def save_file_dialog(self):
		fd = QtGui.QFileDialog.getSaveFileName(self)
		self.ui.lineOutfile.insert(fd)	
	def clear_EqEdit(self):
		self.ui.textEqEdit.clear()
	def clear_Pyout(self):
		self.ui.textPyout.clear()
		self.ui.textPyout.insertPlainText('#!/usr/bin/env python\n')
		self.ui.textPyout.insertPlainText('import rasterIO\n')
		self.ui.textPyout.insertPlainText('import numpy.ma as ma\n\n')
	def save_Pyout(self):
		try:		
			#fd = QtGui.QFileDialog.getSaveFileName(self,"Save script", "Python scripts (*.py)")
			fd = QtGui.QFileDialog.getSaveFileName(self, "Save script", "", "Python files: *.py")			
			if fd != '':
				fd = fd+'.py'
				outfile = open(fd,'w')
				print >> outfile, str(self.ui.textPyout.toPlainText())
				sys.stdout.write('Saved script to file\n')  
		except IOError:
			sys.stderr.write('Error: There was an error saving the python script\n')
		
	def open_Pyout(self):
		try:
			fd = QtGui.QFileDialog.getOpenFileName(self, "Open script", "", "Python files: *.py ;; Text files: *.txt ;; All files: *.*")
			if fd != '':
				infile = open(fd,'r')
				script = infile.read()
				self.ui.textPyout.clear()
				self.ui.textPyout.insertPlainText(script)
		except IOError:
			sys.stderr.write('Error: There was an error opening the python script\n')
	def open_template(self):
		try:
			cdir = os.getcwd()
			template_dir = os.environ['HOME']+'/.qgis/python/plugins/raster_processing_suite/templates/'			
			os.chdir(template_dir)			
			fd = QtGui.QFileDialog.getOpenFileName(self, "Open template script", "", "Python files: *.py ;; Text files: *.txt ;; All files *.*")
			if fd != '':
				infile = open(fd,'r')
				script = infile.read()
				self.ui.textPyout.clear()
				self.ui.textPyout.insertPlainText(script)	
			os.chdir(cdir)
		except IOError:
			sys.stderr.write('Error: There was an error opening the python script\n')

	def print_license(self):
		try:		
			license = open(os.environ['HOME']+'/.qgis/python/plugins/raster_processing_suite/LICENSE.TXT')
			text = license.read()
			#sys.stdout.write(text)
			#print text
			self.ui.textInformation.insertPlainText(text)
		except IOError:
			sys.stdout.write("Error: Can't open LICENSE.TXT'.") 
class RasterProcessingSuite: 

	def __init__(self, iface):
		# Save reference to the QGIS interface
		self.iface = iface

	def initGui(self):  
		# Create action that will start plugin configuration
		self.action = QtGui.QAction(QtGui.QIcon(":/plugins/raster_processing_suite/icon.png"),"Raster Processing Suite", self.iface.mainWindow())
		# connect the action to the run method
		QtCore.QObject.connect(self.action, QtCore.SIGNAL("triggered()"), self.run) 
		self.iface.addPluginToMenu("&PyRaster Tools", self.action)

	def unload(self):
		# Remove the plugin menu item and icon
		self.iface.removePluginMenu("&PyRaster Tools",self.action)

	def start(self):
		print "start"
		myapp = StartQT4()
		myapp.show()
  	# run method that performs all the real work
	def run(self):
		myapp = StartQT4()
		myapp.show()
		result = myapp.exec_() 
		if result == 1: 
		      pass 
	
		   

	
 
