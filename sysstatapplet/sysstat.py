import subprocess
import syslog

from appletlib.app import Application
from appletlib.indicator import Indicator

from PyQt5.Qt import *

class Preferences(QDialog):
    triggerUpdate = pyqtSignal()

    def __init__(self, sysstat):
        super(Preferences,self).__init__()
        self.sysstat = sysstat

        self.layout = QVBoxLayout()
        self.setWindowTitle("%s - Settings" % self.sysstat.name)
        g = QGroupBox("Misc")
        v = QGridLayout()

        row = 0
        v.addWidget(QLabel("Splash position"), row, 0)
        self.splashpos = QSpinBox()
        self.splashpos.setMinimum(0)
        self.splashpos.setMaximum(3)
        self.splashpos.setValue(self.sysstat.splashpos)
        self.splashpos.valueChanged.connect(self.sysstat.setSplashPosition)
        v.addWidget(self.splashpos, row, 1)
        row +=1

        v.addWidget(QLabel("External Command"), row, 0)
        self.extcmd = QLineEdit(self.sysstat.extcmd)
        self.extcmd.returnPressed.connect(
            lambda: self.sysstat.setExternalCmd(self.extcmd.text()))
        v.addWidget(self.extcmd, row, 1)
        row += 1

        v.addWidget(QLabel("Verbose Debugging"), row, 0)
        self.verbose = QCheckBox("")
        self.verbose.toggled.connect(
            lambda checked: self.sysstat.setVerbose(checked))
        v.addWidget(self.verbose, row, 1)
        row += 1

        g.setLayout(v)
        self.layout.addWidget(g)
        self.setLayout(self.layout)

        self.initContents()

    def initContents(self):
        self.setWindowIcon(self.sysstat.systray.icon())
        self.splashpos.setValue(self.sysstat.splashpos)
        self.extcmd.setText(self.sysstat.extcmd)
        self.verbose.setChecked(self.sysstat.verbose)
        self.triggerUpdate.emit()

    def showEvent(self, ev):
        self.initContents()

class SysStat(Indicator):
    def __init__(self,name):
        Indicator.__init__(self, name, interval=2000)
        self.initVars()
        self.initContextMenu()
        self.initStats()
        self.initWidgets()
        qApp.sigusr1.connect(self.restart)

    def initVars(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: initializing variables" % self.name);

        # splash position
        self.splashpos = int(Application.settingsValue(
            '%s/splashpos' % self.name, 0))

        # external command
        self.extcmd = str(Application.settingsValue(
            '%s/extcmd' % self.name, ''))
        self.extcmdTimer = QTimer()
        self.extcmdTimer.timeout.connect(self.checkExternalCmd)
        self.extcmdPopen = None

        # verbose debugging
        self.verbose = bool(Application.settingsValue(
            '%s/verbose' % self.name, False))
        self.prefs = None

    def initContextMenu(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: initializing context menu" % self.name);
        m = QMenu()
        m.addAction(QIcon.fromTheme("view-refresh"), "&Reload",
                    lambda: self.restart())
        m.addAction(QIcon.fromTheme("preferences-other"), "&Settings",
                    lambda: self.prefs.show())
        m.addAction(QIcon.fromTheme("application-exit"), "&Quit", qApp.quit)
        self.systray.setContextMenu(m)

    def initStats(self):
        self.systray.triggerToolTip.connect(self.toolTip)
        self.systray.triggerUpdate.connect(self.update)
        QTimer.singleShot(10, self.update)
        self.systray.activated.connect(self.systrayClicked)

    def initWidgets(self):
        syslog.syslog(syslog.LOG_DEBUG,
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
        syslog.syslog(syslog.LOG_DEBUG,
                      "DEBUG  %s: running external command" % self.name);
        if self.extcmd is None or not len(self.extcmd):
            return
        if not self.extcmdPopen is None:
            return
        cmd = self.extcmd
        self.extcmdPopen = subprocess.Popen(cmd, shell=True)
        self.extcmdTimer.start(500)

    def setSplashPosition(self, pos):
        if self.splashpos != pos:
            self.splashpos = pos
            Application.setSettingsValue(
                '%s/splashpos' % self.name, self.splashpos)
            self.updateSplashGeometry()

    def setExternalCmd(self, extcmd):
        self.extcmd = extcmd
        Application.setSettingsValue('%s/extcmd' % self.name, self.extcmd)

    def setVerbose(self, verbose):
        self.verbose = verbose
        Application.setSettingsValue('%s/verbose' % self.name, self.verbose)

    def systrayClicked(self,reason):
        syslog.syslog(syslog.LOG_DEBUG, "DEBUG  sysstat: systray clicked")
        if reason == QSystemTrayIcon.Trigger or \
           reason == QSystemTrayIcon.DoubleClick:
            if self.splash is None:
                return
            if self.splash.isVisible():
                syslog.syslog(syslog.LOG_DEBUG, "DEBUG  sysstat: hiding splash")
                self.splash.hide()
            else:
                syslog.syslog(syslog.LOG_DEBUG, "DEBUG  sysstat: showing splash")
                self.updateSplashGeometry(hide=True)
                self.splash.show()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.runExternalCmd()
        elif reason == QSystemTrayIcon.Context:
            if self.verbose:
                syslog.syslog(syslog.LOG_DEBUG,
                              "DEBUG  %s: QSystemTrayIcon::Context" % self.name)
        elif reason == QSystemTrayIcon.Unknown:
            syslog.syslog(syslog.LOG_DEBUG,
                          "DEBUG  %s: QSystemTrayIcon::Unknown" % self.name)

    def restart(self):
        syslog.syslog(syslog.LOG_DEBUG, "DEBUG  %s: restarting" % self.name)
        self.reset()
        self.initContextMenu()
        self.initStats()

    def update():
        syslog.syslog(syslog.LOG_DEBUG, "DEBUG  sysstat: update");

    def toolTip(hev):
        syslog.syslog(syslog.LOG_DEBUG, "DEBUG  sysstat: toolTip");
