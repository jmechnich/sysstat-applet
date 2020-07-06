import subprocess
import syslog

from appletlib.app import Application
from appletlib.indicator import Indicator

from PyQt5.Qt import QDialog, QGridLayout, QGroupBox, \
    QLabel, QLineEdit, QMenu, QTimer, qApp, QSystemTrayIcon, QIcon, QVBoxLayout

class Preferences(QDialog):
    def __init__(self, sysstat):
        super(Preferences,self).__init__()
        self.sysstat = sysstat
        self.layout = QVBoxLayout()
        self.init()
        self.setLayout(self.layout)

    def init(self):
        g = QGroupBox("Options for %s" % self.sysstat.name)
        v = QGridLayout()

        tmp = QLabel("External Command")
        v.addWidget(tmp, 0, 0)
        tmp = QLineEdit(self.sysstat.extcmd)
        tmp.returnPressed.connect(lambda: self.sysstat.setExternalCmd(tmp.text()))
        v.addWidget(tmp, 0, 1)

        g.setLayout(v)
        self.layout.addWidget(g)

class SysStat(Indicator):
    def __init__(self,name):
        Indicator.__init__(self, name, interval=2000)
        self.func = self.drawStats
        self.initVars()
        self.initContextMenu()
        self.initStats()
        self.initWidgets()
        qApp.sigusr1.connect( self.restart)

    def initVars(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: initializing variables" % self.name);
        self.extcmd = str(Application.settingsValue('%s/extcmd' % self.name, ''))
        self.extcmdTimer = QTimer(self.systray)
        self.extcmdTimer.timeout.connect(self.checkExternalCmd)
        self.extcmdPopen = None
        self.prefs = None

    def initContextMenu(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: initializing context menu" % self.name);
        m = QMenu()
        m.addAction( QIcon.fromTheme("options"), "&Options", lambda: self.prefs.show())
        m.addAction( QIcon.fromTheme("application-exit"), "&Quit", qApp.quit)
        self.systray.setContextMenu(m)

    def initStats(self):
        self.systray.triggerUpdate.connect( self.func)
        QTimer.singleShot(10, self.func)
        self.systray.activated.connect( self.systrayClicked)

    def initWidgets(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: initializing preferences" % self.name);
        self.prefs = Preferences(self)

    def checkExternalCmd(self):
        if self.extcmdPopen is None:
            return
        returncode = self.extcmdPopen.poll()
        if not returncode is None:
            self.extcmdTimer.stop()
            self.extcmdPopen = None

    def runExternalCmd(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: running external command" % self.name);
        if self.extcmd is None or not len(self.extcmd):
            return
        if not self.extcmdPopen is None:
            return
        cmd = self.extcmd
        self.extcmdPopen = subprocess.Popen(cmd, shell=True)
        self.extcmdTimer.start(500)

    def setExternalCmd(self, extcmd):
        self.extcmd = extcmd
        Application.setSettingsValue('%s/extcmd' % self.name, self.extcmd)

    def systrayClicked(self,reason):
        if reason == QSystemTrayIcon.Trigger or \
           reason == QSystemTrayIcon.DoubleClick:
            if self.splash.isVisible():
                self.splash.hide()
            else:
                self.updateSplashGeometry(hide=True)
                self.splash.show()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.runExternalCmd()
            #self.restart()
        elif reason == QSystemTrayIcon.Context:
            pass
        elif reason == QSystemTrayIcon.Unknown:
            print("unknown")

    def restart(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: restarting" % self.name);
        self.reset()
        self.initContextMenu()
        self.initStats()
