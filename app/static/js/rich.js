function noteInit (scheme, locale) {
    var $note_books_list = $('#note_books_list');
    var $note_books = $('#note_books');
    var $note_list_ul = $('#notes_list_ul');
    var $notes_list = $('#notes_list');

    var $note_content = $('#note_text');
    var $note_title = $('#note_title');
    var $new_note_title = $('#new_note_title');
    var current_note_id = null;

    var $user_settings = $('a#Settings');
    var $save_note = $('#save_note_button');
    var $create_note = $('a#create_note');
    var $create_note_modal = $('button#create_note');
    var $create_category = $('button#create_category');
    var $delete_category = $('button#delete_category');
    var $delete_category_modal = $('a#delete_category');
    var $search_note = $('#search_button');
    var $download_note = $('#download_note_button');
    var $display_passwd = $('#display_passwd');
    var $encrypt_notes = $('input#encrypt_notes');
    var $export_notes = $('button#export_notes');
    var $import_notes = $('button#import');

    var wysihtml5Editor = $note_content.wysihtml5({
        'stylesheets': [
            "/static/css/editor.css", 
            "/static/bootstrap/css/wysiwyg-color.css",
            "/static/highlight/styles/default.css"
        ], 
        'locale': locale,
        'format-code' : true}).data("wysihtml5").editor;
    $(prettyPrint);
    var $create_note_toolbar = $('#create_note_toolbar_button');
    var $save_note_toolbar = $('#save_note_toolbar_button');
    var $delete_note_toolbar = $('#delete_note_toolbar_button');

    var note_scroll = 0;
    var current_category = 'All';
    var local = window.location.host;
    var uri_scheme = (scheme == 'https')? 'wss://' : 'ws://';
    var uri = uri_scheme + local + '/rich/websocket';
    console.log('Uri: ' + uri)

    $('.btn-file :file').on('fileselect', function(event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text'),
            log = numFiles > 1 ? numFiles + ' files selected' : label;
        if( input.length ) {
            input.val(log);
        } else {
            if( log ) alert(log);
        }
    });

    var WebSocket = window.WebSocket || window.MozWebSocket;
    if (WebSocket) {
        try {
            var socket = new WebSocket(uri);
        } catch (e) {}
    }

    if (socket) {
        socket.onopen = function() {
            console.log("websocket onopen");
            $user_settings.bind("click", showSettings);
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
                var note_books_height = $note_books.height() + 5; // add 5 for sure the y-scrollbar not display
                if (note_books_height < 300) {
                    $note_books_list.height(note_books_height);
                } else {
                    $note_books_list.height(300);
                }
            }
            // init note_list_ul
            if (data.notes){
                $note_list_ul.empty();
                data.notes.forEach(function (value, index, array_notes) {
                    console.log(index + ' ' + value);
                    // console.log(note_books);
                    if (data.current_category && data.current_category == "Search") {
                        $note_list_ul.append(
                            '<a id="a_' + value.id + '" class="note_list_item list-group-item">' + 
                                '<p class="col-md-12 note_item_title">' + 
                                    '<span id="note_num_badge" class="badge">' + (index + 1) + '</span>&nbsp' +
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
                    }
                    else {
                        $note_list_ul.append(
                            '<a id="a_' + value.id + '" class="note_list_item list-group-item">' + 
                                '<p class="col-md-12 note_item_title">' + 
                                    '<span id="note_num_badge" class="badge">' + (index + 1) + '</span>&nbsp' + value.file_title + '&nbsp;' + 
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
            }
            // init current_note_id
            if (data.current_note_id){
                console.log("note_id: " + current_note_id);
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                current_note_id = data.current_note_id;
                console.log("note_id: " + current_note_id);
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item active");
            }
            // init selected note
            if (data.note){
                console.log("selected note: " + current_note_id);
                $note_title.val(data.note.file_title);
                wysihtml5Editor.setValue(data.note.rich_content, true);
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
                $('#save_note_modal').modal('show');
            }
        };

        socket.onclose = function() {
            console.log("websocket onclose");
            $note_title.css({'background-color' : '#CC0000'});
        };

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
                $('a#' + current_category + '_query').attr("class","list-group-item");
                current_category = category;
                $('a#' + current_category + '_query').attr("class","list-group-item active");
                // clear search input
                $('#search_input').val('');
                var data = {};
                data['category'] = {'cmd':'select', 'category_name': current_category};
                socket.send(JSON.stringify(data));
                $notes_list.scrollTop(0);
                $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(0);
                note_scroll = 0;
            });
        }

        function initNoteClick(note_id) {
            $('a#a_' + note_id).bind("click", function () {
                var data = {};
                data['note'] = {'cmd':'select', 'note_id':note_id};
                console.log("click old_id: " + current_note_id);
                if (current_note_id != null)
                    $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                current_note_id = note_id;
                console.log("click new_id: " + current_note_id);
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item active");
                socket.send(JSON.stringify(data));
                // $note_content.scrollTop(0);
                $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(0);
                note_scroll = 0;
            });
        }

        function showSettings() {
            if(locale == 'zh') {
                $('input:radio[name="optionsRadios"]').filter('[value="zh_CN"]').attr('checked', true);
            } else {
                $('input:radio[name="optionsRadios"]').filter('[value="en_US"]').attr('checked', true);
            }
            $('#settings_modal').modal('show');
        }

        function saveNote() {
            note_scroll = $('.wysihtml5-sandbox').contents().find('html,body').scrollTop();
            console.log("save scrollTop: " + note_scroll);
            console.log("save note: " + current_note_id);
            var data = {};
            data['note'] = {'cmd':'save', 
                            'note_id':current_note_id, 
                            'note_title':$note_title.val(), 
                            'note_content':$note_content.val(), 
                            'type':current_category, 
                            'q':$('#search_input').val()};
            console.log(data);
            socket.send(JSON.stringify(data));
        }

        function showCreateNote() {
            if (current_category != 'Search' && current_category != 'All') {
                $('#create_note_modal').modal('show');
            }
        }

        function createNote() {
            if (current_category != 'Search' && current_category != 'All') {
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                current_note_id = null;
                $note_title.val($new_note_title.val());
                $new_note_title.val('');
                wysihtml5Editor.setValue('', true);
                $note_content.val('');
                // $note_title.focus();
                saveNote();
                $('.wysihtml5-sandbox').focus();
            }
        }

        function downloadNote() {
            if (current_note_id != null) {
                var url = location.protocol + "//" + local + "/note/?option=download&id=" + current_note_id;
                var win = window.open(url, '_blank');
                win.focus();
            }
        }

        function deleteAll() {
            window.location.href = location.protocol + "//" + local + "/deleterichnotes";
        }

        function createCategory() {
            console.log("create category");
            var data = {};
            data['category'] = {'cmd':'create', 
                                'category_name': escapeHtml($('#category_name').val())};
            socket.send(JSON.stringify(data));
            $('#category_name').val('');
        }

        function deleteCategoryModal() {
            if (current_category != 'Search' && current_category != 'All') {
                $('#delete_category_modal').modal('show');
            }
        }

        function deleteCategory() {
            if (current_category != 'Search' && current_category != 'All') {
                console.log("delete category");
                var data = {};
                data['category'] = {'cmd':'delete', 
                                    'category_name': current_category};
                socket.send(JSON.stringify(data));
                current_category = 'All';
            }
        }

        function reindexNotes() {
            window.location.href = location.protocol + "//" + local + "/rich/?option=rebuild_index";
        }

        function search() {
            console.log("search note");
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
            $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(0);
            note_scroll = 0;
        }

        function displayPassword() {
            var dispass = $display_passwd.val();
            if (dispass == "unable") {
                $display_passwd.val("enable");
                document.getElementById("notes_passwd").type = "text";
            }
            else {
                $display_passwd.val("unable");
                document.getElementById("notes_passwd").type = "password";
            }
        }

        function encryptNotes() {
            var encrypt = $encrypt_notes.val();
            if (encrypt == "unable") {
                $encrypt_notes.val("enable");
            }
            else {
                $encrypt_notes.val("unable");
            }
        }

        function exportNotes() {
            $('#form_export').submit();
            $('#export_modal').modal('hide');
        }

        function importNotes() {
            $('#form_import').submit();
            // upload_notes_ajax();
        }

        function upload_notes_ajax() {   
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
            result = false;
            $.ajaxFileUpload({
                url:'/importrichnotes',
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
                        // var name = data.getElementById("name").innerHTML;
                        // var url = data.getElementById("url").innerHTML;
                        // document.getElementById('bootstrap-wysihtml5-insert-image-url').value = url;
                        console.log("up_file ok");
                        result = true;
                    }
                },
                error: function (data, status, e) {
                    alert(e);
                }
            })
            return result;
        }  

        function onChange() {
            $('.wysihtml5-sandbox').contents().find('html,body').scrollTop(note_scroll);
            console.log("init scrollTop: " + note_scroll);
        }

        $('.wysihtml5-sandbox').contents().find('html,body').on('change', onChange);

        $('#form_search').submit(function () {
            search();
            return false;
        });
    }
}

