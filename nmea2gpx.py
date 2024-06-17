import math
import re    ## regular expressions
import glob
import shutil
import os

GPX_HEADER='<?xml version="1.0" encoding="UTF-8" ?>\n<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">\n'
TRACK_INTERVAL = 30 # meters
SOURCE_DIR = "nmea/";
TARGET_DIR = "gpx/";
TRASH_DIR = "nmea/old/";

def checkDir(directory):
    if not (os.path.isdir(directory)):
        print (directory, "is not a directory");
        exit(1);
        
checkDir(SOURCE_DIR);
checkDir(TARGET_DIR);
checkDir(TRASH_DIR);


def convertLatLon (latLon):
    if (latLon[4] == "."):
        latLon = "" + "0" + latLon
    val = float(latLon[0:3]) + float(latLon[3:])/60
    return val
        

def formatTimestamp(timeStamp):
    # format 130223060009 into 2023-02-13T06:00:09Z
    return "20{}-{}-{}T{}:{}:{}Z".format(timeStamp[4:6], timeStamp[2:4], timeStamp[0:2], timeStamp[6:8], timeStamp[8:10], timeStamp[10:12])
            
            
def generateTrackFile (filename, fromTimeStamp, toTimeStamp):
    rmc = 0
    trackpoints = 0
    lastlat = 0
    lastlon = 0
    n = 0  # line counter for verbose exception handling 
    print ("Processing NMEA file", filename);
    
    f = open("x", "w");
    f.close();
    
    timeStamp = "";
    lastDate = "";
    
    for lines in open(filename, 'r'):
        n += 1;
        line = lines.strip().split(',');
        
        try:
            if (re.match(r"\$[A-Z]{2}RMC", line[0])):
                curdate = line[9];
                curtime = line[1][:6];
                timeStamp = "" + curdate + curtime;
                formattedTimeStamp = formatTimestamp(timeStamp);
                
                if (timeStamp >= fromTimeStamp and timeStamp <= toTimeStamp):
                    rmc += 1;
                    curlat = convertLatLon(line[3]);
                    curlon = convertLatLon(line[5]);

                    # Calculate distance in meters to previously generated waypoint
                    distance = math.sqrt(((curlon - lastlon) * math.cos(curlat/180*math.pi)) ** 2 + (curlat - lastlat) ** 2) * 60 * 1852;
                    
                    if (distance > 10000):
                        lastlat = curlat; lastlon = curlon;   #distance = 0; to deal with initial measurement
                        
                    if (distance > float (TRACK_INTERVAL)):
                        if (curdate != lastDate and not f.closed):
                            f.close();
                            print ("File created with {} trackpoints out of {} RMC sentences".format(trackpoints, rmc))
                            rmc = 0;
                            trackpoints = 0;
                        if (f.closed):
                            trackName = formattedTimeStamp[0:10];
                            trackfilename = TARGET_DIR + os.sep + trackName + ".gpx";
                            f = open(trackfilename, "w");
                            f.write(GPX_HEADER);
                            f.write("<trk><name>" + trackName + "</name><trkseg>");
                            print ("Generating track file", trackfilename);
                        
                        gpx = '  <trkpt lat="{:.6f}" lon="{:.6f}"><time>{}</time></trkpt>' \
                            .format(curlat, curlon, formattedTimeStamp);
                        ### print (gpx)
                        f.write(gpx + "\n");
                        trackpoints += 1;
                        
                        lastlat = curlat;
                        lastlon = curlon;
                lastDate = curdate;
        except Exception as e:
            print ("exception processing line {} of {}: ".format(n, filename) + lines  + str(e));
        if (f.closed):
            exit(1);

    f.write ('</trkseg></trk></gpx>')
    f.close(); 
    print ("File created with {} trackpoints out of {} RMC sentences".format(trackpoints, rmc))
    shutil.move(filename, TRASH_DIR + os.sep + os.path.basename(filename));

if __name__ == '__main__':
    for fname in glob.glob(SOURCE_DIR + os.sep + "*.*"):
        generateTrackFile (fname, "000000", "999999")
    files = glob.glob(TARGET_DIR + os.sep + "*.gpx");
    print ('{ "files": ' + str(files).replace("'", '"') + '}');
    