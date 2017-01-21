#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
pip install pyinstaller
pip install -r ../requires/requirements.txt
sudo apt-get install python-wxgtk3.0 python-wxtools wx3.0-i18n libwxgtk3.0-dev