#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
nohup python ./MyNoteGUI.py > /dev/null 2>&1 &