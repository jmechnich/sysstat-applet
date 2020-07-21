import os
import resource
import syslog

from .sysstat import SysStat
from .util import *

from appletlib.splash import Splash

from PyQt5.Qt import *

class SplashMem(Splash):
    def __init__(self, indicator):
        Splash.__init__(self)
        self.indicator = indicator
        self.initVars()

    def initVars(self):
        self.data = []
        fm = QFontMetrics(self.font)
        pid_max = "00000"
        with open("/proc/sys/kernel/pid_max", "r") as f:
            pid_max = f.read()
        self.br1 = fm.boundingRect(pid_max)
        self.br2 = fm.boundingRect("0000.0%")
        self.margin = 2
        self.w = self.br1.width()+100+self.br2.width()+4*self.margin
        self.h = 5*(self.br2.height()+self.margin)+self.margin
        self.resize(self.w,self.h)

    def paintEvent(self,ev):
        ev.accept()
        lh = self.br2.height()
        p = QPainter(self)
        p.setFont(self.font)
        p.fillRect(self.rect(), self.indicator.systray.bgColor)
        p.setPen(self.indicator.systray.fgColor)
        p.translate(self.margin,self.margin)
        for k in sorted(self.data, key=lambda i: sum(i[2:]), reverse=True)[:5]:
            xpos=0
            p.setPen(Qt.white)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignRight, str(k[0]))
            xpos+=self.br1.width()+self.margin
            p.setPen(self.indicator.systray.fgColor)
            p.drawText(xpos, 0, 100, lh, Qt.AlignRight, k[1])
            xpos+=100+self.margin
            p.setPen(Qt.green)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                       "%5.1f%%" % float(sum(k[2:])*100.))
            p.translate(0,lh+self.margin)
        p.end()

class IndicatorMem(SysStat):
    def __init__(self):
        SysStat.__init__(self, "mem", "xterm -e 'vmstat 1'")
        self.splash = SplashMem(self)
        self.splash.triggerClick.connect(self.splashClicked)
        self.splash.triggerResize.connect(
            lambda ev: self.updateSplashGeometry())

    def initVars(self):
        SysStat.initVars(self)
        self.mem = {}
        self.ps  = {}
        self.keys = [ 'Name', 'Pid', 'VmRSS' ]

    def splashClicked(self,ev):
        if ev.button() == Qt.LeftButton:
            self.runExternalCmd()
        elif ev.button() == Qt.RightButton:
            self.splash.hide()

    def parseProc(self):
        with open('/proc/meminfo') as f:
            counter = 0
            for line in f:
                if counter == 5: break
                l = line.split()
                self.mem[l[0][:-1]] = l[1]
                counter += 1

        dirname = '/proc'
        pids = [pid for pid in os.listdir(dirname) if pid.isdigit()]
        self.ps = {}
        for pid in pids:
            try:
                with open(os.path.join(dirname, pid, "status")) as pf:
                    status = dict([
                        (
                            line.split(':')[0].strip(),
                            ':'.join(line.split(':')[1:]).strip()
                        ) for line in pf.readlines()
                        if line.split(':')[0].strip() in self.keys
                    ])

                    # read pid, name, rss
                    p = int(status.get('Pid', -1))
                    if p < 0:
                        continue

                    name = status.get('Name', None)
                    if name is None:
                        continue

                    rss = status.get('VmRSS', None)
                    if rss is None:
                        continue

                    self.ps[p] = [ name, int(rss.split()[0]) ]

            except Exception as e:
                # ignore all exceptions
                pass

    def update(self):
        if self.verbose.value():
            syslog.syslog( syslog.LOG_DEBUG, "DEBUG  %s: update" % self.name);
        self.parseProc()
        total = int(self.mem["MemTotal"])
        free  = int(self.mem["MemFree"])
        used  = total - free
        buff  = int(self.mem["Buffers"])
        cache = int(self.mem["Cached"])
        aCache = buff+cache
        aUsed  = used-aCache
        percCache = float(aCache)/total
        percUsed  = float(aUsed)/total
        percFree  = float(total-aUsed)/total
        pix = QPixmap(22,22)
        p = QPainter(pix)
        p.fillRect(pix.rect(), self.systray.bgColor)
        margin = 1
        w = pix.width()-2*margin
        h = pix.height()-2*margin
        p.save()
        p.rotate(-90)
        p.translate(-h-margin,margin)
        p.fillRect(0,0,round(percUsed*h),w,self.systray.fgColor)
        p.translate(round(percUsed*h),0)
        c2 = QColor(self.systray.fgColor)
        c2.setAlphaF(0.25)
        p.fillRect(0,0,round(percCache*h),w, c2)
        p.restore()
        p.setPen(self.systray.fgColor)
        f = QFont("Dejavu Sans", 6)
        p.setFont( f)
        p.drawText(margin,margin,w,h/2,Qt.AlignCenter,
                   "%d%%" % round(percUsed*100))
        p.end()
        self.systray.setIcon(QIcon(pix))

        data = []
        for k,v in self.ps.items():
            data += [ [ k, v[0], (v[1])/float(total) ] ]
        self.splash.data = data
        self.splash.update()
