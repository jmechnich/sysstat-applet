from indicator import *
from splash import *
from util import *

from PyQt4.Qt import *

import os, resource

class SplashMem(Splash):
    def __init__(self,indicator):
        Splash.__init__(self, indicator)
        self.initVars()
        
    def initVars(self):
        self.data = []
        fm = QFontMetrics( self.font)
        self.br1 = fm.boundingRect("00000")
        self.br2 = fm.boundingRect("0000.0%")
        self.margin = 2
        self.width = self.br1.width()+100+self.br2.width()+4*self.margin
        height = 5*(self.br2.height()+self.margin)+self.margin
        self.resize( self.width, height)
    
    def paintEvent(self,ev):
        ev.accept()
        #for i in sorted(self.data, key=lambda i: sum(i[2:]), reverse=True)[:5]:
        #    print "%5d %20s: %5.1f%%" % (i[0],i[1][1:-1],sum(i[2:])*100.)
        #print
        lh = self.br2.height()
        p = QPainter(self)
        p.setFont( self.font)
        p.fillRect( self.rect(), self.sti.bgColor)
        p.setPen(self.sti.fgColor)
        p.translate(self.margin,self.margin)
        for k in sorted(self.data, key=lambda i: sum(i[2:]), reverse=True)[:5]:
            xpos=0
            p.setPen(Qt.white)
            p.drawText(xpos, 0, self.br1.width(), lh, Qt.AlignRight, str(k[0]))
            xpos+=self.br1.width()+self.margin
            p.setPen(self.sti.fgColor)
            p.drawText(xpos, 0, 100, lh, Qt.AlignRight, k[1][1:-1])
            xpos+=100+self.margin
            p.setPen(Qt.green)
            p.drawText(xpos, 0, self.br2.width(), lh, Qt.AlignRight,
                       "%5.1f%%" % float(sum(k[2:])*100.))
            p.translate(0,lh+self.margin)
        p.end()

class IndicatorMem(Indicator):
    def __init__(self):
        Indicator.__init__(self, "mem")
        self.func = self.drawStats
        self.initVars()
        self.initContextMenu()
        self.initStats()
        self.splash = SplashMem(self.s)
        
    def initVars(self):
        self.mem = {}
        self.ps  = {}
        
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
                self.updateSplash(True)
                self.splash.show()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.reset()
            self.initContextMenu()
            self.initStats()
        elif reason == QSystemTrayIcon.Context:
            pass
        elif reason == QSystemTrayIcon.Unknown:
            print "unknown"

    def parseProc(self):
        f = open('/proc/meminfo')
        counter = 0
        for line in f:
            if counter == 5: break
            l = line.split()
            self.mem[l[0][:-1]] = l[1]
            counter += 1
        f.close()

        dirname = '/proc'
        pids = [pid for pid in os.listdir(dirname) if pid.isdigit()]
        self.ps = {}
        for pid in pids:
            stat = os.path.join(dirname, pid, "stat")
            if not os.path.isfile(stat): continue
            f = open(stat)
            l = f.readline().split()
            # read pid, comm, rss
            f.close()
            self.ps[int(l[0])] = [ l[1], int(l[23])*(resource.getpagesize()/1024)]

    def drawStats(self):
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
        p.fillRect(pix.rect(), self.s.bgColor)
        margin = 1
        w = pix.width()-2*margin
        h = pix.height()-2*margin
        p.save()
        p.rotate(-90)
        p.translate(-h-margin,margin)
        p.fillRect(0,0,round(percUsed*h),w,self.s.fgColor)
        p.translate(round(percUsed*h),0)
        c2 = QColor(self.s.fgColor)
        c2.setAlphaF(0.5)
        p.fillRect(0,0,round(percCache*h),w, c2)
        p.restore()
        p.setPen(self.s.fgColor)
        f = QFont("Dejavu Sans", 6)
        p.setFont( f)
        p.drawText(margin,margin,w,h/2,Qt.AlignCenter,
                   "%d%%" % round(percUsed*100))
        p.end()
        self.s.setIcon(QIcon(pix))

        data = []
        for k,v in self.ps.iteritems():
            data += [ [ k, v[0], (v[1])/float(total) ] ]
        self.splash.data = data
        self.splash.update()

    def printStats(self):
        self.parseProc()
        total = int(self.mem["MemTotal"])
        free  = int(self.mem["MemFree"])
        used  = total - free
        buff  = int(self.mem["Buffers"])
        cache = int(self.mem["Cached"])
        aUsed = used-buff-cache
        print "%d/%d used (%.2f%%)" % (aUsed,total,float(aUsed)/total*100)
