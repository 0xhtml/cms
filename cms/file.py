"""Module containing different file items."""

import hashlib
import os
from typing import NamedTuple, Optional

import jinja2
import jinja2.nodes
from flask import render_template, request

from .item import Item

TEMPLATE_DIR = "templates"


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _normalize(content: str) -> str:
    return content.replace("\r\n", "\n").strip("\n ")


class File(Item):
    """Class for an arbitrary file."""

    def __init__(self, path: str, icon: str = "📄"):
        """Initialize an arbitrary file."""
        super().__init__(path, [], icon)

    def render(self, **kwargs):
        """Render the file for HTML display."""
        with open(self.fullpath, "r") as file:
            content = file.read()

        content_hash = _hash(content)

        if "form" in kwargs:
            content = kwargs["form"]["content"]

        return render_template(
            "project_file.html",
            path=self.path,
            content=_normalize(content),
            content_hash=content_hash,
            **kwargs,
        )

    def _write(self, file, form: dict[str, str]):
        content = _normalize(form.get("content", ""))
        if content:
            file.write(content + "\n")

    def create(self) -> Optional[str]:
        """Create the file."""
        if os.path.exists(self.fullpath):
            return "Datei existiert bereits."

        open(self.fullpath, "w").close()

    def update(self, form: dict[str, str]) -> Optional[str]:
        """Process the post action on the file."""
        content_hash = request.form.get("content_hash")

        if content_hash is None:
            return "Fehler beim Bearbeiten."

        try:
            with open(self.fullpath, "r+") as file:
                if _hash(file.read()) != content_hash:
                    return (
                        "Datei wurde während des Bearbeiten auf der "
                        "Festplatte verändert. Erneut auf Speichern klicken "
                        "um die Datei auf der Festplatte zu überschreiben."
                    )

                file.seek(0)
                self._write(file, form)
                file.truncate()
        except FileNotFoundError:
            with open(self.fullpath, "w") as file:
                self._write(file, form)


def _is_template(content: str) -> bool:
    for item in jinja2.Environment().parse(content).body:
        if isinstance(item, jinja2.nodes.Block):
            return True
    return False


def _get_template(content: str) -> str:
    for item in jinja2.Environment().parse(content).body:
        if isinstance(item, jinja2.nodes.Extends):
            return item.template.as_const()
    return ""


class _Token(NamedTuple):
    lineno: int
    ttype: str
    value: str


def _parse_block(stream) -> str:
    depth = 1
    data = ""

    while True:
        token = _Token(*next(stream))
        buffer = token.value

        if token.ttype == "block_begin":
            while (token := _Token(*next(stream))).ttype != "name":
                buffer += token.value

            if token.value == "endblock":
                depth -= 1
                if depth <= 0:
                    break
            elif token.value == "block":
                depth += 1

            buffer += token.value

        data += buffer

    return data


def _get_fields(content: str) -> dict[str, str]:
    fields = {}
    stream = jinja2.Environment().lex(content)

    def until(stream, ttype: str) -> _Token:
        while (token := _Token(*next(stream))).ttype != ttype:
            pass
        return token

    for token in stream:
        if _Token(*token).ttype != "block_begin":
            continue

        if until(stream, "name").value != "block":
            continue

        name = until(stream, "name").value
        until(stream, "block_end")

        fields[name] = _normalize(_parse_block(stream))

    return fields


class _HTMLField(NamedTuple):
    name_prefix: str
    placeholder: str
    value: str
    active: bool


class HTMLFile(File):
    """Class for a HTML file."""

    def __init__(self, path: str, icon: str = "🌐"):
        """Initialize a HTML file."""
        super().__init__(path, icon)

    def render(self, **kwargs):
        """Render the HTML file for HTML display."""
        project_template_dir = os.path.join(self.project_dir, TEMPLATE_DIR)
        templates = {
            os.path.join(TEMPLATE_DIR, template)
            for template in os.listdir(project_template_dir)
        }

        with open(self.fullpath) as file:
            content = file.read()

        content_hash = _hash(content)

        if "form" in kwargs:
            template = kwargs["form"]["template"]

            fields = {
                field[len("field_") :]: _HTMLField("field_", "", value, True)
                for field, value in kwargs["form"].items()
                if field.startswith("field_")
            }

            if "content" in kwargs["form"]:
                fields["content"] = _HTMLField(
                    "", "", kwargs["form"]["content"], True
                )
        else:
            template = _get_template(content)

            if template:
                with open(os.path.join(self.project_dir, template)) as file:
                    fields = {
                        name: _HTMLField("field_", placeholder, "", True)
                        for name, placeholder in _get_fields(
                            file.read()
                        ).items()
                    }

                fields.update(
                    {
                        name: _HTMLField(
                            "field_",
                            fields[name].placeholder if name in fields else "",
                            value,
                            name in fields,
                        )
                        for name, value in _get_fields(content).items()
                    }
                )
            else:
                fields = {
                    "content": _HTMLField("", "", _normalize(content), True)
                }

        if template:
            templates.add(template)

        return render_template(
            "project_html.html",
            path=self.path,
            template=template,
            templates=sorted(templates),
            fields=fields,
            content_hash=content_hash,
            **kwargs,
        )

    def _write(self, file, form: dict[str, str]):
        template = request.form.get("template", "")

        content = request.form.get("content")

        fields = {
            key[len("field_") :]: value
            for key, value in request.form.items()
            if key.startswith("field_")
        }

        if template:
            file.write(f'{{% extends "{template}" %}}\n')

        if content is None:
            for field, fcontent in fields.items():
                fcontent = _normalize(fcontent)

                if fcontent:
                    file.write(f"\n{{% block {field} %}}\n")
                    file.write(fcontent + "\n")
                    file.write("{% endblock %}\n")
        else:
            content = _normalize(content)

            if content:
                if template and not _is_template(content):
                    file.write("\n{% block content %}\n")
                    file.write(content + "\n")
                    file.write("{% endblock %}\n")
                else:
                    file.write(content + "\n")
