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

        # list of dicts for actions read from file
        self.actions = []
        # list of dicts for actions to run
        self.valid_actions = []

        # Status flags
        self.valid = False # valid Upload file
        #self.do_action = False
        self.filesmissing = False
        self.move_completed = False

        self.message = ""

        form = self.request.form
        #print(form)

        # Schritt 1: Upload Button gedrückt
        if 'form.button.Upload' in form and 'instructions_file' in form:
            file = form['instructions_file'] # ZPublisher.HTTPRequest.FileUpload     
            self.read_actions(file)
            self.check_actions()
        
            if not self.valid:
                IStatusMessage(self.request).add(self.message)

            if self.filesmissing:
                IStatusMessage(self.request).add((u"Nicht alle aufgeführten Objekte exisitieren. Fehlende Objekte sind rot gekennzeichnet. Das Verschieben kann nur durchgeführt werden, wenn Quell- und Zielobjekt exisitieren. "))                

        # Schritt 2: Verschieben Button gedrückt
        if 'form.button.Move' in form:
            self.valid_actions = eval(form['valid_actions_dict']) # string can be trusted - View needs manager permission - TODO - find more secure solution
            self.valid = True
            #self.do_action = True
            self.move_items()
            IStatusMessage(self.request).add((u"Verschieben erfolgreich"))

        # Abbrechen in Schritt 1 und Schritt 2
        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add((u"Vorgang abgebrochen"))
            self.request.response.redirect("{0}".format(getSite().absolute_url()))
            return False

        return self.index()

    def read_actions(self, file):

        if file.filename == "":
            self.message = "Datei fehlt."
            return

        # skip empty lines
        lines = [line for line in file.readlines() if line.strip()]

        # mehr als 1 Zeile
        if len(lines) <= 1:
            self.valid = False
            self.message = "Die Datei mindestens zwei Zeilen beinhalten."
            return

        # erste Zeile korrekt
        firstline = lines[0].decode()
        if firstline.split(',')[0].strip() != 'source':
            self.valid = False
            self.message = 'Die erste Zeile muss aus "source, target" bestehen.'
            return

        if firstline.split(',')[1].strip() != 'target':
            self.valid = False
            self.message = 'Die erste Zeile muss aus "source, target" bestehen.'
            return

        # jede Zeile genau zwei elemente
        for line in lines[1:]:
            line = line.decode()
            linesplit = line.split(',')
            if len(linesplit) != 2:
                self.valid = False
                self.message = "Nicht alle Zeilen der Datei haben genau zwei Elemente."
                return
            else:
                action = {"source": linesplit[0].strip(), "target": linesplit[1].strip()}
                self.actions.append(action)
        self.valid = True

    def check_actions(self):
        for action in self.actions:
            # check existance
            if api.content.get(action['source']) is None:
                action['source_ok'] = False
            else:
                action['source_ok'] = True

            if api.content.get(action['target']) is None:
                action['target_ok'] = False
            else:
                action['target_ok'] = True
                # check if target is a folder
                if api.content.get(action['target']).Type() != 'Folder':
                    action['target_ok'] = False                

            if action['source_ok'] and action['target_ok']:
                self.valid_actions.append(action)
            else:
                self.filesmissing = True

    def move_items(self):
        for action in self.valid_actions:
            source_object = api.content.get(action['source'])
            target_object = api.content.get(action['target'])

            api.content.move(source_object, target_object)
        self.move_completed =  True
