# -*- coding: utf-8 -*-

# from vk.bulkmove import _
from Products.Five.browser import BrowserView
from zope.interface import implementer
from zope.interface import Interface
from Products.statusmessages.interfaces import IStatusMessage
from zope.component.hooks import getSite
from plone import api

# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class IBulkMoveView(Interface):
    """Marker Interface for IBulkMoveView"""


@implementer(IBulkMoveView)
class BulkMoveView(BrowserView):
    # If you want to define a template here, please remove the template from
    # the configure.zcml registration of this view.
    # template = ViewPageTemplateFile('bulk_move_view.pt')

    def __call__(self):
        # Implement your own actions:

        ## Formular soll in mehreren Schritten abgearbeitet werden
        ## 1. Hochladen der Datei
        ## 2. Anzeige des Ergebnisses der Prüfung auf existierende Pfade
        ## 3. Verschieben nach Bestätigung durchführen
        ##
        ### Problematik ist, dass die aus der Datei eingelesen Daten (die actions) bei der Bestätigung
        ### nochmals mitgesandt werden müssen - da die View neu augerufen wird.


        # TODO ggf. noch Verwendung neuer id implementieren?
        self.errors = {}
        self.valid = False
        self.do_action = False
        self.actions = []
        self.checked_actions = []
        #self.actions2 = []
        self.filesmissing = False
        form = self.request.form
        print(form)

        # Schritt 1: Upload Button gedrückt
        if 'form.button.Upload' in form and 'instructions_file' in form:
            file = form['instructions_file'] # ZPublisher.HTTPRequest.FileUpload     
            self.read_actions(file)
            self.check_actions()
        
            if not self.valid:
                IStatusMessage(self.request).add((u"Fehlende oder ungültige Datei"))

            if self.filesmissing:
                IStatusMessage(self.request).add((u"Nicht alle aufgeführten Objekte exisitieren. Fehlende Objekte sind rot gekennzeichnet. Das Verschieben kann nur durchgeführt werden, wenn Quell- und Zielobjekt exisitieren. "))                

        # Schritt 2: Verschieben Button gedrückt
        if 'form.button.Move' in form:
            #action_records = form['actions'] # eine Liste von Objekten vom Typ 'ZPublisher.HTTPRequest.record'
            #print(type(self.actions))
            self.actions = eval(form['actions_dict']) # string can be trusted - View needs manager permission - TODO - find more secure solution
            self.check_actions()
            self.do_action = True
            self.move_items()
            IStatusMessage(self.request).add((u"Verschieben erfolgreich"))

        # Abbrechen in Schritt 1 und Schritt 2
        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add((u"Vorgang abgebrochen"))
            self.request.response.redirect("{0}".format(getSite().absolute_url()))
            return False

        return self.index()

    def read_actions(self, file):

        lines = file.readlines()

        # mehr als 1 Zeile
        if len(lines) <= 1:
            self.valid = False
            return

        # erste Zeile korrekt
        firstline = lines[0].decode()
        if firstline.split(',')[0].strip() != 'source':
            self.valid = False
            return

        if firstline.split(',')[1].strip() != 'target':
            self.valid = False
            return

        # jede Zeile genau zwei elemente
        for line in lines[1:]:
            line = line.decode()
            linesplit = line.split(',')
            if len(linesplit) != 2:
                self.valid = False
                return
            else:
                action = {"source": linesplit[0].strip(), "target": linesplit[1].strip()}
                self.actions.append(action)
        self.valid = True

    def check_actions(self):
        for action in self.actions:
            checked_action = action.copy()
            checked_action['source_object'] = api.content.get(action['source'])
            # TODO: Check if target is folderish
            checked_action['target_object'] = api.content.get(action['target'])
            if not checked_action['source_object'] or checked_action['target_object']:
                self.filesmissing = True
            self.checked_actions.append(checked_action)

    def move_items(self):
        for action in self.checked_actions:
            if action['source_object'] and action['target_object']:
                print("Verschiebe:" + str(action))
                api.content.move(action['source_object'], action['target_object'])