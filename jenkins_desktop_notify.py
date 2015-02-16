#!/usr/bin/env python
# coding=utf-8
import base64
from datetime import datetime
from json import loads
from threading import Thread
import os
os.environ['http_proxy'] = ''
import urllib2
from urlparse import urljoin
from itertools import imap
from subprocess import Popen
import string
from time import sleep
import os.path
from os.path import expanduser
from cbhttp import cb_auth_header

jenkins_url = 'https://jenkins.codeborne.com:444/view/Wall/'
pause = 60

jobs_file = expanduser("~") + '/.devindicator.jobs'
if os.path.isfile(jobs_file):
    with open(jobs_file) as f:
        includes = [line.strip() for line in f]
else:
    includes = []

def get_jobs(jenkins_url):
    def make_job(job):
        return {
            'url': job.get('url'),
            'name': job.get('name')
        }

    jobs = ask(urljoin(jenkins_url, 'api/json?pretty=true'))
    return imap(make_job, jobs.get('jobs')) if 'jobs' in jobs else []


def jobs_running_info(jobs):
    def make_job(job):
        return job.get('name'), get_job_status(job)
    return dict(make_job(job) for job in jobs)


def get_scm_changes(job_status):
    if 'changeSet' not in job_status:
        return ''
    elif 'items' not in job_status['changeSet']:
        return ''

    return string.join(['  %s - %s' % (change['author']['fullName'], change['msg']) for change in job_status['changeSet']['items']], "<br>")


def get_scm_authors(job_status):
    if 'changeSet' not in job_status:
        return ''
    elif 'items' not in job_status['changeSet']:
        return ''

    authors = [change['author']['fullName'] for change in job_status['changeSet']['items']]
    return u'[%s]' % string.join(set(authors), ", ") if authors else ''


def get_job_status(job):
    url = urljoin(job.get('url'), 'lastBuild/api/json?pretty=true')
    try:
        json = ask(url)
        if 'building' not in json:
            return {'status': 'Failed to get status', 'name': job}
        elif json['building']:
            return {'status': 'RUNNING',
                    'name': json['fullDisplayName'],
                    'duration': '%d%%' % (json['duration']/json['estimatedDuration']*100) if json['duration'] else '',
                    # 'cause': json['actions'][0]['causes'][0]['shortDescription'] + get_scm_changes(json)
                    'cause': get_scm_authors(json)
            }
        else:
            return {'status': json['result'],
                    'name': json['fullDisplayName']}
    except KeyError or ValueError as e:
        return {'status': 'FAILURE',
                'name': '%s: %s' % (job, e)}


def ask(url):
    request = urllib2.Request(url)
    request.add_header("Authorization", u"Basic %s" % cb_auth_header())

    try:
        json_response = urllib2.urlopen(request).read()
    except Exception as e:
        print "Invalid response from url %s, caused by: %s" % (url, e)
        #notify('Jenkins is unavailable', '%s' % e)
        return {}

    try:
        return loads(json_response)
    except ValueError as e:
        print u"Invalid response from url %s, caused by: %s, json: %s" % (url, e, json_response)
        notify('Jenkins is inadequate', '%s' % e)
        return {}


def notify(subject, message, icon='jenkins-alarm.png'):
    icon = os.path.join(os.path.dirname(os.path.realpath(__file__)), icon)
    Popen(['notify-send', subject, message, '-i', icon])


class JenkinsChecker:
    current_status = ''
    old_status_info = {}

    def run(self):
        while True:
            self.check_jobs()
            self.sleep()

    def status_changed(self, old_job_status, new_job_status):
        return 'status' in self.old_status_info and old_job_status['status'] != new_job_status['status']

    def sleep(self):
        sleep(pause)

    def check_jobs(self):
        print
        print "%s Check jenkins status" % datetime.now()

        jobs = get_jobs(jenkins_url)
        if not jobs:
            return

        new_status_info = jobs_running_info(jobs)

        error_message = ''
        working_message = ''
        info_message = ''
        for name, new_job_status in new_status_info.iteritems():
            old_job_status = self.old_status_info.get(name)
            if includes and name not in includes:
                pass
            elif new_job_status['status'] == 'RUNNING':
                working_message = '%s<br>%s %s %s  %s<br>' % (working_message,
                                                              new_job_status['name'],
                                                              new_job_status['status'],
                                                              new_job_status['duration'],
                                                              new_job_status['cause'])
            elif new_job_status['status'] != 'SUCCESS':
                error_message = '%s<br>%s %s' % (error_message, new_job_status['name'], new_job_status['status'])
            elif self.status_changed(old_job_status, new_job_status):
                info_message = '%s<br>%s %s -> %s' % (info_message,
                                                      new_job_status['name'],
                                                      old_job_status['status'],
                                                      new_job_status['status'])

        if error_message:
            current_status = 'ERROR'
            print "Errors found: %s" % error_message
            msg = '%s <br><br> %s<br><br> %s' % (error_message, info_message, working_message)
            notify('Build failed!', msg)
        elif working_message:
            print "Work in progress"
            msg = '%s <br> <br> %s' % (info_message, working_message)
            header = 'Building...'
            #notify(header, msg, 'jenkins-ok.gif')
            current_status = 'IN_PROGRESS'
        else:
            if self.current_status != 'SUCCESS':
                print "No errors found"
                msg = '%s <br> <br> %s' % (info_message, working_message)
                header = 'Builds are ok'
                notify(header, msg, 'jenkins-ok.gif')
            self.current_status = 'SUCCESS'

        self.old_status_info = new_status_info


class JenkinsNotifier(Thread):
    def __init__(self, jenkins_checker):
        super(JenkinsNotifier, self).__init__(name='JenkinsNotifier')
        self.setDaemon(True)
        self.jenkins_checker = jenkins_checker

    def run(self):
        self.jenkins_checker.run()

if __name__ == '__main__':
    JenkinsChecker().run()
