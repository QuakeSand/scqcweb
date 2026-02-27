#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-

import sys
import traceback
import pickle
import os

from seiscomp import core, client, datamodel

app_path = os.path.dirname(__file__)
QC_path = os.path.join(app_path, 'QC_dictionary.pkl')
# List of QC parameters collected by QCListener in correct order written to QC dictionary
QC_headers = ['Latency (s)', 'Delay (s)', 'Timing Quality', 'Gaps Count', 'Overlaps Count', 'Availability (%)']

class InventoryReader(client.Application):
    def __init__(self, argc, argv):
        super().__init__(argc, argv)
        self.setDaemonEnabled(False)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, True)
        self.setLoadStationsEnabled(True)
        self.setLoggingToStdErr(True)
    
    def validateParameters(self):
        if not super().validateParameters():
            return False

        # no database is needed when inventory is provided by an SCML file
        if not self.isInventoryDatabaseEnabled():
            self.setDatabaseEnabled(False, False)

        return True
    
    def run(self):
        now = core.Time.UTC()
        inv = client.Inventory.Instance().inventory()

        sta_list = []
        
        nnet = inv.networkCount()
        for inet in range(nnet):
            network = inv.network(inet)
            for ista in range(network.stationCount()):
                station = network.station(ista)
                try:
                    start = station.start()
                except Exception:
                    continue

                try:
                    end = station.end()
                    if not start <= now <= end:
                        continue
                except Exception:
                    pass
                
                net_sta = network.code() + '.' + station.code()
                if net_sta not in sta_list:
                    sta_list.append(net_sta)
        QC_dict = {}
        for ns in sta_list:
            val = None
            QC_dict.update({ns:[val,val,val,val,val,val]})
        with open(QC_path, 'wb') as f:
            pickle.dump(QC_dict, f)
            
        return True
    
    def done(self):
        client.Application.done(self)

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
    qc_dict = InventoryReader(len(sys.argv), sys.argv)
    qc_dict()
    del qc_dict
    app = QCListener(len(sys.argv), sys.argv)
    return app()

if __name__ == "__main__":
    sys.exit(main())