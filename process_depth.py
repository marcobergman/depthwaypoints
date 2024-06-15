#!/usr/bin/env python
import wx
import socket
import time
import math
import platform
import re    ## regular expressions
import datetime
import locale

GPX_HEADER='<?xml version="1.0" encoding="UTF-8" ?>\n<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">\n'
DEFAULT_INTERVAL = 15
TRACK_INTERVAL = 30


if (platform.system() == "Windows"):
    DEFAULT_FILENAME = "c:\\nmea.log"
    DEFAULT_LAYERPATH = "c:\\ProgramData\\opencpn\\layers\\depths.gpx"
    DEFAULT_TRACKPATH = "c:\\ProgramData\\opencpn\\tracks\\tracks.gpx"
    AUTOFETCH = "autofetch.cmd"
else:
    DEFAULT_FILENAME = "/extra/nmea.log"
    DEFAULT_LAYERPATH = ".opencpn/layers/depths.gpx"
    DEFAULT_TRACKPATH = ".opencpn/tracks/tracks.gpx"
    AUTOFETCH = "autofetch.sh"



class DepthWaypointsFrame(wx.Frame):

    def __init__(self, parent, title):
        super(DepthWaypointsFrame, self).__init__(parent, title = title, size=(510,245))

        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(0,0)

        ## Set up Statictext
        text1 = wx.StaticText(panel, label = "Input file NMEA0183")
        sizer.Add(text1, pos = (0, 0), flag = wx.ALL, border = 3)
        text2 = wx.StaticText(panel, label = "Start time (UTC)")
        sizer.Add(text2, pos = (2, 0), flag = wx.ALL, border = 3)
        text3 = wx.StaticText(panel, label = "End time")
        sizer.Add(text3, pos = (2, 2), flag = wx.ALL, border = 3)
        text4 = wx.StaticText(panel, label = "Tide offset (m above MSL)")
        sizer.Add(text4, pos = (3, 0), flag = wx.ALL, border = 3)
        text5 = wx.StaticText(panel, label = "Max depth")
        sizer.Add(text5, pos = (3, 2), flag = wx.ALL, border = 3)
        text6 = wx.StaticText(panel, label = "Waypoint interval (m)")
        sizer.Add(text6, pos = (4, 0), flag = wx.ALL, border = 3)
        text7 = wx.StaticText(panel)
        sizer.Add(text7, pos = (1, 0), flag = wx.ALL, border = 3, span=(1,4))
        text9 = wx.StaticText(panel)
        sizer.Add(text9, pos = (4, 2), flag = wx.ALL, border = 3)
        text10 = wx.StaticText(panel, label = "Output layer file")
        sizer.Add(text10, pos = (5, 0), flag = wx.ALL, border = 3)
        text11 = wx.StaticText(panel, label = "Output track file")
        sizer.Add(text11, pos = (6, 0), flag = wx.ALL, border = 3)

        ## Setup up controls
        filename = wx.TextCtrl(panel, value=DEFAULT_FILENAME)
        sizer.Add(filename, pos = (0,1), flag = wx.EXPAND|wx.ALL, border = 3, span=(1,4))
        
        def OnChange_filename(event):
            buttonLoad.filename = filename.GetValue()
        self.Bind(wx.EVT_TEXT, OnChange_filename, filename)
        
        def FilenameDialog(event = None):
            dlg = wx.FileDialog(self, "NMEA0183 log file to open",
                defaultDir = os.path.dirname(""),
                defaultFile = os.path.basename("nmea.log"),
                wildcard = "Log files (*.log)|*.log|All files|*")

            if dlg.ShowModal() == wx.ID_OK:
                print ("Selected", dlg.GetPath())
                filename.SetValue(dlg.GetPath())

            dlg.Destroy() 

        self.Bind(wx.EVT_TEXT_ENTER, FilenameDialog, filename)


        # Set up buttons
        buttonSelect = wx.Button(panel, label = "Select file" )
        sizer.Add(buttonSelect, pos = (1, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonSelect.Bind(wx.EVT_BUTTON, FilenameDialog)

        buttonLoad = wx.Button(panel, label = "Load" )
        sizer.Add(buttonLoad, pos = (2, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)

        buttonFetch = wx.Button(panel, label = "Fetch" )
        sizer.Add(buttonFetch, pos = (3, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        
        buttonGenerate = wx.Button(panel, label = "Generate" )
        sizer.Add(buttonGenerate, pos = (4, 4), flag = wx.ALIGN_CENTER|wx.ALL, border = 3)
        buttonGenerate.Disable()

        startTime = wx.TextCtrl(panel, value="", size=(80,20))
        sizer.Add(startTime, pos = (2, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        endTime = wx.TextCtrl(panel, value="", size=(80,20))
        sizer.Add(endTime, pos = (2, 3), flag = wx.EXPAND|wx.ALL, border = 3)
        tideOffset = wx.TextCtrl(panel, value="0", size=(80,10))
        sizer.Add(tideOffset, pos = (3, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        maxDepth = wx.TextCtrl(panel, value="10", size=(80,20))
        sizer.Add(maxDepth, pos = (3, 3), flag = wx.EXPAND|wx.ALL, border = 3)
        interval = wx.TextCtrl(panel, value=str(DEFAULT_INTERVAL), size=(80,20))
        sizer.Add(interval, pos = (4, 1), flag = wx.EXPAND|wx.ALL, border = 3)
        layerfilename = wx.TextCtrl(panel, value=DEFAULT_LAYERPATH, size=(340,20))
        sizer.Add(layerfilename, pos = (5,1), flag = wx.EXPAND|wx.ALL, border = 3, span=(1,4))
        trackfilename = wx.TextCtrl(panel, value=DEFAULT_TRACKPATH, size=(340,20))
        sizer.Add(trackfilename, pos = (6,1), flag = wx.EXPAND|wx.ALL, border = 3, span=(1,4))



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
            print ("Loading NMEA log file {}...".format(filename.GetValue()))
            for lines in open(filename.GetValue(), 'r'):
                try:
                    l += 1
                    line = lines.strip().split(',')
                    if (re.match(r"\$[A-Z]{2}RMC", line[0]) and line[1] != ""):
                        rmc += 1
                        if (line[1] < self.mintime): self.mintime = line[1][:6]
                        if (line[1] > self.maxtime): self.maxtime = line[1][:6]
                        if (line[9] < self.mindate): self.mindate = line[9]
                        if (line[9] > self.maxdate): self.maxdate = line[9]
                    if (re.match(r"\$[A-Z]{2}DPT", line[0])):
                        depth = float(line[1])
                        if (depth < self.mindepth): self.mindepth = depth;
                        if (depth > self.maxdepth): self.maxdepth = depth;
                        dpt += 1
                except Exception as e:
                    print ("could not read line {}: {}".format(l, line))
            text7.SetLabel("Lines={}, RMC={}, DPT={}, depth={} - {}".format(l, rmc, dpt, round(self.mindepth, 1), round(self.maxdepth, 1)))
            startTime.SetValue(self.mintime)
            endTime.SetValue(self.maxtime)
            buttonGenerate.Enable()
            layerfilename.SetValue(DEFAULT_LAYERPATH.replace(".gpx", "-20{}-{}-{}.gpx").format(self.mindate[4:6], self.mindate[2:4], self.mindate[0:2]))
            trackfilename.SetValue(DEFAULT_TRACKPATH.replace("tracks.gpx", "20{}-{}-{}-tracks.gpx").format(self.mindate[4:6], self.mindate[2:4], self.mindate[0:2]))
            print ("OK - File loaded.")
            print ("self.mintime {} self.maxtime {} self.mindate {} self.maxdate {}".format(self.mintime, self.maxtime, self.mindate, self.maxdate))
            
            
        panel.SetSizerAndFit(sizer)

        buttonLoad.Bind(wx.EVT_BUTTON, loadFile)
        
        
        
        def convertLatLon (latLon):
            if (latLon[4] == "."):
                latLon = "" + "0" + latLon
            val = float(latLon[0:3]) + float(latLon[3:])/60
            return val
        
        
        
        def nmeaToIso (timestamp):
            locale.setlocale(locale.LC_ALL, 'en_US')
            try:
                date_time_obj = datetime.datetime.strptime(timestamp, '%d%m%y%H%M%S')
                new_minute = math.floor(date_time_obj.minute/10)*10
                val = date_time_obj.replace(second=0, minute=new_minute).isoformat()
            except Exception as e:
                print ("nmeaToIso", timestamp, str(e))
                pass 
            return val
        
        
        
        def depthIcon (curdepth, waterLevel):
            
            actualDepth = round(float(curdepth) - float(waterLevel) , 1)  # 1 digit
            
            if (actualDepth < 0):
                name = 'dry'
            else:
                name = 'depth'
                
            m = math.floor(abs(actualDepth))
            dm = math.floor((abs(actualDepth) - m )*10)
            icon = "{}_{}-{}".format(name, m, dm)
            
            #if (curdepth == self.mindepth):
            #    print ("yes")
         
            return icon
        
        
        
        def scale (x):
            s = 32
            a = x % 32
            for z in range(5, -1, -1):
                if a > 31:
                    s = 2 ** z
                    a = a - 32
                a = a * 2
            return (s * 1600)



        def generateLayerFile (event):
            rmc = 0
            dpt = 0
            waypoints = 0
            lastlat = 0
            lastlon = 0
            i = 0  # cycle for scale pendulum
            n = 0  # line counter for verbose exception handling 
            print ("Generating layer file", layerfilename.GetValue())
            
            fromTimeStamp = "" + self.mindate + startTime.GetValue()
            toTimeStamp = "" + self.maxdate + endTime.GetValue()
            tideOffsetValue = float(tideOffset.GetValue())
            maxDepthValue = float(maxDepth.GetValue())
            if (tideOffsetValue != 0):
                print ("Warning! Tide Offset = {}.".format(tideOffsetValue))
            text9.SetLabel("")
            
            f = open(layerfilename.GetValue(), "w")
            f.write(GPX_HEADER)
            timeStamp = ""
            
            for lines in open(filename.GetValue(), 'r'):
                n += 1
                line = lines.strip().split(',')
                
                try:
                    if (re.match(r"\$[A-Z]{2}RMC", line[0])):
                        curdate = line[9]
                        curtime = line[1][:6]
                        timeStamp = "" + curdate + curtime
                        
                        if (timeStamp >= fromTimeStamp and timeStamp <= toTimeStamp):
                            rmc += 1
                            curlat = convertLatLon(line[3])
                            curlon = convertLatLon(line[5])
                        #else:
                        #    print ("NOT within time interval")

                            
                    if (re.match(r"\$[A-Z]{2}DPT", line[0])):
                        if (timeStamp >= fromTimeStamp and timeStamp <= toTimeStamp):
                            dpt += 1
                            curdepth = float(line[1])
                            
                            # Caluculate distance to previously generated waypoint
                            distance = math.sqrt(((curlon - lastlon) * math.cos(curlat/180*math.pi)) ** 2 + (curlat - lastlat) ** 2) * 60 * 1852
                            
                            if (distance > 10000):
                                lastlat = curlat; lastlon = curlon;   #distance = 0; to deal with initial measurement
                                
                            if (distance > float (interval.GetValue())):
                                
                                waterLevel = tidalData.getWeighedWaterLevel(nmeaToIso(timeStamp), curlat, curlon)
                                
                                if (curdepth - waterLevel < maxDepthValue and curdepth != 0):
                                    gpx = '  <wpt lat="{:.6f}" lon="{:.6f}"><sym>{}</sym><extensions><opencpn:scale_min_max UseScale="true" ScaleMin="{}" /></extensions></wpt>' \
                                        .format(curlat, curlon, depthIcon(curdepth, waterLevel), scale(i))
                                    ### print (gpx)
                                    f.write(gpx + "\n")
                                    waypoints += 1
                                    i += 1
                                lastlat = curlat
                                lastlon = curlon
                except Exception as e:
                    print ("exception processing line {} of {}: ".format(n, filename.GetValue()) + lines  + str(e))
                    pass
 
 
            text9.SetLabel("{} waypoints".format(waypoints))
            f.write ('</gpx>')
            f.close()
            
            print ("OK - Waypoint file created with {} waypoints".format(waypoints))
            tidalData.printStatistics()
            
            
        def formatTimestamp(timeStamp):
            # format 130223060009 into 2023-02-13T06:00:09Z
            return "20{}-{}-{}T{}:{}:{}Z".format(timeStamp[4:6], timeStamp[2:4], timeStamp[0:2], timeStamp[6:8], timeStamp[8:10], timeStamp[10:12])
            
            
        def generateTrackFile (event):
            rmc = 0
            waypoints = 0
            lastlat = 0
            lastlon = 0
            i = 0  # cycle for scale pendulum
            n = 0  # line counter for verbose exception handling 
            print ("Generating track file", trackfilename.GetValue())
            
            fromTimeStamp = "" + self.mindate + startTime.GetValue()
            toTimeStamp = "" + self.maxdate + endTime.GetValue()
            text9.SetLabel("")
            
            f = open(trackfilename.GetValue(), "w")
            f.write(GPX_HEADER)
            f.write("<trk><name></name><trkseg>")
            timeStamp = ""
            
            for lines in open(filename.GetValue(), 'r'):
                n += 1
                line = lines.strip().split(',')
                
                try:
                    if (re.match(r"\$[A-Z]{2}RMC", line[0])):
                        curdate = line[9]
                        curtime = line[1][:6]
                        timeStamp = "" + curdate + curtime
                        
                        if (timeStamp >= fromTimeStamp and timeStamp <= toTimeStamp):
                            rmc += 1
                            curlat = convertLatLon(line[3])
                            curlon = convertLatLon(line[5])

                            # Caluculate distance to previously generated waypoint
                            distance = math.sqrt(((curlon - lastlon) * math.cos(curlat/180*math.pi)) ** 2 + (curlat - lastlat) ** 2) * 60 * 1852
                            
                            if (distance > 10000):
                                lastlat = curlat; lastlon = curlon;   #distance = 0; to deal with initial measurement
                                
                            if (distance > float (TRACK_INTERVAL)):
                                
                                gpx = '  <trkpt lat="{:.6f}" lon="{:.6f}"><time>{}</time></trkpt>' \
                                    .format(curlat, curlon, formatTimestamp(timeStamp))
                                ### print (gpx)
                                f.write(gpx + "\n")
                                waypoints += 1
                                i += 1
                                
                                lastlat = curlat
                                lastlon = curlon
                except Exception as e:
                    print ("exception processing line {} of {}: ".format(n, filename.GetValue()) + lines  + str(e))
                    pass
 
            f.write ('</trkseg></trk></gpx>')
            f.close()
            
            print ("OK - Track file created with {} waypoints".format(waypoints))

           
        def generateFiles(event):
            generateLayerFile (event)
            generateTrackFile (event)
           
        buttonGenerate.Bind(wx.EVT_BUTTON, generateFiles)
        
        def fetchData (event):
            print ("Fetching tidal data from the internet...")
            tidalData.readStations(tidalData.FETCH_DATA)
            
        buttonFetch.Bind(wx.EVT_BUTTON, fetchData)

        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_CLOSE, self.OnExitApp)
        
    
    def OnExitApp(self, event):
        print ('--- Window closed')
        self.Destroy()
        
import os
full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
os.chdir(path)

print ("Attempting " + AUTOFETCH)
import subprocess
if os.path.exists(AUTOFETCH):
    output = subprocess.check_output(AUTOFETCH, shell=False).decode("utf-8").split("\r\n")
    for line in output:
        print (line)

import tidaldata
tidalData = tidaldata.TidalData()
tidalData.readStations(tidalData.DONT_FETCH_DATA)

app = wx.App()
myFrame = DepthWaypointsFrame(None, title = 'Depth processor')
app.MainLoop()

