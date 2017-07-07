#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from threading import Thread
import re
import time
import json
import commands
import httplib, urllib
from subprocess import Popen, PIPE, STDOUT
from cbhttp import cb_auth_header

autofill_project_id=None
# autofill_project_id=53 # CapitalBank
autofill_repos=['../capitalbank', '../panda']

time_host = "time.codeborne.com"
time_port = 444
time_headers = {"Authorization": "Basic %s" % cb_auth_header()}

class HoursReporter(Thread):
    def __init__(self, indicator):
        super(HoursReporter, self).__init__(name='HoursReporter')
        self.setDaemon(True)
        self.indicator = indicator

    def report_hours_at_the_end_of_day(self):
        commits = self.find_commits()
        if not commits: return

        self.login()
        employees = self.employee_list()
        selected_employee_ids = self.find_employee_ids(employees)

        select_time = self.indicator.select_time
        if select_time is None: select_time = datetime.now()
        if select_time.hour > 10: select_time = select_time.replace(hour=10, minute=0, second=0, microsecond=0)

        time = datetime.now() - select_time
        secondsWith15MinPrecision = int(round(time.seconds / 15.0 / 60.0) * 15 * 60)
        hours = secondsWith15MinPrecision / 3600
        minutes = (secondsWith15MinPrecision - hours*3600) / 60
        data = [('date', select_time.strftime('%d.%m.%Y')),
                ('project', autofill_project_id),
                ('story', ''),
                ('details', commits),
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
                                 for name in self.indicator.selected_names]
        return [id for id in selected_employee_ids if id]

    def add_hours(self, data):
        time_headers["Content-type"] = "application/x-www-form-urlencoded"
        params = urllib.urlencode(data)
        conn = httplib.HTTPSConnection(time_host, time_port)
        conn.request("POST", "/add", params, time_headers)
        response = conn.getresponse()
        print response.status, response.reason, response.getheaders(), response.read()

    def find_commits(self):
        if not self.indicator.selected_names: return ''
        return ''.join([Popen(["git", "log", "--since", "yesterday", "--oneline", "--author", ', '.join(self.indicator.selected_names), "--no-merges", "--format=%s"], stdout=PIPE, cwd=repo).communicate()[0]
                 for repo in autofill_repos])[:400]

    def is_screen_locked(self):
        output = commands.getoutput('ps x')
        return 'unity-panel-service --lockscreen' in output

    def run(self):
        while True:
            hour = datetime.now().hour
            if hour >= 18 and self.indicator.selected_names:
                if self.is_screen_locked():
                    self.report_hours_at_the_end_of_day()
                    self.indicator.selected_names = []
                else:
                    print "Not reporting hours yet as screen is not locked"

            time.sleep(60*10)

    def start(self):
        if autofill_project_id:
            print "Starting hours autoreporter for project %s" % autofill_project_id
            super(HoursReporter, self).start()

if __name__ == "__main__":
    class FakeIndicator:
        def __init__(self, selected_names):
            self.selected_names = selected_names
            self.select_time = None

    reporter = HoursReporter(FakeIndicator(['Anton Keks']))
    reporter.report_hours_at_the_end_of_day()
    # print reporter.find_commits()
