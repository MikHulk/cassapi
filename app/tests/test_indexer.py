import asyncio
import os
from pprint import pprint
from random import randint

from pytest import fixture

from app.es import get_client
from app.legifrance.files import get_files
from app.legifrance.parser import Parser
from app.indexer import Indexer

from .fixtures import client, parser, DATA_DIR


@fixture(scope="function")
def indexer(client):
    index = "test-" + "".join(chr(randint(97, 122)) for _ in range(10))
    print(f"create {index} index")
    # create a dummy document to have something to delete when test went wrong
    client.index(index=index, document={"test": "index"})
    print(f"{index} created")
    yield Indexer(index)
    print(f"delete {index} index")
    client.indices.delete(index=index)
    print(f"{index} deleted")


def test_data_dir():
    d = os.listdir(DATA_DIR)
    assert "test.xml" in d
    assert "full_tree" in d


def test_prepare_doc(parser):
    doc = Indexer.prepare_document(parser)
    assert isinstance(doc, dict)
    assert "numero" in doc
    assert doc["numero"] == parser.numero
    assert "title" in doc
    assert doc["title"] == parser.title
    assert "date" in doc
    assert doc["date"] == parser.date
    assert "chambre" in doc
    assert doc["chambre"] == parser.chambre
    assert "solution" in doc
    assert doc["solution"] == parser.solution
    assert "paragraphes" in doc
    assert doc["paragraphes"] == parser.paragraphes
    assert "paragraphes" in doc
    assert doc["code_chambre"] == parser.code_chambre


def test_index_doc(indexer, parser, client):
    loop = asyncio.get_event_loop()
    resp = loop.run_until_complete(indexer.index_doc(parser))
    pprint(dict(resp))
    assert resp.meta.status == 201
    assert resp["result"] == "created"
    resp = client.get(index=indexer.index, id=parser.identifier)
    assert resp.meta.status == 200
    pprint(dict(resp.body))
    doc = resp.body["_source"]
    assert "identifier" in doc
    assert doc["identifier"] == parser.identifier
    assert "numero" in doc
    assert doc["numero"] == parser.numero
    assert "title" in doc
    assert doc["title"] == parser.title
    assert "date" in doc
    assert doc["date"] == parser.date.isoformat()
    assert "chambre" in doc
    assert doc["chambre"] == parser.chambre
    assert "paragraphes" in doc
    assert doc["code_chambre"] == parser.code_chambre
    assert "solution" in doc
    assert doc["solution"] == parser.solution
    assert "paragraphes" in doc
    assert doc["paragraphes"] == parser.paragraphes


def test_bulk_index(indexer, client):
    parsers = [
        Parser.from_file(path)
        for path in get_files(os.path.join(DATA_DIR, "full_tree"))
    ]
    jobs = [indexer.index_doc(parser) for parser in parsers]
    assert len(jobs) == 92
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(asyncio.gather(*jobs))
    for result in results:
        assert result.meta.status == 201
    for parser in parsers:
        resp = client.get(index=indexer.index, id=parser.identifier)
        assert resp.meta.status == 200
        doc = resp.body["_source"]
        assert "identifier" in doc
        assert doc["identifier"] == parser.identifier
        assert "numero" in doc
        assert doc["numero"] == parser.numero
        assert "title" in doc
        assert doc["title"] == parser.title
        assert "date" in doc
        assert doc["date"] == parser.date.isoformat()
        assert "chambre" in doc
        assert doc["chambre"] == parser.chambre
        assert "paragraphes" in doc
        assert doc["code_chambre"] == parser.code_chambre
        assert "solution" in doc
        assert doc["solution"] == parser.solution
        assert "paragraphes" in doc
        assert doc["paragraphes"] == parser.paragraphes

    client.indices.refresh(index=indexer.index)
    resp = client.count(
        index=indexer.index, query={"prefix": {"identifier": {"value": "juritext"}}}
    )
    pprint(dict(resp))
    assert resp["count"] == 92
