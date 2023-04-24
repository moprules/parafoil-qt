import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtGui import QCloseEvent

from parafoil import PFSim
from flyplot import Graph3DWindow
import time


class MainForm(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle("My Form")
        self.layout = QVBoxLayout()  # type: ignore
        self.setLayout(self.layout)
        # создаем прогресс-бар
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.start_btn = QPushButton("Start!")
        self.start_btn.clicked.connect(self.start_thread)
        self.layout.addWidget(self.start_btn)

        self.abort_btn = QPushButton("Abort")
        self.abort_btn.clicked.connect(self.abort_thread)
        self.layout.addWidget(self.abort_btn)

        self.grafic = Graph3DWindow("grafics/matlab.txt")
        self.grafic.graph.addChart("grafics/test.txt")
        self.grafic.show()

    # Instantiate and start a new thread
    def start_thread(self):
        self.progress_bar.setValue(0)
        self.worker = WorkerThread(self)
        self.worker.start()

    def abort_thread(self):
        if hasattr(self, "worker"):
            self.worker.terminate()

    @Slot(int)
    def update_statusbar(self, value):
        self.progress_bar.setValue(value)

    @Slot(bool)
    def complite_calc(self, value):
        if value:
            self.grafic.graph.addChart("grafics/ans.txt")

    @Slot(list)
    def upd_chart(self, pos):
        self.grafic.graph.updChart("Python", pos)

    def closeEvent(self, event: QCloseEvent):

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
        # Instantiate signals and connect signals to the slots
        self.signals = MySignals()
        self.signals.progresSignal.connect(parent.update_statusbar)
        self.signals.compliteSignal.connect(parent.complite_calc)
        self.signals.updChartSignal.connect(parent.upd_chart)
        self.pos = []

    def run(self):
        # Do something on the worker thread
        st = time.time()
        lander = PFSim("data/space_rider.yaml")
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
            lander.step()

            pos_north = lander.state["pos_north"]
            pos_east = lander.state["pos_east"]
            altitude = lander.state["altitude"]
            self.pos.append([pos_north, pos_east, altitude])

            cnt += 1
            if cnt > 199:
                self.signals.updChartSignal.emit(self.pos)
                loast_alt = start_alt - lander.state["altitude"]
                progres = int(100*loast_alt/start_alt)
                self.signals.progresSignal.emit(progres)
                cnt = 0
        lander.ans_file.close()
        
        self.signals.updChartSignal.emit(self.pos)
        loast_alt = start_alt - lander.state["altitude"]
        progres = int(100*loast_alt/start_alt)
        self.signals.progresSignal.emit(progres)
        # self.signals.compliteSignal.emit(True)
        elapsed = time.time() - st
        print("elapsed =", elapsed)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainForm()
    window.show()
    sys.exit(app.exec())
