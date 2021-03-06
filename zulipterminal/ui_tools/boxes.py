import urwid
from time import ctime
from typing import Any, Tuple, List

from zulipterminal.ui_tools.buttons import MenuButton


class WriteBox(urwid.Pile):
    def __init__(self, view: Any) -> None:
        super(WriteBox, self).__init__(self.main_view(True))
        self.client = view.client
        self.to_write_box = None
        self.stream_write_box = None

    def main_view(self, new: bool) -> Any:
        private_button = MenuButton(u"New Private Message")
        urwid.connect_signal(private_button, 'click', self.private_box_view)
        stream_button = MenuButton(u"New Topic")
        urwid.connect_signal(stream_button, 'click', self.stream_box_view)
        w = urwid.Columns([
            urwid.LineBox(private_button),
            urwid.LineBox(stream_button),
        ])
        if new:
            return [w]
        else:
            self.contents = [(w, self.options())]

    def private_box_view(self, button: Any=None, email: str='') -> None:
        if email == '':
            email = button.email
        self.to_write_box = urwid.Edit(u"To: ", edit_text=email)
        self.msg_write_box = urwid.Edit(u"> ")
        self.contents = [
            (urwid.LineBox(self.to_write_box), self.options()),
            (self.msg_write_box, self.options()),
        ]

    def stream_box_view(self, button: Any=None, caption: str='',
                        title: str='') -> None:
        self.to_write_box = None
        if caption == '':
            caption = button.caption
        self.msg_write_box = urwid.Edit(u"> ")
        self.stream_write_box = urwid.Edit(
            caption=u"Stream:  ",
            edit_text=caption
            )
        self.title_write_box = urwid.Edit(caption=u"Title:  ", edit_text=title)

        header_write_box = urwid.Columns([
            urwid.LineBox(self.stream_write_box),
            urwid.LineBox(self.title_write_box),
        ])
        write_box = [
            (header_write_box, self.options()),
            (self.msg_write_box, self.options()),
        ]
        self.contents = write_box

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if key == 'enter':
            if not self.to_write_box:
                request = {
                    'type': 'stream',
                    'to': self.stream_write_box.edit_text,
                    'subject': self.title_write_box.edit_text,
                    'content': self.msg_write_box.edit_text,
                }
                response = self.client.send_message(request)
            else:
                request = {
                    'type': 'private',
                    'to': self.to_write_box.edit_text,
                    'content': self.msg_write_box.edit_text,
                }
                response = self.client.send_message(request)
            if response['result'] == 'success':
                self.msg_write_box.edit_text = ''
        if key == 'esc':
            self.main_view(False)
        key = super(WriteBox, self).keypress(size, key)
        return key


class MessageBox(urwid.Pile):
    def __init__(self, message: str, model: Any) -> None:
        self.model = model
        self.message = message
        self.caption = None
        self.stream_id = None
        self.title = None
        self.email = None
        super(MessageBox, self).__init__(self.main_view())

    def stream_view(self) -> Any:
        self.caption = self.message['stream']
        self.stream_id = self.message['stream_id']
        self.title = self.message['title']
        stream_title = ('header', [
            ('custom', self.message['stream']),
            ('selected', ">"),
            ('custom', self.message['title'])
        ])
        stream_title = urwid.Text(stream_title)
        time = urwid.Text(('custom', ctime(self.message['time'])),
                          align='right')
        header = urwid.Columns([
            stream_title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def private_view(self) -> Any:
        self.email = self.message['sender_email']
        title = ('header', [('custom', 'Private Message')])
        title = urwid.Text(title)
        time = urwid.Text(('custom', ctime(self.message['time'])),
                          align='right')
        header = urwid.Columns([
            title,
            time,
        ])
        header = urwid.AttrWrap(header, "header")
        return header

    def main_view(self) -> List[Any]:
        if self.message['type'] == 'stream':
            header = self.stream_view()
        else:
            header = self.private_view()
        content = [('name', self.message['sender']), "\n" +
                   self.message['content']]
        content = urwid.Text(content)
        return [header, content]

    def selectable(self):
        return True

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            if button == 1:
                self.keypress(size, 'enter')
                return True
        return super(MessageBox, self).mouse_event(size, event, button, col,
                                                   row, focus)

    def keypress(self, size, key):
        if key == 'enter':
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(
                    email=self.message['sender_email']
                    )
            if self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message['stream'], title=self.message['title']
                    )
        if key == 'c':
            if self.message['type'] == 'private':
                self.model.controller.view.write_box.private_box_view(
                    email=self.message['sender_email']
                    )
            if self.message['type'] == 'stream':
                self.model.controller.view.write_box.stream_box_view(
                    caption=self.message['stream']
                    )
        if key == 'S':
            if self.message['type'] == 'private':
                self.model.controller.narrow_to_user(self)
            if self.message['type'] == 'stream':
                self.model.controller.narrow_to_stream(self)
        if key == 's':
            if self.message['type'] == 'private':
                self.model.controller.narrow_to_user(self)
            if self.message['type'] == 'stream':
                self.model.controller.narrow_to_topic(self)
        if key == 'esc':
            self.model.controller.show_all_messages(self)
        return key
