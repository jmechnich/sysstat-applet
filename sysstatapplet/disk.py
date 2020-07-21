import os
import re
import syslog
import time

from .sysstat import SysStat
from .util import *

from appletlib.splash import Splash
from appletlib.app import Application, SettingsValue

from PyQt5.Qt  import *

class SplashDisk(Splash):
    def __init__(self, indicator):
        Splash.__init__(self)
        self.indicator = indicator
        self.initVars()

    def initVars(self):
        self.data = {}
        fm = QFontMetrics( self.font)
        self.br1 = fm.boundingRect("write")
        self.br2 = fm.boundingRect("000.0KB/s")
        self.margin = 2
        self.w = 3*self.br1.width()+2*self.br2.width()+6*self.margin
        self.h = len(self.data)*(self.br2.height()+self.margin)+self.margin

    def paintEvent(self,ev):
        ev.accept()
        n = len(self.data)
        if n > 1: n+=1
        lh = self.br2.height()
        self.h = n*(lh+self.margin)+self.margin
        self.resize(self.w, self.h)
        p = QPainter(self)
        p.setFont(self.font)
        p.fillRect(self.rect(), self.indicator.systray.bgColor)
        p.setPen(self.indicator.systray.fgColor)
        p.translate(self.margin,self.margin)

        total1=0; total2=0
        for k in sorted(self.data.keys()):
            xpos=0
            p.setPen(Qt.white)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignLeft,  k)
            xpos+=self.br1.width()+self.margin
            p.setPen(self.indicator.systray.fgColor)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignRight, "read")
            xpos+=self.br1.width()+self.margin
            p.setPen(Qt.green)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                       prettyPrintBytesSec(self.data[k][0]))
            xpos+=self.br2.width()+self.margin
            p.setPen(self.indicator.systray.fgColor)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignRight, "write")
            xpos+=self.br1.width()+self.margin
            p.setPen(Qt.red)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                        prettyPrintBytesSec( self.data[k][1]))
            p.translate(0,lh+self.margin)
            total1 += self.data[k][0]
            total2 += self.data[k][1]
        if len(self.data) > 1:
            xpos=0
            p.setPen(Qt.white)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignLeft,  "all")
            xpos+=self.br1.width()+self.margin
            p.setPen(self.indicator.systray.fgColor)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignRight, "read")
            xpos+=self.br1.width()+self.margin
            p.setPen(Qt.green)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                       prettyPrintBytesSec(total1))
            xpos+=self.br2.width()+self.margin
            p.setPen(self.indicator.systray.fgColor)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignRight, "write")
            xpos+=self.br1.width()+self.margin
            p.setPen(Qt.red)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                       prettyPrintBytesSec(total2))
        p.end()

class IndicatorDisk(SysStat):
    def __init__(self):
        SysStat.__init__(self, "disk", "xterm -e 'iostat 1'")
        self.splash = SplashDisk(self)
        self.splash.triggerClick.connect(self.splashClicked)
        self.splash.triggerResize.connect(
            lambda ev: self.updateSplashGeometry())
        self.addPrefs()

    def initVars(self):
        SysStat.initVars(self)
        self.ignoreList = SettingsValue(
            "%s/ignore" % self.name, [], 'QStringList')
        self.old = {}
        self.new = {}

    def splashClicked(self,ev):
        if ev.button() == Qt.LeftButton:
            self.runExternalCmd()
        elif ev.button() == Qt.RightButton:
            self.splash.hide()

    def addPrefs(self):
        g = QGroupBox("Display Options")
        v = QGridLayout()

        v.addWidget(QLabel("Ignore List"), 0, 0)
        ignoreListWid = QLineEdit(", ".join(self.ignoreList.value()))
        ignoreListWid.returnPressed.connect(
            lambda: self.ignoreList.setValue([
                regex.strip() for regex in ignoreListWid.text().split(',')
                if len(regex.strip())
            ]))
        self.ignoreList.valueChanged.connect(
            lambda l: ignoreListWid.setText(','.join(l)))
        v.addWidget(ignoreListWid, 0, 1)

        g.setLayout(v)
        self.prefs.layout.addWidget(g)

    def parseProc(self):
        self.old = dict(self.new)
        self.new = {}
        ignore = re.compile(
            r'|'.join(self.ignoreList.value() + [ r'^loop\d+$', r'^ram\d+$' ]))
        for dirname, dirnames, filenames in os.walk('/sys/block'):
            for subdirname in dirnames:
                if re.match( ignore, subdirname): continue
                stat = os.path.join(dirname, subdirname)
                stat = os.path.join(stat, "stat")
                if not os.path.isfile(stat): continue
                with open(stat) as f:
                    l = f.readline().split()
                    self.new[subdirname] = (int(l[2]), int(l[6]), time.time())

    def update(self):
        if self.verbose.value():
            syslog.syslog( syslog.LOG_DEBUG, "DEBUG  %s: update" % self.name);
        self.parseProc()
        pix = QPixmap(22,22)
        p = QPainter(pix)
        f = QFont("Dejavu Sans", 6)
        p.setFont( f)
        p.fillRect(pix.rect(), self.systray.bgColor)
        n = len(self.new)
        data = {}
        if n > 0:
            margin = 0
            w = pix.width()-2*margin
            h = pix.height()-2*margin
            bh = round(float(h)/n)
            p.translate(margin,margin)
            total1 = 0
            total2 = 0
            for k in sorted(self.new.keys()):
                p.setPen(self.systray.fgColor)
                p.drawText(0, 0, round(w*.75), bh,
                           Qt.AlignRight|Qt.AlignVCenter, k)
                if k in self.old:
                    read    = self.new[k][0]-self.old[k][0]
                    written = self.new[k][1]-self.old[k][1]
                    t       = self.new[k][2]-self.old[k][2]
                    if t == 0: t=1
                    rate1   = float(read)*512/t
                    rate2   = float(written)*512/t
                    total1 += rate1
                    total2 += rate2
                    data[k] = (rate1, rate2)
                    if read:
                        p.fillRect(w-4, round(bh*.5)-4, 4, 4, Qt.green)
                    if written:
                        p.fillRect(w-4, round(bh*.5), 4, 4, Qt.red)
                else:
                    data[k] = (0, 0)
                p.translate(0,round(float(h)/n))
        p.end()
        self.systray.setIcon(QIcon(pix))
        self.splash.data = data
        self.splash.update()
