#!/usr/bin/env python
# coding=utf-8
import base64
from json import loads
import os
import urllib2
from urlparse import urljoin
from itertools import imap
from subprocess import Popen
import string
from time import sleep

jenkins_url = 'https://jenkins.codeborne.com:444/view/All/'


def get_jobs(jenkins_url):
    def make_job(job):
        return {
            'url': job.get('url'),
            'name': job.get('name')
        }

    jobs = ask(urljoin(jenkins_url, 'api/json?pretty=true'))
    print "get_jobs: %s" % jobs
    print
    print

    return imap(make_job, jobs.get('jobs'))


def jobs_running_info(jobs):
    def make_job(job):
        return job.get('name'), running(job)
    return dict(make_job(job) for job in jobs)


def running(job):
    status = get_job_status(job)
    print "get_job_status for %s: %s" % (job, status)
    print
    print

    build = get_last_build(status)
    if build:
        build_info = ask(urljoin(build.get('url'), 'api/json?pretty=true'))
        if build_info.get('building'):
            return "RUNNING"
        return build_info.get('result')
    return "UNKNOWN"


def _make_secure_url(url):
    return string.replace(url, 'com/', 'com:444/')


def get_job_status(job):
    # TODO Use faster URL: https://jenkins.codeborne.com/job/ibank/lastBuild/api/json?pretty=true

    # Current upstream jenkins have bug
    # https://issues.jenkins-ci.org/browse/JENKINS-15713
    # so, running builds can only be acquired with this ugly workarounc
    try:
        url = urljoin(job.get('url'), 'api/json', '?tree=allBuilds[name,url,result,building,number]&pretty=true')
        json = ask(url)
        return {'builds': json['builds']}
    except ValueError as e:
        print "Ignoring invalid job status info at url %s, cause by: %s, json: %s" % (job.get('url'), e, json)
    return {}


def get_last_build(job_status):
    def compare(job1, job2):
        return job1.get('number') < job2.get('number')

    builds = job_status.get('builds')
    if builds is not None and len(builds) > 0:
        builds.sort(cmp=compare)
        return builds[0]
    else:
        return None


def ask(url):
    secure_url = _make_secure_url(url)
    print "ask %s" % secure_url
    print
    print

    request = urllib2.Request(secure_url)
    temp = 'jenkins_viewer:Сколько у государства не воруй — все равно своего не вернешь!'
    base64string = base64.encodestring(temp).replace('\n', '')
    request.add_header("Authorization", u"Basic %s" % base64string)

    try:
        json_response = urllib2.urlopen(request).read()
    except Exception as e:
        print "Ignoring invalid response from url %s, caused by: %s" % (url, e)
        return {}

    try:
        return loads(json_response)
    except ValueError as e:
        print u"Ignoring invalid response from url %s, caused by: %s, json: %s" % (url, e, json_response)
        return {}


def notify(message):
    icon = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'angry-jenkins.png')
    Popen(['notify-send', 'Jenkins on fire!', message, '-i', icon])


def report_required(old_job_status, new_job_status, old_status_info):
    return old_status_info and old_job_status != new_job_status


def run_jenkins_notifier():
    old_status_info = {}
    while True:
        print "Check jenkins status"
        print
        print

        jobs = get_jobs(jenkins_url)  # there may be new jobs
        new_status_info = jobs_running_info(jobs)

        error_message = ''
        for name, new_job_status in new_status_info.iteritems():
            old_job_status = old_status_info.get(name)
            if report_required(old_job_status, new_job_status, old_status_info):
                error_message = '%s<br>Job %s %s -> %s' % (error_message, name, old_job_status, new_job_status)
            elif new_job_status not in ('SUCCESS', 'RUNNING'):
                error_message = '%s<br>Job %s %s' % (error_message, name, new_job_status)

        if error_message:
            print "Error found: %s" % error_message
            notify(error_message)
        else:
            print "No errors found"

        old_status_info = new_status_info
        sleep(5)


if __name__ == '__main__':
    run_jenkins_notifier()
