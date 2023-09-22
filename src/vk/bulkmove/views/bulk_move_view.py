# -*- coding: utf-8 -*-

# from vk.bulkmove import _
from Products.Five.browser import BrowserView
from zope.interface import implementer
from zope.interface import Interface


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
        return self.index()
