"""Module containing folder items."""

import os
from typing import Optional

from flask import render_template

from .item import Item


class Folder(Item):
    """Class for a folder."""

    def __init__(self, path: str, children: list, icon: str = "📂"):
        """Initialize a folder."""
        super().__init__(path, children, icon)

    def render(self, **kwargs):
        """Render the folder for HTML display."""
        return render_template(
            "project_dir.html",
            path=self.path,
            tree=self.children,
            **kwargs,
        )

    def create(self) -> Optional[str]:
        """Create the folder."""
        try:
            os.mkdir(self.fullpath)
        except FileExistsError:
            return "Ordner existiert bereits."


class CollapsedFolder(Folder):
    """Class for a folder whose content is hidden in the tree view."""

    def __init__(self, path: str, children: list, icon: str = "📁"):
        """Initialize a collapsed folder."""
        super().__init__(path, [], icon)
        self._children = children
        plural = "e" if len(children) != 1 else ""
        self.suffix = f" ({len(children)} Element{plural})"

    def render(self, **kwargs):
        """Render the folder for HTML display."""
        return render_template(
            "project_dir.html",
            path=self.path,
            tree=self._children,
            **kwargs,
        )
