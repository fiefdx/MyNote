function noteInit (scheme, locale) {
    var $body = $("body");
    $body.addClass("loading");
    var $goto_header = $("a#navbar_header");
    var $goto_home = $("a#Home_a");
    var $goto_search = $("a#Search_a");
    var $goto_rich = $("a#Rich_a");
    var $goto_note = $("a#Note_a");
    var $goto_help = $("a#Help_a");

    var $div_note_text = $("div#div_note_text");
    var $note_books_list = $('#note_books_list');
    var $note_books = $('#note_books');
    var $note_list_ul = $('#notes_list_ul');
    var $notes_list = $('#notes_list');

    var $note_content = $('#note_text');
    var $note_title = $('#note_title');
    var $new_note_title = $('#new_note_title');
    var current_note_id = null;

    var $user_settings = $('a#Settings');
    var $save_settings = $('button#settings_submit');
    var $save_note = $('#save_note_button');
    var $create_note = $('a#create_note');
    var $create_note_modal = $('button#create_note');
    var $show_create_category = $('a#create_category');
    var $create_category = $('button#create_category');
    var $delete_category = $('button#delete_category');
    var $delete_category_modal = $('a#delete_category');
    var $show_import_notes = $('a#import_notes');
    var $show_export_notes = $('a#export_notes');
    var $show_delete_all = $('a#delete_all');
    var $show_rebuild_index = $('a#rebuild_index');
    var $search_note = $('#search_button');
    var $download_note = $('#download_note_button');
    var $display_passwd = $('#display_passwd');
    var $encrypt_notes = $('input#encrypt_notes');
    var $export_notes = $('button#export_notes');
    var $import_notes = $('button#import');

    var $create_note_toolbar = $('#create_note_toolbar_button');
    var $save_note_toolbar = $('#save_note_toolbar_button');
    var $delete_note_toolbar = $('#delete_note_toolbar_button');

    var note_scroll = 0;
    var current_category = 'All';
    var local = window.location.host;
    var uri_scheme = (scheme == 'https')? 'wss://' : 'ws://';
    var uri = uri_scheme + local + '/rich/websocket';
    console.log('Uri: ' + uri)
    var book_numbers = {};
    var loading_notes_list = false;
    var books = {};
    var action = "";

    tinymce.baseURL = "/static/tinymce";
    var tinymceEditor = null;
    var tinymce_init = false;
    var socket = null;


    if (locale != 'zh_CN') {
        locale = null
    }

    // var WebSocket = window.WebSocket || window.MozWebSocket;
    // if (WebSocket) {
    //     try {
    //         var socket = new WebSocket(uri);
    //     } catch (e) {}
    // }

    tinymce.EditorManager.init({
        selector: "textarea#note_text",
        content_css: "/static/tinymce/skins/lightgray/custom_content.css",
        language : locale,
        relative_urls: true,
        document_base_url: scheme + "://" + local + "/",
        skin : "lightgray",
        plugins: [
            "advlist autolink link insert_image lists charmap preview hr anchor pagebreak fullscreen", //image autoresize spellchecker
            "searchreplace visualblocks visualchars code insertdatetime nonbreaking", //wordcount
            "save table contextmenu directionality emoticons template paste textcolor codesample"
        ],
        fontsize_formats: "8px 10px 11px 12px 13px 14px 16px 18px 20px 24px 30px 36px",
        toolbar: [
            "fontsizeselect | forecolor | bold italic underline | numlist bullist | outdent indent | codesample" // insertfile backcolor | alignleft aligncenter alignright alignjustify
        ],
        menu: {
            file   : {title : 'File'  , items : 'create_note save_note save_note_with_proxy export_note_as_html'}, //newdocument 
            edit   : {title : 'Edit'  , items : 'undo redo | cut copy paste pastetext | selectall | searchreplace'},
            insert : {title : 'Insert', items : 'link insert_image | charmap hr anchor pagebreak insertdatetime'}, // nonbreaking template
            view   : {title : 'View'  , items : 'visualchars visualblocks visualaid | preview fullscreen'},
            format : {title : 'Format', items : 'bold italic underline strikethrough superscript subscript | formats | removeformat'},
            table  : {title : 'Table' , items : 'inserttable tableprops deletetable | cell row column'},
            tools  : {title : 'Tools' , items : 'code'}
        },
        contextmenu: "link insert_image inserttable | cell row column deletetable",
        insertdatetime_formats: ["%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%Y-%m-%d", "%I:%M:%S %p", "%D"],
        statusbar : false,
        forced_root_block : false,
        codesample_dialog_width: 1400,
        codesample_languages: [
            {text: 'HTML/XML', value: 'markup'},
            {text: 'JavaScript', value: 'javascript'},
            {text: 'CSS', value: 'css'},
            {text: 'PHP', value: 'php'},
            {text: 'Ruby', value: 'ruby'},
            {text: 'Python', value: 'python'},
            {text: 'Java', value: 'java'},
            {text: 'C', value: 'c'},
            {text: 'C#', value: 'csharp'},
            {text: 'C++', value: 'cpp'},
            {text: 'Go', value: 'go'},
            {text: 'Lua', value: 'lua'},
            {text: 'Perl', value: 'perl'},
            {text: 'PHP', value: 'php'},
            {text: 'Bash', value: 'bash'},
            {text: 'SQL', value: 'sql'},
            {text: 'Markdown', value: 'markdown'},
            {text: 'JSON', value: 'json'},
            {text: 'YAML', value: 'yaml'},
            {text: 'Rust', value: 'rust'},
            {text: 'R', value: 'r'},
            {text: 'PowerShell', value: 'powershell'},
            {text: 'MakeFile', value: 'makefile'},
            {text: 'Nginx', value: 'nginx'}
        ],
        setup: function(editor) {
            editor.addMenuItem("create_note", {
                icon: "newdocument",
                text: "New note",
                context: "file",
                // shortcut: 'Ctrl+N',
                onclick: showCreateNote,
            });
            editor.addMenuItem("save_note", {
                icon: "save",
                text: "Save note",
                context: "file",
                // shortcut: 'Ctrl+S',
                onclick: saveNote,
            });
            editor.addMenuItem("save_note_with_proxy", {
                icon: "save",
                text: "Save note(proxy)",
                context: "file",
                // shortcut: 'Ctrl+S',
                onclick: saveNoteWithProxy,
            });
            editor.addMenuItem("export_note_as_html", {
                icon: "save",
                text: "Export note as HTML",
                context: "file",
                // shortcut: 'Ctrl+S',
                onclick: exportNoteAsHTML,
            });
            // tinymceEditor = editor;
            // initNoteOperation(editor);

            // editor.on('init', function(args){
            //     var iframe = $("#" + args.target.id + "_ifr");

            //     // get the head element of the iframe's document and inject the javascript
            //     $(iframe[0].contentWindow.document)
            //         .children('html')
            //         .children('head')
            //         // .append('<script type="text/javascript">alert("Executing inside iFrame!");</script>');
            //         .append('<script src="/static/tinymce/plugins/codesample/prism.js"></script>');
            // });
        },
        init_instance_callback : function(editor) {
            var WebSocket = window.WebSocket || window.MozWebSocket;
            if (WebSocket) {
                try {
                    socket = new WebSocket(uri);
                } catch (e) {}
            }
            console.log("Editor: " + editor.id + " is now initialized.");
            tinymceEditor = editor;
            initNoteOperation(editor);
        },
    });


    // console.log("length: ", tinymce.EditorManager.editors.length, tinymce.EditorManager.majorVersion);
    // console.log("editor:", tinymceEditor, tinymce.EditorManager.activeEditor, tinymce.editors.length, tinymce.EditorManager.get(0));

    // $(prettyPrint);

    function initNoteOperation(tinymceEditor) {
        if (socket) {
            socket.onopen = function() {
                console.log("websocket onopen");
                $goto_header.bind("click", gotoHome);
                $goto_home.bind("click", gotoHome);
                $goto_search.bind("click", gotoSearch);
                $goto_rich.bind("click", gotoRich);
                $goto_note.bind("click", gotoNote);
                $goto_help.bind("click", gotoHelp);

                $user_settings.bind("click", showSettings);
                $save_settings.bind("click", saveSettings);
                $save_note.bind("click", saveNote);
                $save_note_toolbar.bind("click", saveNote);
                $create_note_modal.bind("click", createNote);
                $create_note.bind("click", showCreateNote);
                $create_note_toolbar.bind("click", showCreateNote);
                $create_category.bind("click", createCategory);
                $delete_category.bind("click", deleteCategory);
                $search_note.bind("click", search);
                $("button#delete_all").bind("click", deleteAll);
                $("button#reindex_notes").bind("click", reindexNotes);
                $delete_category_modal.bind("click", deleteCategoryModal);
                // $download_note.bind("click", downloadNote);
                $display_passwd.bind("click", displayPassword);
                $encrypt_notes.bind("click", encryptNotes);
                $export_notes.bind("click", exportNotes);
                $import_notes.bind("click", importNotes);
                $notes_list.bind("scroll", loadMoreNotes);
                $("#export_modal").on("show.bs.modal", showExportModal);
                $('#import_modal').on('shown.bs.modal', function () {
                    $('button.btn-default').focus();
                });
                $('#export_modal').on('shown.bs.modal', function () {
                    $('button.btn-default').focus();
                });
                $('#delete_notes_modal').on('shown.bs.modal', function () {
                    $('button.btn-default').focus();
                });
                $('#delete_category_modal').on('shown.bs.modal', function () {
                    $('button.btn-default').focus();
                });
                $('#reindex_modal').on('shown.bs.modal', function () {
                    $('button.btn-default').focus();
                });
                $('#create_note_modal').on('shown.bs.modal', function () {
                    $('input#new_note_title').focus();
                });
                $('#category_modal').on('shown.bs.modal', function () {
                    $('input#category_name').focus();
                });
                $('form#form_create_note').submit(function() {return false;});
                $('form#form_category').submit(function() {return false;});

                $show_create_category.bind("click", showCreateCategory);
                $show_import_notes.bind("click", showImportNotes);
                $show_export_notes.bind("click", showExportNotes);
                $show_delete_all.bind("click", showDeleteNotes);
                $show_rebuild_index.bind("click", showRebuildIndex);

                var div_note_text_height = $("div#div_note_text").height();
                tinymceEditor.theme.resizeTo("100%", div_note_text_height - 58);
            };

            socket.onmessage = function(msg) {
                console.log("websocket onmessage");
                var data = JSON.parse(msg.data);
                console.log(data);
                // init note_books
                if (data.books && data.books.books){
                    $note_books.empty();
                    data.books.books.forEach(function (value, index, array_books) {
                        console.log(index + ' ' + value);
                        $note_books.append(
                            '<a id="' + value + '_query" " class="list-group-item">' + 
                                '<span class="glyphicon glyphicon-book book_icon"></span>&nbsp;' +
                                '<span class="category_name">' + 
                                    data.books.trans[index] + '&nbsp;' +
                                '</span>' + 
                                '<span class="badge category_num">' + data.books.numbers[value] + 
                                '</span>' + 
                            '</a>'
                        );
                        initCategoryClick(value);
                    });
                    $('a#' + current_category + '_query').attr("class","list-group-item active");
                    book_numbers = data.books.numbers;
                    var note_books_height = $note_books.height() + 5; // add 5 for sure the y-scrollbar not display
                    if (note_books_height < 300) {
                        $note_books_list.height(note_books_height);
                    } else {
                        $note_books_list.height(300);
                    }
                    books = data.books;
                }
                // init note_list_ul
                if (data.notes){
                    if (data.note_list_action && data.note_list_action == "init") {
                        $note_list_ul.empty();
                    }
                    var offset = $note_list_ul.children().length;
                    data.notes.forEach(function (value, index, array_notes) {
                        console.log(index + ' ' + value);
                        // console.log(note_books);
                        if (data.current_category && data.current_category == "Search") {
                            $note_list_ul.append(
                                '<a id="a_' + value.id + '" class="note_list_item list-group-item">' + 
                                    '<p class="col-md-12 note_item_title">' + 
                                        '<span id="note_num_badge" class="badge">' + (index + offset + 1) + '</span>&nbsp' +
                                        '<span id="notes_badge" class="badge">' + value.type + '</span>&nbsp' + value.file_title + '&nbsp;' + 
                                    '</p>' +
                                    '<div class="col-md-12 note_description_div">' + 
                                        '<p class="note_item_description">' +value.description + '</p>' + 
                                    '</div>' +
                                    '<p class="note_item_datetime">' + 
                                        '<span class="pull-left">' + value.created_at + '</span>&nbsp;' + 
                                        '<span class="pull-right">' + value.updated_at + '</span>' + 
                                    '</p>' + 
                                '</a>'
                            );
                        } else {
                            $note_list_ul.append(
                                '<a id="a_' + value.id + '" class="note_list_item list-group-item">' + 
                                    '<p class="col-md-12 note_item_title">' + 
                                        '<span id="note_num_badge" class="badge">' + (index + offset + 1) + '</span>&nbsp' + value.file_title + '&nbsp;' + 
                                    '</p>' +
                                    '<div class="col-md-12 note_description_div">' + 
                                        '<p class="note_item_description">' +value.description + '</p>' + 
                                    '</div>' +
                                    '<p class="note_item_datetime">' + 
                                        '<span class="pull-left">' + value.created_at + '</span>&nbsp;' + 
                                        '<span class="pull-right">' + value.updated_at + '</span>' + 
                                    '</p>' + 
                                '</a>'
                            );
                        }
                        initNoteClick(value.id);
                    });
                    loading_notes_list = false;
                }

                if ($note_list_ul.children().length == 0) {
                    current_note_id = null;
                    $note_title.prop('readonly', true);
                    tinymceEditor.setMode('readonly');
                } else {
                    $note_title.prop('readonly', false);
                    tinymceEditor.setMode('design');
                }

                // init current_note_id
                if (data.current_note_id) {
                    console.log("note_id: " + current_note_id);
                    $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                    current_note_id = data.current_note_id;
                    console.log("note_id: " + current_note_id);
                    $('a#a_' + current_note_id).attr("class","note_list_item list-group-item active");
                    if (data.note_list_action && data.note_list_action == "update") {
                        console.log("update note description");
                        if (data.current_note_id && data.note.file_title) {
                            console.log("update note_id: ", data.current_note_id)
                            var span = $('a#a_' + data.current_note_id + " p.note_item_title span");
                            $('a#a_' + data.current_note_id + " p.note_item_title").html('<span id="note_num_badge" class="badge">' + span.html() + '</span>&nbsp' + data.note.file_title + '&nbsp;');
                            $('a#a_' + data.current_note_id + " p.note_item_description").html(data.note.description);
                            $('a#a_' + data.current_note_id + " span.pull-right").html(data.note.updated_at);
                        }
                    }
                }

                // init selected note
                if (data.note){
                    console.log("selected note: " + current_note_id);
                    $note_title.val(data.note.file_title);
                    // wysihtml5Editor.setValue(data.note.rich_content, true);
                    tinymceEditor.setContent(data.note.rich_content, {format: 'raw'});
                    // $('.wysihtml5-sandbox').contents().find('body').css("background-color", "green");
                    // hljs.initHighlightingOnLoad();
                    $('.wysihtml5-sandbox').contents().find('pre code').each(function(i, block) {
                        hljs.highlightBlock(block);
                    });
                }

                // init current_category
                if (data.current_category && data.current_category != current_category){
                    $('a#' + current_category + '_query').attr("class","list-group-item");
                    current_category = data.current_category;
                    $('a#' + current_category + '_query').attr("class","list-group-item active");
                    if (current_category != 'Search') {
                        $('#search_input').val('')
                    }
                }
                // info for save note
                if (data.save) {
                    if (data.save == "save_ok") {
                        $('#save_note_ok_modal').modal('show');
                    } else if (data.save == "save_exist") {
                        $('#save_note_exist_modal').modal('show');
                    } else if (data.save == "save_fail") {
                        $('#save_note_fail_modal').modal('show');
                    } else if (data.save == "create_ok") {
                        $('#create_note_ok_modal').modal('show');
                    } else if (data.save == "create_exist") {
                        $('#create_note_exist_modal').modal('show');
                    } else if (data.save == "create_fail") {
                        $('#create_note_fail_modal').modal('show');
                    } else if (data.save == "create_category_ok") {
                        $('#create_category_ok_modal').modal('show');
                    } else if (data.save == "create_category_exist") {
                        $('#create_category_exist_modal').modal('show');
                    } else if (data.save == "create_category_fail") {
                        $('#create_category_fail_modal').modal('show');
                    }
                }

                if (data.note_list_action && data.note_list_action == "init") {
                    $(document).ready(function() {
                        $notes_list.scrollTop(0);
                    });
                }

                if (!$body.hasClass("mce-fullscreen")) {
                    var div_note_text_height = $("div#div_note_text").height();
                    tinymceEditor.theme.resizeTo("100%", div_note_text_height - 58);
                }

                if (data.option) {
                    if (data.option == "import_notes_success") {
                        $("#import_note_success_modal").modal('show');
                    } else if (data.option == "import_notes_fail") {
                        $("#import_note_fail_modal").modal('show');
                    } else if (data.option == "reindex_notes_success") {
                        $("#reindex_note_success_modal").modal('show');
                    } else if (data.option == "reindex_notes_fail") {
                        $("#reindex_note_fail_modal").modal('show');
                    } else if (data.option == "export_notes_success") {
                        $("#export_note_success_modal").modal('show');
                    } else if (data.option == "export_notes_fail") {
                        $("#export_note_fail_modal").modal('show');
                    }
                }

                $body.removeClass("loading");
                $body.removeClass("saving");
                $div_note_text.removeClass("loading");
            };

            socket.onclose = function() {
                console.log("websocket onclose");
                if ((action == "" || (action != "import_notes" &&
                        action != "delete_notes" &&
                        action != "reindex_notes" &&
                        action != "change_settings" &&
                        action != "goto_home" &&
                        action != "goto_search" &&
                        action != "goto_rich" &&
                        action != "goto_note" &&
                        action != "goto_help")) && !$('#offline_modal').is(':visible')) {
                    changeDialogMarginTop();
                    $('#offline_modal').modal('show');
                }
            };
        }
    }

    var entityMap = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': '&quot;',
        "'": '&#39;',
        "/": '&#x2F;'
    };

    function escapeHtml(string) {
        return String(string).replace(/[&<>"'\/]/g, function (s) {
            return entityMap[s];
        });
    }

    function initCategoryClick(category) {
        $('a#' + category + '_query').bind("click", function () {
            if (socket.readyState === socket.CLOSED) {
                $('#offline_modal').modal('show');
            } else {
                $body.addClass("loading");
                $('a#' + current_category + '_query').attr("class","list-group-item");
                current_category = category;
                $('a#' + current_category + '_query').attr("class","list-group-item active");
                // clear search input
                $('#search_input').val('');
                var data = {};
                data['category'] = {'cmd':'select', 'category_name': current_category};
                socket.send(JSON.stringify(data));
                $notes_list.scrollTop(0);
                // $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(0);
                $('#note_text_ifr').contents().find('html,body').scrollTop(0);
                note_scroll = 0;
            }
        });
    }

    function loadMoreNotes() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            var offset = $note_list_ul.children().length;
            // console.log("note list scroll: ", $(this).scrollTop(), " ", $(this).height(), " ", $note_list_ul.height());
            if (loading_notes_list == false && offset < book_numbers[current_category] && ($(this).scrollTop() + $(this).height() >= $note_list_ul.height())) {
                // console.log("loadMoreNotes");
                var data = {};
                data['category'] = {'cmd':'load',
                                    'category_name': current_category,
                                    'note_id':current_note_id,
                                    'offset':offset,
                                    'q':$('#search_input').val()};
                console.log(data);
                socket.send(JSON.stringify(data));
                loading_notes_list = true;
            }
        }
    }


    function initNoteClick(note_id) {
        $('a#a_' + note_id).bind("click", function () {
            if (socket.readyState === socket.CLOSED) {
                $('#offline_modal').modal('show');
            } else {
                $div_note_text.addClass("loading");
                var data = {};
                data['note'] = {'cmd':'select', 'note_id':note_id};
                console.log("click old_id: " + current_note_id);
                if (current_note_id != null)
                    $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                current_note_id = note_id;
                console.log("click new_id: " + current_note_id);
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item active");
                console.log("socket.readyState: " + socket.readyState);
                socket.send(JSON.stringify(data));
                // $note_content.scrollTop(0);
                // $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(0);
                $('#note_text_ifr').contents().find('html,body').scrollTop(0);
                note_scroll = 0;
            }
        });
    }

    function showSettings() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            if(locale == 'zh' || locale == 'zh_CN') {
                $('input:radio[name="optionsRadios"]').filter('[value="zh_CN"]').prop('checked', true);
            } else {
                $('input:radio[name="optionsRadios"]').filter('[value="en_US"]').prop('checked', true);
            }
            changeDialogMarginTop();
            $('#settings_modal').modal('show');
        }
    }

    function saveSettings() {
        $body.addClass("loading");
        action = "change_settings";
        $('#form_settings').submit();
    }

    function saveNote() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            if (!$body.hasClass("mce-fullscreen")) {
                $div_note_text.addClass("loading");
            } else {
                $body.addClass("saving");
            }
            note_scroll = $('#note_text_ifr').contents().find('html,body').scrollTop();
            console.log("save scrollTop: " + note_scroll);
            console.log("save note: " + current_note_id);
            var data = {};
            data['note'] = {'cmd':'save',
                            'note_id':current_note_id,
                            'note_title':$note_title.val(),
                            // 'note_content':$note_content.val(),
                            'note_content':tinymceEditor.getContent({format: 'raw'}),
                            'type':current_category,
                            'q':$('#search_input').val()};
            console.log(data);
            socket.send(JSON.stringify(data));
        }
    }

    function saveNoteWithProxy() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            if (!$body.hasClass("mce-fullscreen")) {
                $div_note_text.addClass("loading");
            } else {
                $body.addClass("saving");
            }
            note_scroll = $('#note_text_ifr').contents().find('html,body').scrollTop();
            console.log("save scrollTop: " + note_scroll);
            console.log("save note: " + current_note_id);
            var data = {};
            data['note'] = {'cmd':'save',
                            'note_id':current_note_id,
                            'note_title':$note_title.val(),
                            // 'note_content':$note_content.val(),
                            'note_content':tinymceEditor.getContent({format: 'raw'}),
                            'type':current_category,
                            'q':$('#search_input').val(),
                            'proxy':true};
            console.log(data);
            socket.send(JSON.stringify(data));
        }
    }

    function showCreateNote() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            changeDialogMarginTop();
            if (current_category != 'Search' && current_category != 'All') {
                $('#create_note_modal').modal('show');
            } else if (current_category == 'All') {
                $('#create_note_all_modal').modal('show');
            } else if (current_category == 'Search') {
                $('#create_note_search_modal').modal('show');
            }
        }
    }

    function showCreateCategory() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            changeDialogMarginTop();
            $('#category_modal').modal('show');
        }
    }

    function showImportNotes() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            changeDialogMarginTop();
            $('#import_modal').modal('show');
        }
    }

    function showExportNotes() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            changeDialogMarginTop();
            $('#export_modal').modal('show');
        }
    }

    function showDeleteNotes() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            changeDialogMarginTop();
            $('#delete_notes_modal').modal('show');
        }
    }

    function showRebuildIndex() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            changeDialogMarginTop();
            $('div#reindex_modal').modal('show');
        }
    }

    function createNote() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            if (current_category != 'Search' && current_category != 'All') {
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                current_note_id = null;
                // wysihtml5Editor.setValue('', true);
                if (!$body.hasClass("mce-fullscreen")) {
                    $div_note_text.addClass("loading");
                } else {
                    $body.addClass("saving");
                }
                note_scroll = $('#note_text_ifr').contents().find('html,body').scrollTop();
                console.log("save scrollTop: " + note_scroll);
                console.log("save note: " + current_note_id);
                var data = {};
                data['note'] = {'cmd':'save',
                                'note_id':current_note_id,
                                'note_title':$new_note_title.val(),
                                // 'note_content':$note_content.val(),
                                'note_content':'',
                                'type':current_category,
                                'q':$('#search_input').val()};
                $new_note_title.val('');
                console.log(data);
                socket.send(JSON.stringify(data));
                $('.wysihtml5-sandbox').focus();
            }
        }
    }

    function exportNoteAsHTML() {
        if (current_note_id != null) {
            var url = location.protocol + "//" + local + "/rich/?option=download&id=" + current_note_id;
            var win = window.open(url, '_blank');
            win.focus();
        }
    }

    function deleteAll() {
        $body.addClass("loading");
        action = "change_settings";
        window.location.href = location.protocol + "//" + local + "/deleterichnotes";
    }

    function createCategory() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            console.log("create category");
            $body.addClass("loading");
            var data = {};
            data['category'] = {'cmd':'create',
                                'category_name': escapeHtml($('#category_name').val())};
            socket.send(JSON.stringify(data));
            $('#category_name').val('');
        }
    }

    function deleteCategoryModal() {
        if (current_category != 'Search' && current_category != 'All') {
            changeDialogMarginTop();
            $('#delete_category_modal').modal('show');
        } else if (current_category == 'All') {
            $('#delete_all_category_modal').modal('show');
        } else if (current_category == 'Search') {
            $('#delete_search_category_modal').modal('show');
        }
    }

    function deleteCategory() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            $body.addClass("loading");
            if (current_category != 'Search' && current_category != 'All') {
                console.log("delete category");
                var data = {};
                data['category'] = {'cmd':'delete',
                                    'category_name': current_category};
                socket.send(JSON.stringify(data));
                current_category = 'All';
            }
        }
    }

    async function reindexNotes() {
        await sleep(500);
        updateNotesProgress("reindex_notes_progress", 0, 0);
        var isChrome = !!window.chrome;
        if (isChrome) { // fix chrome css
            $("#form_reindex_progress .progress-bar").css("padding-top", "3px");
        }
        $("#reindex_progress_modal").modal('show');

        action = "reindex_notes";
        var file_name = "reindex_notes";
        var xsrf = $('form#form_import input[name=_xsrf]').val();
        var index_flag = {"flag": false};
        var result_index = {"flag": false, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0};
        
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            $.ajax({
                type: "post",
                async: false,
                url: location.protocol + "//" + local + "/indexrichnotesajax",
                data: {"file_name": file_name, "_xsrf": xsrf},
                success: function(data, textStatus) {
                    index_flag = data;
                },
                error: function() {
                    alert("import notes failed!");
                }
            });

            if (index_flag.flag == true) {
                while (!result_index.flag) {
                    if (socket.readyState === socket.CLOSED) {
                        $('#offline_modal').modal('show');
                        return;
                    } else {
                        $.ajax({
                            type: "get",
                            async: false,
                            url: location.protocol + "//" + local + "/indexrichnotesajax",
                            data: {"file_name": file_name},
                            success: function(data, textStatus) {
                                result_index = data;
                            },
                            error: function() {
                                alert("import notes failed!");
                            }
                        });
                        updateNotesProgress("reindex_notes_progress", result_index.tasks, result_index.predict_total);
                        await sleep(500);
                    }
                }
            }

            var option = "";
            if (result_index.flag == true && result_index.total == result_index.tasks) {
                option = "reindex_notes_success";
            } else {
                option = "reindex_notes_fail";
            }

            if (socket.readyState === socket.CLOSED) {
                $('#offline_modal').modal('show');
            } else {
                var data = {};
                data['reinit'] = {'cmd':'reinit', 'option':option};
                socket.send(JSON.stringify(data));
            }

            $("#reindex_progress_modal").modal('hide');
            $body.addClass("loading");
        }
    }

    function search() {
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            console.log("search note");
            $body.addClass("loading");
            $('a#' + current_category + '_query').attr("class","list-group-item");
            var data = {};
            data['category'] = {'cmd':'search',
                                'category_name':current_category,
                                'q':$('#search_input').val()};
            socket.send(JSON.stringify(data));
            current_category = 'Search';
            $('a#' + current_category + '_query').attr("class","list-group-item active");
            $('#search_input').blur();
            $notes_list.scrollTop(0);
            // $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(0);
            $('#note_text_ifr').contents().find('html,body').scrollTop(0);
            note_scroll = 0;
        }
    }

    function displayPassword() {
        var dispass = $display_passwd.val();
        if (dispass == "disable") {
            $display_passwd.val("enable");
            document.getElementById("notes_passwd").type = "text";
        }
        else {
            $display_passwd.val("disable");
            document.getElementById("notes_passwd").type = "password";
        }
    }

    function encryptNotes() {
        var encrypt = $encrypt_notes.val();
        if (encrypt == "disable") {
            $encrypt_notes.val("enable");
        }
        else {
            $encrypt_notes.val("disable");
        }
    }

    function showExportModal(e) {
        $("select#notes_category").empty();
        books.books.forEach(function (value, index, array_books) {
            if (value != "Search") {
                console.log(index + ' ' + value);
                $("select#notes_category").append(
                    '<option value="' + value + '">' + books.trans[index] + '</option>'
                );
            }
        });
    }

    function exportNotes() {
        updateNotesProgress("export_notes_progress", 0, 0);
        updateNotesProgress("archive_notes_progress", 0, 0);
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            var isChrome = !!window.chrome;
            if (isChrome) { // fix chrome css
                $("#form_export_progress .progress-bar").css("padding-top", "3px");
            }
            $("#export_progress_modal").modal('show');
            action = "export_notes";
            var note_category = $('form#form_export select#notes_category').val();
            var encrypt = $('form#form_export input#encrypt_notes').val();
            var password = $('form#form_export input#notes_passwd').val();
            var xsrf = $('form#form_export input[name=_xsrf]').val();
            console.log(note_category + ", " + encrypt + ", " + password + ", " + xsrf);
            exportNotesAjax(note_category, encrypt, password, xsrf);
        }
    }

    async function exportNotesAjax(category, encrypt, password, xsrf) {
        var export_flag = {"flag": false};
        var result_export = {"flag": false, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0};
        var archive_flag = {"flag": false};
        var result_archive = {"flag": false, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0, "package_name": ""};
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            $.ajax({
                type: "post",
                async: false,
                url: location.protocol + "//" + local + "/exportrichnotesajax",
                data: {"notes_category": category, "encrypt": encrypt, "passwd": password, "_xsrf": xsrf},
                success: function(data, textStatus) {
                    export_flag = data;
                },
                error: function() {
                    alert("export notes failed!");
                }
            });

            if (export_flag.flag == true) {
                while (!result_export.flag) {
                    if (socket.readyState === socket.CLOSED) {
                        $('#offline_modal').modal('show');
                        return;
                    } else {
                        $.ajax({
                            type: "get",
                            async: false,
                            url: location.protocol + "//" + local + "/exportrichnotesajax",
                            data: {"notes_category": category},
                            success: function(data, textStatus) {
                                result_export = data;
                            },
                            error: function() {
                                alert("export notes failed!");
                            }
                        });
                        updateNotesProgress("export_notes_progress", result_export.tasks, result_export.predict_total);
                        await sleep(500);
                    }
                }
            }

            if (socket.readyState === socket.CLOSED) {
                $('#offline_modal').modal('show');
                return;
            } else {
                if (result_export.flag == true) {
                    $.ajax({
                        type: "post",
                        async: false,
                        url: location.protocol + "//" + local + "/archiverichnotesajax",
                        data: {"notes_category": category, "encrypt": encrypt, "passwd": password, "_xsrf": xsrf},
                        success: function(data, textStatus) {
                            archive_flag = data;
                        },
                        error: function() {
                            alert("export notes failed!");
                        }
                    });

                    if (archive_flag.flag == true) {
                        while (!result_archive.flag) {
                            if (socket.readyState === socket.CLOSED) {
                                $('#offline_modal').modal('show');
                                return;
                            } else {
                                $.ajax({
                                    type: "get",
                                    async: false,
                                    url: location.protocol + "//" + local + "/archiverichnotesajax",
                                    data: {"notes_category": category},
                                    success: function(data, textStatus) {
                                        result_archive = data;
                                    },
                                    error: function() {
                                        alert("export notes failed!");
                                    }
                                });
                                updateNotesProgress("archive_notes_progress", result_archive.tasks, result_archive.predict_total);
                                await sleep(500);
                            }
                        }
                    }
                }

                var option = "";
                if (result_export.flag == true && result_export.total == result_export.tasks && result_archive.flag == true && result_archive.total == result_archive.tasks) {
                    option = "export_notes_success";
                    downloadNotesPackage(result_archive.package_name);
                } else {
                    option = "export_notes_fail";
                }

                if (socket.readyState === socket.CLOSED) {
                    $('#offline_modal').modal('show');
                } else {
                    var data = {};
                    data['reinit'] = {'cmd':'reinit', 'option':option, 'package_name':result_archive.package_name};
                    socket.send(JSON.stringify(data));
                }

                $("#export_progress_modal").modal('hide');
                $body.addClass("loading");
            }
        }
    }

    function downloadNotesPackage(package_name) {
        var url = location.protocol + "//" + local + "/exportrichnotes?package_name=" + package_name;
        var a = document.createElement('A');
        a.href = url;
        a.download = package_name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    function importNotes() {
        // $body.addClass("loading");
        updateNotesProgress("import_notes_progress", 0, 0);
        updateNotesProgress("index_notes_progress", 0, 0);
        changeDialogMarginTop();
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            var isChrome = !!window.chrome;
            if (isChrome) { // fix chrome css
                $("#form_import_progress .progress-bar").css("padding-top", "3px");
            }
            $("#import_progress_modal").modal('show');
            action = "import_notes";
            var file_name = $('form#form_import input#up_file').val();
            var password = $('form#form_import input#notes_passwd').val();
            var xsrf = $('form#form_import input[name=_xsrf]').val();
            uploadNotesAjax(file_name, password, xsrf);
        }
    }

    function uploadNotesAjax(file_name, password, xsrf) {
        /*
            prepareing ajax file upload
            url: the url of script file handling the uploaded files
                        fileElementId: the file type of input element id and it will be the index of  $_FILES Array()
            dataType: it support json, xml
            secureuri:use secure protocol
            success: call back function when the ajax complete
            error: callback function when the ajax failed

            <input type="hidden" name="_xsrf" value="c15e081397ac43538ae3972b27a3dbf1">
         */
        $.ajaxFileUpload({
            url:'/uploadrichnotesajax',
            secureuri:false,
            fileElementId:'up_file',
            dataType: 'xml',
            success: function (data, status) {
                if(typeof(data.error) != 'undefined') {
                    if(data.error != '') {
                        alert(data.error);
                    } else {
                        alert(data.msg);
                    }
                } else {
                    importNotesAjax(file_name, password, xsrf);
                }
            },
            error: function (data, status, e) {
                alert(e);
            }
        })
    }

    function updateNotesProgress(progress_id, tasks, total) {
        var percentage = "0%";
        if (total > 0) {
            percentage = Math.floor(tasks/total*100);
            if (percentage > 100) {
                percentage = 100;
            }
            percentage += "%";
        }
        var text = percentage; // + " - " + tasks;
        $("#" + progress_id).text(text);
        document.getElementById(progress_id).style.width = percentage;
    }

    async function importNotesAjax(file_name, password, xsrf) {
        var import_flag = {"flag": false};
        var result_import = {"flag": false, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0};
        var index_flag = {"flag": false};
        var result_index = {"flag": false, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0};
        if (socket.readyState === socket.CLOSED) {
            $('#offline_modal').modal('show');
        } else {
            $.ajax({
                type: "post",
                async: false,
                url: location.protocol + "//" + local + "/importrichnotesajax",
                data: {"file_name": file_name, "passwd": password, "_xsrf": xsrf},
                success: function(data, textStatus) {
                    import_flag = data;
                },
                error: function() {
                    alert("import notes failed!");
                }
            });

            if (import_flag.flag == true) {
                while (!result_import.flag) {
                    if (socket.readyState === socket.CLOSED) {
                        $('#offline_modal').modal('show');
                        return;
                    } else {
                        $.ajax({
                            type: "get",
                            async: false,
                            url: location.protocol + "//" + local + "/importrichnotesajax",
                            data: {"file_name": file_name},
                            success: function(data, textStatus) {
                                result_import = data;
                            },
                            error: function() {
                                alert("import notes failed!");
                            }
                        });
                        updateNotesProgress("import_notes_progress", result_import.tasks, result_import.predict_total);
                        await sleep(500);
                    }
                }
            }

            if (socket.readyState === socket.CLOSED) {
                $('#offline_modal').modal('show');
                return;
            } else {
                if (result_import.flag == true) {
                    $.ajax({
                        type: "post",
                        async: false,
                        url: location.protocol + "//" + local + "/indexrichnotesajax",
                        data: {"file_name": file_name, "_xsrf": xsrf},
                        success: function(data, textStatus) {
                            index_flag = data;
                        },
                        error: function() {
                            alert("import notes failed!");
                        }
                    });

                    if (index_flag.flag == true) {
                        while (!result_index.flag) {
                            if (socket.readyState === socket.CLOSED) {
                                $('#offline_modal').modal('show');
                                return;
                            } else {
                                $.ajax({
                                    type: "get",
                                    async: false,
                                    url: location.protocol + "//" + local + "/indexrichnotesajax",
                                    data: {"file_name": file_name},
                                    success: function(data, textStatus) {
                                        result_index = data;
                                    },
                                    error: function() {
                                        alert("import notes failed!");
                                    }
                                });
                                updateNotesProgress("index_notes_progress", result_index.tasks, result_index.predict_total);
                                await sleep(500);
                            }
                        }
                    }
                }
            }

            var option = "";
            if (result_import.flag == true && result_import.total == result_import.tasks && result_index.flag == true && result_index.total == result_index.tasks) {
                option = "import_notes_success";
            } else {
                option = "import_notes_fail";
            }

            if (socket.readyState === socket.CLOSED) {
                $('#offline_modal').modal('show');
            } else {
                var data = {};
                data['reinit'] = {'cmd':'reinit', 'option':option};
                console.log(data);
                socket.send(JSON.stringify(data));
            }

            $("#import_progress_modal").modal('hide');
            $body.addClass("loading");
        }
    }

    function onChange() {
        // $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(note_scroll);
        $('#note_text_ifr').contents().find('html,body').scrollTop(note_scroll);
        console.log("init scrollTop: " + note_scroll);
    }

    // $('.wysihtml5-sandbox').contents().find('html,body').on('change', onChange);
    $('#note_text_ifr').contents().find('html,body').on('change', onChange);

    $('#form_search').submit(function () {
        search();
        return false;
    });

    function gotoHome() {
        $body.addClass("loading");
        action = "goto_home";
        window.location.href = location.protocol + "//" + local + "/";
    }

    function gotoSearch() {
        $body.addClass("loading");
        action = "goto_search";
        window.location.href = location.protocol + "//" + local + "/search";
    }

    function gotoRich() {
        $body.addClass("loading");
        action = "goto_rich";
        window.location.href = location.protocol + "//" + local + "/rich";
    }

    function gotoNote() {
        $body.addClass("loading");
        action = "goto_note";
        window.location.href = location.protocol + "//" + local + "/note";
    }

    function gotoHelp() {
        $body.addClass("loading");
        action = "goto_help";
        window.location.href = location.protocol + "//" + local + "/help";
    }

    function changeDialogMarginTop() {
        if ($body.hasClass("mce-fullscreen")) {
            $('div#body_container').css("margin-top", "-20px");
        } else {
            $('div#body_container').css("margin-top", "80px");
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

