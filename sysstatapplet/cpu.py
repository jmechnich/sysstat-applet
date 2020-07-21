import os
import syslog

from .sysstat import SysStat

from appletlib.splash import Splash

from PyQt5.Qt import *

class SplashCpu(Splash):
    def __init__(self,indicator):
        Splash.__init__(self)
        self.indicator = indicator
        self.initVars()

    def initVars(self):
        self.data = []
        fm = QFontMetrics( self.font)
        pid_max = "00000"
        with open("/proc/sys/kernel/pid_max", "r") as f:
            pid_max = f.read()
        self.br1 = fm.boundingRect(pid_max)
        self.br2 = fm.boundingRect("0000.0%")
        self.margin = 2
        self.w = self.br1.width()+100+self.br2.width()+4*self.margin
        self.h = 5*(self.br2.height()+self.margin)+self.margin
        self.resize(self.w, self.h)

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
            p.drawText(xpos, 0, 100, lh, Qt.AlignRight, k[1][1:-1])
            xpos+=100+self.margin
            p.setPen(Qt.green)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                       "%5.1f%%" % float(sum(k[2:])*100.))
            p.translate(0,lh+self.margin)
        p.end()

class IndicatorCpu(SysStat):
    def __init__(self):
        SysStat.__init__(self, "cpu", "xterm -e htop")
        self.splash = SplashCpu(self)
        self.splash.triggerClick.connect(self.splashClicked)
        self.splash.triggerResize.connect(
            lambda ev: self.updateSplashGeometry())

    def initVars(self):
        SysStat.initVars(self)
        self.old = {}
        self.new = {}
        self.oldps = {}
        self.newps = {}

    def splashClicked(self,ev):
        if ev.button() == Qt.LeftButton:
            self.runExternalCmd()
        elif ev.button() == Qt.RightButton:
            self.splash.hide()

    def parseProc(self):
        with open('/proc/stat') as f:
            new = {}
            for line in f:
                if not line.startswith('cpu'): break
                l = line.split()
                new[l[0]] = (l[1], l[2], l[3], l[4],
                             sum([int(i) for i in l[1:]]))
            if len(self.old):
                self.old = dict(self.new)
            else:
                self.old = new
            self.new = new

        dirname = '/proc'
        pids = [pid for pid in os.listdir(dirname) if pid.isdigit()]
        newps = {}
        for pid in pids:
            stat = os.path.join(dirname, pid, "stat")
            try:
                with open(stat) as f:
                    l = f.readline().split()
                    # read pid, comm, utime, stime
                    newps[int(l[0])] = [ l[1], int(l[13]), int(l[14])]
            except:
                pass

        if len(self.oldps):
            self.oldps = dict(self.newps)
        else:
            self.oldps = newps
        self.newps = newps

    def update(self):
        if self.verbose.value():
            syslog.syslog(syslog.LOG_DEBUG, "DEBUG  %s: update" % self.name);
        self.parseProc()
        pix = QPixmap(22,22)
        p = QPainter(pix)
        p.fillRect(pix.rect(), self.systray.bgColor)
        margin = 1
        w = pix.width()-2*margin
        h = pix.height()-2*margin

        keys = sorted(list(set(self.old.keys()).intersection(self.new.keys())))
        if len(keys) < 3: keys = ['cpu']
        n = len(keys)
        box = QRect(0, 0,(w-(n-1)*margin)/n, h)
        p.save()
        p.rotate(-90)
        p.translate(-h-margin,margin)
        total = 0
        for k in keys:
            user = sum([int(i) for i in self.new[k][0:1]]) - \
                sum([int(i) for i in self.old[k][0:1]])
            system = int(self.new[k][2])-int(self.old[k][2])
            idle  = int(self.new[k][3])-int(self.old[k][3])
            total = self.new[k][4]-self.old[k][4]
            if total == 0: total = 1
            perc1  = float(user)/total
            perc2  = float(system)/total
            p.fillRect(0, 0, round(box.height()*perc2), box.width(),
                       self.systray.fgColor)
            c2 = QColor(self.systray.fgColor)
            c2.setAlphaF(0.25)
            p.fillRect(round(box.height()*perc2), 0,
                       round(box.height()*perc1), box.width(), c2)
            p.translate(0,box.width()+margin)
        p.restore()

        work = sum([int(i) for i in self.new["cpu"][0:2]]) - \
               sum([int(i) for i in self.old["cpu"][0:2]])
        total = self.new["cpu"][4]-self.old["cpu"][4]
        if total == 0: total = 1
        perc1  = float(work)/total
        c1 = QColor(
            round(self.systray.bgColor.red()+self.systray.fgColor.red())/2,
            round(self.systray.bgColor.green()+self.systray.fgColor.green())/2,
            round(self.systray.bgColor.blue()+self.systray.fgColor.blue())/2)
        p.setPen(self.systray.fgColor)
        f = QFont("Dejavu Sans", 6)
        p.setFont( f)
        p.drawText(margin,margin,w,h/2,Qt.AlignCenter,
                   "%d%%" % round((perc1+perc2)*100))
        p.end()
        self.systray.setIcon(QIcon(pix))

        data = []
        for k,v in self.newps.items():
            oldv = self.oldps.get(k)
            if oldv:
                data += [ [ k, v[0],
                          (v[1]-oldv[1])/float(total),
                          (v[2]-oldv[2])/float(total) ] ]
            else:
                data += [ [ k, v[0], 0, 0 ] ]
        self.splash.data = data
        self.splash.update()
