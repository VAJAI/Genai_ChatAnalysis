from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFDirectoryLoader
from PyPDF2 import PdfReader  
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
import os
import shutil

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
pinecone_api_key = os.getenv("PINECONE_API_KEY")

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = "uploaded_documents/"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Upload file endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename}

# Extract text from PDFs
def get_pdf_text(pdf_path):
    text = ""
    pdf_reader = PdfReader(pdf_path)
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text  

# Load documents from directory
def read_doc(directory):
    file_loader = PyPDFDirectoryLoader(directory)
    documents = file_loader.load()
    return documents

# Define Pinecone index name
index_name = "vectorlangchain"

# Connect to Pinecone
pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index(index_name)

# Use correct embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Store document vectors in Pinecone
def store_document_vectors(docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=1000)
    
    if isinstance(docs, list) and isinstance(docs[0], str):
        docs = [Document(page_content=doc) for doc in docs]
    
    chunk_data = text_splitter.split_documents(docs)
    return chunk_data

# Store the vector data for documents in the directory (runs at startup)
docs_path = read_doc('uploaded_documents/')
chunk_datas = store_document_vectors(docs=docs_path)

# Create PineconeVectorStore
Vector_store = PineconeVectorStore.from_documents(
    documents=chunk_datas,
    embedding=embeddings,
    index_name=index_name
)

class QuestionRequest(BaseModel):
    text: str
    file: str = None  

@app.post("/ask")
async def document_chat(question: QuestionRequest):
    pdf_path = os.path.join(UPLOAD_DIRECTORY, question.file) if question.file else None
    context_text = None

    if pdf_path and os.path.exists(pdf_path):
        pdf_text = get_pdf_text(pdf_path)
        chunk_data = store_document_vectors([pdf_text])
        Vector_store.add_documents(chunk_data)
    
    # Retrieve relevant context from Pinecone
    relevant_docs = Vector_store.similarity_search(question.text, k=5)
    context_text = "\n".join([doc.page_content for doc in relevant_docs]) if relevant_docs else None

    if not context_text:
        return {"answer": "No valid context found. Upload a valid PDF file."}

    prompt_template = ChatPromptTemplate.from_template(
        """
        You are a helpful AI assistant to answer questions the based on the given document otherwise just say it IRREVELENT to this topic.
        Answer the question as detailed as possible from the provided content.
        If the answer is not in the provided context, just say: 'Answer is not available in the context.'
        Do not provide incorrect answers.
        
        Context: {Context}
        Question: {question}
        """
    )
    
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    
    llm_chain = prompt_template | llm | StrOutputParser()
    
    response = llm_chain.invoke({"Context": context_text, "question": question.text})
    return {"answer": response}
