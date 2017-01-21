MyNote
======
An application for daily notes, you can write pure text note or rich text note, and you can quickly find what you noted earlier
by search some keywords. I have used it a few years in my daily life and work, and it help me a lot. I code it by myself, some
code is old and may be ugly. It's not perfect, it's work well, it's very useful.

Features
========
1. local html pages import & search (it used in the early version, I'm not use it, since MyNote support rich text note)
2. pure text notes
3. rich text notes based on html
4. note's content & title can be encrypt (images are not encryted)
5. you can copy html web page content to rich text note, when you save it, MyNote will try to save the web page's images to local, it's very helpful when you read the note offline
6. you can backup your notes by export your notes as one compressed file, and you can restore them by import the compressed file
7. interface support english and chinese

Configuration
=============
MyNote/app/configuration.yml or MyNote/configuration.yml
```yaml
# APP_DEBUG
# if true: listen localhost:SERVER_PORT, and ignore the SERVER_HOST, and ignore the BIND_LOCAL.
# if false: bind localhost:SERVER_PORT and SERVER_HOST:SERVER_PORT if BIND_LOCAL is false.
APP_DEBUG: false

# BIND_LOCAL
# if true: and APP_DEBUG is false, bind localhost:SERVER_PORT, and ignore the SERVER_HOST.
# if false: and APP_DEBUG is false, bind localhost:SERVER_PORT and SERVER_HOST:SERVER_PORT.
BIND_LOCAL: false

# SERVER_HOST
# is your computer's ip at local area network
SERVER_HOST: 0.0.0.0
SERVER_PORT: 8008

# SERVER_SCHEME
# a value of (http, https)
# default https
SERVER_SCHEME: https

# MAX_BUFFER_SIZE
# a number config how big your note ball can upload
# default 104857600 = 100M, 134217728 = 128M, 268435456 = 256M, 536870912 = 512M, 1073741824 = 1G
MAX_BUFFER_SIZE: 536870912

# LOG_LEVEL
# a value of (NOSET, DEBUG, INFO, WARNING, ERROR, CRITICAL)
# default NOSET
LOG_LEVEL: INFO

# USB_MODE
# if true: find the relative 'MyNoteData' directory at the same level with 
# 'MyNote' directory, and ignore the DATA_PATH.
# if false: use the DATA_PATH.
USB_MODE: false

# WITH_NGINX
# if true: upload file will through nginx with the upload-module.
# if false: upload file will through tornado, and it use RAM.
WITH_NGINX: false

# ENCRYPT
# if true: note and rich note will be encrypted at background.
# if false: note and rich note will be plaintext at background.
ENCRYPT: true

# ITEMS_PER_PAGE
# a number config how many items per page at local html file search.
# default 10
ITEMS_PER_PAGE: 10

# NOTE_DESCRIPTION_LENGTH
# a number config how many characters at note's or rich note's description.
# default 300
NOTE_DESCRIPTION_LENGTH: 300

# DATA_PATH
# a path for all data
DATA_PATH: /home/breeze/Develop/MyNoteData # you should change it as you require

# DELETE_ORIGINAL_FILE
# if true: delete original html file in the 'source' directory when import it success.
# if false: do not delete it.
DELETE_ORIGINAL_FILE: false

# PROCESS_NUM
# a number config how many process start for import file task.
# default 4
PROCESS_NUM: 4

# THREAD_NUM
# a number config how many thread per process start for import file task.
# default 1
THREAD_NUM: 1

# FUNCTIONS
# functions that you want to use
FUNCTIONS:
  - home   # home & search is for local html search, I'm not use it since MyNote support rich text note
  - search # home & search is for local html search, I'm not use it since MyNote support rich text note
  - note   # pure text note
  - rich   # rich text note
  - help   # it's a empty page now will be complete in the future
```

Installation
============
You can run it from source or binary package, My laptop's OS is Xubuntu 64bit, so I just show how to setup & install it on Xubuntu,
I build a binary package by pyinstaller for Linux 64 bit.

1. from source
   ```bash
   # run app/dev.sh
   cd MyNote/app
   ./dev.sh

   # install tea package
   git clone git@github.com:fiefdx/tea.git
   cd tea
   sudo python ./setup.py install

   # edit the configuration.yml file, before run it.
   # you can try to run MyNote.py or MyNoteGUI.py in terminal, check if error occur
   cd MyNote/app
   python ./MyNote.py or python ./MyNoteGUI.py

   # run app/Install.sh
   cd MyNote/app
   sudo ./Install.sh

   # now you can run it from then applications menu. it under the 'Internet' category
   # open a web browser, recommend firefox or chrome, open page https://localhost:8008
   # you should see the login page, and the register button at top-right corner
   ```

2. from binary package
   ```bash
   # edit the configuration.yml
   # you can try to run MyNote or MyNoteGUI in terminal, check if error occur
   cd MyNote
   ./MyNote or ./MyNoteGUI

   # run app/Install.sh
   cd MyNote
   sudo ./Install.sh

   # now you can run it from then applications menu. it under the 'Internet' category
   # open a web browser, recommend firefox or chrome, open page https://localhost:8008
   # you should see the login page, and the register button at top-right corner
   ```


