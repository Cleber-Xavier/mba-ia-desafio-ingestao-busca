import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

load_dotenv()

OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")
DATABASE_URL = os.getenv("DATABASE_URL")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")


PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def search_prompt(question=None):
    if not OPENAI_EMBEDDING_MODEL or not OPENAI_CHAT_MODEL or not DATABASE_URL or not PG_VECTOR_COLLECTION_NAME:
        print("Erro: variáveis faltando no .env. Confira os modelos, DATABASE_URL e PG_VECTOR_COLLECTION_NAME.")
        return None

    # ---- PREPARAR (roda UMA vez) ----
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=PG_VECTOR_COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
    )
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL)

    # ---- RESPONDER (roda a CADA pergunta) ----
    def responder(pergunta):
        resultados = vector_store.similarity_search_with_score(pergunta, k=10)
        contexto = "\n\n".join(doc.page_content for doc, _ in resultados)
        prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=pergunta)
        resposta = llm.invoke(prompt)
        return resposta.content

    return responder


if __name__ == "__main__":
    responder = search_prompt()
    print(responder("Qual o faturamento da Alfa Energia S.A.?"))    