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


def testar_busca(pergunta):
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=PG_VECTOR_COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
    )
    resultados = vector_store.similarity_search_with_score(pergunta, k=10)

    print(f"Resultados encontrados: {len(resultados)}")
    for doc, score in resultados:
        print(f"[score {score:.4f}] {doc.page_content[:80]}")

    contexto = "\n\n".join(doc.page_content for doc, _ in resultados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=pergunta)

    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL)
    resposta = llm.invoke(prompt)

    print("\nRESPOSTA:", resposta.content)
    return resposta.content


def search_prompt(question=None):
    if question is None:
        question = input("Faça sua pergunta: ").strip()
    if not question:
        return None
    return testar_busca(question)


if __name__ == "__main__":
    search_prompt()
    