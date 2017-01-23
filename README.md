MyNote
======
(中文版本请参看[这里](#mynote_zh))

An application for daily notes, you can write pure text note or rich text note, and you can quickly find what you noted earlier
by search some keywords. I have used it a few years in my daily life and work, and it help me a lot. I code it by myself, some
code is old and may be ugly. It's not perfect, it's work well, it's very useful.

It works like this:
![Alt text](/doc/rich_note_en.png?raw=true "rich_text_note_page")

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
  - help   # it's a empty page right now, it will be complete in the future
```

Installation
============
You can run it from source or binary package, My laptop's OS is Xubuntu 64bit, so I just show how to setup & install it on Xubuntu.

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

3. build binary package
   ```bash
   # run MyNote/build.sh
   cd MyNote
   ./build.sh
   # it will generate a dist/MyNote directory
   ```

Operations & Screenshots
========================

1. login page, register a user, then you can login
   ![Alt text](/doc/login_page_en.png?raw=true "login_page")

2. rich text note page, create a category, then you can create note under it
   ![Alt text](/doc/rich_note_en.png?raw=true "rich_text_note_page")

3. pure text note page, create a category, then you can create note under it
   ![Alt text](/doc/text_note_en.png?raw=true "pure_text_note_page")

4. there is no direct operation for delete a note, you should empty the note's title & content, then save it, that will delete a note

Binary Package Download Links
=============================

I build Windows 32bit package and Linux 64bit package, under windows the performance is not as good as under linux, but it still work well

1. [Windows 32bit](https://pan.baidu.com/s/1pLnTRtx)
2. [Linux 64bit](https://pan.baidu.com/s/1slRfu37)

<a name="mynote_zh"><a>

MyNote
======
这一个笔记应用，可以用来写纯文本笔记，或者富文本笔记，提供全文搜索功能可以快速查阅以往的笔记。在过去的几年里，我一直在用它来帮助我记住工作和生活中碰到的新知识。
有些代码相对较老，也是限于当时本人的技术能力，所以，这些代码会很难看，但是，它们还是工作的不错的。到目前为止，它还不是一个很完美的工具，会有bug，不过，确实非
常实用。

笔记工作界面如下:
![Alt text](/doc/rich_note_zh.png?raw=true "rich_text_note_page")

笔记特性
======
1. 本地html文件导入和搜索功能（这个功能在我实现了富文本笔记后就基本不用了）
2. 纯文本笔记功能
3. 富文本笔记功能（基于html）
4. 笔记标题和内容加密功能（笔记中的图片是不会被加密的）
5. 复制到富文本笔记中的网页中的图片会自动保存到本地，方便离线时阅读笔记
6. 可以将笔记备份成压缩包，也可以将备份的压缩包导入恢复笔记
7. 笔记界面支持中文和英文

笔记配置项
========
配置文件为 MyNote/app/configuration.yml 或 MyNote/configuration.yml （取决于是生成的二进制包运行，还是源码运行）
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
DATA_PATH: /home/breeze/Develop/MyNoteData # 更改这个配置为你想存储笔记数据的目录

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
  - home   # home和search是为了本地html搜索功能，自从笔记支持富文本后，这个功能我就不用了
  - search # home和search是为了本地html搜索功能，自从笔记支持富文本后，这个功能我就不用了
  - note   # 纯文本笔记功能
  - rich   # 富文本笔记功能
  - help   # 目前帮助页面还是空白页，之后会添加帮助文档内容
```

笔记安装步骤
==========
你可以从源码直接运行，也可以打包成可执行文件后运行，由于我用的是Xubuntu 64位，所以，就只写一下在Xubuntu下的安装步骤。

1. 从源码运行
   ```bash
   # 运行 app/dev.sh
   cd MyNote/app
   ./dev.sh

   # 安装tea包，用来加密笔记内容
   git clone git@github.com:fiefdx/tea.git
   cd tea
   sudo python ./setup.py install

   # 在运行笔记之前要先更改configuration.yml配置文件
   # 可以在终端中运行MyNote.py或者MyNoteGUI.py，观察是否有报错
   cd MyNote/app
   python ./MyNote.py 或 python ./MyNoteGUI.py

   # 运行app/Install.sh安装脚本
   cd MyNote/app
   sudo ./Install.sh

   # 现在你可以从系统程序菜单运行MyNote了
   # 在服务启动后，用浏览器（推荐用火狐或谷歌浏览器）打开https://localhost:8008
   # 应该就可以看到登录页面了，登录页面右上角有用户注册入口
   ```

2. 从二进制包运行
   ```bash
   # 在运行笔记之前要先更改configuration.yml配置文件
   # 可以在终端中运行MyNote或者MyNoteGUI，观察是否有报错
   cd MyNote
   ./MyNote or ./MyNoteGUI

   # 运行app/Install.sh安装脚本
   cd MyNote
   sudo ./Install.sh

   # 现在你可以从系统程序菜单运行MyNote了
   # 在服务启动后，用浏览器（推荐用火狐或谷歌浏览器）打开https://localhost:8008
   # 应该就可以看到登录页面了，登录页面右上角有用户注册入口
   ```

3. 打二进制包
   ```bash
   # 运行打包脚本MyNote/build.sh
   cd MyNote
   ./build.sh
   # 脚本会自动生成dist/MyNote目录，MyNote就是打好的二进制包的根目录
   ```

常见操作和截屏
===========

1. 登录页面，注册用户后就可以登录了
   ![Alt text](/doc/login_page_zh.png?raw=true "login_page")

2. 富文本笔记页面，新建类别后，就可以在新建的类别下新建笔记了
   ![Alt text](/doc/rich_note_zh.png?raw=true "rich_text_note_page")

3. 纯文本笔记页面，新建类别后，就可以在新建的类别下新建笔记了
   ![Alt text](/doc/text_note_zh.png?raw=true "pure_text_note_page")

4. 笔记中没有直接删除一篇笔记的功能，把想要删除的笔记的标题和内容清空，再保存该笔记，该篇笔记就会被删除了

二进制包下载地址
=============

我打包了Windows 32位和Linux 64位的二进制包，笔记在windows下的性能没有在linux下的性能好，不过依然工作正常

1. [Windows 32位](https://pan.baidu.com/s/1pLnTRtx)
2. [Linux 64位](https://pan.baidu.com/s/1slRfu37)
