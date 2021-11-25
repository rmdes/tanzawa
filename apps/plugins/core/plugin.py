import importlib
import pathlib
from abc import abstractmethod
from enum import Enum
from typing import Optional, Protocol, TypeVar

from plugins.models import MPlugin


class DisplaySize(Enum):

    X_SMALL = "xsmall"
    SMALL = "small"
    REGULAR = "regular"
    LARGE = "large"
    X_LARGE = "xlarge"


class Slot(Enum):
    TOP = "top"
    LEFT = "left"
    RIGHT = "right"
    BOTTOM = "bottom"


class Plugin(Protocol):
    """"""

    name: str
    description: str
    # A unique namespaced identifier for the plugin
    identifier: str
    default_size: DisplaySize = DisplaySize.REGULAR
    default_slot = Slot.TOP

    @property
    def public_has_top_nav(self) -> bool:
        """Does this plugin have public facing top nav?"""
        return False

    @abstractmethod
    def public_top_nav_icon(self) -> str:
        """Return an emoji that will be displayed next to the top nav item."""
        raise NotImplementedError

    @abstractmethod
    def public_top_nav_content(self) -> str:
        """Return html to be output on the page after the top nav icon"""
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return MPlugin.objects.filter(identifier=self.identifier).values_list("enabled", flat=True).first() or False

    @property
    def plugin_module(self) -> str:
        """Return the python module path to the plugin's module"""
        return ".".join(self.__module__.split(".")[:-1])

    @property
    def urls(self) -> Optional[str]:
        """Return the path to the _public_ url configuration for a plugin"""
        # TODO: Make this check for a urls.py and return None if not exists
        return f"{self.plugin_module}.urls"

    @property
    def admin_urls(self) -> Optional[str]:
        """Return the path to the _admin_ url configuration for a plugin"""
        return f"{self.plugin_module}.admin_urls"

    @property
    def has_migrations(self):
        """Check if a plugin has migration directory.

        Uses pathlib instead of importlib to avoid importing modules.
        """

        migration_module = pathlib.Path(importlib.util.find_spec(self.__module__).origin).parent / "migrations"
        return migration_module.is_dir()


TanzawaPlugin = TypeVar("TanzawaPlugin", bound=Plugin)
