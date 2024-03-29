import csv
import glob
from datetime import datetime
import pytz
import math
import os
import locale

import http.client
import re
from urllib.parse import urlparse

STATIONSFILE = "tidalstations.conf"
DATADIR = "data/"



def getHttps(url):
    o = urlparse(url)
    import ssl
    conn = http.client.HTTPSConnection(o.netloc, context = ssl._create_unverified_context())
    conn.request("GET", "{}?{}".format(o.path, o.query))

    r1 = conn.getresponse()
    if (r1.status != 200):
        print ("*** Could not retrieve {}".format(url))
        return
    d = r1.headers['content-disposition']
    #print (d)
    fname = re.findall("filename=(.+)", d)[0].split(";")[0]
    
    print ("Fetching {} from {}...".format(fname, o.netloc))

    data1 = r1.read()
    
    dateStamp = datetime.now().strftime("%Y-%m-%d-")
    f = open(DATADIR + dateStamp + fname, "wb")
    f.write(data1)
    f.close()
    
    conn.close()

    
    
class TidalData(object):

    FETCH_DATA = 1
    DONT_FETCH_DATA = 0

    stations = {}
   
    corrected = 0
    uncorrected = 0

    
    class TidalStation (object):
    
        
        def __init__(self, stationName, sourceType, csvFileName, stationLat, stationLon, stationSource):
            self.stationName = stationName
            self.sourceType = sourceType
            self.csvFileName = csvFileName
            self.stationLat = float(stationLat)
            self.stationLon = float(stationLon)
            self.stationSource = stationSource
            
            self.waterLevel = {} # dict of waterLevel measurements
 
 
 
        def loadStationData(self):
            # For this station, read tidal data from all CSV files that are defined for it, into self.waterLevel{} records
            print ("Loading {} for {}".format(self.csvFileName, self.stationName))
            locale.setlocale(locale.LC_ALL, 'en_US')
            local=pytz.timezone('Etc/GMT-1')
            
            f = 0
            for file in glob.glob(DATADIR + self.csvFileName):
                with open(file) as csvfile:
                    tidalRows = csv.reader(csvfile, delimiter=';')
                    headers = next(tidalRows, None)
                    n = 0
                    for row in tidalRows:
                        try:
                            date_time_str = row[0] + " " + row[1];  # e.g. 26-2-2022 16:20:00
                            date_time_obj = datetime.strptime(date_time_str, '%d-%m-%Y %H:%M:%S')
                            date_time_utc = local.localize(date_time_obj, is_dst=None).astimezone(pytz.utc).replace(tzinfo=None).isoformat()
                            if (row[4] != ""):
                                self.waterLevel[date_time_utc] = row[4]
                                n += 1
                        except Exception as e:
                            print ("*** loadStationData: (file = {}, row={}, error = {}".format(file, row, str(e)))
                            pass
                    print ("- file {} read; {} waterLevels.".format(file, n))
                    f += 1
                    
            if (f == 0):
                print ("No file: go online and press Fetch to download csv files.")



        def getStationWaterLevel (self, utcTimeStamp):
            try:
                result = int(self.waterLevel[utcTimeStamp])
            except:
                result = None
            return result



        def getStationDistance(self, lat, lon):
            # Get the distance between the given latlon position to this station, in NM
            distance = math.sqrt(((lon - self.stationLon) * math.cos(lat/180*math.pi)) ** 2 + (lat - self.stationLat) ** 2) * 60
            return distance
 
 
        # End of class definition TidalStation



    def readStations(self, action):
        if (not os.path.exists(DATADIR)):
            os.mkdir(DATADIR) # Initial
        for file in glob.glob("*.csv"):
            os.rename (file, DATADIR + file)
        try:
            with open (STATIONSFILE, newline='') as stationsfile:
                allstations = csv.reader(stationsfile, delimiter='\t')
                for row in allstations:
                    tidalStation = self.TidalStation(row[0], row[1], row[2], row[3], row[4], row[5])
                    self.stations[row[0]] = tidalStation
                    if (action == self.FETCH_DATA):
                        getHttps(row[5])
                    tidalStation.loadStationData()
            print ("OK - Tidal stations processed.")
        except Exception as e:
            print (str(e))
            print ("Could not load '{}'. Not able to correct for tidal changes.".format(STATIONSFILE))
            print ("This file can be downloaded from github and needs to be put in the same directory as the python/exe file.")



    def getWeighedWaterLevel(self, utcTimeStamp, lat, lon):
        m = 0
        n = 0
        try:
            for station in self.stations:
                distanceToStation = self.stations[station].getStationDistance(lat, lon)
                weighingFactor = 1 / distanceToStation
                waterLevel = self.stations[station].getStationWaterLevel(utcTimeStamp)
                
                if (waterLevel != None):
                    m += self.stations[station].getStationWaterLevel(utcTimeStamp) * weighingFactor
                    n += weighingFactor
                
            if (n != 0):
                result = m / n / 100
                self.corrected += 1
            else:
                result = 0
                self.uncorrected += 1
            
        except Exception as e:
                print ("*** getWeighedWaterLevel:", utcTimeStamp, lat, lon, n, m, distanceToStation, str(e))
                self.uncorrected += 1
                result = 0
                
        return result



    def printStatistics(self):
        print ("{}% of waypoints corrected with tidal data".format(100* self.corrected/(self.uncorrected+self.corrected)) )
        self.corrected = 0
        self.uncorrected = 0
    
    

if __name__ == '__main__':
    tidalData = TidalData()
    tidalData.readStations()
    t = '2022-02-26T11:20:00'
    print ("Kornwerd", tidalData.stations['Kornwerd'].getStationWaterLevel(t))
    print ("Harlingen", tidalData.stations['Harlingen'].getStationWaterLevel(t))
    print ("Average:", tidalData.getAverageWaterLevel(t))
    print ("Weighed average (nabij Harlingen):", tidalData.getWeighedWaterLevel(t, 53.176993333, 5.40))
    print ("Weighed average (nabij Kornwerd):", tidalData.getWeighedWaterLevel(t, 53.079620000, 5.33))
    print ("Weighed average (ongeveer in het midden):", tidalData.getWeighedWaterLevel(t, 53.126993333, 5.37))

