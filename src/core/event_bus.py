"""
Шина событий: подписка и публикация по типу события.
Модель публикует факт (враг убит), слушатели реагируют, не зная друг о друге.
Также это алгоритм Observer.
"""
from collections import defaultdict
from typing import Callable

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable]] = defaultdict(list) # Для нового ключа автоматически создаёт пустой список

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: Callable) -> None:
        handlers = self._subscribers.get(event_type)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def publish(self, event: object) -> None:
        for handler in list(self._subscribers.get(type(event), ())):
            handler(event)

    def clear(self) -> None:
        self._subscribers.clear()
