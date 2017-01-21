#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
shortcut="/usr/share/applications/MyNote.desktop"
if [ -e $shortcut ]
then
    sudo rm "$shortcut"
fi
sudo rm "/usr/local/bin/mynote"
sudo rm "/usr/local/bin/mynotegui"
sudo rm "/usr/share/pixmaps/mynote.png"