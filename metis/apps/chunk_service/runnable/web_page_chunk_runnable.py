from typing import List

from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langserve import add_routes

from apps.chunk_service.runnable.base_chunk_runnable import BaseChunkRunnable
from apps.chunk_service.user_types.web_page_chunk_request import WebPageChunkRequest


class WebPageChunkRunnable(BaseChunkRunnable):
    def __init__(self):
        pass

    def parse(self, request: WebPageChunkRequest) -> List[Document]:
        loader = RecursiveUrlLoader(request.url, max_depth=request.max_depth)
        web_docs = loader.load()
        transformer = BeautifulSoupTransformer()
        docs = transformer.transform_documents(web_docs)
        return self.parse_docs(docs, request)

    def register(self, app):
        add_routes(app,
                   RunnableLambda(self.parse).with_types(input_type=WebPageChunkRequest, output_type=List[Document]),
                   path='/webpage_chunk')

