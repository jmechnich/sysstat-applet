from appletlib.indicator import Indicator

from PyQt5.Qt import QMenu, QTimer, qApp, QSystemTrayIcon, QIcon

class SysStat(Indicator):
    def __init__(self,name):
        Indicator.__init__(self, name, interval=2000)
        self.func = self.drawStats
        self.initVars()
        self.initContextMenu()
        self.initStats()
        qApp.sigusr1.connect( self.restart)

    def initContextMenu(self):
        m = QMenu()
        m.addAction( QIcon.fromTheme("application-exit"), "&Quit", qApp.quit)
        self.s.setContextMenu(m)

    def initStats(self):
        self.s.triggerUpdate.connect( self.func)
        QTimer.singleShot(10,  self.func)
        self.s.activated.connect( self.systrayClicked)

    def systrayClicked(self,reason):
        if reason == QSystemTrayIcon.Trigger or \
           reason == QSystemTrayIcon.DoubleClick:
            if self.splash.isVisible():
                self.splash.hide()
            else:
                self.updateSplashGeometry(hide=True)
                self.splash.show()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.reset()
            self.initContextMenu()
            self.initStats()
        elif reason == QSystemTrayIcon.Context:
            pass
        elif reason == QSystemTrayIcon.Unknown:
            print("unknown")

    def restart(self):
        self.reset()
        self.initContextMenu()
        self.initStats()
