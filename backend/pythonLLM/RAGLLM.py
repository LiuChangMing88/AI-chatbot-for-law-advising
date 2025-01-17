GENERATE_MODEL_NAME= "Qwen/Qwen2.5-Coder-32B-Instruct"
EMBEDDINGS_MODEL_NAME="keepitreal/vietnamese-sbert"
QDRANT_URL = "https://e8b175ef-98b7-480c-a651-92f6f634a6b9.europe-west3-0.gcp.cloud.qdrant.io:6333"
QDRANT_COLLECTION_NAME = "Law-DB-SBERT-VN-CustomChunk-vietnamese-sbert"
HUGGINGFACE_API_KEY= "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"
QDRANT_API_KEY = "yMIGHgLaj0rJzyn3sxSe5xQaOixnWo5b8eHXsJNhV_vZVdkgnoEuqA"

from langchain.retrievers import WikipediaRetriever
from langchain.vectorstores import Qdrant
from langchain.llms import HuggingFaceHub
from qdrant_client import QdrantClient
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

class LLMServe:
    def __init__(self) -> None:
        # Initialize components with direct variables
        self.embeddings = self.load_embeddings()
        self.retriever = self.load_retriever(embeddings=self.embeddings)
        self.llm = self.load_llm()
        self.prompt = self.load_prompt_template()
        self.rag_pipeline = self.load_rag_pipeline(
            llm=self.llm,
            retriever=self.retriever,
            prompt=self.prompt
        )

    def load_embeddings(self):
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDINGS_MODEL_NAME
        )
        return embeddings

    def load_retriever(self, embeddings):
        """
        Configure the retriever using Qdrant.
        """
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            prefer_grpc=False
        )
        db = Qdrant(
            client=client,
            embeddings=embeddings,
            collection_name=QDRANT_COLLECTION_NAME
        )
        base_retriever = db.as_retriever(search_kwargs={"k": 15})
        return base_retriever

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
                "top_k": 10
            },
            huggingfacehub_api_token=HUGGINGFACE_API_KEY
        )
        return llm

    def load_prompt_template(self):
        query_template = (
            "Bạn là một trợ lý tư vấn pháp luật thông minh trả lời câu hỏi dựa trên ngữ cảnh (context). \n\n"
            "### Context:\n{context} \n\n"
            "### Human: {question} \n\n"
            "### Assistant:"
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

    def rag(self):
        self.retriever = self.load_retriever(embeddings=self.embeddings)
        self.rag_pipeline = self.load_rag_pipeline(
            llm=self.llm,
            retriever=self.retriever,
            prompt=self.prompt
        )
        return self.rag_pipeline