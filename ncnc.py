#!/usr/bin/env python3

import os
import requests
from requests.auth import HTTPBasicAuth
import configparser
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2




debug = False


class Ncnc:

    def load_config(self):
        self.configfile_fullpath = os.path.expanduser('~') + "/" + self.configfile

        if os.path.exists(self.configfile_fullpath):
            config = configparser.ConfigParser()
            config.read(self.configfile_fullpath)
            self.ncapiurl = config['nc']['url']
            self.ncapiurl_full = self.ncapiurl + '/index.php/apps/news/api/v1-2'
            self.ncuser = config['nc']['user']
            self.nccred = HTTPBasicAuth(config['nc']['user'], config['nc']['password'])
        else:
            print("there is no config file")
            self.on_pref(None, None)

    def save_config(self, url, u, p):
        config = configparser.ConfigParser()
        config['nc'] = {'url': url,
                    'user': u,
                    'password': p}
        self.configfile_fullpath = os.path.expanduser('~') + "/" + self.configfile
        with open(self.configfile_fullpath, 'w') as cfg:
            config.write(cfg)
        self.load_config()


    # ----------------------
    # convention:
    # GET: parameters in the URL
    # POST: parameters as JSON in the request body
    # PUT: parameters as JSON in the request body
    # DELETE: parameters as JSON in the request body


    def ncget(self, url):
        resp = requests.get(self.ncapiurl_full + url, auth=self.nccred)
        resp.raise_for_status()
        resp_dict = resp.json()
        return resp_dict


    # def ncpost(url, body):
    #    resp = requests.post(self.ncapiurl + url, json=body, auth=self.nccred)
    #    resp.raise_for_status()
    #    resp_dict = resp.json()
    #    return resp_dict


    def ncput(self, url, body):
        resp = requests.put(self.ncapiurl_full + url, json=body, auth=self.nccred)
        resp.raise_for_status()
        resp_dict = resp.json()
        return resp_dict


    # def ncdelete(url, body):
    #    resp = requests.delete(self.ncapiurl + url, json=body, auth=self.nccred)
    #    resp.raise_for_status()
    #    resp_dict = resp.json()
    #    return resp_dict

    # ----------------------


    def get_folders(self):
        return self.ncget("/folders")


    def get_feeds(self):
        return self.ncget("/feeds")


    def get_unread_articles(self):
        return self.ncget("/items?type=3&getRead=false&batchSize=-1")


    def get_starred_articles(self):
        return self.ncget("/items?type=2&getRead=true&batchSize=-1")


    # ----------------------

    # Notify the News app of unread articles:
    # PUT /items/unread/multiple {"items": [1, 3, 5] }


    def notify_unread(self, items):
        payload = {"items": items}
        return self.ncput("/items/unread/multiple", payload)


    # Notify the News app of read articles:
    # PUT /items/read/multiple {"items": [1, 3, 5]}

    def notify_read(self, items):
        payload = {"items": items}
        return self.ncput("/items/read/multiple", payload)


    # Notify the News app of starred articles:
    # PUT /items/starred/multiple {"items": [{"feedId": 3, "guidHash": "hashxyz123"}, ...]}

    def notify_starred(self, items):
        payload = {"items": items}
        return self.ncput("/items/starred/multiple", payload)


    # Notify the News app of unstarred articles:
    # PUT /items/unstarred/multiple {"items": [{"feedId": 3, "guidHash": "hashxyz123"}, ...]}

    def notify_unstarred(self, items):
        payload = {"items": items}
        return self.ncput("/items/unstarred/multiple", payload)


    # Get new items and modified items:
    # GET /items/updated?lastModified=12123123123&type=3

    def get_new_and_modified_items(self, lastid):
        return self.ncget("/items/updated?lastModified=" + str(lastid) + "&type=3")


    ##############################################################################

    def sync_folders(self):
        self.folders_dict.clear()

        try:
            self.folders_json_ncdata = self.get_folders()

            # print(resp_dict)
            folder_list = self.folders_json_ncdata['folders']
            # print(folder_list)
            for fdict in folder_list:
                # print(fmap)
                # print(str(fmap['id']) + " " + fmap['name'])
                self.folders_dict[fdict['id']] = fdict['name']
            print(self.folders_dict)
        except requests.exceptions.HTTPError as e:
            print("Bad HTTP status code:", e)
        except requests.exceptions.RequestException as e:
            print("Network error:", e)


    def sync_feeds(self):
        self.feeds_dict.clear()
        self.feeds_by_folders_dict.clear()

        try:
            self.feeds_json_ncdata = self.get_feeds()

            # print(resp_dict)
            feed_list = self.feeds_json_ncdata['feeds']
            # print(folder_list)
            for fdict in feed_list:
                # print(fmap)
                # print(str(fmap['id']) + " " + fmap['name'])
                # self.feeds_dict[fdict['id']] = fdict['title']
                self.feeds_dict[fdict['id']] = fdict
                self.feeds_by_folders_dict.setdefault(fdict['folderId'], list())
                self.feeds_by_folders_dict[fdict['folderId']].append(fdict['id'])
            print("->   self.feeds_dict     ", self.feeds_dict)
            print("->   self.feeds_by_folders_dict     ", self.feeds_by_folders_dict)
        except requests.exceptions.HTTPError as e:
            print("Bad HTTP status code:", e)
        except requests.exceptions.RequestException as e:
            print("Network error:", e)


    def sync_unread_articles(self):
        self.unreaditems_dict.clear()
        self.unreaditems_by_feeds_dict.clear()

        try:
            # if (self.lastItemdId == -1):
            #    self.unreaditmes_json_ncdata = get_unread_articles()
            # else:
            #    self.unreaditmes_json_ncdata = get_new_and_modified_items(self.lastItemdId)
            self.unreaditmes_json_ncdata = self.get_unread_articles()

            unreaditems_list = self.unreaditmes_json_ncdata['items']
            self.lastItemdId = unreaditems_list[0]["lastModified"]

            print("lastModified == ", self.lastItemdId)

            for idict in unreaditems_list:
                self.unreaditems_dict[idict['id']] = idict
                self.unreaditems_by_feeds_dict.setdefault(idict['feedId'], list())
                self.unreaditems_by_feeds_dict[idict['feedId']].append(idict['id'])
        except requests.exceptions.HTTPError as e:
            print("Bad HTTP status code:", e)
        except requests.exceptions.RequestException as e:
            print("Network error:", e)


    def run_sync(self):
        if self.ncapiurl_full == '' or self.nccred == '':
            print("Not configured.   self.ncapiurl == '' or self.nccred == ''")
            return

        if len(self.read_items) > 0:
            self.notify_read(self.read_items)
            self.read_items.clear()

        self.sync_folders()
        self.sync_feeds()
        self.sync_unread_articles()

        # build_firstpane()

        self.selected_folder = -1
        self.selected_feed = -1


    # TODO: sort the folder list
    def build_firstpane(self):
        if self.ncapiurl_full == '' or self.nccred == '':
            print("Not configured.   self.ncapiurl == '' or self.nccred == ''")
            return

        self.firstpane_model = Gtk.TreeStore(str, int, int, int)

        # feeds with unread items # items -> feeds -> self.folders_dict
        ufeeds = self.unreaditems_by_feeds_dict.keys()
        print("ufeeds  ==  ", ufeeds)
        # folders with 'feeds with unread items'
        ufolders = []
        for feedid in ufeeds:
            ufolders.append(self.feeds_dict[feedid]['folderId'])
        print("folders with unread items (ufolders) ==  ", ufolders)

        folder_unreaditems_count = {}
        feeds_unreaditems_count = {}
        for key, value in self.folders_dict.items():
            if key in ufolders:
                for feedid in self.feeds_by_folders_dict[key]:
                    if feedid in ufeeds:
                        feeds_unreaditems_count[feedid] = len(self.unreaditems_by_feeds_dict[feedid])
                        folder_unreaditems_count.setdefault(key, 0)
                        folder_unreaditems_count[key] += feeds_unreaditems_count[feedid]

        total_unreaditems_count = 0
        for i in folder_unreaditems_count.values():
            total_unreaditems_count += i
        rootiter = self.firstpane_model.append(None, [str("All"), -1, -1, total_unreaditems_count])

        for key, value in self.folders_dict.items():
            if key in ufolders:
                # iter = self.firstpane_model.append(rootiter, [str(value)])
                iter = self.firstpane_model.append(rootiter, [str(value), key, -1, folder_unreaditems_count[key]])
                # print("---> ", self.feeds_by_folders_dict[key])
                # if (key in self.feeds_by_folders_dict):
                for feedid in self.feeds_by_folders_dict[key]:
                    if feedid in ufeeds:
                        self.firstpane_model.append(iter, [str(self.feeds_dict[feedid]['title']), key, feedid,
                                                           feeds_unreaditems_count[feedid]])
                        # print("f == ", feedid)
                        # print("feed == ", self.feeds_dict[int(feedid)])
        # clear treeview
        for c in self.firstpane_treeview.get_columns():
            self.firstpane_treeview.remove_column(c)

        ren1 = Gtk.CellRendererText()
        col1 = Gtk.TreeViewColumn('FF', ren1, text=0)
        col1.add_attribute(ren1, 'text', 0)
        # col1.set_fixed_width(400)
        col1.set_max_width(300)
        self.firstpane_treeview.append_column(col1)

        ren2 = Gtk.CellRendererText()
        col2 = Gtk.TreeViewColumn('FolderId', ren2, text=1)
        col2.add_attribute(ren2, 'text', 0)
        if (not debug):
            col2.set_visible(False)
        self.firstpane_treeview.append_column(col2)

        ren3 = Gtk.CellRendererText()
        col3 = Gtk.TreeViewColumn('FeedId', ren3, text=2)
        col3.add_attribute(ren3, 'text', 0)
        if (not debug):
            col3.set_visible(False)
        self.firstpane_treeview.append_column(col3)

        ren4 = Gtk.CellRendererText()
        col4 = Gtk.TreeViewColumn('Unread', ren4, text=3)
        col4.add_attribute(ren4, 'text', 0)
        self.firstpane_treeview.append_column(col4)

        self.firstpane_treeview.set_model(self.firstpane_model)
        self.firstpane_treeview.expand_all()


    def build_secondpane(self):
        if self.ncapiurl_full == '' or self.nccred == '':
            print("Not configured.   self.ncapiurl == '' or self.nccred == ''")
            return

        self.secondpane_model = Gtk.ListStore(str, int, int)

        if (self.selected_folder == -1):
            # All selected
            for key, value in self.unreaditems_dict.items():
                self.secondpane_model.append(
                    [self.unreaditems_dict[key]['title'],
                     self.unreaditems_dict[key]['feedId'],
                     self.unreaditems_dict[key]['id']])
        elif (self.selected_feed == -1):
            # Folder seleccted
            feeds = self.feeds_by_folders_dict[self.selected_folder]
            for f in feeds:
                if f in self.unreaditems_by_feeds_dict:
                    for i in self.unreaditems_by_feeds_dict[f]:
                        self.secondpane_model.append(
                            [self.unreaditems_dict[i]['title'],
                             self.unreaditems_dict[i]['feedId'],
                             self.unreaditems_dict[i]['id']])
        else:
            # Feed selected
            for i in self.unreaditems_by_feeds_dict[self.selected_feed]:
                self.secondpane_model.append([self.unreaditems_dict[i]['title'],
                                              self.unreaditems_dict[i]['feedId'],
                                              self.unreaditems_dict[i]['id']])
        # clear treeview
        for c in self.secondpane_treeview.get_columns():
            self.secondpane_treeview.remove_column(c)

        # TODO: set backroud and/rot bold text
        # cell.set_property("background", "orange")

        ren1 = Gtk.CellRendererText()
        col1 = Gtk.TreeViewColumn('title', ren1, text=0)
        col1.add_attribute(ren1, 'text', 0)
        # col1.set_fixed_width(400)
        col1.set_max_width(300)
        self.secondpane_treeview.append_column(col1)

        ren2 = Gtk.CellRendererText()
        col2 = Gtk.TreeViewColumn('itemid', ren2, text=1)
        col2.add_attribute(ren2, 'text', 0)
        if (not debug):
            col2.set_visible(False)
        self.secondpane_treeview.append_column(col2)

        ren3 = Gtk.CellRendererText()
        col3 = Gtk.TreeViewColumn('itemid', ren3, text=2)
        col3.add_attribute(ren3, 'text', 0)
        if (not debug):
            col3.set_visible(False)
        self.secondpane_treeview.append_column(col3)

        self.secondpane_treeview.set_model(self.secondpane_model)


    def build_thirdpane(self):
        self.thirdpane_webview = WebKit2.WebView()
        self.thirdpane_scrolled_window.add(self.thirdpane_webview)


    def on_sync(self, button, name):
        self.run_sync()
        print("Button", name, "was clicked")
        self.build_firstpane()
        # clear treeview
        for c in self.secondpane_treeview.get_columns():
            self.secondpane_treeview.remove_column(c)


    def on_pref(self, action, param):
        pref_dial_builder = Gtk.Builder()
        pref_dial_builder.add_from_file("ui/pref_dialog.glade")

        self.pref_dialog = pref_dial_builder.get_object("pdialog")

        pref_ok_button = pref_dial_builder.get_object("prefok")
        pref_ok_button.connect("clicked", self.on_pref_ok, "ok")

        self.pref_url = pref_dial_builder.get_object("url_entry")
        self.pref_url.set_text(self.ncapiurl)
        self.pref_usr = pref_dial_builder.get_object("username_entry")
        self.pref_usr.set_text(self.ncuser)
        self.pref_pswd = pref_dial_builder.get_object("password_entry")

        self.pref_dialog.present()


    def on_pref_ok(self, button, msg):
        print("Pref OK", self.pref_url.get_text(), self.pref_usr.get_text(), self.pref_pswd.get_text())
        self.save_config(self.pref_url.get_text(), self.pref_usr.get_text(), self.pref_pswd.get_text())
        self.pref_dialog.destroy()

        self.on_sync(self, None, msg)


    def on_about(self, action, param):
        about_dial_builder = Gtk.Builder()
        about_dial_builder.add_from_file("ui/about_dialog.glade")
        self.about_dialog = about_dial_builder.get_object("about_dialog")
        about_ok_button = about_dial_builder.get_object("about_ok")
        about_ok_button.connect("clicked", self.on_about_ok, "ok")
        self.about_dialog.present()


    def on_about_ok(self, button, msg):
        self.about_dialog.destroy()


    def on_selection_1pane(self, selection):
        print("1 pane clicked")
        treestore, iter = selection.get_selected()
        if iter:
            path = treestore.get_path(iter).to_string()
            tn = treestore.get_value(iter, 0)  # Title/Name
            fo = treestore.get_value(iter, 1)  # FolderId
            fe = treestore.get_value(iter, 2)  # FeedId
            uc = treestore.get_value(iter, 3)  # UnreadCount
            print(path, tn, fo, fe, uc)
            self.selected_folder = fo
            self.selected_feed = fe
        self.build_secondpane()


    def on_selection_2pane(self, selection):
        print("2 pane clicked")
        treestore, iter = selection.get_selected()
        if iter:
            path = treestore.get_path(iter).to_string()
            tn = treestore.get_value(iter, 0)  # Title/Name
            fe = treestore.get_value(iter, 1)  # FeedId
            ii = treestore.get_value(iter, 2)  # ItemId
            print(path, tn, ii, fe)

            # print("BODY == ", self.unreaditems_dict[ii]['body'])
            self.thirdpane_webview.load_html(self.unreaditems_dict[ii]['body'])
            self.read_items.append(ii)
            print("self.read_items = ", self.read_items)


    ###################################################################################################################

    def __init__(self):
        self.configfile = ".ncnc.cfg"
        self.read_items = []

        # self.ncapiurl = ''
        # self.ncapiurl_full = ''
        # self.ncuser = ''
        # self.nccred = ''

        self.folders_json_ncdata = {}
        self.folders_dict = {}  # folderid-fordername

        self.feeds_json_ncdata = {}
        self.feeds_dict = {}  # feedid-feedtitle
        self.feeds_by_folders_dict = {}  # folderid-[feedids]

        self.unreaditmes_json_ncdata = {}
        self.unreaditems_dict = {}  # itemid-{itemfields}
        self.unreaditems_by_feeds_dict = {}  # feedid-[itemids]

        self.lastItemdId = -1
        self.selected_folder = -1
        self.selected_feed = -1

        # self.pref_dialog = ''
        # self.about_dialog = ''
        # self.pref_url = ''
        # self.pref_usr = ''
        # self.pref_pswd = ''


        builder = Gtk.Builder()
        builder.add_from_file("ui/mainwindow.glade")
        self.window = builder.get_object("window1")
        self.window.connect("destroy", Gtk.main_quit)
        self.window.set_title("Nextcloud News Client (ncnc)")
        sync_button = builder.get_object("sync_button")
        sync_button.connect("clicked", self.on_sync, "sync")
        pref_button = builder.get_object("pref_menuitem")
        pref_button.connect("activate", self.on_pref, "sync")
        about_button = builder.get_object("about_menuitem")
        about_button.connect("activate", self.on_about, "sync")

        # 1st pane. Folders and Feeds.
        self.firstpane_treeview = builder.get_object("firstpane_treeview")
        selection = self.firstpane_treeview.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect("changed", self.on_selection_1pane)

        # 2nd pane. Items (articles)
        self.secondpane_treeview = builder.get_object("secondpane_treeview")
        selection = self.secondpane_treeview.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect("changed", self.on_selection_2pane)

        # 3rd pane. WebView (article)
        self.thirdpane_scrolled_window = builder.get_object("thirdpane_scrwindows")

        self.load_config()
        self.run_sync()
        self.build_firstpane()
        self.build_secondpane()
        self.build_thirdpane()

        self.window.show_all()


if __name__ == "__main__":
    main = Ncnc()
    Gtk.main()
