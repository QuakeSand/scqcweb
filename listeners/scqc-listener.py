#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-

import glob
import sys
import traceback
import pickle
import csv
import os

from obspy import read_inventory
from seiscomp import core, client, datamodel

app_path = os.path.normpath('/opt/scqcweb')
QC_path = os.path.join(app_path,'listeners', 'QC_dictionary.pkl')
# Specify path to StationXMl files (obspy xml reader not currently working with SeisComP XMLs)
xml_path = os.path.join('/opt','seiscomp', 'StaXML')
# QC_headers is just for reference, must match values in scqcweb
QC_headers = ['Latency (s)', 'Delay (s)', 'Timing Quality', 'Gaps Count', 'Overlaps Count', 'Availability (%)']

# Create list of active stations
def stationcheck():
    sta_list = []
    glob_path = xml_path + '/*.xml'
    for xml_file in glob.iglob(glob_path, recursive=False):
        inv = read_inventory(xml_file, format="STATIONXML")
        for net in inv:
            for sta in net:
                net_sta = net.code + '.' + sta.code
                if net_sta not in sta_list:
                    if sta.end_date is None:
                        sta_list.append(net_sta)
    return sta_list

# Create QC dictionary from list of active stations
def createQCdict():
    QC_dict = {}
    ns_list = stationcheck()
    for ns in ns_list:
        val = None
        QC_dict.update({ns:[val,val,val,val,val,val]})
    with open(QC_path, 'wb') as f:
        pickle.dump(QC_dict, f)

class QCListener(client.Application):
    def __init__(self, argc, argv):
        client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(True)
        self.setMessagingUsername("qclistener")
        self.setDatabaseEnabled(False, False)
        self.setPrimaryMessagingGroup(client.Protocol.LISTENER_GROUP)
        self.addMessagingSubscription("QC")
        self.setLoggingToStdErr(False)

    def run(self):
        try:
            return client.Application.run(self)

        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: sys.stderr.write(i)
            return False

    def handleMessage(self, msg):
        try:
            dm = core.DataMessage.Cast(msg)
            if dm:
                with open(QC_path, 'rb') as file:
                    QC_dict = pickle.load(file)
                for att in dm:
                    wfq = datamodel.WaveformQuality.Cast(att)
                    if wfq.parameter() == 'latency':
                        print("%s.%s.%s.%s" % (wfq.waveformID().networkCode(), wfq.waveformID().stationCode(), wfq.waveformID().locationCode(), wfq.waveformID().channelCode()), wfq.start(), wfq.type(), wfq.parameter(), wfq.value())
                        staID = str(wfq.waveformID().networkCode()) + "." + str(wfq.waveformID().stationCode())
                        latency = round(wfq.value(),1)
                        QC_dict[staID][0] = latency
                        with open(QC_path, 'wb') as f:
                            pickle.dump(QC_dict, f)
                    if wfq.parameter() == 'delay':
                        print("%s.%s.%s.%s" % (wfq.waveformID().networkCode(), wfq.waveformID().stationCode(), wfq.waveformID().locationCode(), wfq.waveformID().channelCode()), wfq.start(), wfq.type(), wfq.parameter(), wfq.value())
                        staID = str(wfq.waveformID().networkCode()) + "." + str(wfq.waveformID().stationCode())
                        delay = round(wfq.value(),1)
                        QC_dict[staID][1] = delay
                        with open(QC_path, 'wb') as f:
                            pickle.dump(QC_dict, f)
                    if wfq.parameter() == 'timing quality':
                        print("%s.%s.%s.%s" % (wfq.waveformID().networkCode(), wfq.waveformID().stationCode(), wfq.waveformID().locationCode(), wfq.waveformID().channelCode()), wfq.start(), wfq.type(), wfq.parameter(), wfq.value())
                        staID = str(wfq.waveformID().networkCode()) + "." + str(wfq.waveformID().stationCode())
                        timing_quality = round(wfq.value(),1)
                        QC_dict[staID][2] = timing_quality
                        with open(QC_path, 'wb') as f:
                            pickle.dump(QC_dict, f)
                    if wfq.parameter() == 'gaps count':
                        print("%s.%s.%s.%s" % (wfq.waveformID().networkCode(), wfq.waveformID().stationCode(), wfq.waveformID().locationCode(), wfq.waveformID().channelCode()), wfq.start(), wfq.type(), wfq.parameter(), wfq.value())
                        staID = str(wfq.waveformID().networkCode()) + "." + str(wfq.waveformID().stationCode())
                        gaps_count = round(wfq.value(),1)
                        QC_dict[staID][3] = gaps_count
                        with open(QC_path, 'wb') as f:
                            pickle.dump(QC_dict, f)
                    if wfq.parameter() == 'overlaps count':
                        print("%s.%s.%s.%s" % (wfq.waveformID().networkCode(), wfq.waveformID().stationCode(), wfq.waveformID().locationCode(), wfq.waveformID().channelCode()), wfq.start(), wfq.type(), wfq.parameter(), wfq.value())
                        staID = str(wfq.waveformID().networkCode()) + "." + str(wfq.waveformID().stationCode())
                        overlaps_count = round(wfq.value(),1)
                        QC_dict[staID][4] = overlaps_count
                        with open(QC_path, 'wb') as f:
                            pickle.dump(QC_dict, f)
                    if wfq.parameter() == 'availability':
                        print("%s.%s.%s.%s" % (wfq.waveformID().networkCode(), wfq.waveformID().stationCode(), wfq.waveformID().locationCode(), wfq.waveformID().channelCode()), wfq.start(), wfq.type(), wfq.parameter(), wfq.value())
                        staID = str(wfq.waveformID().networkCode()) + "." + str(wfq.waveformID().stationCode())
                        availability = round(wfq.value(),1)
                        QC_dict[staID][5] = availability
                        with open(QC_path, 'wb') as f:
                            pickle.dump(QC_dict, f)
        except:
            info = traceback.format_exception(*sys.exc_info())
            for i in info: 
                sys.stderr.write(i)

def main():
    createQCdict()
    app = QCListener(len(sys.argv), sys.argv)
    return app()

if __name__ == "__main__":
    sys.exit(main())