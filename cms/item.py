"""Module containing base class for items."""

import os
from typing import Optional

PROJECT_DIR = "projects"


class Item:
    """Base class for an item."""

    def __init__(self, path: str, children: list, icon: str):
        """Initialize an item."""
        self.path = path
        self.icon = icon
        self.name = path.strip(os.sep).split(os.sep)[-1]
        self.suffix = ""
        self.children = children

    @property
    def fullpath(self) -> str:
        """Get the full path required to open the item from python."""
        return os.path.join(PROJECT_DIR, self.path)

    @property
    def project_dir(self) -> str:
        """Get the path to the project directory containing the item."""
        return os.path.join(PROJECT_DIR, self.path.split(os.sep)[0])

    def render(self, **kwargs):
        """Render the item for HTML display."""
        raise NotImplementedError

    def create(self) -> Optional[str]:
        """Create the item."""
        raise NotImplementedError

    def update(self, form: dict[str, str]) -> Optional[str]:
        """Process the post action on the item."""
        return "Bearbeiten dieser Datei/dieses Ordners ist nicht möglich."
