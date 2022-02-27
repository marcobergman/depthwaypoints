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
                            #print (row)
                            date_time_str = row[0] + " " + row[1];  # e.g. 26-2-2022 16:20:00
                            date_time_obj = datetime.datetime.strptime(date_time_str, '%d-%m-%Y %H:%M:%S')
                            date_time_utc = local.localize(date_time_obj, is_dst=None).astimezone(pytz.utc).replace(tzinfo=None).isoformat()
                            if (row[4] != ""):
                                self.waterLevel[date_time_utc] = row[4]
                                n += 1
                        except Exception as e:
                            pass
                            #print ("*** loadStationData:", str(e))
                    #print (self.waterLevel)
                    print (" -", n, "waterLevels read")
                    f += 1
                    
            print (f, "files read")



        def getStationWaterLevel (self, utcTimeStamp):       
            return int(self.waterLevel[utcTimeStamp])



        def getStationDistance(self, lat, lon):
            # In NM between (lat, lon) and station
            distance = math.sqrt(((lon - self.stationLon) * math.cos(lat/180*math.pi)) ** 2 + (lat - self.stationLat) ** 2) * 60
            return distance
 
 
        # End of class definition TidalStation




    def readStations(self):
        with open (STATIONSFILE, newline='') as statsionsfile:
            allstations = csv.reader(statsionsfile, delimiter='\t')
            for row in allstations:
                tidalStation = self.TidalStation(row[0], row[1], row[2], row[3], row[4], row[5])
                self.stations[row[0]] = tidalStation
                tidalStation.loadStationData()



    def getAverageWaterLevel(self, utcTimeStamp):
        m = 0
        n = 0
        for station in self.stations:
            try:
                m += self.stations[station].getStationWaterLevel(utcTimeStamp)
                n += 1
            except Exception as e:
                #print ("*** getAverageWaterLevel:", str(e))
                pass
                
        return (m / n)

 

    def getWeighedWaterLevel(self, utcTimeStamp, lat, lon):
        m = 0
        n = 0
        try:
            for station in self.stations:
                distanceToStation = self.stations[station].getStationDistance(lat, lon)
                weighingFactor = 1 / distanceToStation
                m += self.stations[station].getStationWaterLevel(utcTimeStamp) * weighingFactor
                n += weighingFactor
                
            result = m / n
            self.corrected += 1
            
        except Exception as e:
                # print ("*** getWeighedWaterLevel:", str(e))
                self.uncorrected += 1
                result = None
                
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
    print ("Kornwerd 2022-03-01T11:20:00", tidalData.stations['Kornwerd'].getStationWaterLevel(t))
    print ("Harlingen 2022-03-01T11:20:00", tidalData.stations['Harlingen'].getStationWaterLevel(t))
    print ("Average:", tidalData.getAverageWaterLevel(t))
    print ("Weighed average (nabij Harlingen):", tidalData.getWeighedWaterLevel(t, 53.176993333, 5.40))
    print ("Weighed average (nabij Kornwerd):", tidalData.getWeighedWaterLevel(t, 53.079620000, 5.33))
    print ("Weighed average (ongeveer in het midden):", tidalData.getWeighedWaterLevel(t, 53.126993333, 5.37))

