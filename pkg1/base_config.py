from abc import ABC, abstractmethod


class BaseConfig(ABC):
    @classmethod
    def is_none_ok(cls) -> bool:
        return False

    @abstractmethod
    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        pass
