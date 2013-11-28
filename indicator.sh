#!/bin/sh
ps aux | fgrep python | fgrep indicator.py | fgrep -v grep > /dev/null
if [ "$?" != "0" ] ; then
  python `dirname $0`/indicator.py > `dirname $0`/indicator.log 2>&1 &
fi

ps aux | fgrep python | fgrep jenkins_desktop_notify.py | fgrep -v grep > /dev/null
if [ "$?" != "0" ] ; then
  python /home/xp/work/dev-indicator/jenkins_desktop_notify.py > /home/xp/work/dev-indicator/jenkins_desktop_notify.log 2>&1 &
fi
