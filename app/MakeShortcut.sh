#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
cmd_path=`pwd`
mynote_path="$cmd_path/MyNote"
mynotegui_path="$cmd_path/MyNoteGUI"
icon_path="$cmd_path/static/mynote.png"

if [ ! -e $mynote_path ]
then
    mynote_path="$cmd_path/MyNote.py"
fi

if [ ! -e $mynotegui_path ]
then
    mynotegui_path="$cmd_path/MyNoteGUI.py"
fi

sudo ln -sf "$mynote_path" "/usr/local/bin/mynote"
sudo ln -sf "$mynotegui_path" "/usr/local/bin/mynotegui"
sudo cp -f "$icon_path" "/usr/share/pixmaps/mynote.png"

touch ./MyNote.desktop
content="[Desktop Entry]
Name=MyNote
Comment=MyNote
Exec=mynotegui
Icon=mynote
Type=Application
Terminal=false
Categories=GNOME;GTK;Utility;Network;Office;"
echo -e "$content" > ./MyNote.desktop
sudo chmod +x ./MyNote.desktop