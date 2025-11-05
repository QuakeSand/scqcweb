#!/usr/bin/env seiscomp-python
# -*- coding: utf-8 -*-

import sys
import traceback
import csv
from seiscomp import client, datamodel

class ListStreamsApp(client.Application):

    def __init__(self, argc, argv):
        client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(True, False)
        self.setLoggingToStdErr(True)
        self.setDaemonEnabled(False)
#       self.setLoadInventoryEnabled(True)

    def validateParameters(self):
        try:
            if not client.Application.validateParameters(self):
                return False
            return True
        except Exception:
            traceback.print_exc()
            sys.exit(-1)

    def run(self):
        try:
            dbr = datamodel.DatabaseReader(self.database())
            inv = datamodel.Inventory()
            dbr.loadNetworks(inv)

            sta_list = []
            result = []
            act_list = []
            nc_list = []

            for inet in range(inv.networkCount()):
                network = inv.network(inet)
                dbr.load(network)
                for ista in range(network.stationCount()):
                    station = network.station(ista)
                    for iloc in range(station.sensorLocationCount()):
                        location = station.sensorLocation(iloc)
                        for istr in range(location.streamCount()):
                            stream = location.stream(istr)
                            try:
                                start = stream.start()
                            except Exception:
                                continue
                            try:
                                end = stream.end()
                            except Exception:
                                end = None
                                pass
                            if end is None:
                                if station.code() not in sta_list:
                                    mystream = stream.code()
                                    if mystream.startswith('HN'):
                                        result.append((network.code(), station.code(), location.code(), stream.code()))
                                        sta_list.append(station.code())
            for net, sta, loc, cha in result:
                nslc = str(net) + "." + str(sta) + "." + str(loc) + "." + str(cha)
                print(nslc)
                act_list.append(nslc)
                with open('actlist.csv', 'w', newline='') as csvfile:
                    wr = csv.writer(csvfile)
                    wr.writerow(act_list)
                ns = str(net) + "." + str(sta)
                nc_list.append(ns)
                with open('nclist.csv', 'w', newline='') as csvfile2:
                    wr = csv.writer(csvfile2)
                    wr.writerow(nc_list)

            return True
        except Exception:
            traceback.print_exc()
            sys.exit(-1)

def main():
    app = ListStreamsApp(len(sys.argv), sys.argv)
    return app()

if __name__ == "__main__":
    sys.exit(main())
