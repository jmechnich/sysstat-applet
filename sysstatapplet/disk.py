from appletlib.splash import Splash

from PyQt5.Qt  import *

import time, os, re

from sysstatapplet.sysstat import SysStat
from sysstatapplet.util import *

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
        self.width = 3*self.br1.width()+2*self.br2.width()+6*self.margin
        
    def paintEvent(self,ev):
        ev.accept()
        n = len(self.data)
        if n > 1: n+=1
        lh = self.br2.height()
        height = n*(lh+self.margin)+self.margin
        self.resize( self.width, height)
        p = QPainter(self)
        p.setFont( self.font)
        p.fillRect( self.rect(), self.indicator.systray.bgColor)
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
        SysStat.__init__(self, "disk")
        self.splash = SplashDisk(self)

    def initVars(self):
        SysStat.initVars(self)
        self.old = {}
        self.new = {}
        
    def parseProc(self):
        self.old = dict(self.new)
        new = {}
        for dirname, dirnames, filenames in os.walk('/sys/block'):
            for subdirname in dirnames:
                if re.match( r'^loop\d+$|^ram\d+$', subdirname): continue
                stat = os.path.join(dirname, subdirname)
                stat = os.path.join(stat, "stat")
                if not os.path.isfile(stat): continue
                with open(stat) as f:
                    l = f.readline().split()
                    new[subdirname] = (int(l[2]), int(l[6]), time.time())
        if len(self.old):
            self.old = dict(self.new)
        else:
            self.old = new
        self.new = new                

    def drawStats(self):
        self.parseProc()
        if not len(self.old): return
        pix = QPixmap(22,22)
        p = QPainter(pix)
        f = QFont("Dejavu Sans", 6)
        p.setFont( f)
        p.fillRect(pix.rect(), self.systray.bgColor)
        margin = 0
        w = pix.width()-2*margin
        h = pix.height()-2*margin
        n = len(self.new)
        bh = round(float(h)/n)
        p.translate(margin,margin)
        data = {}
        total1 = 0
        total2 = 0
        for k in sorted(self.new.keys()):
            if not k in self.old: continue
            read    = self.new[k][0]-self.old[k][0]
            written = self.new[k][1]-self.old[k][1]
            t       = self.new[k][2]-self.old[k][2]
            if t == 0: t=1
            rate1   = float(read)*512/t
            rate2   = float(written)*512/t
            total1 += rate1
            total2 += rate2
            p.setPen(self.systray.fgColor)
            p.drawText( 0, 0, round(w*.75), bh, Qt.AlignRight|Qt.AlignVCenter, k)
            if read:
                p.fillRect( w-4, round(bh*.5)-4, 4, 4, Qt.green)
            if written:
                p.fillRect( w-4, round(bh*.5), 4, 4, Qt.red)
            p.translate(0,round(float(h)/n))
            data[k] = ( rate1, rate2 )
        p.end()
        self.systray.setIcon(QIcon(pix))
        self.splash.data = data
        self.splash.update()
        
    def printStats(self):
        self.parseProc()
        if not len(self.old): return
        total1 = 0
        total2 = 0
        for k in sorted(self.new.keys()):
            if not k in self.old: continue
            read    = self.new[k][0]-self.old[k][0]
            written = self.new[k][1]-self.old[k][1]
            t       = self.new[k][2]-self.old[k][2]
            if t == 0: t=1
            rate1   = float(read)*512/t
            rate2   = float(written)*512/t
            total1  += rate1
            total2  += rate2
            print("%s: read %s, written %s, total %s" % \
                (k,
                 prettyPrintBytesSec(rate1),
                 prettyPrintBytesSec(rate2),
                 prettyPrintBytesSec(rate1+rate2))
            )
        print("all: read %s, written %s, total %s" % \
            (prettyPrintBytesSec(total1),
             prettyPrintBytesSec(total2),
             prettyPrintBytesSec(total1+total2))
        )
        print()
