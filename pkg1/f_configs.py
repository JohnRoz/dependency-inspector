from abc import ABC, abstractmethod

from pkg1.base_config import BaseConfig


class FooConfigA(BaseConfig):
    config: "FooConfigB"

    def __init__(self):
        super().__init__()
        self.config = FooConfigB()

    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        return set()


class FooConfigB(BaseConfig):
    config: "FooConfigC"

    def __init__(self):
        super().__init__()
        self.config = FooConfigC()

    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        return set()


class FooConfigC(BaseConfig):
    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        return set()


class FooConfigD(BaseConfig):
    config_c: "FooConfigC"
    config_e: "FooConfigE"

    def __init__(self):
        super().__init__()
        self.config_c = FooConfigC()
        self.config_e = FooConfigE()

    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        return set()


class FooConfigE(BaseConfig):
    config: "FooConfigA"

    def __init__(self):
        super().__init__()
        self.config = FooConfigA()

    @classmethod
    def is_none_ok(cls) -> bool:
        return True

    @classmethod
    def get_required_dependencies(cls) -> set[type["BaseConfig"]]:
        return set()


# A -> {B}
# B -> {C}
# C -> {}
# D -> {C, E}
# E -> {A}
