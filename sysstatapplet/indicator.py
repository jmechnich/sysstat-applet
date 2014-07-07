from systray import *
import sip

from PyQt4.Qt import *

class Indicator:
    indicators = []

    def __init__(self,name):
        if self not in self.indicators:
            self.indicators += [self]
        self.name = name
        self.initSystray()
        self.splash = None
    
    def __del__(self):
        if self in self.indicators:
            self.indicators.remove(self)

    def initSystray(self):
        self.s = SystemTrayIcon(self.name)
        p = QPixmap(22,22)
        p.fill(self.s.bgColor)
        self.s.setIcon(QIcon(p))
        self.s.show()

    def reset(self):
        sip.delete(self.s)
        self.initSystray()
        for i in self.indicators:
            QTimer.singleShot(0, i.updateSplash)
        
    def boundingBox(self):
        r = QRect()
        for i in self.indicators:
            r = r.united( i.s.geometry())
        return r
    
    def updateSplash(self, hide=False):
        if not self.splash: return
        if hide: self.hideAllSplashes()
        r = self.s.geometry()
        #r = self.boundingBox()
        r.translate( 0, r.height()+3)
        self.splash.move(r.topLeft())

    def hideAllSplashes(self):
        for i in self.indicators:
            if i.splash:
                i.splash.hide()
        
        
