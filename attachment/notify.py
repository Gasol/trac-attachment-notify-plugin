#
# Copyright (C) 2013 KKBOX Technologies Limited
# Copyright (C) 2013 Gasol Wu <gasol.wu@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from datetime import datetime
from inspect import getargspec
from trac.attachment import IAttachmentChangeListener
from trac.core import Component, implements
from trac.util.datefmt import utc
from trac.util.text import CRLF, obfuscate_email_address, wrap
from trac.util.translation import deactivate, reactivate
from trac.notification import NotifyEmail
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.resource import get_resource_url

class AttachmentNotify(Component):
    implements(IAttachmentChangeListener)

    def attachment_added(self, attachment):
        self._notify_attachment(attachment, True)

    def attachment_deleted(self, attachment):
        self._notify_attachment(attachment, False)

    def attachment_reparented(self, attachment, old_parent_realm, old_parent_id):
        pass

    def _get_parent_ticket(self, attachment):
        resource = attachment.resource
        while resource:
            if 'ticket' == resource.realm:
                break
            resource = resource.parent

        try:
            if resource and resource.id:
                return Ticket(self.env, resource.id)
        except ResourceNotFound:
            return

    def _notify_attachment(self, attachment, add):
        ticket = self._get_parent_ticket(attachment)
        if not ticket:
            return

        filename = attachment.filename
        author = attachment.author
        now = attachment.date or datetime.now(utc)
        action = add and 'added' or 'deleted'
        body = 'Attachment "%s" %s' % (filename, action)

        if add:
            raw_url = get_resource_url(self.env,
                                       attachment.resource,
                                       self.env.abs_href,
                                       format='raw')
            body += "\n\n%s" % raw_url if raw_url else ''

        if attachment.description:
            body += "\n\n" + attachment.description

        an = AttachmentNotifyEmail(self.env)
        an.notify_attachment(ticket, author, filename, now, body)

class AttachmentNotifyEmail(TicketNotifyEmail):
    def __init__(self, env):
        super(AttachmentNotifyEmail, self).__init__(env)
        ambiguous_char_width = env.config.get('notification',
                                              'ambiguous_char_width',
                                              'single')
        self.ambiwidth = (1, 2)[ambiguous_char_width == 'double']

    def notify_attachment(self, ticket, author, filename, modtime, body):
        """Send ticket attachment notification (untranslated)"""
        t = deactivate()
        translated_fields = ticket.fields
        try:
            ticket.fields = TicketSystem(self.env).get_ticket_fields()

            self.ticket = ticket
            self.modtime = modtime
            self.newticket = False
            self.reporter = ''
            self.owner = ''

            link = self.env.abs_href.ticket(ticket.id)
            summary = self.ticket['summary']
            ticket_values = ticket.values.copy()
            ticket_values['id'] = ticket.id

            wrap_kargs = {
                'initial_indent': ' ',
                'subsequent_indent': ' ',
                'linesep': CRLF
            }
            if 'ambiwidth' in getargspec(wrap)[0]:
                wrap_kargs['ambiwidth'] = self.ambiwidth

            ticket_values['description'] = wrap(
                ticket_values.get('description', ''),
                self.COLS,
                **wrap_kargs
            )

            ticket_values['new'] = self.newticket
            ticket_values['link'] = link
            subject = 'Re: ' + self.format_subj(summary)
            author = obfuscate_email_address(author)
            change = { 'author': author }

            self.data.update({
                'ticket_props': self.format_props(),
                'ticket_body_hdr': self.format_hdr(),
                'subject': subject,
                'ticket': ticket_values,
                'change': change,
                'changes_body': body,
                })

            NotifyEmail.notify(self, ticket.id, subject)
        finally:
            ticket.fields = translated_fields
            reactivate(t)
