#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path
if [ -e "./dist" ]
then
    rm -rf ./dist
fi
pyinstaller ./MyNote.spec
pyinstaller ./MyNoteGUI.spec
cp -rf ./dist/MyNoteGUI/* ./dist/MyNote/
rm -rf ./dist/MyNoteGUI
rm -rf ./build