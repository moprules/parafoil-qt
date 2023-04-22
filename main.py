import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QProgressBar

from parafoil import PFSim
from flyplot import Graph3DWindow

# Create a basic window with a layout and a button


class MainForm(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle("My Form")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        # создаем прогресс-бар
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.button = QPushButton("Click me!")
        self.button.clicked.connect(self.start_thread)
        self.layout.addWidget(self.button)

        self.grafic = Graph3DWindow("grafics/matlab.txt")
        self.grafic.show()

    # Instantiate and start a new thread
    def start_thread(self):
        instanced_thread = WorkerThread(self)
        instanced_thread.start()

    # Create the Slots that will receive signals
    @Slot(str)
    def update_str_field(self, message):
        print(message)

    @Slot(int)
    def update_int_field(self, value):
        print(value)

    @Slot(int)
    def update_statusbar(self, value):
        self.progress_bar.setValue(value)

    @Slot(bool)
    def complite_calc(self, value):
        if value:
            self.grafic.graph.addChart("grafics/ans.txt")


# Signals must inherit QObject
class MySignals(QObject):
    progresSignal = Signal(int)
    compliteSignal = Signal(bool)


# Create the Worker Thread
class WorkerThread(QThread):
    def __init__(self, parent: MainForm):
        QThread.__init__(self, parent)
        # Instantiate signals and connect signals to the slots
        self.signals = MySignals()
        self.signals.progresSignal.connect(parent.update_statusbar)
        self.signals.compliteSignal.connect(parent.complite_calc)

    def run(self):
        # Do something on the worker thread
        lander = PFSim("data/space_rider.yaml")
        # Собираем модель при первом запуске
        lander.build()
        # Задаём начальные состояния
        lander.init_state()
        start_alt = lander.state["altitude"]
        # Цикл расчёта
        while lander.state["time"] < lander.model["time"]["final"] and lander.state["altitude"] > 0:
            lander.step()
            loast_alt = start_alt - lander.state["altitude"]
            progres = int(100*loast_alt/start_alt)
            self.signals.progresSignal.emit(progres)
        lander.ans_file.close()
        self.signals.compliteSignal.emit(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainForm()
    window.show()
    sys.exit(app.exec())
