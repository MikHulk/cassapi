"""Process legifrance xml file content.

This file can display the processed content of an xml file if
excuted directly providing a path to a such file as positonnal
argument.

example:
  $ python -m pydoc app/scripts/initscript.py

"""

from datetime import datetime
import re
import warnings
from xml.dom import minidom
from xml.dom import Node


def clean(dom):
    """Unprettify xml dom in order to process it"""
    return minidom.parseString("".join(dom.toxml().strip("\n").split("\n")))


class InvalidDocument(Exception): ...


class Parser:
    """Parser for Legifrance XML.
    One can instantiate directly from a dom or via the static method
    `from_file`, which directly takes the path to an xml file.
    """

    def __init__(self, dom):
        self.dom = clean(dom)

    @staticmethod
    def from_file(path):
        """Take a path to an xml file and returns a parser."""
        with open(path) as f:
            dom = minidom.parse(path)
        return Parser(dom)

    @staticmethod
    def _parse_node(node):
        if node.nodeType == Node.ELEMENT_NODE:
            res = {}
            children = node.childNodes
            for child in children:
                if (
                    len(child.childNodes) == 1
                    and child.childNodes[0].nodeType == Node.TEXT_NODE
                ):
                    content = child.childNodes[0].nodeValue
                else:
                    content = Parser._parse_node(child)

                visited = res.get(child.nodeName)
                if visited:
                    if isinstance(visited, list):
                        visited.append(content)
                    else:
                        res[child.nodeName] = [visited, content]
                else:
                    res[child.nodeName] = content
            return res
        elif node.nodeType == Node.TEXT_NODE:
            return node.nodeValue

    def parse_single_node(self, name):
        """Searches for a node that is expected to appear only once in the
        document, and throws an error if it doesn't.
        """
        nodes = self.dom.getElementsByTagName(name)
        if len(nodes) != 1:
            raise InvalidDocument(f"more than one {name} tag in the dom")
        return Parser._parse_node(nodes[0])

    @property
    def meta_commun(self):
        """Returns content of the so called "META_COMMUN" tag as dict"""
        return self.parse_single_node("META_COMMUN")

    @property
    def meta_spec(self):
        """Returns content of the so called "META_SPEC" tag as dict."""
        return self.parse_single_node("META_SPEC")

    @property
    def meta(self):
        """Returns content of the so called "META" tag as dict"""
        return self.parse_single_node("META")

    @property
    def identifier(self):
        """Unified identifier."""
        return self.meta_commun["ID"]

    @property
    def numero(self):
        """The identifier under META_JURI/NUMERO in source."""
        return self.meta_spec.get("META_JURI", {}).get("NUMERO")

    @property
    def title(self):
        """The title of the ruling."""
        return self.meta_spec.get("META_JURI", {}).get("TITRE", "")

    @property
    def date(self):
        """Date of the ruling as python date object."""
        return datetime.strptime(
            self.meta_spec.get("META_JURI", {}).get("DATE_DEC", ""), "%Y-%m-%d"
        )

    @property
    def code_chambre(self):
        """Name of the court called "chambre" in french law."""
        return self.meta_spec.get("META_JURI_JUDI", {}).get("FORMATION")

    @property
    def chambre(self):
        """Name of the court called "chambre" in french law."""
        return (
            self.meta_spec.get("META_JURI_JUDI", {})
            .get("FORMATION")
            .replace("_", " ")
            .title()
        )

    @property
    def solution(self):
        """The decision of the court."""
        return self.meta_spec.get("META_JURI", {}).get("SOLUTION", "")

    @property
    def texte(self):
        """Returns content of the so called "TEXTE" tag as a list of lines
        preserving empty lines."""
        text_block = self.dom.getElementsByTagName("BLOC_TEXTUEL")
        if len(text_block) != 1:
            raise InvalidDocument("More than one or no `BLOC_TEXTUEL` tag")
        content = text_block[0].getElementsByTagName("CONTENU")
        if len(content) != 1:
            raise InvalidDocument(
                "More than one or no `CONTENU` into `BLOC_TEXTUEL` tag"
            )
        return [
            child.nodeValue.strip("\n") if child.nodeType == Node.TEXT_NODE else ""
            for child in content[0].childNodes
        ]

    @property
    def paragraphes(self):
        """Returns a list of paragraphes as list of lines."""
        raw = "\n".join(self.texte)
        return [re.split(r"\n\n*", s) for s in re.split(r"\n\n\n+", raw)]

    @property
    def num_arrêt(self):
        """Tries to find the ruling(the "Arrêt") identifier in the text.
        Return None on failure."""
        raw = "\n".join(self.texte)
        found = re.search(r"^\s*[A-a]rrêt\s+n°\s+(\w.+)$", raw, re.M)
        if found:
            return found.group(1).strip()
        return

    @property
    def num_pourvoi(self):
        """Tries to find the appeal(the "Pourvoi") identifier in the text.
        Return None on failure."""
        raw = "\n".join(self.texte)
        found = re.search(r"^\s*[Pp]ourvoi\s+n°\s+(\w.+)$", raw, re.M)
        if found:
            return found.group(1).strip()
        return

    @property
    def liens(self):
        """Returns content of the so called "LINKS" tag as a list"""
        links = self.parse_single_node("LIENS")
        if isinstance(links, list):
            res = []
            for link in links:
                if "LIEN" in link:
                    link = link["LIEN"]
                    if isinstance(link, list):
                        res += link
                    elif isinstance(link, str):
                        res.append(link)
            return res
        else:
            link = links.get("LIEN")
            if isinstance(link, list):
                return link
            elif isinstance(link, str):
                return [link]
            else:
                return []

    @property
    def sommaire(self):
        """Returns content of the so called "SOMMAIRE" tag as dict."""
        return self.parse_single_node("SOMMAIRE")


if __name__ == "__main__":
    import sys
    from pprint import pprint

    path = sys.argv[1]
    p = Parser.from_file(path)
    pprint(p.meta)
    print("\n\n".join("\n".join(lines) for lines in p.paragraphes))
    print("\n")

    print(p.title)
    pprint(p.sommaire)
    pprint(p.liens)
    print()

    print(f"Chambre:\t{p.chambre}")
    print(f"Identifiant:\t{p.identifier}")
    print(f"Numéro:\t\t{p.numero}")
    print(f"Le:\t\t{p.date.strftime('%d-%m-%Y')}")
    print(f"Arrêt n°:\t{p.num_arrêt}")
    print(f"Pourvoi n°:\t{p.num_pourvoi}")
    print(f"Solution:\t{p.solution}")
    print()

    print(f"{len(p.paragraphes)} paragraphes")
    print(f"{len(p.texte)} lignes")
    print(f"{len(' '.join(p.texte).split())} mots")
    print(f"{len(''.join(p.texte))} signes")
