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

    var current_category = 'All';
    var local = window.location.host;
    var uri_scheme = (scheme == 'https')? 'wss://' : 'ws://';
    var uri = uri_scheme + local + '/note/websocket';
    console.log('Uri: ' + uri)
    var book_numbers = {};
    var loading_notes_list = false;
    var books = {};

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
            $create_note.bind("click", showCreateNote);
            $create_note_modal.bind("click", createNote);
            $create_category.bind("click", createCategory);
            $delete_category.bind("click", deleteCategory);
            $search_note.bind("click", search);
            $("button#delete_all").bind("click", deleteAll);
            $("button#reindex_notes").bind("click", reindexNotes);
            $delete_category_modal.bind("click", deleteCategoryModal);
            $download_note.bind("click", downloadNote);
            $display_passwd.bind("click", displayPassword);
            $encrypt_notes.bind("click", encryptNotes);
            $export_notes.bind("click", exportNotes);
            $import_notes.bind("click", importNotes);
            $notes_list.bind("scroll", loadMoreNotes);
            $("#export_modal").on("show.bs.modal", showExportModal);
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
                    }
                    else {
                        $note_list_ul.append(
                            '<a id="a_' + value.id + '" class="note_list_item list-group-item">' + 
                                '<p class="col-md-12 note_item_title">' + 
                                    '<span id="note_num_badge" class="badge">' + (index + offset + 1) + '</span>&nbsp' + value.file_title + '&nbsp;' + 
                                '</p>' +
                                '<div class="col-md-12 note_description_div">' + 
                                    '<p class="note_item_description">' + value.description + '</p>' + 
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
            // init current_note_id
            if (data.current_note_id){
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
                $note_content.val(data.note.file_content);
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
            if (data.note_list_action && data.note_list_action == "init") {
                $(document).ready(function() {
                    $notes_list.scrollTop(0);
                });
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
            });
        }

        function loadMoreNotes() {
            var offset = $note_list_ul.children().length;
            console.log("note list scroll: ", $(this).scrollTop(), " ", $(this).height(), " ", $note_list_ul.height(), " ", loading_notes_list);
            if (loading_notes_list == false && offset < book_numbers[current_category] && ($(this).scrollTop() + $(this).height() >= $note_list_ul.height())) {
                console.log("loadMoreNotes");
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
                $note_content.scrollTop(0);
            });
        }

        function showSettings() {
            if(locale == 'zh' || locale == 'zh_CN') {
                $('input:radio[name="optionsRadios"]').filter('[value="zh_CN"]').prop('checked', true);
            } else {
                $('input:radio[name="optionsRadios"]').filter('[value="en_US"]').prop('checked', true);
            }
            $('#settings_modal').modal('show');
        }

        function saveNote() {
            console.log("save note: " + current_note_id);
            var data = {};
            data['note'] = {'cmd':'save', 
                            'note_id':current_note_id, 
                            'note_title':$note_title.val(), 
                            'note_content':$note_content.val(), 
                            'type':current_category, 
                            'q':$('#search_input').val()};
            socket.send(JSON.stringify(data));
        }

        function showCreateNote() {
            if (current_category != 'Search' && current_category != 'All') {
                $('#create_note_modal').modal('show');
            } else if (current_category == 'All') {
                $('#create_note_all_modal').modal('show');
            } else if (current_category == 'Search') {
                $('#create_note_search_modal').modal('show');
            }
        }

        function createNote() {
            if (current_category != 'Search' && current_category != 'All') {
                $('a#a_' + current_note_id).attr("class","note_list_item list-group-item");
                current_note_id = null;
                $note_title.val($new_note_title.val());
                $new_note_title.val('');
                $note_content.val('');
                saveNote();
                setTimeout(function() {
                    $note_content.focus();
                }, 0);
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
            window.location.href = location.protocol + "//" + local + "/deletenotes";
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
            window.location.href = location.protocol + "//" + local + "/note/?option=rebuild_index";
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
            $note_content.scrollTop(0);
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
            $('#form_export').submit();
            $('#export_modal').modal('hide');
        }

        function exportNotesAjax() {
            var formdata = $('form#form_export').serializeArray();
            $('#export_modal').modal('hide');
            $.ajax({
                type: "post",
                async: false,
                url: location.protocol + "//" + local + "/exportnotes",
                data: formdata,
                success: function(data, textStatus) {
                    console.log(data);
                    console.log("post ajax success.");
                    window.open($(this).prop('action'))
                },
                error: function() {
                    console.log("post ajax failed!");
                }

            });
        }

        function importNotes() {
            $('#form_import').submit();
        }

        $('#form_search').submit(function () {
            search();
            return false;
        });
    }
}

