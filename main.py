import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6 import QtWidgets
from PySide6 import QtGui

from parafoil import PFSim
from flyplot import Graph3DWindow
import flyplot
import time
import os


class PlayButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.played: bool = False
        self.isFirst: bool = True


class MainForm(QtWidgets.QWidget):
    def __init__(self, path_to_model: str = ""):
        super().__init__()
        self.path_to_model = path_to_model

        self.setWindowTitle("My Form")

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        browse_layout = QtWidgets.QHBoxLayout()
        self.browse_label = QtWidgets.QLabel(self.path_to_model)
        self.browse_label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                        QtWidgets.QSizePolicy.MinimumExpanding)
        browse_layout.addWidget(self.browse_label)
        browse_button = QtWidgets.QPushButton("Открыть")
        browse_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                    QtWidgets.QSizePolicy.Fixed)
        browse_button.clicked.connect(self.on_browse)
        browse_layout.addWidget(browse_button)
        self.layout.addLayout(browse_layout)

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
        self.layout.addLayout(process_layout)

        # self.start_btn = QtWidgets.QPushButton("Start!")
        # self.start_btn.clicked.connect(self.start_thread)
        # self.layout.addWidget(self.start_btn)

        # self.abort_btn = QtWidgets.QPushButton("Abort")
        # self.abort_btn.clicked.connect(self.abort_thread)
        # self.layout.addWidget(self.abort_btn)

        self.grafic = Graph3DWindow("grafics/matlab.txt")
        self.grafic.graph.addChart("grafics/test.txt")
        self.grafic.show()

    @Slot()
    def on_play(self):
        if self.play_btn.isFirst:
            self.play_btn.isFirst = False
            self.progress_bar.setValue(0)
            self.worker = WorkerThread(self)
            self.worker.start()

        self.play_btn.played = not self.play_btn.played
        if self.play_btn.played:
            self.play_btn.setIcon(flyplot.get_icon("pause"))
            self.worker.playStatus = True
        else:
            if hasattr(self, "worker"):
                # self.worker.terminate()
                self.worker.playStatus = False
                # self.worker.closeFiles()
            # self.play_btn.isFirst = True
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
                self.worker.closeFiles()
            self.play_btn.isFirst = True
            self.play_btn.setIcon(flyplot.get_icon("play"))
            self.progress_bar.setValue(0)

    @Slot()
    def abort_thread(self):
        if hasattr(self, "worker"):
            self.worker.terminate()

    @Slot(int)
    def update_progressbar(self, value):
        self.progress_bar.setValue(value)

    @Slot(bool)
    def complite_calc(self, value):
        if value:
            self.play_btn.isFirst = True
            self.play_btn.setIcon(flyplot.get_icon("play"))

    @Slot(list)
    def upd_chart(self, pos):
        self.grafic.graph.updChart("Python", pos)

    def closeEvent(self, event: QtGui.QCloseEvent):

        if hasattr(self, "worker"):
            self.worker.terminate()

        if self.grafic:
            self.grafic.close()

        super().closeEvent(event)


# Signals must inherit QObject
class MySignals(QObject):
    progresSignal = Signal(int)
    compliteSignal = Signal(bool)
    updChartSignal = Signal(list)


# Create the Worker Thread
class WorkerThread(QThread):
    def __init__(self, parent: MainForm):
        QThread.__init__(self, parent)
        self.lander = PFSim(parent.path_to_model, "grafics")
        self.signals = MySignals()
        self.signals.progresSignal.connect(parent.update_progressbar)
        self.signals.compliteSignal.connect(parent.complite_calc)
        self.signals.updChartSignal.connect(parent.upd_chart)
        self.playStatus = True
        self.pos = []

    def closeFiles(self):
        for key in self.lander.files:
            self.lander.files[key].close()

    def run(self):
        # Do something on the worker thread
        st = time.time()
        lander = self.lander
        # Собираем модель при первом запуске
        lander.build()
        # Задаём начальные состояния
        lander.init_state()
        self.pos = []
        start_alt = lander.state["altitude"]
        pos_north = lander.state["pos_north"]
        pos_east = lander.state["pos_east"]
        altitude = lander.state["altitude"]
        self.pos.append([pos_north, pos_east, altitude])
        # Цикл расчёта
        cnt = 0
        while lander.state["time"] < lander.model["time"]["final"] and lander.state["altitude"] > 0:
            if self.playStatus:

                lander.step()

                pos_north = lander.state["pos_north"]
                pos_east = lander.state["pos_east"]
                altitude = lander.state["altitude"]
                self.pos.append([pos_north, pos_east, altitude])

                cnt += 1
                if cnt >= 200:
                    self.signals.updChartSignal.emit(self.pos)
                    loast_alt = start_alt - lander.state["altitude"]
                    progres = int(100*loast_alt/start_alt)
                    self.signals.progresSignal.emit(progres)
                    cnt = 0
            else:
                time.sleep(0.5)


        self.closeFiles()

        self.signals.updChartSignal.emit(self.pos)
        loast_alt = start_alt - lander.state["altitude"]
        progres = int(100*loast_alt/start_alt)
        self.signals.progresSignal.emit(progres)
        self.signals.compliteSignal.emit(True)
        elapsed = time.time() - st
        print("elapsed =", elapsed)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainForm("data/space_rider.yaml")
    window.show()
    sys.exit(app.exec())
