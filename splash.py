from util import *

from PyQt4.Qt import *

class Splash(QWidget):
    def __init__(self,sti):
        QWidget.__init__(self)
        self.setWindowFlags(Qt.SplashScreen|Qt.WindowStaysOnTopHint);
        self.setGeometry(0,0,1,1)
        self.setWindowOpacity(0.75)
        self.sti = sti
        self.font = QFont("Dejavu Sans", 8)
