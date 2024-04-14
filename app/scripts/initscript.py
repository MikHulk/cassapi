"""This script takes an url to a data source fetch all tar file and indexes
the documents under the index provided in Elastic Search.
Files are first extracted in a directory into the the given working_dir, then
resulting folders are processed in chronological order.
Each document is then indexed in ES.

Usage (from project root, increase size limit if you got errors about that):
  $ ulimit -n 2048
  $ PYTHONPATH=. python app/scripts/initscript.py \\
    https://echanges.dila.gouv.fr/OPENDATA/CASS/ . 'test-xxx'

At the end of the transfert the script displays a report and ask you for
the extracted tree removing. Answer 'y' if you want to.
"""

import asyncio
import concurrent.futures
import os
import re
import shutil
import tarfile

import aiohttp

from app.es import get_client
from app.legifrance.parser import Parser
from app.legifrance.files import get_files
from app.indexer import Indexer


class Loader:
    """Take an url for legifrance xml and indexes their content into
    Elastic Search.
    """

    def __init__(self, legifrance_url, working_dir, index):
        self.url = legifrance_url
        self.working_dir = working_dir
        self.index = index

    @staticmethod
    def _write_file(fd, chunk):
        fd.write(chunk)

    def extract(self, target):
        """Extract the tar under target."""
        path = os.path.join(self.working_dir, target)
        with tarfile.open(path, mode="r:gz") as f:
            f.extractall(path=self.working_dir)
        os.remove(path)

    async def list_targets(self):
        """Retrieve link to tar files from the source url."""
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(self.url) as resp:
                text = await resp.text()
        return re.findall(r'<a href="(CASS_\d{8}-\d{6}\.tar\.gz)">', text)

    async def process_target(self, target):
        """Fetch a tar file from source."""
        print("fetch", target)
        loop = asyncio.get_running_loop()
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(f"{self.url}/{target}") as resp:
                with open(os.path.join(self.working_dir, target), "wb") as fd:
                    async for chunk in resp.content.iter_chunked(100):
                        await loop.run_in_executor(None, Loader._write_file, fd, chunk)
        print("extract", target)
        await loop.run_in_executor(None, self.extract, target)
        print(target, "done")

    async def process_targets(self, targets):
        """Fetch all available files from source."""
        await asyncio.gather(*(loader.process_target(target) for target in targets))

    async def index_file(self, indexer, fpath):
        """Parse xml under `path` found, and indexes it in ES."""
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                parser = await loop.run_in_executor(pool, Parser.from_file, fpath)
            except Exception as e:
                exc = e.__class__
                print(
                    f"⚠ ERROR: {fpath}: {exc.__module__} {exc.__name__} {e}",
                    file=sys.stderr,
                )
            else:
                return await indexer.index_doc(parser)

    def bulk_index(self):
        """Walks into the directory, parse each xml found, and indexes it."""
        loop = asyncio.get_event_loop()
        indexer = Indexer(self.index)
        results = {}
        for d in sorted(os.listdir(self.working_dir)):
            print("process", d)
            results[d] = loop.run_until_complete(
                asyncio.gather(
                    *(
                        self.index_file(indexer, f)
                        for f in get_files(os.path.join(self.working_dir, d))
                    )
                )
            )
        return results

    def clean(self):
        shutil.rmtree(self.working_dir)


if __name__ == "__main__":
    import asyncio
    from argparse import ArgumentParser
    from datetime import date
    from pprint import pprint
    import sys

    parser = ArgumentParser(
        description="Fetch data from the specified source url and indexes the "
        "document under the specified index in Elastic Search"
    )
    parser.add_argument(
        "source_url",
        metavar="url",
        type=str,
        help="the url where fetch xml documents",
    )
    parser.add_argument(
        "wdir",
        metavar="dir",
        type=str,
        help="the working dir where files will be processed",
    )
    parser.add_argument(
        "index",
        metavar="index",
        type=str,
        help="the index under which documents will be indexed",
    )

    args = parser.parse_args()
    path = f'work-{date.today().strftime("%y%m%d")}'
    os.mkdir(os.path.join(args.wdir, path))
    loop = asyncio.get_event_loop()

    loader = Loader(args.source_url, path, args.index)
    targets = loop.run_until_complete(loader.list_targets())
    loop.run_until_complete(loader.process_targets(targets))
    results = loader.bulk_index()
    for k, v in results.items():
        processed = 0
        created = 0
        updated = 0
        error = 0
        parsing_error = 0
        for result in v:
            if result:
                processed += 1
                if result.meta.status == 201:
                    created += 1
                elif result.meta.status == 200:
                    updated += 1
                elif result.meta.status >= 400:
                    error += 1
            else:
                parsing_error += 1
        print(
            f"{k:3} {processed:3} processed, {created:3} created, "
            f"{updated:3} updated, {error:3} on error and "
            f"{parsing_error:3} errors on parsing"
        )
    r = input("clean? ")
    if r == "y":
        loader.clean()
    print("bye")
