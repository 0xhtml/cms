"""Main file."""

import os
import shutil
from typing import Optional

from flask import Flask, redirect, render_template, request, url_for

from .file import TEMPLATE_DIR, File, HTMLFile
from .folder import CollapsedFolder, Folder
from .item import PROJECT_DIR, Item

app = Flask(__name__)

_PROJECT_TEMPLATE = "src/project_template"
_COLLAPSED_DIRS = {"static", TEMPLATE_DIR}


def _create_dirs():
    os.makedirs(PROJECT_DIR, exist_ok=True)


@app.get("/")
def index():
    """Serve index page with project selection and creation."""
    _create_dirs()

    projects = os.listdir(PROJECT_DIR)
    projects.sort()

    return render_template("index.html", projects=projects)


def _check_path_name(name: str, label: str, chars: str) -> Optional[str]:
    if not name:
        return f"Kein {label}"

    clean_name = name
    for char in chars:
        clean_name = clean_name.replace(char, "c")

    if not name.isascii() or not clean_name.isalnum():
        return (
            f"Der {label} darf nur aus Buchstaben (keine Umlaute), Zahlen und "
            f"{', '.join(chars)} bestehen."
        )


@app.post("/create-project")
def create_project():
    """Create a new project."""
    _create_dirs()

    project_name = request.form.get("project-name", "").strip()

    if (msg := _check_path_name(project_name, "Projektname", "-")) is not None:
        # TODO: Show msg nicely
        return msg

    try:
        shutil.copytree(
            _PROJECT_TEMPLATE,
            f"{PROJECT_DIR}/{project_name}",
            copy_function=shutil.copy,
        )
    except FileExistsError:
        return "Ein Projekt unter dem Projektnamen existiert bereits."

    return redirect(url_for("project", path=project_name))


def _get_item(path: str, root: bool = True) -> Item:
    urlpath = path.replace(PROJECT_DIR + "/", "")
    inner_path = urlpath.split("/", 1)[-1]

    if inner_path.split("/", 1)[0] not in _COLLAPSED_DIRS:
        if path.endswith(".html"):
            # TODO: Check if os.path.isfile is True
            return HTMLFile(urlpath)

    if "." in path:
        # TODO: Check if os.path.isfile is True
        return File(urlpath)

    children = []

    if os.path.isdir(path):
        for subpath in sorted(os.listdir(path)):
            children.append(_get_item(f"{path}/{subpath}", False))

    if inner_path in _COLLAPSED_DIRS:
        return CollapsedFolder(urlpath, children)

    return Folder(urlpath, children)


@app.get("/project/<path:path>")
def project(path: str):
    """Show a project item."""
    _create_dirs()

    fullpath = f"{PROJECT_DIR}/{path}"

    if not os.path.exists(fullpath):
        return "404"

    item = _get_item(fullpath)

    return item.render()


@app.post("/update-item/<path:path>")
def update_item(path: str):
    """Update a project item."""
    _create_dirs()

    if not os.path.exists(f"{PROJECT_DIR}/{path.split('/')[0]}"):
        return "404"

    item = _get_item(f"{PROJECT_DIR}/{path}")

    if (msg := item.update(request.form)) is not None:
        return item.render(msg=msg, form=request.form)

    return redirect(url_for("project", path=path))


@app.post("/create-item/<path:path>")
def create_item(path: str):
    """Create a project item."""
    _create_dirs()

    parent_path = f"{PROJECT_DIR}/{path}"

    if not os.path.exists(parent_path):
        return "404"

    item_name = request.form.get("item", "").strip()

    if (msg := _check_path_name(item_name, "Dateiname", "-.")) is not None:
        return _get_item(parent_path).render(msg=msg, form=request.form)

    item = _get_item(f"{parent_path}/{item_name}")

    if (msg := item.create()) is not None:
        return _get_item(parent_path).render(msg=msg, form=request.form)

    return redirect(url_for("project", path=f"{path}/{item_name}"))
