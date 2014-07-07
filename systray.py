from PyQt4.Qt import *

class SystemTrayIcon(QSystemTrayIcon):
    triggerUpdate = pyqtSignal()
    def __init__(self,name):
        QSystemTrayIcon.__init__(self)
        s = QSettings()
        self.fgColor = QColor(
            self.setSettingsValue(s, "fgColor", QColor("#33b0dc")))
        self.bgColor = QColor(
            self.setSettingsValue(s, "bgColor", QColor("#144556")))
        self.interval = self.setSettingsValue(
            s, "%s/interval" % name, 1000).toInt()[0]
        
        pix = QPixmap(22,22)
        p = QPainter(pix)
        p.fillRect(pix.rect(), Qt.black)
        p.end()
        self.setIcon(QIcon(pix))
        self.startTimer( self.interval)

    def setSettingsValue( self, s, key, default):
        var = s.value(key, default)
        if not s.contains(key): s.setValue( key, var)
        return var

    def timerEvent(self,ev):
        self.triggerUpdate.emit()
