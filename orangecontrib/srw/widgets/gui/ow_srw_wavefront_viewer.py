import sys
import numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from silx.gui.plot.StackView import StackViewMainWindow

from wofry.propagator.propagator import PropagationManager, PropagationMode
from wofrysrw.propagator.propagators2D.srw_fresnel import SRW_APPLICATION

from orangecontrib.srw.util.srw_util import SRWPlot
from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget

class SRWWavefrontViewer(SRWWidget):

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 545

    want_main_area=1
    view_type=Setting(1)

    plotted_tickets=None

    def __init__(self, show_automatic_box=True, show_view_box=True):
        super().__init__(show_automatic_box)

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.view_box = oasysgui.widgetBox(plot_tab, "Plotting", addSpace=False, orientation="horizontal")

        if show_view_box:
            view_box_1 = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical", width=350)

            self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Plot Results",
                                                labelWidth=220,
                                                items=["No", "Yes"],
                                                callback=self.set_PlotQuality, sendSelectedValue=False, orientation="horizontal")
        else:
            self.view_type = 1
            self.view_type_combo = QtWidgets.QWidget()


        #* -------------------------------------------------------------------------------------------------------------
        propagation_box = oasysgui.widgetBox(self.view_box, "", addSpace=False, orientation="vertical")

        self.le_srw_live_propagation_mode = gui.lineEdit(propagation_box, self, "srw_live_propagation_mode", "Propagation Mode", labelWidth=150, valueType=str, orientation="horizontal")
        self.le_srw_live_propagation_mode.setAlignment(Qt.AlignCenter)
        self.le_srw_live_propagation_mode.setReadOnly(True)
        font = QFont(self.le_srw_live_propagation_mode.font())
        font.setBold(True)
        self.le_srw_live_propagation_mode.setFont(font)

        self.set_srw_live_propagation_mode()

        #* -------------------------------------------------------------------------------------------------------------


        self.tab = []
        self.tabs = oasysgui.tabWidget(plot_tab)

        self.initializeTabs()

        self.srw_output = QtWidgets.QTextEdit()
        self.srw_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.srw_output)

        self.srw_output.setFixedHeight(600)
        self.srw_output.setFixedWidth(600)

    def set_srw_live_propagation_mode(self):
        self.srw_live_propagation_mode = "Element by Element" if PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == PropagationMode.STEP_BY_STEP  else \
                                          "Whole beamline at Final Screen" if PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == PropagationMode.WHOLE_BEAMLINE else \
                                          "Unknown"

        palette = QPalette(self.le_srw_live_propagation_mode.palette())

        color = 'dark green' if PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == PropagationMode.STEP_BY_STEP  else \
                'dark red' if PropagationManager.Instance().get_propagation_mode(SRW_APPLICATION) == PropagationMode.WHOLE_BEAMLINE else \
                'black'

        palette.setColor(QPalette.Text, QColor(color))
        palette.setColor(QPalette.Base, QColor(243, 240, 140))
        self.le_srw_live_propagation_mode.setPalette(palette)


    def initializeTabs(self):
        current_tab = self.tabs.currentIndex()

        size = len(self.tab)
        indexes = range(0, size)
        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = self.getTitles()
        self.tab = []
        self.plot_canvas = []

        for title in self.getTitles():
            self.tab.append(oasysgui.createTabPage(self.tabs, title))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.tabs.setCurrentIndex(current_tab)


    def set_PlotQuality(self):
        self.progressBarInit()

        if self.is_do_plots():
            if not self.plotted_tickets is None:
                try:
                    self.initializeTabs()

                    self.plot_results(self.plotted_tickets, 80)
                except Exception as exception:
                    QtWidgets.QMessageBox.critical(self, "Error",
                                               str(exception),
                        QtWidgets.QMessageBox.Ok)

                    raise exception
        else:
            self.initializeTabs()

        self.progressBarFinished()


    def plot_1D(self, ticket, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = SRWPlot.Detailed1DWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_1D(ticket, var, title, xtitle, ytitle, xum=xum)

        self.progressBarSet(progressBarValue)


    def plot_2D(self, ticket, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = SRWPlot.Detailed2DWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_2D(ticket, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum)

        self.progressBarSet(progressBarValue)

    def plot_3D(self, data3D, dataE, dataX, dataY, progressBarValue, plot_canvas_index,  title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = StackViewMainWindow()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        xmin = numpy.min(dataX)
        xmax = numpy.max(dataX)
        ymin = numpy.min(dataY)
        ymax = numpy.max(dataY)

        stepX = dataX[1]-dataX[0]
        stepY = dataY[1]-dataY[0]
        if len(dataE) > 1: stepE = dataE[1]-dataE[0]
        else: stepE = 1.0

        if stepE == 0.0: stepE = 1.0
        if stepX == 0.0: stepX = 1.0
        if stepY == 0.0: stepY = 1.0

        dim0_calib = (dataE[0],stepE)
        dim1_calib = (ymin, stepY)
        dim2_calib = (xmin, stepX)

        data_to_plot = numpy.swapaxes(data3D, 1, 2)

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[plot_canvas_index].setGraphTitle(title)
        self.plot_canvas[plot_canvas_index].setLabels(["Photon Energy [eV]",ytitle,xtitle])
        self.plot_canvas[plot_canvas_index].setColormap(colormap=colormap)
        self.plot_canvas[plot_canvas_index].setStack(numpy.array(data_to_plot),
                                                     calibrations=[dim0_calib, dim1_calib, dim2_calib] )


    def show_power_density(self):
        return True

    def is_do_plots(self):
        return self.view_type == 1

    def plot_results(self, tickets = [], progressBarValue=80):
        if self.is_do_plots():
            if not tickets is None:
                if not len(tickets) == 0:
                    self.view_type_combo.setEnabled(False)

                    SRWPlot.set_conversion_active(self.getConversionActive())

                    variables = self.getVariablesToPlot()
                    titles = self.getTitles(with_um=True)
                    xtitles = self.getXTitles()
                    ytitles = self.getYTitles()
                    xums = self.getXUM()
                    yums = self.getYUM()

                    progress = (100 - progressBarValue) / len(tickets)

                    try:
                        for i in range(0, len(tickets)):
                            if type(tickets[i]) is tuple:
                                if len(tickets[i]) == 4:
                                    self.plot_3D(tickets[i][0], tickets[i][1], tickets[i][2], tickets[i][3], progressBarValue + (i+1)*progress, plot_canvas_index=i, title=titles[i], xtitle=xtitles[i], ytitle=ytitles[i], xum=xums[i], yum=yums[i])
                            else:
                                if len(variables[i]) == 1:
                                    self.plot_1D(tickets[i], progressBarValue + (i+1)*progress, variables[i],                     plot_canvas_index=i, title=titles[i], xtitle=xtitles[i], ytitle=ytitles[i], xum=xums[i])
                                else:
                                    self.plot_2D(tickets[i], progressBarValue + (i+1)*progress, variables[i][0], variables[i][1], plot_canvas_index=i, title=titles[i], xtitle=xtitles[i], ytitle=ytitles[i], xum=xums[i], yum=yums[i])
                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: bad content\nexception: " + str(e))

                    self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Nothing to Plot")

        self.plotted_tickets = tickets

    def writeStdOut(self, text):
        cursor = self.srw_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.srw_output.setTextCursor(cursor)
        self.srw_output.ensureCursorVisible()

    def onReceivingInput(self):
        self.initializeTabs()

    def getVariablesToPlot(self):
        return [[1, 2], [1, 2], [1, 2]]

    def getTitles(self, with_um=False):
        if with_um: return ["Intensity SE [ph/s/.1%bw/mm^2]",
                            "Phase SE [rad]",
                            "Intensity ME [ph/s/.1%bw/mm^2]"]
        else: return ["Intensity SE", "Phase SE", "Intensity ME (Convolution)"]

    def getXTitles(self):
        return ["X [um]", "X [um]", "X [um]"]

    def getYTitles(self):
        return ["Y [um]", "Y [um]", "Y [um]"]

    def getXUM(self):
        return ["X [um]", "X [um]", "X [um]"]

    def getYUM(self):
        return ["Y [um]", "Y [um]", "Y [um]"]

    def getConversionActive(self):
        return True

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SRWWavefrontViewer()
    ow.show()
    a.exec_()
    ow.saveSettings()
