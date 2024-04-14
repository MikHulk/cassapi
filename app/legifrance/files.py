"""Utilities aimed at process files from legifrance.

Allows you to browse a file tree and validate documents into if executed
directly by providing the path to the directory.

example:
  $ python app/legifrance/files.py app/tests/test_data/full_tree
"""

import os


def get_files(path):
    """Return generator on xml files under a path."""
    for p, _, files in os.walk(path):
        if files:
            for f in files:
                if f.endswith(".xml"):
                    yield os.path.join(p, f)


if __name__ == "__main__":
    import sys
    from parser import Parser, InvalidDocument

    path = sys.argv[1]
    valid = 0
    invalid = 0
    processed = 0
    for fpath in get_files(path):
        print(fpath)

        processed += 1
        try:
            p = Parser.from_file(fpath)
            print(p.date.strftime("%c"), p.identifier, p.numero)
            print(p.title)
            print(p.chambre)
            print("\n".join(p.liens))
            print(f"{' '.join(p.texte[:9])}...")
        except Exception as e:
            exc = e.__class__
            print(
                f"⚠ ERROR: {fpath}: {exc.__module__} {exc.__name__} {e}",
                file=sys.stderr,
            )
            invalid += 1
        else:
            valid += 1
        print()
    print(f"{processed} processed files, {valid} OK, {invalid} with error.")
