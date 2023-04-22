import sys
from PySide6 import QtWidgets
from parafoil import PFSim
from flyplot import Graph3DWindow


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = Graph3DWindow("grafics/matlab.txt")

    lander = PFSim("data/space_rider.yaml")
    lander.start()
    w.graph.addChart("grafics/ans.txt")
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
