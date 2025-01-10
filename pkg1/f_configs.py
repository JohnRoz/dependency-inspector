from abc import ABC, abstractmethod

from pkg1.base_config import BaseConfig


class FooConfig(BaseConfig):

    @abstractmethod
    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        pass
