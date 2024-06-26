
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains import RetrievalQA
from langchain.schema.output_parser import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain.vectorstores.utils import filter_complex_metadata


class ChatPDF:
    vector_store = None
    retriever = None
    chain = None

    def __init__(self):
        self.model = ChatOllama(model="mistral")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, chunk_overlap=20)
        self.prompt = PromptTemplate.from_template(
            """
            <s> [INST] You are an assistant for question-answering tasks. 
            Use the following context to answer the question. If you don't 
            know the answer, just say you don't know. Use three sentences 
            and be concise in your answer. [/INST] </s> 
            [INST] Question: {question} 
            Context: {context} 
            Answer: [/INST]
            """
        )

    def ingest(self, url: str):
        loader = WebBaseLoader(url)
        docs = loader.load()
        chunks = self.text_splitter.split_documents(docs)
        chunks = filter_complex_metadata(chunks)

        vector_store = Chroma.from_documents(
            documents=chunks, embedding=GPT4AllEmbeddings())
        self.retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 3,
                "score_threshold": 0.5,
            },
        )

        self.chain = RetrievalQA.from_chain_type(self.model, retriever=vector_store.as_retriever())


    def ask(self, query: str):
        if not self.chain:
            return "Please, add a URL first."
        invocation = self.chain.invoke(query)
        print(invocation)
        return invocation['result']

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None
