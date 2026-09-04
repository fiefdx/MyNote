#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
if [ -e "./dist" ]
then
    rm -rf ./dist
fi
python3 -m PyInstaller ./MyNote.spec
python3 -m PyInstaller ./MyNoteGUI.spec
cp -rf ./dist/MyNoteGUI/* ./dist/MyNote/
rm -rf ./dist/MyNoteGUI
rm -rf ./build
