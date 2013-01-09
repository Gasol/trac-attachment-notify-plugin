from trac.core import Component, implements
from trac.attachment import IAttachmentChangeListener

class AttachmentNotify(Component):
    implements(IAttachmentChangeListener)

    def attachment_added(attachment):
        pass

    def attachment_deleted(attachment):
        pass

    def attachment_reparented(attachment, old_parent_realm, old_parent_id):
        pass
