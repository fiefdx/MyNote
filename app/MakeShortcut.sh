#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
cmd_path=`pwd`
touch ./MyNote.desktop
content="[Desktop Entry]
Name=MyNote
Comment=MyNote
Exec=\"$cmd_path/MyNote.sh\" %F
Icon=$cmd_path/static/favicon.ico
Type=Application
Terminal=false
Categories=GNOME;GTK;Utility;Network;Office;"
echo -e "$content" > ./MyNote.desktop
sudo chmod +x ./MyNote.desktop