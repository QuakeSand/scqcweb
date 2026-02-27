# scqcweb
Web-based flask application to monitor seismic network station and server health

This application was originally written on Red Hat 7, but is currently being
developed on a Red Hat 9 system.

Be sure to edit the config.ini file with appropriate information for your system.

I recommend creating a python virtual environment and running scqcweb as a 
service using systemctl. 

To create the python virtual environment using conda, use the following commands:

conda create -n scqcweb python=3.12
conda activate scqcweb
conda install obspy cartopy pytest pytest-json pandas flask flask-session 
    flask-sqlalchemy flask-script flask-wtf gunicorn mysqlclient twisted 
    matplotlib psutil

To run scqcweb as a service using systemd, create a service file in the 
appropriate system directory, such as /etc/systemd/system/. Below are some
example commands to create the service. Make sure the paths are correct 
for your system, indlugin the paths in the env_vars.systemd file in the listener
folder.

sudo nano /etc/systemd/system/scqcweb.service
[Unit]
Description=SCQC Web App
After=multi-user.target

[Service]
Type=simple
User=your_username
Group=your_group
PIDFile=/opt/scqcweb/scqcweb.pid
WorkingDirectory=/opt/scqcweb
Environment=FLASK_CONFIG=production
Environment=”TEMPLATES_AUTO_RELOAD=1”
ExecStart=/opt/conda/envs/scqcweb/bin/gunicorn –config /opt/scqcweb/gunicorn_config.py scqcweb:app
Restart=always

[Install]
WantedBy=multi-user.target
Ctrl-x
Save modified buffer? Y
File name to write … Enter
sudo systemctl daemon-reload
sudo systemctl start scqcweb.service
sudo systemctl enable scqcweb.service

In order for the network home page to work, you must run an appropiate listener
to pull messages from central acquisiton system, such as SeisComP or Earthworm.
A listener for SeisComP has been developed and include in the listener folder
(scqc_listener.py). I recommend running scqc_listener as a service using the 
same python executable you use for your SeisComP system. Below are some
example commands to create the service. Make sure the paths are correct 
for your system.

sudo nano /etc/systemd/system/scqc-listener.service
[Unit]
Description=SeisComP QC Listener
After=multi-user.target

[Service]
Type=simple
User=scp_super
Group=seiscomp
PIDFile=/opt/scqcweb/listeners/scqclistener.pid
EnvironmentFile=/opt/scqcweb/listeners/env_vars.systemd
WorkingDirectory=/opt/scqcweb
ExecStart=/opt/conda/envs/scqcweb/bin/python /opt/scqcweb/listeners/scqc-listener.py
Restart=always

[Install]
WantedBy=multi-user.target
Ctrl-x
Save modified buffer? Y
File name to write … Enter
sudo systemctl daemon-reload
sudo systemctl start scqc-listener.service
sudo systemctl enable scqc-listener.service
