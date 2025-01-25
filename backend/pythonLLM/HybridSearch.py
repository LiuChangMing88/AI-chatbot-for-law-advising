GENERATE_MODEL_NAME= "Qwen/Qwen2.5-Coder-32B-Instruct"
EMBEDDINGS_MODEL_NAME_1 = "truro7/vn-law-embedding"
EMBEDDINGS_MODEL_NAME_2 = "tranguyen/halong_embedding-legal-document-finetune"
QDRANT_COLLECTION_NAME = "VietnamLegalText-Hybrid-title"
QDRANT_URL = url = "https://353d1aa4-a096-439c-8db8-9213123fda06.europe-west3-0.gcp.cloud.qdrant.io:6333"

from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from langchain.vectorstores import Qdrant
from langchain.llms import HuggingFaceHub
from qdrant_client import QdrantClient, models
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from typing import List, Any
from pydantic import Field
from dotenv import load_dotenv
import os

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


class FusionRetriever(BaseRetriever):
    client: Any = Field(...)
    embeddings_1: Any = Field(...)
    embeddings_2: Any = Field(...)
    collection_name: str = Field(...)
    vector_name_1: str = Field(default="vn-law-embedding")
    vector_name_2: str = Field(default="halong_embedding")

    def __init__(
        self, 
        client, 
        embeddings_1, 
        embeddings_2, 
        collection_name,
        vector_name_1="vn-law-embedding",
        vector_name_2="halong_embedding"
    ):
        super().__init__(
            client=client,
            embeddings_1=embeddings_1,
            embeddings_2=embeddings_2,
            collection_name=collection_name,
            vector_name_1=vector_name_1,
            vector_name_2=vector_name_2
        )

    def _get_relevant_documents(self, query: str) -> List[Document]:
        # Generate embeddings using both models
        vector_1 = self.embeddings_1.embed_query(query)
        vector_2 = self.embeddings_2.embed_query(query)
        
        # Set up prefetch queries for both vectors
        prefetch = [
            models.Prefetch(
                query=vector_1,
                using=self.vector_name_1,
                limit=100,
            ),
            models.Prefetch(
                query=vector_2,
                using=self.vector_name_2,
                limit=100,
            ),
        ]
        
        # Query with RRF fusion
        results = self.client.query_points(
            self.collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF,
            ),
            with_payload=True,
            limit=50,
        )

        return [
            Document(
                page_content=point.payload.get("chunk_text", ""),
                metadata=point.payload
            )
            for point in results.points
        ]

class LLMServe:
    def __init__(self) -> None:
        # Initialize components with direct variables
        self.embeddings_1 = self.load_embeddings(EMBEDDINGS_MODEL_NAME_1)
        self.embeddings_2 = self.load_embeddings(EMBEDDINGS_MODEL_NAME_2)
        self.retriever = self.load_retriever(embeddings_1=self.embeddings_1, embeddings_2=self.embeddings_2)
        self.llm = self.load_llm()
        self.prompt = self.load_prompt_template()
        self.rag_pipeline = self.load_rag_pipeline(
            llm=self.llm,
            retriever=self.retriever,
            prompt=self.prompt
        )

    def load_embeddings(self, model_name):
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name
        )
        return embeddings

    def load_retriever(self, embeddings_1, embeddings_2):
        """
        Configure the retriever using Qdrant with fusion search.
        """
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            prefer_grpc=False
        )
        
        fusion_retriever = FusionRetriever(
            client=client,
            embeddings_1=embeddings_1,
            embeddings_2=embeddings_2,
            collection_name=QDRANT_COLLECTION_NAME,
        )
        return fusion_retriever

    def load_llm(self):
        """
        Use Hugging Face Hub API for LLM.
        """
        llm = HuggingFaceHub(
            repo_id=GENERATE_MODEL_NAME,
            model_kwargs={
                "max_new_tokens": 1000,
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 10,
            },
            huggingfacehub_api_token=HUGGINGFACE_API_KEY
        )
        return llm

    def load_prompt_template(self):
        query_template = (
        "Bạn là một trợ lý tư vấn pháp luật thông minh. Bạn sẽ trả lời các câu hỏi dựa trên ngữ cảnh pháp luật đã cung cấp trong Context. "
        "Hãy đảm bảo rằng câu trả lời của bạn chi tiết, đầy đủ và chính xác. Nếu không có đủ thông tin trong Context để trả lời, hãy nói rằng bạn không có đủ thông tin để trả lời.\n\n"
        "Hãy trả lời một cách bình thường nếu như người dùng không hỏi ở phần Người dùng:"
        "### Context:\n{context}\n\n"
        "### Người dùng: {question}\n\n"
        "### Câu trả lời của bạn:\n"
        )
        prompt = PromptTemplate(
            template=query_template,
            input_variables=["context", "question"]
        )
        return prompt

    def load_rag_pipeline(self, llm, retriever, prompt):
        rag_pipeline = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": prompt
            },
            return_source_documents=True
        )
        return rag_pipeline


    def load_rag_pipeline(self, llm, retriever, prompt):
        rag_pipeline = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": prompt
            },
            return_source_documents=True
        )
        return rag_pipeline

    def rag(self):
        self.retriever = self.load_retriever(embeddings=self.embeddings)
        self.rag_pipeline = self.load_rag_pipeline(
            llm=self.llm,
            retriever=self.retriever,
            prompt=self.prompt
        )
        return self.rag_pipeline
    
llm_service = LLMServe()

def get_response(query: str):
    response = llm_service.rag_pipeline({"query": query})
    return response