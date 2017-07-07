import os
import time
from threading import Thread
import subprocess
from subprocess import Popen, PIPE, STDOUT

class AutoUpdate(Thread):
    def __init__(self, indicator):
        super(AutoUpdate, self).__init__(name='AutoUpdate')
        self.setDaemon(True)
        self.indicator = indicator

    def _check_for_updates(self):
        if subprocess.call("echo `wget -qO- stash.codeborne.com/devindicator/version` | diff version -", shell=True):
            print "Downloading updates..."
            wget = Popen(["wget", "-qO-", "https://stash.codeborne.com/devindicator/devindicator.tar.gz"], cwd=os.path.dirname(os.path.realpath(__file__)), stdout=PIPE)
            subprocess.check_call(["tar", "xzf", "-", "--directory", os.path.dirname(os.path.realpath(__file__))], stdin=wget.stdout);
            self.indicator.restart()

    def run(self):
        while True:
            try:
                self._check_for_updates()
                time.sleep(60*5)
            except Exception as e:
                print 'Failed to update: %s' % e
                time.sleep(60*60)


