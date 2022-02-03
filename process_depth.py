#!/usr/bin/env python
import wx
import socket
import time
import math

DEFAULT_FILENAME = "c:\\vdr.txt"
DEFAULT_OUTPUTPATH = "c:\\ProgramData\\opencpn\\layers\\dieptes.gpx"
GPX_HEADER='<?xml version="1.0" encoding="UTF-8" ?>\n<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">\n'

class SimulatorFrame(wx.Frame):

    def __init__(self, parent, title):
        super(SimulatorFrame, self).__init__(parent, title = title, size=(510,220))

        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(0,0)

        ## Set up Statictext
        text1 = wx.StaticText(panel, label = "Input file NMEA0183")
        sizer.Add(text1, pos = (0, 0), flag = wx.ALL, border = 3)
        text2 = wx.StaticText(panel, label = "Start time")
        sizer.Add(text2, pos = (2, 0), flag = wx.ALL, border = 3)
        text3 = wx.StaticText(panel, label = "End time")
        sizer.Add(text3, pos = (2, 2), flag = wx.ALL, border = 3)
        text4 = wx.StaticText(panel, label = "Start tide")
        sizer.Add(text4, pos = (3, 0), flag = wx.ALL, border = 3)
        text5 = wx.StaticText(panel, label = "End tide")
        sizer.Add(text5, pos = (3, 2), flag = wx.ALL, border = 3)
        text6 = wx.StaticText(panel, label = "Interval (m)")
        sizer.Add(text6, pos = (4, 0), flag = wx.ALL, border = 3)
        text7 = wx.StaticText(panel)
        sizer.Add(text7, pos = (1, 0), flag = wx.ALL, border = 3)
        text9 = wx.StaticText(panel)
        sizer.Add(text9, pos = (4, 2), flag = wx.ALL, border = 3)
        text10 = wx.StaticText(panel, label = "Output file GPX")
        sizer.Add(text10, pos = (5, 0), flag = wx.ALL, border = 3)

        ## Setup up controls
        filename = wx.TextCtrl(panel, value=DEFAULT_FILENAME)
        sizer.Add(filename, pos = (0,1), flag = wx.EXPAND|wx.ALL, border = 3, span=(1,4))
        
        def OnChange_filename(event):
             buttonLoad.filename = filename.GetValue()
        self.Bind(wx.EVT_TEXT, OnChange_filename, filename)

        # Set up buttons
        buttonLoad = wx.Button(panel, label = "Load" )
        sizer.Add(buttonLoad, pos = (1, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        #buttonLoad.filename = filename.GetValue()
        buttonGenerate = wx.Button(panel, label = "Generate" )
        sizer.Add(buttonGenerate, pos = (4, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonGenerate.Disable()

        startTime = wx.TextCtrl(panel, value="", size=(80,20))
        sizer.Add(startTime, pos = (2, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        endTime = wx.TextCtrl(panel, value="", size=(80,20))
        sizer.Add(endTime, pos = (2, 3), flag = wx.EXPAND|wx.ALL, border = 3)
        startTide = wx.TextCtrl(panel, value="0", size=(80,10))
        sizer.Add(startTide, pos = (3, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        endTide = wx.TextCtrl(panel, value="0", size=(80,20))
        sizer.Add(endTide, pos = (3, 3), flag = wx.EXPAND|wx.ALL, border = 3)
        interval = wx.TextCtrl(panel, value="10", size=(80,20))
        sizer.Add(interval, pos = (4, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        
        def OnChange_startTide(event):
            endTide.SetValue(startTide.GetValue())
        self.Bind(wx.EVT_TEXT, OnChange_startTide, startTide)

        outputfilename = wx.TextCtrl(panel, value=DEFAULT_OUTPUTPATH, size=(340,20))
        sizer.Add(outputfilename, pos = (5,1), flag = wx.EXPAND|wx.ALL, border = 3, span=(1,4))

        def loadFile(event):
            l = 0
            rmc = 0
            dpt = 0
            self.mintime = "999999"
            self.mindate = "999999"
            self.maxtime = "000000"
            self.maxdate = "000000"
            self.mindepth = 99.0
            self.maxdepth = -99.0
            text7.SetLabel("")
            for lines in open(filename.GetValue(), 'r'):
                l += 1
                line = lines.strip().split(',')
                if (line[0] == "$GPRMC"):
                    rmc += 1
                    if (line[1] < self.mintime): self.mintime = line[1][:6]
                    if (line[1] > self.maxtime): self.maxtime = line[1][:6]
                    if (line[9] < self.mindate): self.mindate = line[9]
                    if (line[9] > self.maxdate): self.maxdate = line[9]
                if (line[0] == "$SDDPT"):
                    depth = float(line[1])
                    if (depth < self.mindepth): self.mindepth = depth;
                    if (depth > self.maxdepth): self.maxdepth = depth;
                    dpt += 1
            text7.SetLabel("Lines={}, RMC={}, DPT={}, depth={} - {}".format(l, rmc, dpt, self.mindepth, self.maxdepth))
            startTime.SetValue(self.mintime)
            endTime.SetValue(self.maxtime)
            buttonGenerate.Enable()
            outputfilename.SetValue(DEFAULT_OUTPUTPATH.replace(".gpx", "-20{}-{}-{}.gpx").format(self.mindate[4:6], self.mindate[2:4], self.mindate[0:2]))
        panel.SetSizerAndFit(sizer)

        buttonLoad.Bind(wx.EVT_BUTTON, loadFile)
        
        
        
        def convertLatLon (latLon):
            if (latLon[4] == "."):
                latLon = "" + "0" + latLon
            val = float(latLon[0:3]) + float(latLon[3:])/60
            return val
        
        
        
        def depthIcon (curdepth, startTide, endTide):
            actualDepth = round(float(curdepth) - (float(startTide) + float(endTide))/2, 1)  # 1 digit
            
            if (actualDepth < 0):
                name = 'dry'
            else:
                name = 'depth'
                
            m = math.floor(abs(actualDepth))
            dm = math.floor((abs(actualDepth) - m )*10)
            icon = "{}_{}-{}".format(name, m, dm)
            
            if (curdepth == self.mindepth):
                print ("yes")
         
            return icon
        
        
        
        def scale (x):
            s = 32
            a = x % 32
            for z in range(5, -1, -1):
                if a > 31:
                    s = 2 ** z
                    a = a - 32
                a = a * 2
            return (s * 800)



        def generateFile (event):
            rmc = 0
            dpt = 0
            waypoints = 0
            lastlat = 0
            lastlon = 0
            i = 0
            fromTimeStamp = "" + self.mindate + startTime.GetValue()
            toTimeStamp = "" + self.maxdate + endTime.GetValue()
            text9.SetLabel("")
            f = open(outputfilename.GetValue(), "w")
            f.write(GPX_HEADER)
            
            for lines in open(filename.GetValue(), 'r'):
                line = lines.strip().split(',')
                
                if (line[0] == "$GPRMC"):
                    curdate = line[9]
                    curtime = line[1][:6]
                    timeStamp = "" + curdate + curtime
                    
                    if (timeStamp >= fromTimeStamp and timeStamp <= toTimeStamp):
                        rmc += 1
                        curlat = convertLatLon(line[3])
                        curlon = convertLatLon(line[5])
                        
                if (line[0] == "$SDDPT"):
                    if (timeStamp >= fromTimeStamp and timeStamp <= toTimeStamp):
                        dpt += 1
                        curdepth = line[1]
                        distance = math.sqrt(((curlon - lastlon) * math.cos(curlat/180*math.pi)) ** 2 + (curlat - lastlat) ** 2) * 60 * 1852
                        
                        if (distance > 10000):
                            lastlat = curlat; lastlon = curlon; #distance = 0;
                            
                        if (distance > float (interval.GetValue())):
                            waypoints += 1
                            gpx = '  <wpt lat="{}" lon="{}"><sym>{}</sym><extensions><opencpn:scale_min_max UseScale="true" ScaleMin="{}" /></extensions></wpt>' \
                                .format(curlat, curlon, depthIcon(curdepth, startTide.GetValue(), endTide.GetValue()), scale(i))
                            print (gpx)
                            f.write(gpx + "\n")
                            lastlat = curlat; lastlon = curlon; i += 1;
                            
            text9.SetLabel("{} waypoints".format(waypoints))
            f.write ('</gpx>')
            f.close()
           
        buttonGenerate.Bind(wx.EVT_BUTTON, generateFile)

        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_CLOSE, self.OnExitApp)
        
    
    def OnExitApp(self, event):
        print ('--- Window closed')
        self.Destroy()
        

app = wx.App()
myFrame = SimulatorFrame(None, title = 'Depth processor')
app.MainLoop()

