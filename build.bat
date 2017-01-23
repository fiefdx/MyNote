if exist .\dist (rd .\dist /s/q)
pyinstaller .\MyNote.spec
pyinstaller .\MyNoteGUI.spec
xcopy /s/y .\dist\MyNoteGUI\* .\dist\MyNote\
rd .\dist\MyNoteGUI /s/q
rd .\build /s/q