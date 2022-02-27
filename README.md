# Depthwaypoints

Tool that converts depth soudings from NMEA0183 log files into waypoints in GPX files, with the depth encoded in the \<sym\> tags. With the right UserIcons, this shows depth soundings in plotters like OpenCPN. User Icons provided need to be copied into the UserIcons directory of OpenCPN. The waypoints are distributed over increasing scale levels, so they don't clutter at higher scales.
  
![image](https://user-images.githubusercontent.com/17980560/155900561-626678cb-8857-496f-8f5f-5710de48799d.png)

The tool requires NMEA0183 DPT and RMC messages in a log file. To record such a log file, you can use
* the OpenCPN VDR plugin (Voyage Data Recorder), or
* the [SignalK SK-NMEA0183-VDR plugin](https://github.com/marcobergman/sk-nmea0183-vdr).

The tool provides corrections for tidal water if comma-separated are provided according to the configuration file `tidalstations.conf`.
