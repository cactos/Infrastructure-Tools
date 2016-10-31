Cactos Monitoring Dashboard
=================
Dashboard for visualization of the monitoring data from the Cactos cluster

Installation
----------------
- This Project in implemented for Python 2.7
- required packages
    - python 
    - python-pip 
    - python-virtualenv
- clone the repo
- if you want to run the Dashboard in python's virtualenv
    - create and start virtualenv in the project's folder with
        ```
        virtualenv .virtualenv
        source .virtualenv/bin/activate
        ```
- install dependencies (eventually you need root privileges)
    ```
    pip install -r requirements.txt
    ```
- register the Dashboard as a service
    - create a script in /etc/init.d/ with following content
        ```
        #!bin/bash

        # if dashboard runs in virtualenv
        source /path/to/dashboard/.virtualenv/bin/activate

        cd /path/to/dashboard/
        
        # pipe output to nohup or dev null
        # start the app
        nohup python main.py &
        ```
    - make sure it's executable
        ```
        chmod 755 <script>
        ```
    - add symbolic links
        ```
        update-rc.d <script> defaults
        ```
    - if you wish to remove the script from startup
        ```
        update-rc.d <script> remove
        ```

Settings
----------------
Adjust the **config.yml** entries:

```
servers:
    thrift: <ip-thrift-server>
    port: <port-thrift-server>

worker:
    # interval for polling from thrift server
    # this value shouldn't be changed
    sleeper: 10 

paths:
    # change if you want to save data in other location
    storagePath: data/storage

app:
    host: 0.0.0.0
    # set the port
    port: XXXX
```

REST-API
----------------
tba
