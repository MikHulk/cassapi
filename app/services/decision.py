from datetime import datetime, timedelta
from functools import lru_cache

import elasticsearch

from app.es import async_client
from app.model import Decision, DecisionSummary


class DecisionService:
    """Manages data fetch from the Elastic Search backend."""

    KEEP = timedelta(minutes=5)

    def __init__(self, index):
        self.index = index
        self._count = None
        self.count_last_refresh = None
        self._count_court = {}

    @property
    async def count(self):
        """Count of document indexed on the backend."""
        if self._count is None or self.count_last_refresh + self.KEEP < datetime.now():
            self.count_last_refresh = datetime.now()
            async with async_client() as client:
                resp = await client.count(
                    index=self.index,
                    query={"match_all": {}},
                )
            self._count = resp["count"]
        return self._count

    async def count_court(self, court):
        """Count of document indexed on the backend for a specific court."""
        if (
            court not in self._count_court
            or self._count_court[court]["last_refresh"] + self.KEEP < datetime.now()
        ):

            async with async_client() as client:
                resp = await client.count(
                    index=self.index,
                    query={"match": {"code_chambre": court.lower()}},
                )
            self._count_court[court] = {
                "_last_refresh": datetime.now(),
                "count": resp["count"],
            }
        return self._count_court[court]["count"]

    async def get_summary_for_court(self, court, cursor=0, size=None):
        """Retrieves a summary of indexed documents for a specific court."""

        async with async_client() as client:
            resp = await client.search(
                index=self.index,
                fields=["title", "identifier", "code_chambre"],
                query={"match": {"code_chambre": court.lower()}},
                sort=[{"date": {"order": "asc", "format": "strict_date"}}],
                size=size,
                from_=cursor,
                _source=False,
            )
        for item in resp["hits"]["hits"]:
            yield DecisionSummary(
                identifier=item["fields"]["identifier"][0],
                title=item["fields"]["title"][0],
                code_chambre=item["fields"]["code_chambre"][0],
            )

    async def get_summary(self, cursor=0, size=None):
        """Retrieves a summary of indexed documents for all courts."""
        async with async_client() as client:
            resp = await client.search(
                index=self.index,
                fields=["title", "identifier", "code_chambre"],
                query={"match_all": {}},
                sort=[{"date": {"order": "asc", "format": "strict_date"}}],
                size=size,
                from_=cursor,
                _source=False,
            )
        for item in resp["hits"]["hits"]:
            yield DecisionSummary(
                identifier=item["fields"]["identifier"][0],
                title=item["fields"]["title"][0],
                code_chambre=item["fields"]["code_chambre"][0],
            )

    async def get_decision(self, identifier):
        """Get the detail of a decision with its identifier."""
        async with async_client() as client:
            try:
                resp = await client.get(index=self.index, id=identifier)
            except elasticsearch.NotFoundError:
                return None
        payload = resp["_source"]
        return Decision(
            title=payload["title"],
            identifier=payload["identifier"],
            numero=payload["numero"],
            paragraphes=payload["paragraphes"],
            chambre=payload["chambre"],
            code_chambre=payload["code_chambre"],
        )

    async def fulltext_search(self, query):
        """Performs a fulltext search on the indexed documents."""

        async with async_client() as client:
            resp = await client.search(
                index=self.index,
                fields=["title", "identifier", "code_chambre"],
                query={"match": {"paragraphes": {"query": query}}},
                _source=False,
            )
        for item in resp["hits"]["hits"]:
            yield (
                item["_score"],
                DecisionSummary(
                    identifier=item["fields"]["identifier"][0],
                    title=item["fields"]["title"][0],
                    code_chambre=item["fields"]["code_chambre"][0],
                ),
            )
