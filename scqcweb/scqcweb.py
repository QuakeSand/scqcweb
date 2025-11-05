# -*- coding: utf-8 -*-
"""
Created in Feb 2024
Monitors Seismic Network SOH Data
Need to use with a listener(s)

@author: nnovoa
"""

import glob
import io
import matplotlib.pyplot as plt
import os
import pandas as pd
import pickle
import sqlite3
import subprocess
import time

from datetime import datetime, timedelta
from flask import Flask, jsonify, make_response, render_template, request, session, url_for
from flask_session import Session
from flask_wtf import FlaskForm
#from logging.config import dictConfig
from obspy.clients.filesystem.sds import Client
from obspy import read_inventory, UTCDateTime
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
from wtforms import DateField, StringField, SelectField, SubmitField, TimeField
from wtforms.validators import DataRequired, InputRequired, ValidationError

#Create the Flask App
app = Flask(__name__)

#Set up Secret Key for Session Management
app.secret_key = "water"

#Initialize Flask-Session
app.config['SESSION_COOKIE_SECURE'] = False # uses https or not
app.config['SESSION_PERMANENT'] = False     # Sessions expire when browser closes
app.config['SESSION_TYPE'] = "filesystem"     # Store session data on the filesystem
app.config['SESSION_FILE_DIR'] = "flask_session"
Session(app)

# Define global variables
app_path = os.path.normpath('/opt/scqcweb')
SDS_path = os.path.normpath('/data/seiscomp/archive')
# Specify path to StationXMl files (obspy xml reader not currently working with SeisComP XMLs)
xml_path = os.path.normpath('/opt/seiscomp/StaXML')
QC_path = os.path.join(app_path,'listeners', 'QC_dictionary.pkl')
systemdb_path = os.path.join(app_path, 'listeners', 'system_monitor.db')
# Use SDS instead of FDSN becuase it is much faster
client = Client(SDS_path)
# List of Quality Control headers (needs to match scqc-listener handleMessage)
QC_headers = ['Latency (s)', 'Delay (s)', 'Timing Quality', 'Gaps Count', 'Overlaps Count', 'Availability (%)']

# Dictionary(Lookup table) for SOH abbreviations
SOH_desc = {'dcz': 'HNZ DC Offset',
            'dcn': 'HNN DC Offset',
            'dc2': 'HN2 DC Offset',
            'dce': 'HNE DC Offset',
            'dc1': 'HN1 DC Offset',
            'rmz': 'HNZ 60-s RMS',
            'rmn': 'HNN 60-s RMS',
            'rm2': 'HN2 60-s RMS',
            'rme': 'HNE 60-s RMS',
            'rm1': 'HN1 60-s RMS',
            'mxz': 'HNZ 60-s Max Amplitude',
            'mxn': 'HNN 60-s Max Amplitude',
            'mx2': 'HN2 60-s Max Amplitude',
            'mxe': 'HNE 60-s Max Amplitude',
            'mx1': 'HN1 60-s Max Amplitude',
            'cpu': 'CPU Load Average (x 100)',
            'deg': 'Temperature (°C x 10)',
            'dsk': 'Disk Usage (%)',
            'lcq': 'Timing Quality (%)',
            'vep': 'System Voltage (mV)',
            'vec': 'System Current',
            'vvx': 'External DC Voltage (mV)',
            'vvb': 'Battery Input',
            'vsp': 'Sensor Power',
            'vbb': 'Sensor/comms Current'
            }

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

# Get sysmtem monitoring stats from sqlite database
def read_stats(sdate2, edate2):
    conn = sqlite3.connect(systemdb_path)
    cursor = conn.cursor()
    # Select data from the database
    select_str = "SELECT * FROM system_stats WHERE timestamp BETWEEN '" + sdate2 + "' AND '" + edate2 +"'"
    cursor.execute(select_str)
    rows = cursor.fetchall()  # Fetch all rows from the query
    # Close the connection
    conn.close()
    return rows

#Collect SOH data and create matplotlib figure
def soh_plot(sta_id, soh_id, sta_time):
    ns_id = sta_id.split(".")
    end_time = UTCDateTime.now().date
    soh_time = end_time - timedelta(days=sta_time)
    st = client.get_waveforms(ns_id[0], ns_id[1], "*", soh_id, UTCDateTime(soh_time), UTCDateTime(end_time))
    if len(st) > 0:
        fig, ax = plt.subplots(1, 1, figsize=(5, 1.5), layout="constrained", dpi=200)
        for tr in st:
            if soh_id in ['rmz', 'rmn', 'rm2', 'rme', 'rm1', 'mxz', 'mxn', 'mx2', 'mxe', 'mx1']:
                ax.scatter(tr.times("matplotlib"), tr.data, s=2, color='g', label=ns_id)
            else:
                ax.plot(tr.times("matplotlib"), tr.data, linestyle='-', color='g', label=ns_id)
        if soh_id in ['dsk', 'lcq']:
            ax.set_ylim(0, 105)
        ax.xaxis.set_major_formatter(DateFormatter('%b %d %Y'))
        ax.xaxis.set_major_locator(DayLocator(interval=2))
        if soh_id in SOH_desc.keys():
            description = SOH_desc.get(soh_id)
            title = description + ' - ' + ns_id[0] + '.' + ns_id[1]
            ax.set_title(title)
        ax.grid(True, which='major', axis='both')
        #ax.tick_params(axis='x', labelrotation=45)
        ax.tick_params(axis='both', labelsize=6)
        ax.set_xlim(soh_time, end_time)
        return fig, ax
    else:
        return None, None

# Create image from matplotlib figure and return it as a response
def fig2resp(fig):
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    plt.close(fig)  # Close the figure to free memory
    return response

# For truncating latencies
def truncate(n, decimals=0):
	multiplier = 10**decimals
	return int(n * multiplier) / multiplier

# Color the QC Table Cells
def cell_color(val):
	if val is None:
		cell_color = 'white'
	elif val < 0:
		cell_color = '#F97979'
	elif val < 5:
		cell_color = 'lightgreen'
	elif val < 10:
		cell_color = '#F9DA79'
	else:
		cell_color = '#F97979'
	return 'background-color: %s' % cell_color

def timing_color(val):
	if val is None:
		timing_color = 'white'
	elif val < 80:
		timing_color = '#F97979'
	elif val < 101:
		timing_color = 'lightgreen'
	else:
		timing_color = ''
	return 'background-color: %s' % timing_color

def availability_color(val):
	if val is None:
		availability_color = '#F97979'
	elif val < 90:
		availability_color = '#F97979'
	elif val < 95:
		availability_color = '#F9DA79'
	elif val < 101:
		availability_color = 'lightgreen'
	else:
		availability_color = ''
	return 'background-color: %s' % availability_color

def count_color(val):
	if val is None:
		count_color = '#F97979'
	elif val < 5:
		count_color = 'lightgreen'
	elif val < 10:
		count_color = '#F9DA79'
	else:
		count_color = '#F97979'
	return 'background-color: %s' % count_color

# Create forms to use for various web pages
class StationForm(FlaskForm):
    station = SelectField('Station', validators=[InputRequired()])
    sta_days = StringField('Days', validators=[InputRequired()])
    submit = SubmitField('Submit')

class PPSDForm(FlaskForm):
    PPSDstation = SelectField('Station', validators=[InputRequired()])
    submit = SubmitField('Submit')

class HeliForm(FlaskForm):
    heli_channel = SelectField('Specify Channel', validators=[DataRequired()])
    sdate = DateField('Specify Start Date/Time (UTC):', format='%Y-%m-%d', validators=[DataRequired()])
    stime = TimeField('Specify Start Time:', format='%H:%M', validators=[DataRequired()])
    edate = DateField('Specify End Date/Time (UTC):', format='%Y-%m-%d', validators=[DataRequired()])
    etime = TimeField('Specify End Time:', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class RTForm(FlaskForm):
    rt_channel = SelectField('Specify Channel:', validators=[DataRequired()])

class ServerForm(FlaskForm):
    sdate2 = DateField('Specify Start Date (UTC):', default=(UTCDateTime.now().date-timedelta(days=30)), format='%Y-%m-%d', validators=[DataRequired()])
    edate2 = DateField('Specify End Date (UTC):', default=UTCDateTime.now().date, format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Create necessary pickle files
with app.app_context():
    createQCdict()

# Home page (Network page)
@app.route('/')
def index():
    with open(QC_path, 'rb') as f:
        QC_dict = pickle.load(f)
    umtime = os.path.getmtime(QC_path)
    ultime = datetime.fromtimestamp(umtime).strftime('%Y-%m-%d %H:%M:%S')
    #app.logger.info(SOH_dict)
    style_td = dict(selector="td", props=[('font-size', '10pt'),('border-style', 'solid')])
    style_th = dict(selector="th", props=[('font-size', '12pt'),('border-style', 'solid')])
    df = pd.DataFrame.from_dict(QC_dict, orient='index', columns=QC_headers)
    df = df.sort_index(axis = 0)
    df = df.style.map(cell_color, subset=pd.IndexSlice[:, ['Latency (s)', 'Delay (s)']])\
		.map(timing_color, subset=pd.IndexSlice[:, ['Timing Quality']])\
		.map(count_color, subset=pd.IndexSlice[:, ['Gaps Count', 'Overlaps Count']])\
		.map(availability_color, subset=pd.IndexSlice[:, ['Availability (%)']])\
		.set_properties(**{'text-align': 'center','border-collapse' : 'collapse'})\
		.set_table_styles([style_td, style_th])\
		.format(precision=1)
    return render_template('network.html', tables=[df.to_html(classes='data', header="true")], updated=ultime)

# Station page and associated plots
@app.route('/station', methods=['GET', 'POST'])
def soh_post():
    stations = client.get_all_stations()
    sta_tuplelist = []
    for key, value in stations:
        net_sta = key + '.' + value
        sta_tuplelist.append((net_sta, net_sta))
    form = StationForm()
    form.station.choices = sta_tuplelist
    global sta_id
    global sta_time
    if form.validate_on_submit:
        sta_id = form.station.data
        if form.sta_days.data is not None:
            sta_time = int(form.sta_days.data)
        else:
            sta_time = 0
    return render_template('station.html', form=form)

@app.route('/plot/soh/<sohid>')
def plot_soh(sohid):
    if sta_time != 0:
        soh_id = sohid
        fig, ax = soh_plot(sta_id, soh_id, sta_time)
        if fig is None:
            return ('', 204)
        else:
            response = fig2resp(fig)
            return response
    else:
        return ('', 204)

# PPSD page
@app.route('/ppsd', methods=['GET', 'POST'])
def ppsd_post():
    stations = client.get_all_stations()
    sta_tuplelist = []
    for key, value in stations:
        net_sta = key + '.' + value
        sta_tuplelist.append((net_sta, net_sta))
    form = PPSDForm()
    form.PPSDstation.choices = sta_tuplelist
    global staPPSD
    imagelist = []
    if form.validate_on_submit():
        staPPSD = form.PPSDstation.data
        if staPPSD is not None:
            imageList = []
            PPSD_path = os.path.join(app_path,'static', 'ppsd')
            for image in os.listdir(PPSD_path):
                if image.startswith(staPPSD):
                    imageList.append(image)
            imageList.sort(key=lambda x: x[-12:-5])
            imagelist = ['ppsd/' + image for image in imageList]
    return render_template('ppsd.html', form=form, imagelist=imagelist)

# Helicorder page
@app.route('/heli', methods=['GET', 'POST'])
def heli_post():
    nslc_all = client.get_all_nslc(datetime=UTCDateTime.now())
    nslc_tuplelist = []
    for nslc_code in nslc_all:
        net, sta, loc, chan = nslc_code
        if chan.startswith('HN'):
            nslc = net + '.' + sta + '.' + loc + '.' + chan
            nslc_tuplelist.append((nslc, nslc))
    form = HeliForm()
    form.heli_channel.choices = nslc_tuplelist
    if request.method == 'POST':
        if form.validate_on_submit():
            session['heli_channel'] = form.heli_channel.data
            session['sdate'] = form.sdate.data
            session['stime'] = form.stime.data
            session['edate'] = form.edate.data
            session['etime'] = form.etime.data
    return render_template('heli.html', form=form)

@app.route('/plot/heli')
def plot_heli():
    heli_channel = session.get('heli_channel')
    if heli_channel is not None:
        sdate = session.get('sdate')
        stime = session.get('stime')
        edate = session.get('edate')
        etime = session.get('etime')
        sdt_str = str(sdate) + "T" + str(stime)
        edt_str = str(edate) + "T" + str(etime)
        sdt = UTCDateTime(sdt_str)
        edt = UTCDateTime(edt_str)
        nslc_id = heli_channel.split(".")
        st = client.get_waveforms(nslc_id[0], nslc_id[1], nslc_id[2], nslc_id[3], sdt, edt)
        if len(st) > 0:
            fig = st.plot(type="dayplot", interval=60, right_vertical_labels=False, vertical_scaling_range=5e3, one_tick_per_line=True, show_y_UTC_label=False)
            response = fig2resp(fig)
            return response
        else:
            return ('No data found', 204)
    else:
        return ('', 204)

# Real-time page
@app.route('/rt', methods=['GET', 'POST'])
def rt_post():
    nslc_all = client.get_all_nslc(datetime=UTCDateTime.now())
    nslc_tuplelist = []
    for nslc_code in nslc_all:
        net, sta, loc, chan = nslc_code
        if chan.startswith('HN'):
            nslc = net + '.' + sta + '.' + loc + '.' + chan
            nslc_tuplelist.append((nslc, nslc))
    form = RTForm()
    form.rt_channel.choices = nslc_tuplelist
    return render_template('rt.html', form=form)

@app.route('/plot/rt', methods=['POST'])
def plot_rt():
    rt_channel = request.get_json()
    if rt_channel is not None:
        now_str = UTCDateTime.now().strftime('%Y-%m-%d %H:%M:%S')
        subprocess.run(['/opt/seiscomp/seiscomp_6.4.3/bin/scheli', 'capture', '--stream', rt_channel, '-o', '/opt/scqcweb/static/images/rt_temp.png', '--end-time', now_str])
        #Line below should work, but doesn't
        #image_path = url_for('static', filename='/images/rt_temp.png')
        image_path = "static/images/rt_temp.png"
        return jsonify({'image_url': f'/{image_path}?t={int(time.time())}'})
    else:
        return ('', 204)

# Server page
@app.route('/server', methods=['GET', 'POST'])
def server_post():
    form = ServerForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            session['sdate2'] = form.sdate2.data
            session['edate2'] = form.edate2.data
    return render_template('server.html', form=form)

@app.route('/plot/server')
def plot_server():
    sdate2 = session.get('sdate2')
    edate2 = session.get('edate2')
    edate2 = edate2.strftime("%Y-%m-%d %H:%M:%S")
    sdate2 = sdate2.strftime("%Y-%m-%d %H:%M:%S")
    stats = read_stats(sdate2, edate2)
    # Process data for plotting
    if len(stats) > 0:
        time_data = [stat[1] for stat in stats]
        datetime_objects = [datetime.strptime(time, "%Y-%m-%d %H:%M:%S") for time in time_data]
        cpu_usage = [stat[2] for stat in stats]
        mem_usage = [stat[3] for stat in stats]
        root_usage = [stat[4] for stat in stats]
        var_usage = [stat[5] for stat in stats]
        data_usage = [stat[6] for stat in stats]
        opt_usage = [stat[7] for stat in stats]
        home_usage = [stat[8] for stat in stats]
        min1_usage = [stat[9] for stat in stats]
        min5_usage = [stat[10] for stat in stats]
        min15_usage = [stat[11] for stat in stats]
        min_date = min(datetime_objects)
        max_date = max(datetime_objects)
        # Create a Matplotlib figure
        fig, ax = plt.subplots(3, 1, figsize=(6, 10), layout="constrained", dpi=200)
        ax[0].plot(datetime_objects, root_usage, linestyle='-', color='r', label='/ (Root)')
        ax[0].plot(datetime_objects, var_usage, linestyle='-', color='g', label='/Var')
        ax[0].plot(datetime_objects, data_usage, linestyle='-', color='b', label='/Data')
        ax[0].plot(datetime_objects, opt_usage, linestyle='-', color='m', label='/Opt')
        ax[0].plot(datetime_objects, home_usage, linestyle='-', color='c', label='/Home')
        ax[0].set_title('Disk Usage')
        ax[0].set_ylabel('Percent (%)', fontsize=10)
        ax[0].legend(loc='upper center', bbox_to_anchor=(0.5, -0.35), ncol=3)
        ax[0].grid(True, which='major', axis='y')
        ax[0].set_ylim(0, 100)
        ax[0].set_xlim(min_date, max_date)
        ax[0].tick_params(axis='x', labelrotation=45)
        ax[0].tick_params(axis='both', labelsize=8)
        ax[0].xaxis.set_major_formatter(DateFormatter('%b %d %H:%M'))
        ax[1].plot(datetime_objects, cpu_usage, linestyle='-', color='b', label='CPU')
        ax[1].plot(datetime_objects, mem_usage, linestyle='-', color='r', label='Memory')
        ax[1].set_title('CPU and Memory Usage')
        ax[1].set_ylabel('Percent (%)', fontsize=10)
        ax[1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.35), ncol=3)
        ax[1].grid(True, which='major', axis='y')
        ax[1].set_ylim(0, 100)
        ax[1].set_xlim(min_date, max_date)
        ax[1].tick_params(axis='x', labelrotation=45)
        ax[1].tick_params(axis='both', labelsize=8)
        ax[1].xaxis.set_major_formatter(DateFormatter('%b %d %H:%M'))
        ax[2].plot(datetime_objects, min1_usage, linestyle='-', color='r', label='1-min')
        ax[2].plot(datetime_objects, min5_usage, linestyle='-', color='g', label='5-min')
        ax[2].plot(datetime_objects, min15_usage, linestyle='-', color='b', label='15-min')
        ax[2].set_title('CPU Load')
        ax[2].set_ylabel('Load', fontsize=10)
        ax[2].legend(loc='upper center', bbox_to_anchor=(0.5, -0.35), ncol=3)
        ax[2].grid(True, which='major', axis='y')
        ax[2].set_ylim(bottom=0)
        ax[2].set_xlim(min_date, max_date)
        ax[2].tick_params(axis='x', labelrotation=45)
        ax[2].tick_params(axis='both', labelsize=8)
        ax[2].xaxis.set_major_formatter(DateFormatter('%b %d %H:%M'))
        if len(datetime_objects) < 7200:
            ax[0].xaxis.set_major_locator(HourLocator(interval=4))
            ax[1].xaxis.set_major_locator(HourLocator(interval=4))
            ax[2].xaxis.set_major_locator(HourLocator(interval=4))
        else:
            ax[0].xaxis.set_major_locator(DayLocator(interval=5))
            ax[1].xaxis.set_major_locator(DayLocator(interval=5))
            ax[2].xaxis.set_major_locator(DayLocator(interval=5))
        fig.get_layout_engine().set(hspace=0.1)
        
        # Return the figure as a response
        response = fig2resp(fig)
        return response
    else:
        return ('No data found', 204)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=False)