#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from threading import Thread
import re
import time
import httplib, urllib
from cbhttp import cb_auth_header

time_host = "time.codeborne.com"
time_port = 444
select_time = None

class HoursReporter(Thread):
    def __init__(self):
        super(HoursReporter, self).__init__(name='HoursReporter')
        self.setDaemon(True)

    def report_hours_at_the_end_of_day(self):
        global select_time, selected_names
        if select_time == None: select_time = datetime.now()
        if select_time.hour > 10: select_time = select_time.replace(hour=10, minute=0, second=0, microsecond=0)
        time = (datetime.now() - select_time)
        secondsWith15MinPrecision = int(round(time.seconds / 15.0 / 60.0) * 15 * 60)
        hours = secondsWith15MinPrecision / 3600
        minutes = (secondsWith15MinPrecision - hours*3600) / 60
        data = {'date':select_time.strftime('%d.%m.%Y'), 'employees':8, 'project':53, 'story':'', 'details':'Autofilled by dev-indicator', 'hours':hours, 'minutes':minutes}
        print "Reporting %s" % data
        self.post(data)

    def post(self, data):
        conn = httplib.HTTPSConnection(time_host, time_port)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Authorization": "Basic %s" % cb_auth_header()}
        conn.request("GET", "/login", None, headers)
        response = conn.getresponse()
        headers["Cookie"] = re.sub(';Path=.*', '', response.getheader("set-cookie"))
        print headers
        params = urllib.urlencode(data)
        conn = httplib.HTTPSConnection(time_host, time_port)
        conn.request("POST", "/add", params, headers)
        response = conn.getresponse()
        print response.status, response.reason, response.getheaders(), response.read()


    def run(self):
        while True:
            hour = datetime.now().hour
            if hour == 18:
                self.report_hours_at_the_end_of_day()
            time.sleep(60*55)

if __name__ == "__main__":
    HoursReporter().report_hours_at_the_end_of_day()
