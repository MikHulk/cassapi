import asyncio
from contextlib import asynccontextmanager
import os
import sys

from elasticsearch import AsyncElasticsearch, Elasticsearch

from app.exceptions import ConfigurationError


def get_config_from_env():
    try:
        return {
            "passwd": os.environ["ELASTIC_PASSWORD"],
            "user": os.environ["ELASTIC_USER"],
            "url": os.environ["ELASTIC_URL"],
            "ca_certs": os.environ["ELASTIC_CERTS_PATH"],
        }
    except KeyError:
        raise ConfigurationError("No ES configuration in the environment")


@asynccontextmanager
async def async_client():
    """Context manager providing an async client for ES provided
    that ELASTIC_USER, ELASTIC_PASSWORD, ELASTIC_CERTS_PATH and
    ELASTIC_URL are set in the environment.
    """
    config = get_config_from_env()
    client = AsyncElasticsearch(
        config["url"],
        ca_certs=config["ca_certs"],
        basic_auth=(config["user"], config["passwd"]),
    )
    try:
        yield client
    finally:
        await client.close()


def get_client(config=None):
    """Convenient function aimed at providing a sync ES client for testing
    purpose. The caller is responsible for closing the session.
    One can provide client config with kw "config" or set them in the
    environment.
    """
    config = config or get_config_from_env()
    return Elasticsearch(
        config["url"],
        ca_certs=config["ca_certs"],
        basic_auth=(config["user"], config["passwd"]),
    )


if __name__ == "__main__":
    from pprint import pprint

    async def main():
        async with async_client() as client:
            resp = await client.info()
        pprint(dict(resp))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
