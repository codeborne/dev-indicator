#!/bin/sh
# sudo apt install python3-gi libayatana-appindicator3-1 libayatana-appindicator3-dev gir1.2-ayatanaappindicator3-0.1
ps aux | fgrep python | fgrep indicator.py | fgrep -v grep > /dev/null
if [ "$?" != "0" ] ; then
  cd `dirname $0`
  python3 indicator.py > indicator.log 2>&1 &
fi
