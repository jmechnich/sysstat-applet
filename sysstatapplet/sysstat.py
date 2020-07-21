import subprocess
import syslog

from appletlib.app import Application, SettingsValue
from appletlib.indicator import Indicator

from PyQt5.Qt import *

class Preferences(QDialog):
    def __init__(self, sysstat):
        super(Preferences,self).__init__()
        self.sysstat = sysstat

        self.layout = QVBoxLayout()
        self.setWindowTitle("%s - Settings" % self.sysstat.name)

        g = self.sysstat.getPrefs()
        self.layout.addWidget(g)

        g = QGroupBox("Misc")
        v = QGridLayout()

        row = 0
        v.addWidget(QLabel("External Command"), row, 0)
        self.extcmd = QLineEdit(self.sysstat.extcmd.value())
        self.extcmd.returnPressed.connect(
            lambda: self.sysstat.extcmd.setValue(self.extcmd.text()))
        v.addWidget(self.extcmd, row, 1)
        row += 1

        v.addWidget(QLabel("Verbose Debugging"), row, 0)
        verbose = QCheckBox("")
        verbose.toggled.connect(
            lambda checked: self.sysstat.verbose.setValue(checked))
        self.sysstat.verbose.valueChanged.connect(verbose.setChecked)
        v.addWidget(verbose, row, 1)
        row += 1

        g.setLayout(v)
        self.layout.addWidget(g)
        self.setLayout(self.layout)

        self.initContents()

    def initContents(self):
        self.setWindowIcon(self.sysstat.systray.icon())
        self.extcmd.setText(self.sysstat.extcmd.value())

    def showEvent(self, ev):
        self.initContents()

class SysStat(Indicator):
    def __init__(self, name, extcmd=''):
        Indicator.__init__(self, name, interval=2000)
        self.extcmd_default = extcmd
        self.initVars()
        self.initContextMenu()
        self.initStats()
        self.initWidgets()
        qApp.sigusr1.connect(self.restart)

    def initVars(self):
        syslog.syslog( syslog.LOG_DEBUG,
                       "DEBUG  %s: initializing variables" % self.name);

        # external command
        self.extcmd = SettingsValue(
            '%s/extcmd' % self.name, self.extcmd_default, str)
        self.extcmdTimer = QTimer()
        self.extcmdTimer.timeout.connect(self.checkExternalCmd)
        self.extcmdPopen = None

        # verbose debugging
        self.verbose = SettingsValue('%s/verbose' % self.name, False, bool)
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
        extcmd = self.extcmd.value()
        if not len(extcmd):
            return
        if not self.extcmdPopen is None:
            return
        self.extcmdPopen = subprocess.Popen(extcmd, shell=True)
        self.extcmdTimer.start(500)

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
            if self.verbose.value():
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
