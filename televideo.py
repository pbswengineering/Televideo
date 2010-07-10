#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

# Copyright 2009 Paolo Bernardi <villa.lobos@tiscali.it>
#
# This program is under the MIT/X11 license terms. The license
# text together with a brief Italian introduction is written
# in the COPYING file.
#
# Basically this utility allows you to browse through RAI's Televideo
# by using an handy graphical interface; it's just a scraper over
# www.televideo.rai.it.
#
# SOME TERMINOLOGY:
#   page: the Televideo has pages :-P
#   part: a sub page


import gtk, os, re, socket, sys, threading, urllib

# Where are the images, gtkbuilder xml & co.?
# They can be in /usr/share/televideo or in the current directory
if os.path.exists('/usr/share/televideo/televideo.xml'):
	RESOURCE_PATH = '/usr/share/televideo/'
else:
	RESOURCE_PATH = os.path.abspath(sys.path[0])

# Some utilities

def check_external_programs():
    """Checks if any required external program is missing."""

    convert = os.system('which convert > /dev/null') == 0

    # This structure allows for an easily extensible function;
    # it's here because at first, together with convert I also
    # used axel or something like that.
    error = ''
    if not convert: error += 'Dovresti installare ImageMagik.\n'

    ok = convert
    if not ok:
        m = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                buttons=gtk.BUTTONS_CLOSE,
                                message_format=error)
        m.set_title('Manca qualcosa...')
        m.run()
        m.destroy()

    return ok


def resize_png(width, height, source, destination):
    """Resizes a png images where source is the original image
    file name, destination the resized image file name and
    width and height are the new image sizes."""

    os.system('convert -resize %sx%s "%s" "%s"' % (width, height, source, destination))


def http_get(url):
    """Fetches the data from the given http url, trying three times
    before giving up."""

    count = 0
    result = ''
    ok = False
    while count < 3 and not ok:
        try:
            result = urllib.urlopen(url).read()
            ok = True
        except:
            count += 1
    return result


def no_problem_unlink(file):
    """Deletes the given file without raising errors if the deletion
    couldn't be done."""

    try:
        os.unlink(file)
    except:
        # Nothing to delete?... No problem
        pass


class TelevideoWebClient:
    """Manages fetching the online televideo pages."""

    RESIZE_FACTOR = 1.4

    # For these see www.televideo.rai.it
    ORIGINAL_WIDTH = 360
    ORIGINAL_HEIGHT = 400

    def __init__(self, directory):
        """Resets the default fields values and creates the
        temporary directory."""

        self.baseUrl = 'http://www.televideo.rai.it/televideo/pub/tt4web/Nazionale'
        self.mapUrl = 'http://www.televideo.rai.it/televideo/pub/pagina.jsp?p=PAGE&s=PART&r=Nazionale&idmenumain=2&pagetocall=pagina.jsp'
        self.directory = directory
        self.default = directory + '/not-found.png'
        self.loading = directory + '/loading.png'
        self.download = directory + '/pagina.png'
        self.factor_file = directory + '/resize_factor'
        self.fetched = ''

        # If the temporary directory doesn't exist, creates it
        if not os.path.exists(directory):
            os.mkdir(directory)

        if not os.path.exists(self.factor_file):
            f = open(self.factor_file, 'w')
            f.write(str(self.RESIZE_FACTOR) + '\n')
            f.close()
        else:
            f = open(self.factor_file, 'r')
            self.RESIZE_FACTOR = float(f.read())
            f.close()

        self.set_resize_factor(self.RESIZE_FACTOR)

    def set_resize_factor(self, factor):
        """Adjusts the image resize factor, eventually redisplaying
        the currently visualized picture (the televideo page)."""

        self.RESIZE_FACTOR = factor
        f = open(self.factor_file, 'w')
        f.write(str(factor) + '\n')
        f.close()
        width = self.ORIGINAL_WIDTH * factor
        height = self.ORIGINAL_HEIGHT * factor
        src = RESOURCE_PATH
        orig_default = src + '/not-found.png'
        orig_loading = src + '/loading.png'
        resize_png(width, height, orig_default, self.default)
        resize_png(width, height, orig_loading, self.loading)

    def fetch_map(self, page, part):
        """Fetches the mouse click mapping informations from the
        Televideo selected page in order to respond to clicks on
        parts of the page.
        Returns a map as tuple's list; each tuple is
        (x1, y1, x2, y2, page, part)"""

        source = self.mapUrl.replace('PAGE', str(page)).replace('PART', str(part))
        html = http_get(source).replace("\n", "")
        map_string = html.split('<map name="map1">')[1].split('</map>')[0]
        p = re.compile('<area COORDS="(?P<x1>\\d+),(?P<y1>\\d+),(?P<x2>\\d+),(?P<y2>\\d+),?" href="popupTelevideo.jsp\?p=(?P<page>\\d+)&s=(?P<part>\\d+)&r=Nazionale">')
        map = [(int(a[0]) * self.RESIZE_FACTOR, int(a[1]) * self.RESIZE_FACTOR, int(a[2]) * self.RESIZE_FACTOR, int(a[3]) * self.RESIZE_FACTOR, int(a[4]), int(a[5]) + 1) for a in p.findall(map_string)]
        return map

    def fetch(self, page, part):
        """Fetches the given Televideo page."""

        file = '/page-' + str(page)
        if part > 1:
            file += '.' + str(part)
        file += '.png'

        source = self.baseUrl + file
        destination = self.download

        no_problem_unlink(destination + '-small')
        no_problem_unlink(destination)

        image = http_get(source)
        if image.find('Not Found') == -1 and len(image) > 0:
            f = open(destination + '-small', 'w')
            f.write(image)
            f.close()

        if os.path.exists(destination + '-small') and os.path.getsize(destination + '-small') > 0:
            width = self.ORIGINAL_WIDTH * self.RESIZE_FACTOR
            height = self.ORIGINAL_HEIGHT * self.RESIZE_FACTOR
            resize_png(width, height, destination + '-small', destination)
            return destination
        else:
            return self.default


class Televideo:
    """Manages the graphical interface."""

    def on_window_destroy(self, widget, data=None):
        """It just quits."""
        gtk.main_quit()

    def on_pageNumber_activate(self, widget, data=None):
        """Responds to user modification of the page text box."""
        self.page = int(self.pageNumber.get_text())
        self.part = 1
        self.refresh()

    def on_pagePart_activate(self, widget, data=None):
        """Responds to user modification of the page part (sub page)
        text box."""

        self.part = int(self.pagePart.get_text())
        self.refresh()

    def on_btPagePrev_clicked(self, widget, data=None):
        """Responds to the user click on the previous page button."""

        if self.page > 1:
            self.page -= 1
            self.part = 1
            self.refresh()

    def on_btSubPagePrev_clicked(self, widget, data=None):
        """Responds to the user click on the previous sub page
        button."""

        if self.part > 1:
            self.part -= 1
            self.refresh()

    def on_btSubPageNext_clicked(self, widget, data=None):
        """Responds to the user click on the next sub page button."""

        self.part += 1
        self.refresh()

    def on_btPageNext_clicked(self, widget, data=None):
        """Responds to the user click on the next page button."""

        self.page += 1
        self.part = 1
        self.refresh()

    def on_eventBox_button_press_event(self, widget, data=None):
        """Responds to the user click on the page image."""

        if self.enabled == True:
            for m in self.map:
                x1, y1, x2, y2, xpage, xpart = m
                if x1 <= data.x <= x2 and y1 <= data.y <= y2:
                    self.page = xpage
                    self.part = xpart
                    self.refresh()
                    break

    def on_eventBox_motion_notify_event(self, widget, data=None):
        """Displays an hand cursor if the mouse pointer is over a
        clickable spot."""

        if self.enabled == True:
            found = False
            for m in self.map:
                x1, y1, x2, y2, xpage, xpart = m
                if x1 <= data.x <= x2 and y1 <= data.y <= y2:
                    found = True
                    break
            if found == True:
                widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
            else:
                widget.window.set_cursor(None)

    def on_btHelp_clicked(self, widget, data=None):
        m = gtk.MessageDialog(type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_CLOSE)
        m.set_title('Scorciatoie da tastiera')
        m.set_markup("""<u><b>CONTROLLO DA TASTIERA</b></u>

<b>←</b>\t pagina precedente
<b>→</b>\t pagina successiva
<b>↑</b>\t sotto-pagina precedente
<b>↓</b>\t sotto-pagina successiva

<b>－</b>\t rimpicciolisci
<b>+</b>\t ingrandisci

<b>F5</b>\t ricarica la pagina corrente
<b>Q</b>\t esci dal programma


<u><b>NOTA:</b></u>
I numeri di pagina sono cliccabili a mo' di collegamenti ipertestuali.
""")
        m.run()
        m.destroy()

    def on_window_key_press_event(self, widget, data=None):
        """Handles the keyboard events."""

        if not self.enabled:
            return

        if data.keyval == gtk.keysyms.plus:
            self.webclient.set_resize_factor(self.webclient.RESIZE_FACTOR + 0.1)
            self.refresh()
        elif data.keyval == gtk.keysyms.minus:
            if self.webclient.RESIZE_FACTOR > 1.2:
                self.webclient.set_resize_factor(self.webclient.RESIZE_FACTOR - 0.1)
                self.refresh()
        elif data.keyval == gtk.keysyms.F5:
            self.refresh()
        elif data.keyval == gtk.keysyms.Left:
            self.on_btPagePrev_clicked(widget)
        elif data.keyval == gtk.keysyms.Right:
            self.on_btPageNext_clicked(widget)
        elif data.keyval == gtk.keysyms.Up:
            self.on_btSubPagePrev_clicked(widget)
        elif data.keyval == gtk.keysyms.Down:
            self.on_btSubPageNext_clicked(widget)
        elif data.keyval in (gtk.keysyms.q, gtk.keysyms.Q):
            self.on_window_destroy(widget)

    def __init__(self):
        """Loads the graphical interface and sets it up."""

        try:
            builder = gtk.Builder()
            builder.add_from_file(RESOURCE_PATH + '/televideo.xml')
        except:
            print 'Failed to load UI XML file'
            sys.exit(1)

        # Get the widgets which will be referenced here
        self.window = builder.get_object('window')
        self.vbox = builder.get_object('vbox')
        self.pageNumber = builder.get_object('pageNumber')
        self.pagePart = builder.get_object('pagePart')
        self.btPagePrev = builder.get_object('btPagePrev')
        self.btSubPagePrev = builder.get_object('btSubPagePrev')
        self.btSubPageNext = builder.get_object('btSubPageNext')
        self.btPageNext = builder.get_object('btPageNext')

        # Minor adjustments
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

        # GTK and Glade sucks
        self.eventBox = gtk.EventBox()
        self.eventBox.connect('button-press-event',self.on_eventBox_button_press_event)
        self.eventBox.connect('motion-notify-event',self.on_eventBox_motion_notify_event)
        self.eventBox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        self.eventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.POINTER_MOTION_MASK)
        self.vbox.add(self.eventBox)

        self.pageImage = gtk.Image()
        self.pageImage.set_padding(5, 5)
        self.eventBox.add(self.pageImage)

        # Zoom
        self.window.connect('key-press-event', self.on_window_key_press_event)

        # Connects the signals with the current class methods
        builder.connect_signals(self)

        # Stuff needed to do the dirty job
        self.enabled = False
        self.page = 100
        self.part = 1
        self.webclient = TelevideoWebClient(os.getenv('HOME') + '/.televideo-tmp')
        self.pageImage.set_from_file(self.webclient.loading)
        self.refresh()

    def enable_controls(self, boolean):
        """Enables or disables the user controls."""

        self.enabled = boolean
        self.pageNumber.set_sensitive(boolean)
        self.pagePart.set_sensitive(boolean)
        self.btPagePrev.set_sensitive(boolean)
        self.btSubPagePrev.set_sensitive(boolean)
        self.btSubPageNext.set_sensitive(boolean)
        self.btPageNext.set_sensitive(boolean)

    def refresh(self):
        """Displays the current page image in an asynchronous way."""

        if self.eventBox.window != None:
            self.eventBox.window.set_cursor(None)
        self.enable_controls(False)
        threading.Thread(target=self.thread_refresh).start()

    def thread_refresh(self):
        """Displays the current page image in a synchronous way."""

        self.pageNumber.set_text(str(self.page))
        self.pagePart.set_text(str(self.part))
        self.pageImage.set_from_file(self.webclient.loading)

        file = self.webclient.fetch(self.page, self.part)
        self.map = ()
        if file != self.webclient.default:
            self.map = self.webclient.fetch_map(self.page, self.part)
        self.pageImage.set_from_file(file)
        self.enable_controls(True)

    def main(self):
        """Starts the main loop."""

        self.window.show_all()
        gtk.main()


if __name__ == '__main__':
    if check_external_programs():
        # We have the software, but is there an Internet link?
        try:
            socket.gethostbyname('www.google.com')
        except:
            m = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE)
            m.set_title('Errore')
            m.set_markup('Per usare questo programma devi essere connesso ad Internet.')
            m.run()
            m.destroy()
            sys.exit(1)

        gtk.gdk.threads_init()
        Televideo().main()
