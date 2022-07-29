__author__ = 'pascal capone'

'''Required packages'''
#General:
import sys
import argparse
import re
import numpy as np
import json
#matplotlib:
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('Qt5Agg')
#astropy:
from astropy.io import fits
#PyQt5:
from PyQt5 import QtCore, QtWidgets, uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as FigureToolbar
#Debug:
import datetime
#Test:
#import glob
#import random

'''Catalogs'''
with open(sys.path[0] + "/extensions_catalog.json", "r") as file:
    extensions = json.load(file)
    
units = {"m": 1., "cm": 1e-2, "mm": 1e-3, "µm": 1e-6, "nm": 1e-9, "Å": 1e-10}

'''FITS 1D Spectrum Plotter'''
Ui_MainWindow, QtBaseClass = uic.loadUiType(sys.path[0] + "/fits1dsp_main.ui")
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        self.help_window = HelpWindow()
        
        self.button_help.clicked.connect(self.help)
        self.button_quit.clicked.connect(self.quit)
        self.button_browse_fits.clicked.connect(self.browse_fits)
        self.button_select_all_fits.clicked.connect(self.select_all_fits)
        self.button_unselect_all_fits.clicked.connect(self.unselect_all_fits)
        self.button_remove_fits.clicked.connect(self.remove_fits)
        self.button_clear_fits.clicked.connect(self.clear_fits)
        self.button_info_fits.clicked.connect(self.load_info)
        self.button_browse_telluric.clicked.connect(self.browse_telluric)
        self.button_remove_telluric.clicked.connect(self.remove_telluric)
        self.button_clear_telluric.clicked.connect(self.clear_telluric)
        self.button_plot_separate.clicked.connect(self.plot_separate)
        self.button_plot_together.clicked.connect(self.plot_together)
        
        self.table_fits.setColumnWidth(0, 29)         
        self.table_fits.itemClicked.connect(self.select_fits)
        self.selected_fits = list()
        
        self.tabWidget_info.clear()
        self.tabWidget_info.setUsesScrollButtons(True)
        self.info_fits = list()
    
        self.table_telluric.setColumnWidth(0, 29)
        self.table_telluric.itemClicked.connect(self.select_telluric)
        self.selected_telluric = None
        self.selected_telluric_data = None
        
        self.tabWidget_plot.clear()
        self.plotted_fits = list()
        self.plotted_channel = list()
        
        #self.button_test.clicked.connect(self.test)
    
    #def test(self):

    def help(self):
        self.help_window.display_help()
        
    def quit(self):
        plt.close('all')
        self.close()
    
    def browse_fits(self):
        files_fits = QtWidgets.QFileDialog.getOpenFileNames(self, "Select one or more reduced FITS files", " ", filter = "*.fits")[0]
        self.make_table_fits(files_fits)
        
    def make_table_fits(self, files):
        row = self.table_fits.rowCount()
        self.table_fits.setRowCount(row + len(files))
        for item in files:
            checkbox_fits = QtWidgets.QTableWidgetItem(row)
            checkbox_fits.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                   QtCore.Qt.ItemIsEnabled)
            checkbox_fits.setCheckState(QtCore.Qt.Unchecked)
            self.table_fits.setItem(row, 0, checkbox_fits)
            self.table_fits.setItem(row, 1, QtWidgets.QTableWidgetItem(item))
            with fits.open(item) as hdul:
                self.table_fits.setItem(row, 2, QtWidgets.QTableWidgetItem(hdul[0].header["OBJECT"]))
                self.table_fits.setItem(row, 3, QtWidgets.QTableWidgetItem(hdul[0].header["DATE-OBS"]))
                self.table_fits.setItem(row, 4, QtWidgets.QTableWidgetItem(hdul[0].header["INSTRUME"]))
                try:
                    self.table_fits.setItem(row, 5, QtWidgets.QTableWidgetItem(hdul[0].header["SUBSYS"]))
                except:
                    self.table_fits.setItem(row, 5, QtWidgets.QTableWidgetItem("-"))
                hdul.close()
            row += 1
            
    def select_fits(self, checkbox):
        if checkbox.column() == 0:
            if checkbox.checkState() == QtCore.Qt.Checked:
                if self.table_fits.item(checkbox.row(), 1) not in self.selected_fits:
                    self.selected_fits.append(self.table_fits.item(checkbox.row(), 1))
                else:
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nInstruction: Make sure to click on the checkbox and not on the table cell containing it.")
            if checkbox.checkState() == QtCore.Qt.Unchecked:
                try:
                    self.selected_fits.remove(self.table_fits.item(checkbox.row(), 1))
                except:
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nInstruction: Make sure to click on the checkbox and not on the table cell containing it.")

    def select_all_fits(self):
        self.selected_fits.clear()
        for r in range(self.table_fits.rowCount()):
            self.table_fits.item(r, 0).setCheckState(QtCore.Qt.Checked)
            self.selected_fits.append(self.table_fits.item(r, 1))
        
    def unselect_all_fits(self):
        self.selected_fits.clear()
        for r in range(self.table_fits.rowCount()):
            self.table_fits.item(r, 0).setCheckState(QtCore.Qt.Unchecked)
    
    def remove_fits(self):
        rows = [self.table_fits.row(item) for item in self.selected_fits]
        rows.sort(reverse = True)
        for r in rows:
            item = self.table_fits.item(r, 1)
            
            if item in self.info_fits:
                tab_index = np.where(item == np.array(self.info_fits))[0][0]
                self.info_fits.remove(item)
                self.tabWidget_info.removeTab(tab_index)
            
            if item in self.selected_fits:
                self.selected_fits.remove(item)
            
            index = [j for j in range(len(self.plotted_fits)) if item in self.plotted_fits[j]]
            index.sort(reverse = True)
            for i in index:
                del self.plotted_fits[i]
                del self.plotted_channel[i]
                self.tabWidget_plot.removeTab(i)
                
            self.table_fits.removeRow(r)
        
        #Change the name of the remaining tabs accordingly to their new position in the selection table
        for item in self.info_fits:
            tab_index = np.where(item == np.array(self.info_fits))[0][0]
            tab_name = "File " + str(self.table_fits.row(item) + 1)
            self.tabWidget_info.setTabText(tab_index, tab_name)
        
        for items in self.plotted_fits:
            tab_index = [i for i in range(len(self.plotted_fits)) if items == self.plotted_fits[i]]
            for i in tab_index:
                if len(self.plotted_fits[i]) == 1:
                    tab_name = "File " + str(self.table_fits.row(items[0]) + 1)
                else:
                    tab_name = "Files "
                    for i, item in enumerate(items):
                        tab_name += str(self.table_fits.row(item) + 1) + ","
                    tab_name = tab_name[:-1]
                tab_name += " (" + self.plotted_channel[i] + ")"
                self.tabWidget_plot.setTabText(i, tab_name)
                
    
    def clear_fits(self):
        self.table_fits.clearContents()
        self.table_fits.setRowCount(0)
        self.selected_fits.clear()
        self.info_fits.clear()
        self.tabWidget_info.clear()
        self.plotted_fits.clear()
        self.plotted_channel.clear()
        self.tabWidget_plot.clear()
        
    def load_info(self):
        if self.selected_fits == list():
            self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nError: No FITS file selected.")
        else:
            for item in self.selected_fits:
                if item in self.info_fits:
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nWarning: Selected FITS file already inspected.")
                else:
                    self.info_fits.append(item)
                    
                    tab_name = "File " + str(self.table_fits.row(item) + 1) #Take the numbering of the selection table
                    self.tabWidget_info.addTab(InfoTab(self.tabWidget_info), tab_name)
                    tab_index = self.tabWidget_info.count() - 1
                    tab_table_extension = self.tabWidget_info.widget(tab_index).table_extension
                    tab_table_extension.itemClicked.connect(self.select_extension)
                    tab_text_header = self.tabWidget_info.widget(tab_index).textBox_header
                    
                    filename = item.text()
                    with fits.open(filename) as hdul:
                        tab_table_extension.setRowCount(len(hdul))
                        for row, ext in enumerate(hdul):
                            checkbox_extension = QtWidgets.QTableWidgetItem(row)
                            checkbox_extension.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                                        QtCore.Qt.ItemIsEnabled)
                            if row == 0:
                                checkbox_extension.setCheckState(QtCore.Qt.Checked)
                            else:
                                checkbox_extension.setCheckState(QtCore.Qt.Unchecked)
                            tab_table_extension.setItem(row, 0, checkbox_extension)
                            tab_table_extension.setItem(row, 1, QtWidgets.QTableWidgetItem(ext.name))
                            try:
                                tab_table_extension.setItem(row, 2, QtWidgets.QTableWidgetItem(ext.header["XTENSION"].capitalize() + "HDU"))
                            except:
                                tab_table_extension.setItem(row, 2, QtWidgets.QTableWidgetItem("PrimaryHDU"))
                        tab_text_header.setText(repr(hdul[0].header))
                        hdul.close()
                        
    def select_extension(self, checkbox):
        if checkbox.column() == 0:
            if checkbox.checkState() == QtCore.Qt.Checked:
                rows = list(np.arange(self.tabWidget_info.currentWidget().table_extension.rowCount()))
                rows.remove(checkbox.row())
                for r in rows:
                    self.tabWidget_info.currentWidget().table_extension.item(r, 0).setCheckState(QtCore.Qt.Unchecked)
                filename = self.info_fits[self.tabWidget_info.currentIndex()].text()
                with fits.open(filename) as hdul:
                    self.tabWidget_info.currentWidget().textBox_header.setText(repr(hdul[checkbox.row()].header))
            if checkbox.checkState() == QtCore.Qt.Unchecked:
                rows = list(np.arange(self.tabWidget_info.currentWidget().table_extension.rowCount()))
                rows.remove(checkbox.row())
                for r in rows:
                    if self.tabWidget_info.currentWidget().table_extension.item(r, 0).checkState() == QtCore.Qt.Checked:
                        self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nInstruction: Make sure to click on the checkbox and not on the table cell containing it.")
                        break
                    if r == rows[-1]:
                        checkbox.setCheckState(QtCore.Qt.Checked)

    def browse_telluric(self):
        self.files_telluric = QtWidgets.QFileDialog.getOpenFileNames(self, "Select one or more telluric masks", " ", filter = "*.dat")[0]
        row = self.table_telluric.rowCount()
        self.table_telluric.setRowCount(row + len(self.files_telluric))
        for item in self.files_telluric:
            checkbox_telluric = QtWidgets.QTableWidgetItem(row)
            checkbox_telluric.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                   QtCore.Qt.ItemIsEnabled)
            checkbox_telluric.setCheckState(QtCore.Qt.Unchecked)
            self.table_telluric.setItem(row, 0, checkbox_telluric)
            self.table_telluric.setItem(row, 1, QtWidgets.QTableWidgetItem(item))
            try: # ??? This should not be necessary actually
                i = [pos for pos, char in enumerate(item) if char == "/"][-1]
                self.table_telluric.setItem(row, 2, QtWidgets.QTableWidgetItem(item[i+1:-4]))
            except:
                self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nWarning: Name of selected telluric mask not available.")
            row += 1

    def select_telluric(self, checkbox):
        if checkbox.column() == 0:
            if checkbox.checkState() == QtCore.Qt.Checked:
                self.selected_telluric = self.table_telluric.item(checkbox.row(), 1)
                self.selected_telluric_data = np.loadtxt(self.selected_telluric.text())
                rows = list(np.arange(self.table_telluric.rowCount()))
                rows.remove(checkbox.row())
                for r in rows:
                    self.table_telluric.item(r, 0).setCheckState(QtCore.Qt.Unchecked)
            if checkbox.checkState() == QtCore.Qt.Unchecked:
                self.selected_telluric = None
                self.selected_telluric_data = None
                
    def remove_telluric(self):
        self.table_telluric.removeRow(self.selected_telluric.row())
        self.selected_telluric = None
        self.selected_telluric_data = None
    
    def clear_telluric(self):
        self.table_telluric.clearContents()
        self.table_telluric.setRowCount(0)
        self.selected_telluric = None
        self.selected_telluric_data = None

    def plot_separate(self):
        if self.selected_fits == list():
            self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nError: No FITS file selected.")
        else:
            channel = self.comboBox_channel.currentText()
            for item in self.selected_fits:
                if ([item] in self.plotted_fits) and (channel in [self.plotted_channel[i] for i in [j for j in range(len(self.plotted_fits)) if [item] == self.plotted_fits[j]]]):
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nWarning: FITS file " + str(self.table_fits.row(item) + 1) + " already plotted.")
                    continue
                
                filename = item.text()
                try:
                    obj, date, instrument, wave, flux, err = self.get_data(filename)
                except:
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nError: Structure of FITS file " + str(self.table_fits.row(item) + 1) + " not present in the extensions catalog.")
                    continue
                
                if self.checkBox_normalization.checkState() == QtCore.Qt.Checked: # !!! Data not divided in échelle orders needs to be treated differently
                    flux_cont = list()
                    for w, f, e in zip(wave, flux, err):
                        flux_cont.append(self.fit_continuum(w, f, 1/e, 3))
                    flux /= flux_cont
                
                tab_name = "File " + str(self.table_fits.row(item) + 1) + " (" + channel + ")" #Take the numbering of the selection table
                self.tabWidget_plot.addTab(PlotTab(self.tabWidget_plot), tab_name)
                tab = self.tabWidget_plot.widget(self.tabWidget_plot.count() - 1)
                
                tab.ax.set_xlabel("Wavelength ["+self.comboBox_units.currentText()+"]")
                tab.ax.set_ylabel(r"Flux [abtr.]")
                tab.ax.grid(True, lw = 0.5 , c = 'grey', alpha = 0.5)
                tab.ax.plot(wave.flatten(), flux.flatten(), ls = '-', lw = 0.5, marker = '.', ms = 0.5, c = 'black', label = obj + " | " + date + " | " + instrument)
                try:
                    tab.ax.fill_between(self.selected_telluric_data[:,0], self.selected_telluric_data[:,1]*np.nanmax(flux), where=((self.selected_telluric_data[:,0] > np.nanmin(wave)) & (self.selected_telluric_data[:,0] < np.nanmax(wave))), facecolor = 'grey', alpha = 0.5)
                except:
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nWarning: No telluric mask selected for FITS file " + str(self.table_fits.row(item) + 1) + ".")
                tab.ax.legend()
                tab.fig.tight_layout()
                
                self.plotted_fits.append([item])
                self.plotted_channel.append(channel)

    def plot_together(self):
        channel = self.comboBox_channel.currentText()
        selected_fits_copy = self.selected_fits.copy() # ??? Requirement of a copy needs clarification
        #selected_fits_copy.append(channel)
        if self.selected_fits == list():
            self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nError: No FITS file selected.")
        elif (selected_fits_copy in self.plotted_fits) and (channel in [self.plotted_channel[i] for i in [j for j in range(len(self.plotted_fits)) if selected_fits_copy == self.plotted_fits[j]]]): # ??? np.where() doesn't seem to work
                self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nWarning: Selected FITS files already plotted.")
        else:
            if len(self.selected_fits) == 1:
                tab_name = "File " + str(self.table_fits.row(self.selected_fits[0]) + 1)
            else:
                tab_name = "Files "
                for i, item in enumerate(self.selected_fits):
                    tab_name += str(self.table_fits.row(item) + 1) + "," #Take the numbering of the selection table
                tab_name = tab_name[:-1]
            tab_name += " (" + channel + ")"
            self.tabWidget_plot.addTab(PlotTab(self.tabWidget_plot), tab_name)
            tab = self.tabWidget_plot.widget(self.tabWidget_plot.count() - 1)

            tab.ax.set_xlabel("Wavelength ["+self.comboBox_units.currentText()+"]")
            tab.ax.set_ylabel(r"Flux [abtr.]")
            tab.ax.grid(True, lw = 0.5 , c = 'grey', alpha = 0.5)
            for item in self.selected_fits:
                filename = item.text()
                try:
                    obj, date, instrument, wave, flux, err = self.get_data(filename)
                except:
                    self.tabWidget_plot.removeTab(self.tabWidget_plot.count() - 1)
                    self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nError: Structure of FITS file " + str(self.table_fits.row(item) + 1) + " not present in the extensions catalog.")
                    return
                
                if self.checkBox_normalization.checkState() == QtCore.Qt.Checked:
                    flux_cont = list()
                    for w, f, e in zip(wave, flux, err):
                        flux_cont.append(self.fit_continuum(w, f, 1/e, 3))
                    flux /= flux_cont
                    
                tab.ax.plot(wave.flatten(), flux.flatten(), ls = '-', lw = 0.5, marker = '.', ms = 0.5, label = obj + " | " + date + " | " + instrument)
            try:
                # !!! The limits np.nanmin(wave) and np.nanmax)(wave) are defined based on the last dataset, not overall.
                tab.ax.fill_between(self.selected_telluric_data[:,0], self.selected_telluric_data[:,1]*np.nanmax(flux), where=((self.selected_telluric_data[:,0] > np.nanmin(wave)) & (self.selected_telluric_data[:,0] < np.nanmax(wave))), facecolor = 'grey', alpha = 0.5)
            except:
                self.textBox_debug.append(str(datetime.datetime.now())[0:19] + "\nWarning: No telluric mask selected for selected FITS files.")
            tab.ax.legend()
            tab.fig.tight_layout()
            
            self.plotted_fits.append(selected_fits_copy) # ??? Requirement of a copy needs clarification
            self.plotted_channel.append(channel)
            
    def get_data(self, filename):
        with fits.open(filename) as hdul:
            obj = hdul[0].header["OBJECT"]
            date = hdul[0].header["DATE-OBS"][0:19]
            instrument = hdul[0].header["INSTRUME"]
            channel = self.comboBox_channel.currentText()
            
            _flux = hdul[extensions[instrument][channel]['flux']['data']].data
            _err = hdul[extensions[instrument][channel]['error']['data']].data
            _wave = hdul[extensions[instrument][channel]['wavelength']['data']].data
            _wave = (extensions[instrument][channel]['wavelength']['units']/units[self.comboBox_units.currentText()])*_wave # units conversion
            hdul.close()
        return obj, date, instrument, _wave, _flux, _err
        
    def fit_continuum(self, x, y, w, deg):
        x_cut = x[10:-10]
        y_cut = y[10:-10]
        w_cut = w[10:-10]
        #Mask bad pixel:
        m_nan = ~np.any(np.isnan([x_cut, y_cut, w_cut]), axis = 0)
        m_inf = ~np.any(np.isinf([x_cut, y_cut, w_cut]), axis = 0)
        m_null = ~np.any(np.array([x_cut, y_cut, w_cut]) == 0, axis = 0)
        m = np.logical_and(np.logical_and(m_nan, m_inf), m_null)
        #Polynomial fit:
        p_fit = np.polyfit(x_cut[m], y_cut[m], deg, w = w_cut[m])
        p = np.poly1d(p_fit)
        return p(x)
        
Ui_InfoTab, QtBaseClass = uic.loadUiType(sys.path[0] + "/fits1dsp_infotab.ui")
class InfoTab(QtWidgets.QTabWidget, Ui_InfoTab):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self)
        Ui_InfoTab.__init__(self)
        self.setupUi(self)
        
        self.table_extension.setColumnWidth(0, 29)
        
Ui_PlotTab, QtBaseClass = uic.loadUiType(sys.path[0] + "/fits1dsp_plottab.ui")
class PlotTab(QtWidgets.QTabWidget, Ui_PlotTab):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self)
        Ui_PlotTab.__init__(self)
        self.setupUi(self)
        
        self.fig, self.ax = plt.subplots(dpi = 35)
        self.canvas = FigureCanvas(self.fig)
        self.mpl_toolbar = FigureToolbar(self.canvas, self)
        self.layout = QtWidgets.QGridLayout(self.canvasWidget)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.mpl_toolbar)
        
Ui_HelpWindow, QtBaseClass = uic.loadUiType(sys.path[0] + "/fits1dsp_help.ui")
class HelpWindow(QtWidgets.QMainWindow, Ui_HelpWindow):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self)
        Ui_HelpWindow.__init__(self)
        self.setupUi(self)
        
    def display_help(self):
        help = open(sys.path[0] + "/fits1dsp_HowTo.txt", "r").read()
        self.textBox_help.append(help)
        self.show()
        
def convert_parser_input(args):
    files = list()
    if args.files != None:
        for i, path in enumerate(args.files):
            if path[-5:] == ".fits":
                files.append(path)
            else:
                try:
                    with open(path) as f:
                        for line in f.readlines():
                            paths = [path for path in re.split(',|;|\"|\'|\s+', line) if path[-5:] == ".fits"]
                            for path in paths:
                                files.append(path)
                except:
                    print("Warning: File type of argument " + str(i) +" not understood.")
                    continue
    args.files = files
    return args
        
if __name__ == "__main__":
    #Command line arguments:
    parser = argparse.ArgumentParser(description = "Display 1D FITS spectra.")
    parser.add_argument('-f', '--files', nargs='*' , help = "FITS files to be selected on start, as path to the individual FITS files or to files containing a list of paths to the individual FITS files.")
    args = convert_parser_input(parser.parse_args())
    globals().update(vars(args))
    #App:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show() 
    if len(args.files) != 0:
        window.make_table_fits(args.files)
        window.select_all_fits()
    
    sys.exit(app.exec_())
