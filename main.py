import os
import sys
import time
import numpy as np
from typing import List
from collections import defaultdict
from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6 import QtWidgets
from PySide6 import QtGui
from PySide6 import QtCore

from parafoil import PFSim
import flyplot

# Поддержка многоокнного режима для OpenGl
QtCore.QCoreApplication.setAttribute(
    QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)


class PlayButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.played: bool = False
        self.isFirst: bool = True


class ResListItem(QtWidgets.QListWidgetItem):
    def __init__(self, parent, text: str, file_path: str, height=15, width=100):
        super().__init__(parent)

        self.setText(text)
        self.file_path = file_path
        self.setSizeHint(QtCore.QSize(width, height))
        self.setTextAlignment(Qt.AlignLeft)


class ResListWidget(QtWidgets.QListWidget):
    """Виджет с результатами расчёта"""

    def __init__(self, parent, *args, **kargs):
        super().__init__(*args, **kargs)
        self.itemDoubleClicked.connect(self.on_item_double_click)
        self.my_parent = parent

    def on_item_double_click(self, item: ResListItem):
        self.my_parent.openPlot(item)

    def contextMenuEvent(self, event):
        item: ResListItem = self.itemAt(event.pos())
        print(item.text())
        print(item.windows)
        # Создаем контекстное меню
        contextMenu = QtWidgets.QMenu(self)

        # Добавляем пункты меню
        openAction = QtGui.QAction('Открыть')
        contextMenu.addAction(openAction)

        # if item.windows:
        #     # Добавляем пункты меню
        #     openNewWindow = QtGui.QAction('Открыть в')
        #     # icon = flyplot.get_icon("grafic")
        #     # openNewWindow.setIcon(icon)
        #     contextMenu.addAction(openNewWindow)

        # Показываем контекстное меню
        contextMenu.exec(event.globalPos())

    def setRes(self, lander: PFSim):
        self.clear()
        ress = [res_name for res_name in lander.files]
        ress.sort()
        for res in ress:
            ResListItem(self, res, lander.files[res].name, height=15)

        # self.setItemHeight(15)
        self.setFixedHeight(15*(len(ress)+1))


class MainForm(QtWidgets.QWidget):
    def __init__(self, path_to_model: str = ""):
        super().__init__()
        self.path_to_model = path_to_model

        self.setWindowTitle("parafoil-qt")
        self.setWindowIcon(flyplot.get_icon("calc"))
        self.setMinimumWidth(230)

        self.__layout = QtWidgets.QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.__layout)
        browse_layout = QtWidgets.QHBoxLayout()
        self.browse_label = QtWidgets.QLabel(self.path_to_model)
        self.browse_label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                        QtWidgets.QSizePolicy.Minimum)
        browse_layout.addWidget(self.browse_label)
        browse_button = QtWidgets.QPushButton("Открыть")
        browse_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                    QtWidgets.QSizePolicy.Fixed)
        browse_button.clicked.connect(self.on_browse)
        browse_layout.addWidget(browse_button)
        self.__layout.addLayout(browse_layout)

        process_layout = QtWidgets.QHBoxLayout()
        self.play_btn = PlayButton()
        icon = flyplot.get_icon("play")
        self.play_btn.setIcon(icon)
        self.play_btn.setFlat(True)
        self.play_btn.clicked.connect(self.on_play)
        process_layout.addWidget(self.play_btn)
        # создаем прогресс-бар
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        process_layout.addWidget(self.progress_bar)
        self.__layout.addLayout(process_layout)

        chart_btns_layout = QtWidgets.QHBoxLayout()
        empty3DButton = QtWidgets.QPushButton("3D")
        empty3DButton.clicked.connect(self.on_empty3D)
        chart_btns_layout.addWidget(empty3DButton)
        empty2DButton = QtWidgets.QPushButton("2D")
        empty2DButton.clicked.connect(self.on_empty2D)
        chart_btns_layout.addWidget(empty2DButton)
        self.__layout.addLayout(chart_btns_layout)

        self.resList = ResListWidget(self)
        self.resList.hide()
        self.__layout.addWidget(self.resList)

        # Список открытых результатов
        self.openPlots = defaultdict(lambda: {"path": "", "wins": []})
        self.windows = []
        # self.grafic = Graph3DWindow("grafics/matlab.txt")
        # self.grafic.graph.addChart("grafics/test.txt")
        # self.grafic.show()

    def wasClosed(self, w):
        for val in self.openPlots.values():
            try:
                val["wins"].remove(w)
            except:
                pass

    def openPlot(self, item: ResListItem):
        plot_name = item.text()
        chart_type = "3D" if plot_name == "tr_3d" else "2D"
        self.worker.setBlockPlay(True)
        w = flyplot.PlotWindow(main_window=self,
                               chart_type=chart_type)
        w.show()
        w.addChart(item.file_path)
        self.windows.append(w)
        self.openPlots[plot_name]["path"] = item.file_path
        self.openPlots[plot_name]["wins"].append(w)

        self.worker.setBlockPlay(False)

    @Slot()
    def on_empty3D(self):
        w = flyplot.PlotWindow(chart_type="3D")
        self.windows.append(w)
        w.show()

    @Slot()
    def on_empty2D(self):
        w = flyplot.PlotWindow(chart_type="2D")
        self.windows.append(w)
        w.show()

    @Slot()
    def on_play(self):
        if self.play_btn.isFirst:
            self.play_btn.isFirst = False
            self.progress_bar.setValue(0)
            self.lander = PFSim(self.path_to_model, "grafics")
            # Собираем модель при первом запуске
            self.lander.build()
            # Задаём начальные состояния
            self.lander.init_state()
            self.resList.setRes(self.lander)
            self.resList.show()
            self.worker = WorkerThread(self, self.lander)
            self.worker.setBlockPlay(False)
            self.worker.start()

        self.play_btn.played = not self.play_btn.played
        if self.play_btn.played:
            self.play_btn.setIcon(flyplot.get_icon("pause"))
            self.worker.setBlockPlay(False)
        else:
            self.worker.setBlockPlay(True)
            self.play_btn.setIcon(flyplot.get_icon("play-pause"))

    def on_browse(self):
        dialog = QtWidgets.QFileDialog(
            parent=None,
            caption="Выберете файл модели расчёта",
            directory=os.path.abspath("."))
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)  # type: ignore
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)  # type: ignore
        if dialog.exec():
            model_file = dialog.selectedFiles()[0]
            self.browse_label.setText(os.path.abspath(model_file))
            if hasattr(self, "worker"):
                self.worker.terminate()
                self.lander.closeFiles()
            self.play_btn.isFirst = True
            self.play_btn.setIcon(flyplot.get_icon("play"))
            self.progress_bar.setValue(0)
            self.openPlots = defaultdict(lambda: {"path": "", "wins": []})

    @Slot(float)
    def update_progressbar(self, value: float):
        progres = int(100*value)
        if progres > 100:
            progres = 100
        self.progress_bar.setValue(progres)

    @Slot()
    def complite_calc(self):
        self.play_btn.isFirst = True
        self.play_btn.setIcon(flyplot.get_icon("play"))

    @Slot(dict)
    def upd_chart(self, cache: dict):
        for plot_name in self.openPlots:
            kargs = {}
            if plot_name == "tr_3d":
                kargs["pos"] = cache["pos"]
            elif plot_name == "tr_xy":
                kargs["x"] = cache["x"]
                kargs["y"] = cache["y"]
            elif plot_name == "tr_xz":
                kargs["x"] = cache["x"]
                kargs["y"] = cache["z"]
            elif plot_name == "tr_xy":
                kargs["x"] = cache["y"]
                kargs["y"] = cache["z"]
            else:
                kargs["x"] = cache["t"]
                kargs["y"] = cache[plot_name]

            file_path = self.openPlots[plot_name]["path"]
            for w in self.openPlots[plot_name]["wins"]:
                w.updChart(file_path, **kargs)

    def closeEvent(self, event: QtGui.QCloseEvent):

        if hasattr(self, "worker"):
            self.worker.terminate()

        for w in self.windows:
            w.close()

        super().closeEvent(event)


# Signals must inherit QObject
class MySignals(QObject):
    progresSignal = Signal(float)
    compliteSignal = Signal()
    updChartSignal = Signal(dict)


# Create the Worker Thread
class WorkerThread(QThread):
    def __init__(self, parent: MainForm, lander: PFSim):
        QThread.__init__(self, parent)
        self.lander = lander
        self.signals = MySignals()
        self.signals.progresSignal.connect(parent.update_progressbar)
        self.signals.compliteSignal.connect(parent.complite_calc)
        self.signals.updChartSignal.connect(parent.upd_chart)
        self.__playBlockStatus = False
        self.cache = {}
        self.cache["t"] = []
        self.cache["x"] = []
        self.cache["y"] = []
        self.cache["z"] = []
        self.cache["pos"] = []
        self.cache["alpha"] = []
        self.cache["beta"] = []
        self.cache["gamma"] = []
        self.cache["roll"] = []
        self.cache["pitch"] = []
        self.cache["yaw"] = []
        self.cache["velocity"] = []
        self.cache["C_D"] = []
        self.cache["C_Y"] = []
        self.cache["C_L"] = []
        self.cnt = 0

    def setBlockPlay(self, val: bool):
        self.__playBlockStatus = val
        if self.__playBlockStatus:
            for file in self.lander.files:
                self.lander.files[file].flush()
            self.signals.updChartSignal.emit(self.cache)
            self.clearCache()
            self.cnt = 0

    def clearCache(self):
        for val in self.cache.values():
            val.clear()

    def updateCache(self):
        t = self.lander.state["time"]
        x = self.lander.state["pos_north"]
        y = self.lander.state["pos_east"]
        z = self.lander.state["altitude"]
        pos = (x, y, z)
        alpha = self.lander.state["alpha"][0]
        beta = self.lander.state["sideslip_angle"][0]
        gamma = self.lander.state["trajv"]
        roll = self.lander.state["roll"]
        pitch = self.lander.state["pitch"]
        yaw = self.lander.state["yaw"]
        velocity = self.lander.state["Vrefn"][0]
        aeroforce = self.lander.state["aeroforce"]
        C_D = aeroforce[0, 0]
        C_Y = aeroforce[1, 0]
        C_L = aeroforce[2, 0]

        self.cache["t"].append(t)
        self.cache["x"].append(x)
        self.cache["y"].append(y)
        self.cache["z"].append(z)
        self.cache["pos"].append(pos)
        self.cache["alpha"].append(np.rad2deg(alpha))
        self.cache["beta"].append(np.rad2deg(beta))
        self.cache["gamma"].append(np.rad2deg(gamma))
        self.cache["roll"].append(np.rad2deg(roll))
        self.cache["pitch"].append(np.rad2deg(pitch))
        self.cache["yaw"].append(np.rad2deg(yaw))
        self.cache["velocity"].append(velocity)
        self.cache["C_D"].append(C_D)
        self.cache["C_Y"].append(C_Y)
        self.cache["C_L"].append(C_L)

    def run(self):
        # Do something on the worker thread
        st = time.time()
        start_alt = self.lander.state["altitude"]
        self.updateCache()
        # Цикл расчёта
        self.cnt = 0
        while self.lander.state["time"] < self.lander.model["time"]["final"] and self.lander.state["altitude"] > 0:
            if not self.__playBlockStatus:

                self.lander.step()
                self.updateCache()

                self.cnt += 1
                if self.cnt >= 200:
                    loast_alt = start_alt - self.lander.state["altitude"]
                    self.signals.progresSignal.emit(loast_alt/start_alt)
                    self.signals.updChartSignal.emit(self.cache)
                    self.clearCache()
                    self.cnt = 0
            else:
                time.sleep(0.5)

        self.lander.closeFiles()

        self.signals.updChartSignal.emit(self.cache)
        loast_alt = start_alt - self.lander.state["altitude"]
        self.signals.progresSignal.emit(loast_alt/start_alt)
        self.signals.compliteSignal.emit()
        elapsed = time.time() - st
        print("elapsed =", elapsed)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainForm("data/space_rider.yaml")
    window.show()
    sys.exit(app.exec())
