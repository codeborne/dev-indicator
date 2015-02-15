#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from threading import Thread
import re
import time
import json
import httplib, urllib
from cbhttp import cb_auth_header

autofill_project_id=53 # CapitalBank

time_host = "time.codeborne.com"
time_port = 444
time_headers = {"Authorization": "Basic %s" % cb_auth_header()}

selected_names = ['Anton Keks', 'Kirill Klenski', 'Openway']
select_time = None

class HoursReporter(Thread):
    def __init__(self):
        super(HoursReporter, self).__init__(name='HoursReporter')
        self.setDaemon(True)

    def report_hours_at_the_end_of_day(self):
        global select_time, selected_names

        self.login()
        employees = self.employee_list()
        selected_employee_ids = self.find_employee_ids(employees)

        if select_time == None: select_time = datetime.now()
        if select_time.hour > 10: select_time = select_time.replace(hour=10, minute=0, second=0, microsecond=0)

        time = (datetime.now() - select_time)
        secondsWith15MinPrecision = int(round(time.seconds / 15.0 / 60.0) * 15 * 60)
        hours = secondsWith15MinPrecision / 3600
        minutes = (secondsWith15MinPrecision - hours*3600) / 60
        data = [('date',select_time.strftime('%d.%m.%Y')),
                ('project', autofill_project_id),
                ('story', ''),
                ('details', 'Autofilled by dev-indicator'),
                ('hours', hours), ('minutes', minutes)]
        for id in selected_employee_ids: data += [('employees', id)]
        print "Reporting %s" % data
        self.add_hours(data)

    def login(self):
        if not "Cookie" in time_headers:
            conn = httplib.HTTPSConnection(time_host, time_port)
            conn.request("GET", "/login", None, time_headers)
            response = conn.getresponse()
            time_headers["Cookie"] = re.sub(';Path=.*', '', response.getheader("set-cookie"))

    def employee_list(self):
        conn = httplib.HTTPSConnection(time_host, time_port)
        conn.request("POST", "/employee-list", None, time_headers)
        return json.loads(conn.getresponse().read())

    def find_employee_ids(self, employees):
        selected_employee_ids = [next((e['id'] for e in employees if e['name'] == name), None)
                                 for name in selected_names]
        return [id for id in selected_employee_ids if id]

    def add_hours(self, data):
        time_headers["Content-type"] = "application/x-www-form-urlencoded"
        params = urllib.urlencode(data)
        conn = httplib.HTTPSConnection(time_host, time_port)
        conn.request("POST", "/add", params, time_headers)
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
