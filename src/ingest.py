import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
DATABASE_URL = os.getenv("DATABASE_URL")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")



def ingest_pdf():
    # 1. Validar: todas as variáveis existem? O arquivo do PDF existe?
    #    (falhar cedo, com mensagem clara)

    # 2. Carregar o PDF -> lista de Document (1 por página). Imprimir quantas páginas.
    loader = PyPDFLoader(PDF_PATH)
    paginas = loader.load()
    print(f"Páginas carregadas: {len(paginas)}")
    

    # 3. Dividir em chunks de 1000 com overlap de 150. Imprimir quantos chunks.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(paginas)
    print(f"Chunks criados: {len(chunks)}")
   
    # 4. Criar o objeto de embeddings com o modelo do .env
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    # 5. Criar o PGVector (embeddings + nome da collection + conexão)
    #    e adicionar os chunks. Imprimir "Ingestão concluída".
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=PG_VECTOR_COLLECTION_NAME,
        pre_delete_collection=True,
        connection=DATABASE_URL,
        use_jsonb=True,
    )
    vector_store.add_documents(chunks)
    print("Ingestão concluída")
    


if __name__ == "__main__":
    ingest_pdf()