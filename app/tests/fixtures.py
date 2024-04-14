import os

from pytest import fixture

from app.es import get_client
from app.legifrance.parser import Parser


DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


@fixture(scope="session")
def parser():
    yield Parser.from_file(os.path.join(DATA_DIR, "test.xml"))


@fixture(scope="session")
def client():
    print("open ES session")
    client = get_client()
    yield client
    print("close ES session")
    client.close()
