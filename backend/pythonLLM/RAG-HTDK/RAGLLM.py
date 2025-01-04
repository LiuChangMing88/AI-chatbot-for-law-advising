GENERATE_MODEL_NAME= "Qwen/Qwen2.5-1.5B-Instruct"
EMBEDDINGS_MODEL_NAME="keepitreal/vietnamese-sbert"
QDRANT_URL = "https://e8b175ef-98b7-480c-a651-92f6f634a6b9.europe-west3-0.gcp.cloud.qdrant.io:6333"
QDRANT_COLLECTION_NAME = "Law-DB-SBERT-VN-CustomChunk-vietnamese-sbert"
HUGGINGFACE_API_KEY= "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"
QDRANT_API_KEY = "yMIGHgLaj0rJzyn3sxSe5xQaOixnWo5b8eHXsJNhV_vZVdkgnoEuqA"

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
model_rerank = AutoModelForSequenceClassification.from_pretrained('amberoad/bert-multilingual-passage-reranking-msmarco').to(device)
tokenizer_rerank = AutoTokenizer.from_pretrained('amberoad/bert-multilingual-passage-reranking-msmarco')

from langchain.schema.document import Document
from langchain.schema import BaseRetriever
from langchain.retrievers import WikipediaRetriever
from typing import List

class RerankRetriever(BaseRetriever):
    vectorstore: BaseRetriever

    def get_relevant_documents(self, query: str) -> List[Document]:
        docs = self.vectorstore.get_relevant_documents(query=query)
        candidates = [doc.page_content for doc in docs]
        queries = [query] * len(candidates)

        if tokenizer_rerank is None or model_rerank is None:
            raise ValueError("Tokenizer and model for reranking are not initialized.")

        features = tokenizer_rerank(
            queries,
            candidates,
            padding=True,
            truncation=True,
            max_length=256,  # Ensure the max_length is set to the model's max input length
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            scores = model_rerank(**features).logits
            values, indices = torch.sum(scores, dim=1).sort(descending=True)

        return [docs[idx.item()] for idx in indices[:5]]
    
from langchain.retrievers import WikipediaRetriever
from langchain.vectorstores import Qdrant
from langchain.llms import HuggingFacePipeline
from qdrant_client import QdrantClient
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA,MultiRetrievalQAChain
from langchain.llms import VLLM
from langchain.llms import HuggingFaceHub

class LLMServe:
    def __init__(self) -> None:
        self.embeddings = self.load_embeddings()
        self.retriever = self.load_retriever(embeddings=self.embeddings)
        self.pipe = self.load_model_pipeline(max_new_tokens=300)
        self.prompt = self.load_prompt_template()
        self.rag_pipeline = self.load_rag_pipeline(llm=self.pipe,
                                            retriever=self.retriever,
                                            prompt=self.prompt)
    def load_embeddings(self):
        embeddings = HuggingFaceEmbeddings(
          model_name=EMBEDDINGS_MODEL_NAME,
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
        # Use the Qdrant retriever directly
        retriever = db.as_retriever(search_kwargs={"k": 15})
        return retriever

    def load_model_pipeline(self,max_new_tokens=100):
      llm = VLLM(
          model=GENERATE_MODEL_NAME,
          trust_remote_code=True,  # mandatory for hf models
          max_new_tokens=max_new_tokens,
            # temperature=1.0,
            # top_k=50,
            # top_p=0.9,
          top_k=10,
          top_p=0.95,
          temperature=0.4,
          dtype="half",
      )
      return llm

    def load_prompt_template(self):
        query_template = "Bạn là một trợ lý tư vấn pháp luật thông minh trả lời câu hỏi dựa trên ngữ cảnh (context).\n\n### Context:{context} \n\n### Human: {question}\n\n### Assistant:"
        prompt = PromptTemplate(template=query_template,
                        input_variables= ["context","question"])
        return prompt

    def load_rag_pipeline(self,llm,retriever,prompt):
        rag_pipeline = RetrievalQA.from_chain_type(
        llm=llm, chain_type='stuff',
        retriever=retriever,
        chain_type_kwargs={
        "prompt": prompt
        },
        return_source_documents=True)
        return rag_pipeline
        
    def rag(self):
        self.retriever = self.load_retriever(embeddings=self.embeddings)
        self.rag_pipeline = self.load_rag_pipeline(llm=self.pipe,
                                      retriever=self.retriever,
                                      prompt=self.prompt)
        return self.rag_pipeline
    
# Initialize the LLMServe class
app = LLMServe()

# Get RAG pipeline
rag_pipeline = app.rag()

question = "Thanh toán, cấp kinh phí đối với phương thức đấu thầu cung ứng dịch vụ công ích thủy lợi được quy định như thế nào?"

# Get response
response = rag_pipeline({"query": question})

# Print result
print("\nAnswer:", response)