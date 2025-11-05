# -*- coding: utf-8 -*-
"""
Created on Fri April 19 2024

@author: nnovoa
"""

import os

from obspy import read_inventory, UTCDateTime
from obspy.clients.filesystem.sds import Client
from obspy.signal import PPSD

PPSD_path = os.path.join('/data', 'ppsd')
SDS_path = os.path.join('/data', 'seiscomp', 'archive')
client = Client(SDS_path)

def main():
    logf = open("SDS_ppsd.log", "w")
    os.chdir(PPSD_path)
    stations = client.get_all_stations()
    etime = UTCDateTime.now()
    # Calculate starttime one day before end time
    stime = etime - 86400
    #stime = etime - 604800
    for station in stations:
        station_dir = station[0] + '.' + station[1]
        if not os.path.exists(station_dir):
            os.makedirs(station_dir)
            print("Directory created successfully!")
        os.chdir(station_dir)
        xml_name = station[0] + '_' + station[1] + '.xml'
        inv_path = os.path.join('/opt', 'seiscomp', 'StaXML', xml_name)
        print("Inventory path is %s!" % inv_path)
        try:
            inv = read_inventory(inv_path)
            st = client.get_waveforms(station[0], station[1], "*", "HN?", stime, etime)
            print("Succefsully read inventory and waveforms for %s!" % xml_name)
        except Exception as error:
            logf.write("Failed to read inventory or collect waveforms for {0}: {1}\n".format(str(xml_name),str(error)))
        finally:
            pass
        for tr in st:
            span = tr.stats.endtime - tr.stats.starttime
            if span >= 3600:
                try:
                    nslc = tr.stats.network + '.' + tr.stats.station + '.' + tr.stats.location + '.' + tr.stats.channel
                    ppsd = PPSD(tr.stats, metadata=inv)
                    ppsd.add(tr)
                    plot_name = nslc + '_' + etime.strftime("%Y%m%d") + '.png'
                    #npz_name = nslc + '_' + etime.strftime("%Y%m%d") + '.npz'
                    ppsd.plot(filename=plot_name, cumulative=True, xaxis_frequency=True)
                    #ppsd.save_npz(npz_name)
                    plot_target = os.path.join(PPSD_path, station_dir, plot_name)
                    SCQCW_link = os.path.join('/opt', 'scqcweb', 'static', 'ppsd', plot_name)
                    os.symlink(plot_target, SCQCW_link)
                except Exception as error:
                    logf.write("Failed to calculate ppsd for {0}: {1}\n".format(str(nslc),str(error)))
                finally:
                    pass   
        os.chdir(PPSD_path)               

if __name__=="__main__":
    main()