import csv
import glob
import datetime
import pytz
import math

STATIONSFILE = "tidalstations.conf"

class TidalData(object):

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
            print ("Loading station data for station {} with name {}".format(self.stationName, self.csvFileName))
            local=pytz.timezone('Etc/GMT-1')
            
            f = 0
            for file in glob.glob(self.csvFileName):
                print (" - reading file {}".format(file))
                with open(file) as csvfile:
                    tidalRows = csv.reader(csvfile, delimiter=';')
                    n = 0
                    for row in tidalRows:
                        try:
                            date_time_str = row[0] + " " + row[1];  # e.g. 26-2-2022 16:20:00
                            date_time_obj = datetime.datetime.strptime(date_time_str, '%d-%m-%Y %H:%M:%S')
                            date_time_utc = local.localize(date_time_obj, is_dst=None).astimezone(pytz.utc).replace(tzinfo=None).isoformat()
                            if (row[4] != ""):
                                self.waterLevel[date_time_utc] = row[4]
                                n += 1
                        except Exception as e:
                            #print ("*** loadStationData:", str(e))
                            pass
                    print (" -", n, "waterLevels read")
                    f += 1
                    
            print (f, "files read")
            if (f == 0):
                print ("Csv files can be downloaded from {}.\nSee the file '{}'.".format(self.stationSource, STATIONSFILE))



        def getStationWaterLevel (self, utcTimeStamp):
            try:
                result = int(self.waterLevel[utcTimeStamp])
            except:
                result = None
            return result



        def getStationDistance(self, lat, lon):
            # In NM between (lat, lon) and station
            distance = math.sqrt(((lon - self.stationLon) * math.cos(lat/180*math.pi)) ** 2 + (lat - self.stationLat) ** 2) * 60
            return distance
 
 
        # End of class definition TidalStation




    def readStations(self):
        try:
            with open (STATIONSFILE, newline='') as stationsfile:
                allstations = csv.reader(stationsfile, delimiter='\t')
                for row in allstations:
                    tidalStation = self.TidalStation(row[0], row[1], row[2], row[3], row[4], row[5])
                    self.stations[row[0]] = tidalStation
                    tidalStation.loadStationData()
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
                result = m / n
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
        print ("{} waypoints corrected with tidal data".format(self.corrected) )
        print ("{} waypoints NOT corrected with tidal data".format(self.uncorrected) )
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

