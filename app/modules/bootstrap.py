# -*- coding: utf-8 -*-
'''
Created on 2013-10-31
@summary:
@author: YangHaitao
'''

import tornado.web
import logging
import math
from utils.html import add_params_to_url

from config import CONFIG

LOG = logging.getLogger(__name__)


class SetImg(tornado.web.UIModule):
    def render(self, sha1):
        pass

class ShareTable(tornado.web.UIModule):
    def render(self, sharedict):
        def construct_th(file_title_list):
            html = ""
            html += '<tr>'
            for title in file_title_list[:-1]:
                html += '<th style="min-width: 40px; font-size: 12px; white-space:wrap;">' + self.locale.translate(title).encode("utf-8") + '</th>'
            html += '<th style="width: 120px; min-width: 60px; font-size: 12px; white-space:wrap;">' + self.locale.translate(file_title_list[-1]).encode("utf-8") + '</th>'
            html += '</tr>'
            return html

        def construct_tr(file_info_list):
            html = ""
            html += '<tr>'
            file_name = file_info_list[0]
            for info in file_info_list:
                html += '''<td style='min-width: 40px;'>
                                <p style='min-width: 40px; font-size: 12px; white-space:wrap;'>%s</p>
                           </td>
                        '''%info
            html += '''<td><button type="button" id="%s" class="btn span6" style="min-width: 55px;" onclick="download_file('%s')">'''%(file_name, file_name) + self.locale.translate("Download").encode("utf-8")
            html += '''</button>'''
            html += '''<button type="button" id="%s" class="btn span6" style="min-width: 55px;" onclick="delete_file('%s')">'''%(file_name, file_name) + self.locale.translate("Delete").encode("utf-8")
            html += '''</button></td>'''
            html += '</tr>'
            return html

        html = ""
        html += '<table id="fileinfo" name="fileinfo" class="table table-striped table-bordered table-condensed">'
        html += construct_th(sharedict['file_title_list'])
        for file_info_list in sharedict['file_info_list']:
            html += construct_tr(file_info_list)
        html += '</table>'
        return html

class NotesList(tornado.web.UIModule):
    def render(self, elements):
        def construct_li(element):
            # word-break:break-all;word-wrap:break-word; 
            html = ""  #element.url
            # html += '<li id="' + element.sha1 + '" style="margin-bottom: 0px; text-align: left; list-style: none outside none;">'
            html += '<a href = "" class="note_list_item list-group-item" id="a_%s" onclick="change_href(\'a_%s\',\'%s\',\'%s\')">'%(element.noteid, element.noteid, element.noteid, element.notetype)
            html += "<p class='col-md-12 note_item_title'>" + element.file_title + "</p>"
            html += "<div class='col-md-12 note_description_div'><p class='note_item_description'>" + element.description + "</p></div>"
            html += "<p class='note_item_datetime'><span class='pull-left'>" + element.created_at + "</span>" + "&nbsp;<span class='pull-right'>" + element.updated_at + "</span></p>"
            html += "</a>"
            # html += "</li>"
            return html

        html = ""
        for element in elements:
            html += construct_li(element)
        return html

class RichNotesList(tornado.web.UIModule):
    def render(self, elements):
        def construct_li(element):
            # word-break:break-all;word-wrap:break-word; 
            html = ""  #element.url
            # html += '<li id="' + element.sha1 + '" style="margin-bottom: 0px; text-align: left; list-style: none outside none;">'
            html += '<a href = "" class="note_list_item list-group-item" id="a_%s" onclick="change_href(\'a_%s\',\'%s\',\'%s\')">'%(element.noteid, element.noteid, element.noteid, element.notetype)
            html += "<p class='col-md-12 note_item_title'>" + element.file_title + "</p>"
            html += "<div class='col-md-12 note_description_div'><p class='note_item_description'>" + element.description + "</p></div>"
            html += "<p class='note_item_datetime'><span class='pull-left'>" + element.created_at + "</span>" + "&nbsp;<span class='pull-right'>" + element.updated_at + "</span></p>"
            html += "</a>"
            # html += "</li>"
            return html

        html = ""
        for element in elements:
            html += construct_li(element)
        return html

class ThumbnailCollections(tornado.web.UIModule):
    def render(self, elements, column_count = 1):
        '''
          @summary: construct Thumbnail Collections

          @param elements: a list of ThumbnailItem
          @param column_count: count of the column
          @result:
        '''
        def construct_li(element):
            html = ""
            html += '<li class="item_li">'
            html += "<a id='html' href = '" + element.url + "' target='_blank'>"
            html += "<p class='item_title'>" + element.title + "</p>"
            html += "</a>"
            html += "<div class='item_excerpts_div'><p class='item_excerpts'>" + element.excerpts + "</p></div>"
            html += "<p class='item_description'>" + self.locale.translate("Storage time") + ": " + element.description + "</p>"
            for text, link in element.add_links:
                html += "&nbsp;&nbsp;&nbsp;&nbsp;"
                # print text
                html += "<a href = " + link + " target='_blank'>" + text + "</a>"
            html += "</li>"
            return html

        import math
        if column_count < 0:
            column_count = 4
        if column_count >= 12:
            column_count = 12

        html = ""
        html += """
         <div class="row">
        """
        # calculate max row number
        total_count = len(elements)
        row_count = int(math.ceil(total_count * 1.0 / column_count))

        for i in xrange(column_count):
            html += """
                <div class="col-md-%s">
                    <ul class="list-unstyled">
                """ %(12 / column_count)
            for j in xrange(row_count):
                current_index = i * row_count + j
                if current_index < total_count:
                    element = elements[current_index]
                    html += construct_li(element)
                else:
                    break
            html += """
                    </ul>
                </div>
            """
        html += """
        </div>
        """
        return html

class Paginator(tornado.web.UIModule):
    '''
    @summary: create paginator

    '''
    def render(self, total_count, current_page = 1, items_per_page = 10, typed_search_string = "", query = ""):
        '''
        @summary:

        @param total_page: total page number
        @param current_page: current page number

        @result:
        '''
        def format_li(url, page_number, active = False):
            url_tmp = ""
            url_tmp = add_params_to_url(url, dict({"page": page_number}))
            if active:
                return "<li class=\"active\"><a href=\"%s\">%s</a></li>\n" %(url_tmp, page_number)
            else:
                return "<li><a href=\"%s\">%s</a></li>\n" %(url_tmp, page_number)
            return ""

        url = "/search?q=%s&query=%s"%(typed_search_string, query)
        if total_count <= 0:
            return ""
        # when there is only one page, not need to display the paginator
        total_page = int(math.ceil(total_count * 1.0/ items_per_page))
        if total_page <= 1:
            return ""
        html = ""
        html = "<div id='paginator' class='row'>\n"
        html += "<ul class=\"pagination\">\n"
        max_pages_pre = 5
        max_pages_post = 4

        if current_page <= max_pages_pre:
            max_pages_pre = current_page - 1
        if current_page + max_pages_post >= total_page:
            max_pages_post = total_page - current_page

        if current_page > 1:
            url_pre_page = add_params_to_url(url, dict({"page": current_page - 1}))
            html += "<li><a href=\"%s\">&laquo;</a></li>\n"%(url_pre_page,)

        # construct previous page links
        for i in xrange(max_pages_pre):
            html += format_li(url, current_page - max_pages_pre + i)
        # construct current page link
        html += format_li(url, current_page, True)
        # construct post page links
        for i in xrange(max_pages_post):
            html += format_li(url, current_page + 1 + i)
        # construct next page link
        if current_page < total_page - 1:
            url_next_page = add_params_to_url(url, dict({"page": current_page + 1}))
            html += "<li><a href=\"%s\">&raquo;</a></li>\n"%(url_next_page,)
        html += "</ul>\n"
        html += "</div>\n"
        return html
