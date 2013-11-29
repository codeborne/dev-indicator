#!/usr/bin/env python
# coding=utf-8
import base64
from datetime import datetime
from json import loads
import os
import urllib2
from urlparse import urljoin
from itertools import imap
from subprocess import Popen
import string
from time import sleep

jenkins_url = 'https://jenkins.codeborne.com:444/view/All/'
pause = 60*3
excludes = []


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


def _make_secure_url(url):
    return string.replace(url, 'com/', 'com:444/')


def get_job_status(job):
    url = urljoin(job.get('url'), 'lastBuild/api/json?pretty=true')
    try:
        json = ask(url)
        if json['building']:
            return {'status': 'RUNNING',
                    'name': json['fullDisplayName'],
                    'duration': '%d%%' % (json['duration']/json['estimatedDuration']*100) if json['duration'] else '',
                    'cause': json['actions'][0]['causes'][0]['shortDescription']}
        else:
            return {'status': json['result'],
                    'name': json['fullDisplayName']}
    except ValueError as e:
        return {'status': 'FAILURE',
                'name': '%s: %s' % (job, e)}


def ask(url):
    secure_url = _make_secure_url(url)
    request = urllib2.Request(secure_url)
    temp = 'jenkins_viewer:Сколько у государства не воруй — все равно своего не вернешь!'
    base64string = base64.encodestring(temp).replace('\n', '')
    request.add_header("Authorization", u"Basic %s" % base64string)

    try:
        json_response = urllib2.urlopen(request).read()
    except Exception as e:
        print "Ignoring invalid response from url %s, caused by: %s" % (secure_url, e)
        notify('Jenkins is unavailable', '%s' % e)
        return {}

    try:
        return loads(json_response)
    except ValueError as e:
        print u"Ignoring invalid response from url %s, caused by: %s, json: %s" % (secure_url, e, json_response)
        notify('Jenkins is inadequate', '%s' % e)
        return {}


def notify(subject, message, icon='jenkins-alarm.png'):
    icon = os.path.join(os.path.dirname(os.path.realpath(__file__)), icon)
    Popen(['notify-send', subject, message, '-i', icon])


def status_changed(old_job_status, new_job_status, old_status_info):
    return old_status_info and old_job_status['status'] != new_job_status['status']


def run_jenkins_notifier():
    current_status = None
    old_status_info = {}
    while True:
        print
        print "%s Check jenkins status" % datetime.now()

        jobs = get_jobs(jenkins_url)
        if not jobs:
            sleep(pause)
            continue

        new_status_info = jobs_running_info(jobs)

        error_message = ''
        info_message = ''
        for name, new_job_status in new_status_info.iteritems():
            old_job_status = old_status_info.get(name)
            if name in excludes:
                pass
            elif new_job_status['status'] == 'RUNNING':
                info_message = '%s<br>%s %s %s<br>  %s<br>' % (info_message,
                                                               new_job_status['name'],
                                                               new_job_status['status'],
                                                               new_job_status['duration'],
                                                               new_job_status['cause'])
            elif new_job_status['status'] != 'SUCCESS':
                error_message = '%s<br>%s %s' % (error_message, new_job_status['name'], new_job_status['status'])
            elif status_changed(old_job_status, new_job_status, old_status_info):
                info_message = '%s<br>%s %s -> %s' % (info_message,
                                                      new_job_status['name'],
                                                      old_job_status['status'],
                                                      new_job_status['status'])

        if error_message:
            current_status = 'ERROR'
            print "Errors found: %s" % error_message
            msg = '%s <br>__________<br> %s' % (error_message, info_message) if info_message else error_message
            notify('Build failed!', msg)
        else:
            if current_status != 'SUCCESS':
                print "No errors found"
                notify('Builds are ok', info_message, 'jenkins-ok.gif')
            current_status = 'SUCCESS'

        old_status_info = new_status_info
        sleep(pause)


if __name__ == '__main__':
    run_jenkins_notifier()
