#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
shortcut="/usr/share/applications/MyNote.desktop"
if [ -e $shortcut ]
then
	sudo rm "$shortcut"
fi