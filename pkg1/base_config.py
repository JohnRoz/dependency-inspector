from abc import ABC, abstractmethod


class BaseConfig(ABC):
    @classmethod
    @abstractmethod
    def is_none_ok(cls) -> bool:
        return False

    @classmethod
    @abstractmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        pass
