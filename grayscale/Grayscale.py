# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Grayscale
                                 A QGIS plugin
 Turns rgb rasters into single band rasters.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject, QgsRasterInterface, Qgis
from osgeo import gdal, osr, ogr
import numpy as np

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Grayscale_dialog import GrayscaleDialog
import os.path



class Grayscale:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Grayscale_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Grayscale')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Grayscale', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):


        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """
        icon_path = ":/plugins/Grayscale/icon.png"
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        print(icon_path)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Grayscale/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Grayscale'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&Grayscale'),
                action)
            self.iface.removeToolBarIcon(action)

    def sel_output_file(self):

        fn, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select output file ","", 'TIFF *.tif') #TODO: disallow invalid path names, allow other file formats
        self.dlg.leOutput.setText(fn)

    def create_grayscale_raster(self, raster, filename, round):

        ds = gdal.Open(raster.dataProvider().dataSourceUri())
        bc = raster.bandCount()
        gs = [0 for i in range(bc)]
        for x in range(bc):
            gs[x] = ds.GetRasterBand(x + 1).ReadAsArray() / bc
        arr_gs = sum(gs)
        if round == True:
            arr_gs = np.round(arr_gs)
        x_extent = ds.RasterXSize
        y_extent = ds.RasterYSize
        geot = ds.GetGeoTransform()
        proj = ds.GetProjection()

        driver = gdal.GetDriverByName('GTiff')
        n_ds = driver.Create(filename, xsize=x_extent, ysize=y_extent, bands=1, eType=gdal.GDT_Float32)
        n_ds.GetRasterBand(1).WriteArray(arr_gs)

        n_ds.SetGeoTransform(geot)
        srs = osr.SpatialReference()
        srs.SetUTM(35, 1)
        srs.SetWellKnownGeogCS('ETRS89') #TODO: let user set cs and UTM
        n_ds.SetProjection(proj)
        n_ds = None

        iface = self.iface
        rlayer = iface.addRasterLayer(filename)
        self.iface.messageBar().pushMessage("Grayscale successful",
        "Output raster written in " + filename,
        level=Qgis.Success, duration=5)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = GrayscaleDialog()
            self.dlg.pbOutput.clicked.connect(self.sel_output_file)

        layers = QgsProject.instance().layerTreeRoot().children()
        self.dlg.cbLayers.clear()
        self.dlg.cbLayers.addItems([layer.name() for layer in layers])

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            layer_index = self.dlg.cbLayers.currentIndex()
            raster = layers[layer_index].layer()
            n_fn = self.dlg.leOutput.displayText()
            do_round = self.dlg.chbRound.isChecked()
            self.create_grayscale_raster(raster,n_fn, do_round)#TODO: add a progress bar and an option to cancel
