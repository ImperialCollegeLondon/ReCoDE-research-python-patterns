from abc import ABC, abstractmethod


class BaseView(ABC):
    @abstractmethod
    def render(self) -> None: ...
