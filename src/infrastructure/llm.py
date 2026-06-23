from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain.chains import RetrievalQA
from src.core.interfaces import LanguageModel, VectorStore

class TinyLlamaModel(LanguageModel):
    def __init__(self, model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        pipe = pipeline(
            "text-generation", 
            model=model_id, 
            device_map="auto",
            max_new_tokens=512, 
            do_sample=True, 
            temperature=0.7, 
            top_k=50, 
            top_p=0.95,
            return_full_text=False,
            clean_up_tokenization_spaces=False
        )
        self.llm = HuggingFacePipeline(pipeline=pipe)

    def generate(self, prompt: str) -> str:
        return self.llm.invoke(prompt)

class RAGChain:
    """Uma classe utilitária para orquestrar a cadeia de busca e geração."""
    def __init__(self, llm: TinyLlamaModel, vector_store: VectorStore):
        # Como o LangChain RetrievalQA espera um retriever específico do LangChain:
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm.llm,
            chain_type="stuff",
            retriever=vector_store.db.as_retriever(search_kwargs={"k": 2})
        )

    def ask(self, query: str) -> str:
        response = self.qa_chain.invoke(query)
        return response['result']
