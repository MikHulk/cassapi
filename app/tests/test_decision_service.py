import asyncio
import os
from pprint import pprint
from random import randint

import pytest
from pytest import fixture

from app.es import get_client
from app.legifrance.parser import Parser
from app.legifrance.files import get_files
from app.indexer import Indexer

from app.services.decision import DecisionService

from .fixtures import client, parser, DATA_DIR


@fixture(scope="session")
def indexer(client):
    index = "test-" + "".join(chr(randint(97, 122)) for _ in range(10))
    print(f"create {index} index")
    # create a dummy document to have something to delete when test went wrong
    client.index(index=index, document={"test": "index"}, id=1)
    print(f"{index} created")
    yield Indexer(index)
    print(f"delete {index} index")
    client.indices.delete(index=index)
    print(f"{index} deleted")


@fixture(scope="module")
def with_data(indexer, parser, client):
    parsers = [
        Parser.from_file(path)
        for path in get_files(os.path.join(DATA_DIR, "full_tree"))
    ]
    jobs = [indexer.index_doc(parser) for parser in parsers]
    assert len(jobs) == 92
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(asyncio.gather(*jobs))
    client.delete(index=indexer.index, id=1)
    client.indices.refresh(index=indexer.index)


@fixture(scope="session")
def service(indexer):
    yield DecisionService(indexer.index)


@pytest.mark.usefixtures("with_data")
def test_count(service):
    loop = asyncio.get_event_loop()
    assert loop.run_until_complete(service.count) == 92


@pytest.mark.usefixtures("with_data")
def test_get_summary_no_size(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary()
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 10
    first = res[0]
    pprint(dict(first))
    assert first.identifier == "JURITEXT000048176061"
    assert first.title == (
        "Cour de cassation, criminelle, Chambre criminelle, 3 octobre 2023, "
        "23-80.251, Publié au bulletin"
    )


@pytest.mark.usefixtures("with_data")
def test_get_all_summary(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary(size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 92
    first = res[0]
    pprint(dict(first))
    assert first.identifier == "JURITEXT000048176061"
    assert first.title == (
        "Cour de cassation, criminelle, Chambre criminelle, 3 octobre 2023, "
        "23-80.251, Publié au bulletin"
    )
    last = res[-1]
    pprint(dict(last))
    assert last.identifier == "JURITEXT000048430356"


@pytest.mark.usefixtures("with_data")
def test_get_first(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary(size=1)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 1
    first = res[0]
    pprint(dict(first))
    assert first.identifier == "JURITEXT000048176061"
    assert first.title == (
        "Cour de cassation, criminelle, Chambre criminelle, 3 octobre 2023, "
        "23-80.251, Publié au bulletin"
    )


@pytest.mark.usefixtures("with_data")
def test_get_last(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary(size=1, cursor=91)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 1
    first = res[0]
    pprint(dict(first))
    assert first.identifier == "JURITEXT000048430356"
    assert first.title == (
        "Cour de cassation, Assemblée plénière, 17 novembre 2023, 21-20.723, "
        "Publié au bulletin"
    )


@pytest.mark.usefixtures("with_data")
def test_no_result(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary(size=10, cursor=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 0


@pytest.mark.usefixtures("with_data")
def test_get_decision_by_id(service):
    loop = asyncio.get_event_loop()
    decision = loop.run_until_complete(service.get_decision("JURITEXT000048430356"))
    pprint(dict(decision))
    assert decision.identifier == "JURITEXT000048430356"
    assert decision.numero == "P2300672"
    assert decision.title == (
        "Cour de cassation, Assemblée plénière, 17 novembre 2023, 21-20.723, "
        "Publié au bulletin"
    )
    assert len(decision.paragraphes) == 53


@pytest.mark.usefixtures("with_data")
def test_get_decision_not_found(service):
    loop = asyncio.get_event_loop()
    assert loop.run_until_complete(service.get_decision("JURITEXT000042430356")) is None


@pytest.mark.usefixtures("with_data")
def test_get_all_for_crim(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("CHAMBRE_CRIMINELLE", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 10
    for dec in res:
        assert dec.code_chambre == "CHAMBRE_CRIMINELLE"


@pytest.mark.usefixtures("with_data")
def test_get_all_for_civile_3(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("CHAMBRE_CIVILE_3", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 15
    for dec in res:
        assert dec.code_chambre == "CHAMBRE_CIVILE_3"


@pytest.mark.usefixtures("with_data")
def test_get_all_for_civile_2(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("CHAMBRE_CIVILE_2", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 22
    for dec in res:
        assert dec.code_chambre == "CHAMBRE_CIVILE_2"


@pytest.mark.usefixtures("with_data")
def test_get_all_for_civile_1(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("CHAMBRE_CIVILE_1", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 9
    for dec in res:
        assert dec.code_chambre == "CHAMBRE_CIVILE_1"


@pytest.mark.usefixtures("with_data")
def test_get_all_for_comm(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("CHAMBRE_COMMERCIALE", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 23
    for dec in res:
        assert dec.code_chambre == "CHAMBRE_COMMERCIALE"


@pytest.mark.usefixtures("with_data")
def test_get_all_for_soc(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("CHAMBRE_SOCIALE", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 12
    for dec in res:
        assert dec.code_chambre == "CHAMBRE_SOCIALE"


@pytest.mark.usefixtures("with_data")
def test_get_all_for_plen(service):
    loop = asyncio.get_event_loop()
    gen = service.get_summary_for_court("ASSEMBLEE_PLENIERE", size=92)
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 1
    for dec in res:
        assert dec.code_chambre == "ASSEMBLEE_PLENIERE"


@pytest.mark.usefixtures("with_data")
def test_fulltext_search(service):
    loop = asyncio.get_event_loop()
    gen = service.fulltext_search("accident gendarmerie audi")
    res = []
    count = 0
    while True:
        try:
            res.append(loop.run_until_complete(gen.__anext__()))
            count += 1
        except StopAsyncIteration:
            break
    assert count == 6
    (score, first) = res[0]
    print(score)
    assert score > 10.0
    dec = loop.run_until_complete(service.get_decision(first.identifier))
    content = "".join(
        "".join(lines) for paragraph in dec.paragraphes for lines in paragraph
    )
    assert "accident" in content
    assert "gendarmerie" in content
    assert "audi" in content
