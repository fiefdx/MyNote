// change this for bootstrap3 by YangHaitao 2013-11-10
// change this for add datetime by YangHaitao 2014-05-13
// change this for international by YangHaitao 2014-10-27
!function($, wysi) {
    "use strict";

    var tpl = {
        "create-note": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
                "<button id='create_note_toolbar_button' class='btn btn-toolbar" + size + "' data-wysihtml5-action='createNote' title='" + locale.create_note.create_note + "' tabindex='-1'><span class='glyphicon glyphicon-file'></span></button>" +
            "</div>";
        },

        "save-note": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
                "<button id='save_note_toolbar_button' class='btn btn-toolbar" + size + "' data-wysihtml5-action='saveNote' title='" + locale.save_note.save_note + "' tabindex='-1'><span class='glyphicon glyphicon-floppy-save'></span></button>" +
            "</div>";
        },

        "delete-note": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-action='deleteNote' title='" + locale.delete_note.delete_note + "' tabindex='-1'><span class='glyphicon glyphicon-floppy-remove'></span></button>" +
            "</div>";
        },

        "download-note": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-action='downloadNote' title='" + locale.download_note.download_note + "' tabindex='-1'><span class='glyphicon glyphicon-cloud-download'></span></button>" +
            "</div>";
        },

        "font-styles": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<button class='btn btn-toolbar dropdown-toggle" + size + "' data-toggle='dropdown'>" +
              "<span class='glyphicon glyphicon-font'></span>&nbsp;<span class='current-font'>" + locale.font_styles.normal + "</span>&nbsp;<b class='caret'></b>" +
              "</button>" +
              "<ul class='dropdown-menu'>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='div' tabindex='-1'>" + locale.font_styles.normal + "</a></li>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h1' tabindex='-1'>" + locale.font_styles.h1 + "</a></li>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h2' tabindex='-1'>" + locale.font_styles.h2 + "</a></li>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h3' tabindex='-1'>" + locale.font_styles.h3 + "</a></li>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h4'>" + locale.font_styles.h4 + "</a></li>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h5'>" + locale.font_styles.h5 + "</a></li>" +
                "<li><a data-wysihtml5-command='formatBlock' data-wysihtml5-command-value='h6'>" + locale.font_styles.h6 + "</a></li>" +
              "</ul>" +
            "</div>";
        },

        "emphasis": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='bold' title='CTRL+B' tabindex='-1'>" + locale.emphasis.bold + "</button>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='italic' title='CTRL+I' tabindex='-1'>" + locale.emphasis.italic + "</button>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='underline' title='CTRL+U' tabindex='-1'>" + locale.emphasis.underline + "</button>" +
              "</div>" +
            "</div>";
        },

        "lists": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='insertUnorderedList' title='" + locale.lists.unordered + "' tabindex='-1'><span class='glyphicon glyphicon-list'></span></button>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='insertOrderedList' title='" + locale.lists.ordered + "' tabindex='-1'><span class='glyphicon glyphicon-th-list'></span></button>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='Outdent' title='" + locale.lists.outdent + "' tabindex='-1'><span class='glyphicon glyphicon-indent-right'></span></button>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='Indent' title='" + locale.lists.indent + "' tabindex='-1'><span class='glyphicon glyphicon-indent-left'></span></button>" +
              "</div>" +
            "</div>";
        },

        "link": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<div class='bootstrap-wysihtml5-insert-link-modal modal fade' tabindex='-1' role='dialog' aria-hidden='true'>" +
                  "<div class='modal-dialog'>" +
                      "<div class='modal-content'>" +
                        "<div class='modal-header'>" +
                          "<a class='close' data-dismiss='modal'>&times;</a>" +
                          "<h3>" + locale.link.insert + "</h3>" +
                        "</div>" +
                        "<div class='modal-body'>" +
                          "<input value='http://' class='bootstrap-wysihtml5-insert-link-url input-xlarge form-control'>" +
                          "<label class='checkbox'> <input type='checkbox' class='bootstrap-wysihtml5-insert-link-target' checked>" + locale.link.target + "</label>" +
                        "</div>" +
                        "<div class='modal-footer'>" +
                          "<a href='#' class='btn btn-default' data-dismiss='modal'>" + locale.link.cancel + "</a>" +
                          "<a href='#' class='btn btn-primary' data-dismiss='modal'>" + locale.link.insert + "</a>" +
                        "</div>" +
                      "</div>" +
                  "</div>" +
              "</div>" +
              "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='createLink' title='" + locale.link.insert + "' tabindex='-1'><span class='glyphicon glyphicon-share'></span></button>" +
            "</div>";
        },

        "image": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<div class='bootstrap-wysihtml5-insert-image-modal modal fade' tabindex='-1' role='dialog' data-backdrop='static' aria-hidden='true'>" +
                  "<div class='modal-dialog'>" +
                      "<div class='modal-content'>" +
                        "<div class='modal-header'>" +
                          "<a class='close' data-dismiss='modal'>&times;</a>" +
                          "<h3>" + locale.image.insert + "</h3>" +
                        "</div>" +
                        "<div class='modal-body'>" +
                            '<div class="row col-xs-12" style="background:; margin-left: 0px; padding-left: 0px; padding-right: 0px;">' +
                                '<div class="col-xs-12">' +
                                    '<div class="input-group col-xs-12" style="padding-left: 0px; padding-right: 0px;">' +
                                        '<span class="input-group-btn">' +
                                            '<span type="button" class="btn btn-primary" onclick="upload_picture_ajax()">' + locale.image.upload + '</span>' +
                                            '<span class="btn btn-primary btn-file" style="margin-left: 0px;">' +
                                                locale.image.choose + '<input id="up_picture" type="file" name="up_file">' +
                                            '</span>' +
                                        '</span>' +
                                        '<input type="text" class="form-control" readonly>' +
                                    '</div>' +
                                    '<div class="row well col-xs-12" style="padding-left: 0px; padding-right: 0px; margin-top: 10px; margin-bottom: 0px;">' +
                                        '<span class="col-xs-2" style="padding: 0px 6px; text-align: right;">' + locale.image.picture_width + '</span>' +
                                        '<input value="600" type="number" min="0" class="bootstrap-wysihtml5-insert-image-width px-input col-xs-2" style="">' +
                                        '<span class="col-xs-2" style="padding: 0px 6px; text-align: left;">' + locale.image.px + '</span>' +
                                        '<span class="col-xs-2" style="padding: 0px 6px; text-align: right;">' + locale.image.picture_height + '</span>' +
                                        '<input value="0" type="number" min="0" class="bootstrap-wysihtml5-insert-image-height px-input col-xs-2" style="">' +
                                        '<span class="col-xs-2" style="padding: 0px 6px; text-align: left;">' + locale.image.px + '</span>' +
                                    '</div>' +
                                    '<input value="http://" id="bootstrap-wysihtml5-insert-image-url" class="bootstrap-wysihtml5-insert-image-url input-xlarge form-control col-xs-12" style="margin-top: 10px;">' +
                                '</div>' +
                            '</div>' +
                        "</div>" +
                        "<div class='modal-footer'>" +
                          "<a href='#' class='btn btn-default' data-dismiss='modal'>" + locale.image.cancel + "</a>" +
                          "<a href='#' class='btn btn-primary' data-dismiss='modal'>" + locale.image.insert + "</a>" +
                        "</div>" +
                      "</div>" +
                  "</div>" +
              "</div>" +
              "<button class='btn btn-toolbar" + size + "' data-wysihtml5-command='insertImage' title='" + locale.image.insert + "' tabindex='-1'><span class='glyphicon glyphicon-picture'></span></button>" +
            "</div>";
        },

        "html": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-action='change_view' title='" + locale.html.edit + "' tabindex='-1'><span class='glyphicon glyphicon-pencil'></span></button>" +
              "</div>" +
            "</div>";
        },

        "color": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
              "<button type='button' class='btn btn-toolbar dropdown-toggle" + size + "' data-toggle='dropdown' tabindex='-1'>" +
                "<span class='current-color'>" + locale.colours.black + "</span>&nbsp;<b class='caret'></b>" +
              "</button>" +
              "<ul class='dropdown-menu'>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='black'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='black'>" + locale.colours.black + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='silver'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='silver'>" + locale.colours.silver + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='gray'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='gray'>" + locale.colours.gray + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='maroon'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='maroon'>" + locale.colours.maroon + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='red'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='red'>" + locale.colours.red + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='purple'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='purple'>" + locale.colours.purple + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='green'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='green'>" + locale.colours.green + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='olive'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='olive'>" + locale.colours.olive + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='navy'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='navy'>" + locale.colours.navy + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='blue'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='blue'>" + locale.colours.blue + "</a></li>" +
                "<li><div class='wysihtml5-colors' data-wysihtml5-command-value='orange'></div><a class='wysihtml5-colors-title' data-wysihtml5-command='foreColor' data-wysihtml5-command-value='orange'>" + locale.colours.orange + "</a></li>" +
              "</ul>" +
            "</div>";
        },

        "date": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-action='insertDate' title='" + locale.date.insert + "' tabindex='-1'><span class='glyphicon glyphicon-calendar'></span></button>" +
            "</div>";
        },

        "code": function(locale, options) {
            var size = (options && options.size) ? ' btn-'+options.size : '';
            return "<div class='btn-group'>" +
                "<button class='btn btn-toolbar" + size + "' data-wysihtml5-action='formatCode' title='" + locale.format.format + "' tabindex='-1'><span class='glyphicon glyphicon-list-alt'></span></button>" +
            "</div>";
        },
    };

    var templates = function(key, locale, options) {
        return tpl[key](locale, options);
    };


    var Wysihtml5 = function(el, options) {
        this.el = el;
        var toolbarOpts = options || defaultOptions;
        for(var t in toolbarOpts.customTemplates) {
          tpl[t] = toolbarOpts.customTemplates[t];
        }
        // this.toolbar = this.append($("<div/>", {'class' : "btn-group", 'style': "display:none"})).createToolbar(el, toolbarOpts);
        this.toolbar = this.createToolbar(el, toolbarOpts);
        this.editor =  this.createEditor(options);

        window.editor = this.editor;

        $('iframe.wysihtml5-sandbox').each(function(i, el){
            $(el.contentWindow).off('focus.wysihtml5').on({
                'focus.wysihtml5' : function(){
                    $('li.dropdown').removeClass('open');
                }
            });
        });
    };

    Wysihtml5.prototype = {

        constructor: Wysihtml5,

        createEditor: function(options) {
            options = options || {};
            
            // Add the toolbar to a clone of the options object so multiple instances
            // of the WYISYWG don't break because "toolbar" is already defined
            options = $.extend(true, {}, options);
            options.toolbar = this.toolbar[0];

            var editor = new wysi.Editor(this.el[0], options);

            if(options && options.events) {
                for(var eventName in options.events) {
                    editor.on(eventName, options.events[eventName]);
                }
            }
            return editor;
        },

        createToolbar: function(el, options) {
            var self = this;
            // var custom_toolbar = $("<div/>", {
            //     'class' : "btn-group custom-wysihtml5-toolbar",
            //     // 'style': "display:none"
            // });
            var toolbar = $("<div/>", {
                'class' : "wysihtml5-toolbar btn-group",
                'style': "display:none"
            });
            // var toolbar = $("<ul/>", {
            //     'class' : "wysihtml5-toolbar",
            //     'style': "display:none"
            // });
            var culture = options.locale || defaultOptions.locale || "en";
            for(var key in defaultOptions) {
                var value = false;

                if(options[key] !== undefined) {
                    if(options[key] === true) {
                        value = true;
                    }
                } else {
                    value = defaultOptions[key];
                }

                if(value === true) {
                    toolbar.append(templates(key, locale[culture], options));

                    if(key === "html") {
                        this.initHtml(toolbar);
                    }

                    if(key === "link") {
                        this.initInsertLink(toolbar);
                    }

                    if(key === "image") {
                        this.initInsertImage(toolbar);
                    }

                    if(key === "create-note") { //yht 2014-10-25
                        this.initCreate(toolbar);
                    }

                    if(key === "save-note") { //yht 2014-10-25
                        this.initSave(toolbar);
                    }

                    if(key === "date") { //yht
                        this.initInsertDate(toolbar);
                    }

                    if(key === "code") { //yht
                        this.initFormatCode(toolbar);
                    }
                }
            }

            if(options.toolbar) {
                for(key in options.toolbar) {
                    toolbar.append(options.toolbar[key]);
                }
            }

            toolbar.find("a[data-wysihtml5-command='formatBlock']").click(function(e) {
                var target = e.target || e.srcElement;
                var el = $(target);
                self.toolbar.find('.current-font').text(el.html());
            });

            toolbar.find("a[data-wysihtml5-command='foreColor']").click(function(e) {
                var target = e.target || e.srcElement;
                var el = $(target);
                self.toolbar.find('.current-color').text(el.html());
            });

            this.el.before(toolbar);
            return toolbar
            // change by yht
            // custom_toolbar.append(toolbar)
            // this.el.before(custom_toolbar);
            
            // return custom_toolbar;
        },

        initHtml: function(toolbar) {
            var changeViewSelector = "button[data-wysihtml5-action='change_view']"; // a2button
            toolbar.find(changeViewSelector).click(function(e) {
                toolbar.find('button.btn').not(changeViewSelector).toggleClass('disabled'); //yht change "a.btn" to "button.btn"
                setTimeout(function(){
                    $('.wysihtml5-sandbox').contents().find('pre code').each(function(i, block) {
                        hljs.highlightBlock(block);
                    });
                }, 1000);
                console.log("Highlight");
            });
        },

        initCreate: function(toolbar) {
            var self = this;
            var createNoteSelector = "button[data-wysihtml5-action='createNote']";
            var caretBookmark;

            toolbar.find(createNoteSelector).click(function(e) {
                if (caretBookmark) {
                  self.editor.composer.selection.setBookmark(caretBookmark);
                  caretBookmark = null;
                }
                this.blur();
            });
        },

        initSave: function(toolbar) {
            var self = this;
            var saveNoteSelector = "button[data-wysihtml5-action='saveNote']";
            var caretBookmark;

            toolbar.find(saveNoteSelector).click(function(e) {
                if (caretBookmark) {
                  self.editor.composer.selection.setBookmark(caretBookmark);
                  caretBookmark = null;
                }
                this.blur();
            });
        },

        initInsertDate: function(toolbar) {
            var self = this;
            var insertDateSelector = "button[data-wysihtml5-action='insertDate']";
            var caretBookmark;

            function twoDigital(num) {
                if(num < 10)
                  return '0' + num
                else
                  return num
            }

            toolbar.find(insertDateSelector).click(function(e) {
                var now = new Date();
                var year = now.getFullYear();
                var month = twoDigital(now.getMonth() + 1);
                var date = twoDigital(now.getDate());
                var hour = twoDigital(now.getHours());
                var minute = twoDigital(now.getMinutes());
                var second = twoDigital(now.getSeconds());
                var now_string = year + "-" + month + "-" + date + " " + hour + ":" + minute + ":" + second;
                if (caretBookmark) {
                  self.editor.composer.selection.setBookmark(caretBookmark);
                  caretBookmark = null;
                }
                self.editor.composer.commands.exec("insertHTML", now_string);
                // self.editor.composer.commands.exec("insertHTML", "<table><tbody><tr><td>content</td></tr></tbody></table>");
                self.editor.currentView.element.focus();
            });
        },

        initFormatCode: function(toolbar) {
            var self = this;
            var formatCodeSelector = "button[data-wysihtml5-action='formatCode']";
            var caretBookmark;

            toolbar.find(formatCodeSelector).click(function(e) {
                if (caretBookmark) {
                  self.editor.composer.selection.setBookmark(caretBookmark);
                  caretBookmark = null;
                }
                self.editor.composer.commands.exec("formatCode");
                self.editor.currentView.element.focus();
            });
        },

        initInsertImage: function(toolbar) {
            var self = this;
            var insertImageModal = toolbar.find('.bootstrap-wysihtml5-insert-image-modal');
            var urlInput = insertImageModal.find('.bootstrap-wysihtml5-insert-image-url');
            var widthInput = insertImageModal.find('.bootstrap-wysihtml5-insert-image-width');
            var heightInput = insertImageModal.find('.bootstrap-wysihtml5-insert-image-height');
            var insertButton = insertImageModal.find('a.btn-primary'); //a2button
            var initialValue = urlInput.val();
            var caretBookmark;

            var insertImage = function() {
                // alert($("input#bootstrap-wysihtml5-insert-image-url").value);
                var url = urlInput.val();
                var imgWidth = widthInput.val();
                var imgHeight = heightInput.val();
                urlInput.val(initialValue);
                self.editor.currentView.element.focus();
                if (caretBookmark) {
                  self.editor.composer.selection.setBookmark(caretBookmark);
                  caretBookmark = null;
                }
                // self.editor.composer.commands.exec("insertImage", url);
                if (imgWidth > 0 && imgHeight == 0) {
                    self.editor.composer.commands.exec('insertImage', { src: url, width: imgWidth});
                } else if (imgWidth > 0 && imgHeight > 0) {
                    self.editor.composer.commands.exec('insertImage', { src: url, width: imgWidth, height: imgHeight});
                } else if (imgWidth == 0 && imgHeight > 0) {
                    self.editor.composer.commands.exec('insertImage', { src: url, height: imgHeight});
                } else {
                    self.editor.composer.commands.exec('insertImage', { src: url});
                }
            };

            urlInput.keypress(function(e) {
                if(e.which == 13) {
                    insertImage();
                    insertImageModal.modal('hide');
                }
            });

            insertButton.click(insertImage);

            insertImageModal.on('shown', function() {
                urlInput.focus();
            });

            insertImageModal.on('hide', function() {
                self.editor.currentView.element.focus();
            });

            toolbar.find('button[data-wysihtml5-command=insertImage]').click(function() { // a2button
                var activeButton = $(this).hasClass("wysihtml5-command-active");

                if (!activeButton) {
                    // alert("OK");
                    self.editor.currentView.element.focus(false);
                    caretBookmark = self.editor.composer.selection.getBookmark();
                    insertImageModal.appendTo('body').modal('show');
                    insertImageModal.on('click.dismiss.modal', '[data-dismiss="modal"]', function(e) {
                        e.stopPropagation();
                    });
                    return false;
                }
                else {
                    return true;
                }
            });
        },

        initInsertLink: function(toolbar) {
            var self = this;
            var insertLinkModal = toolbar.find('.bootstrap-wysihtml5-insert-link-modal');
            var urlInput = insertLinkModal.find('.bootstrap-wysihtml5-insert-link-url');
            var targetInput = insertLinkModal.find('.bootstrap-wysihtml5-insert-link-target');
            var insertButton = insertLinkModal.find('a.btn-primary'); //a2button
            var initialValue = urlInput.val();
            var caretBookmark;

            var insertLink = function() {
                var url = urlInput.val();
                urlInput.val(initialValue);
                self.editor.currentView.element.focus();
                if (caretBookmark) {
                  self.editor.composer.selection.setBookmark(caretBookmark);
                  caretBookmark = null;
                }

                var newWindow = targetInput.prop("checked");
                self.editor.composer.commands.exec("createLink", {
                    'href' : url,
                    'target' : (newWindow ? '_blank' : '_self'),
                    'rel' : (newWindow ? 'nofollow' : '')
                });
            };
            var pressedEnter = false;

            urlInput.keypress(function(e) {
                if(e.which == 13) {
                    insertLink();
                    insertLinkModal.modal('hide');
                }
            });

            insertButton.click(insertLink);

            insertLinkModal.on('shown', function() {
                urlInput.focus();
            });

            insertLinkModal.on('hide', function() {
                self.editor.currentView.element.focus();
            });

            toolbar.find('button[data-wysihtml5-command=createLink]').click(function() { //a2button
                var activeButton = $(this).hasClass("wysihtml5-command-active");

                if (!activeButton) {
                    self.editor.currentView.element.focus(false);
                    caretBookmark = self.editor.composer.selection.getBookmark();
                    insertLinkModal.appendTo('body').modal('show');
                    insertLinkModal.on('click.dismiss.modal', '[data-dismiss="modal"]', function(e) {
                        e.stopPropagation();
                    });
                    return false;
                }
                else {
                    return true;
                }
            });
        }
    };

    // these define our public api
    var methods = {
        resetDefaults: function() {
            $.fn.wysihtml5.defaultOptions = $.extend(true, {}, $.fn.wysihtml5.defaultOptionsCache);
        },
        bypassDefaults: function(options) {
            return this.each(function () {
                var $this = $(this);
                $this.data('wysihtml5', new Wysihtml5($this, options));
            });
        },
        shallowExtend: function (options) {
            var settings = $.extend({}, $.fn.wysihtml5.defaultOptions, options || {}, $(this).data());
            var that = this;
            return methods.bypassDefaults.apply(that, [settings]);
        },
        deepExtend: function(options) {
            var settings = $.extend(true, {}, $.fn.wysihtml5.defaultOptions, options || {});
            var that = this;
            return methods.bypassDefaults.apply(that, [settings]);
        },
        init: function(options) {
            var that = this;
            return methods.shallowExtend.apply(that, [options]);
        }
    };

    $.fn.wysihtml5 = function ( method ) {
        if ( methods[method] ) {
            return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.wysihtml5' );
        }    
    };

    $.fn.wysihtml5.Constructor = Wysihtml5;

    var defaultOptions = $.fn.wysihtml5.defaultOptions = {
        "create-note": true, //yht 2014-10-25
        "save-note": true, //yht 2014-10-25
        "delete-note": false, //yht 2014-10-25
        "download-note": false, //yht 2014-10-25
        "font-styles": true,
        "color": true,
        "emphasis": true,
        "lists": true,
        "html": true,
        "link": true,
        "image": true,
        "date": true, //yht
        "code": true, //yht
        events: {},
        parserRules: {
            classes: {
                // (path_to_project/lib/css/wysiwyg-color.css)
                "wysiwyg-color-silver" : 1,
                "wysiwyg-color-gray" : 1,
                "wysiwyg-color-white" : 1,
                "wysiwyg-color-maroon" : 1,
                "wysiwyg-color-red" : 1,
                "wysiwyg-color-purple" : 1,
                "wysiwyg-color-fuchsia" : 1,
                "wysiwyg-color-green" : 1,
                "wysiwyg-color-lime" : 1,
                "wysiwyg-color-olive" : 1,
                "wysiwyg-color-yellow" : 1,
                "wysiwyg-color-navy" : 1,
                "wysiwyg-color-blue" : 1,
                "wysiwyg-color-teal" : 1,
                "wysiwyg-color-aqua" : 1,
                "wysiwyg-color-orange" : 1
            },
            tags: {
                "b":  {},
                "i":  {},
                "br": {},
                "ol": {},
                "ul": {},
                "li": {},
                "h1": {},
                "h2": {},
                "h3": {},
                "h4": {},
                "h5": {},
                "h6": {},
                "blockquote": {},
                "u": 1,
                "img": {
                    "check_attributes": {
                        "width": "numbers",
                        "alt": "alt",
                        "src": "url",
                        "height": "numbers"
                    }
                },
                "a":  {
                    check_attributes: {
                        'href': "url", // important to avoid XSS
                        'target': 'alt',
                        'rel': 'alt'
                    }
                },
                "span": 1,
                "div": 1,
                // to allow save and edit files with code tag hacks
                "code": 1,
                "pre": 1
                // yht add
                // "p": 1,
                // "table": 1,
                // "tbody": 1,
                // "thead": 1,
                // "tfoot": 1,
                // "tr": 1,
                // "th": 1,
                // "td": 1
            }
        },
        stylesheets: ["/static/css/wysiwyg-color.css"], 
        // stylesheets: ["./lib/css/wysiwyg-color.css"], // (path_to_project/lib/css/wysiwyg-color.css)
        locale: "en"
    };

    if (typeof $.fn.wysihtml5.defaultOptionsCache === 'undefined') {
        $.fn.wysihtml5.defaultOptionsCache = $.extend(true, {}, $.fn.wysihtml5.defaultOptions);
    }

    var locale = $.fn.wysihtml5.locale = {
        en: {
            create_note: {
                create_note: "Create Note"
            },
            save_note: {
                save_note: "Save Note"
            },
            delete_note: {
                delete_note: "Delete Note"
            },
            download_note: {
                download_note: "Download Note"
            },
            font_styles: {
                normal: "Normal text",
                h1: "Heading 1",
                h2: "Heading 2",
                h3: "Heading 3",
                h4: "Heading 4",
                h5: "Heading 5",
                h6: "Heading 6"
            },
            emphasis: {
                bold: "Bold",
                italic: "Italic",
                underline: "Underline"
            },
            lists: {
                unordered: "Unordered list",
                ordered: "Ordered list",
                outdent: "Outdent",
                indent: "Indent"
            },
            link: {
                insert: "Insert link",
                cancel: "Cancel",
                target: "Open link in new window"
            },
            image: {
                insert: "Insert image",
                cancel: "Cancel",
                choose: "Choose File",
                upload: "Upload",
                picture_width: "Width:",
                picture_height: "Height:",
                px: "pixels"
            },
            date: {    //yht
                insert: "Insert date"
            },
            html: {
                edit: "Edit HTML"
            },
            colours: {
                black: "Black",
                silver: "Silver",
                gray: "Grey",
                maroon: "Maroon",
                red: "Red",
                purple: "Purple",
                green: "Green",
                olive: "Olive",
                navy: "Navy",
                blue: "Blue",
                orange: "Orange"
            },
            format: {
                format: "Format Code"
            }
        },
        zh: {
            create_note: {
                create_note: "新建笔记"
            },
            save_note: {
                save_note: "保存笔记"
            },
            delete_note: {
                delete_note: "删除笔记"
            },
            download_note: {
                download_note: "下载笔记"
            },
            font_styles: {
                normal: "普通文本",
                h1: "标题 1",
                h2: "标题 2",
                h3: "标题 3",
                h4: "标题 4",
                h5: "标题 5",
                h6: "标题 6"
            },
            emphasis: {
                bold: "加粗",
                italic: "倾斜",
                underline: "下划线"
            },
            lists: {
                unordered: "无序列表",
                ordered: "有序列表",
                outdent: "减少缩进",
                indent: "增加缩进"
            },
            link: {
                insert: "插入链接",
                cancel: "取消",
                target: "在新的窗口打开链接"
            },
            image: {
                insert: "插入图片",
                cancel: "取消",
                choose: "选择图片",
                upload: "上传",
                picture_width: "宽度:",
                picture_height: "高度:",
                px: "象素",
            },
            date: {    //yht
                insert: "插入时间"
            },
            html: {
                edit: "编辑HTML"
            },
            colours: {
                black: "黑色",
                silver: "银灰色",
                gray: "灰色",
                maroon: "栗色",
                red: "红色",
                purple: "紫色",
                green: "绿色",
                olive: "橄榄色",
                navy: "深蓝色",
                blue: "蓝色",
                orange: "橙色"
            },
            format: {
                format: "格式化代码"
            }
        }

    };

}(window.jQuery, window.wysihtml5);
