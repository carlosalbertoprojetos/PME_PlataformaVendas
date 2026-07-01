from collections import defaultdict

from eventos.events import DomainEvent


class EventDispatcher:
    def __init__(self):
        self._handlers = defaultdict(list)
        self._global_handlers = []

    def subscribe(self, event_type, handler):
        if handler in self._handlers[event_type]:
            return
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler):
        if handler in self._global_handlers:
            return
        self._global_handlers.append(handler)

    def dispatch(self, event: DomainEvent):
        for handler in [*self._global_handlers, *self._handlers.get(event.tipo, [])]:
            handler(event)
        return event


dispatcher = EventDispatcher()


def dispatch_event(event: DomainEvent):
    return dispatcher.dispatch(event)


def register_event_handler(event_type, handler):
    dispatcher.subscribe(event_type, handler)


def register_global_event_handler(handler):
    dispatcher.subscribe_all(handler)
