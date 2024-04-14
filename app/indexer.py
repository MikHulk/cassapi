from app.es import async_client


class Indexer:
    """Utility class for indexing a document from legifrance under
    a specific index.
    """

    def __init__(self, index):
        self.index = index

    @staticmethod
    def prepare_document(parser):
        """Takes a parser instance and prepare the document for indexing."""
        return {
            "identifier": parser.identifier,
            "numero": parser.numero,
            "title": parser.title,
            "date": parser.date,
            "chambre": parser.chambre,
            "code_chambre": parser.code_chambre,
            "solution": parser.solution,
            "paragraphes": parser.paragraphes,
            "arret": parser.num_arrêt,
            "pourvoi": parser.num_pourvoi,
            "liens": parser.liens,
        }

    async def index_doc(self, parser):
        """Indexes a document using `parser.identifier` as id."""
        document = Indexer.prepare_document(parser)
        async with async_client() as client:
            resp = await client.index(
                index=self.index,
                document=document,
                id=parser.identifier,
            )
        return resp
