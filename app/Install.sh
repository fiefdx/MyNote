#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
./MakeShortcut.sh
sudo cp ./MyNote.desktop /usr/share/applications/MyNote.desktop
pip install -r ../requires/requirements.txt