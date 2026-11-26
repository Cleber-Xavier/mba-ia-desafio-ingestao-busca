# Ingestão e Busca Semântica com LangChain e Postgres

Desafio técnico do **MBA em Engenharia de Software com IA (Full Cycle)**: um RAG mínimo que lê um PDF, guarda seu conteúdo como vetores no PostgreSQL com pgVector e responde perguntas via linha de comando **usando apenas o conteúdo do PDF**.

> Enunciado original: [devfullcycle/mba-ia-desafio-ingestao-busca](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca)

## Status

| Etapa | Situação |
|---|---|
| Banco PostgreSQL + pgVector via Docker Compose | ✅ Concluído |
| Ingestão do PDF (`src/ingest.py`) | ✅ Concluído |
| Busca semântica (`src/search.py`) | 🚧 Em desenvolvimento |
| Chat no terminal (`src/chat.py`) | 🚧 Em desenvolvimento |

## Como funciona

```
INGESTÃO (executa 1x)                         CONSULTA (a cada pergunta)
document.pdf                                  pergunta do usuário (chat.py)
  → PyPDFLoader (1 Document por página)         → embedding da pergunta
  → RecursiveCharacterTextSplitter (1000/150)   → busca dos 10 chunks mais próximos (k=10)
  → OpenAIEmbeddings (1 vetor por chunk)        → prompt com o CONTEXTO + LLM
  → PGVector (Postgres + pgVector)              → resposta no terminal
```

## Tecnologias e escolhas

| Camada | Escolha | Por quê |
|---|---|---|
| Linguagem | Python 3.13 | Obrigatório no desafio |
| Orquestração | LangChain | Loader, splitter, embeddings e vector store prontos; troca de provedor com mudança mínima |
| Banco vetorial | PostgreSQL 17 + pgVector 0.8 | Vetores e metadados no mesmo banco relacional, consultáveis com SQL |
| Infra local | Docker Compose | Banco idêntico em qualquer máquina, com um comando |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dimensões) | Modelo leve e barato; o PDF gera só 67 chunks, então a ingestão custa frações de centavo |
| LLM | OpenAI `gpt-6-luna` | Modelo mais leve e barato da família GPT-6, suficiente para "ler o contexto e responder" |

Alternativas consideradas: Google Gemini (tem plano gratuito, mas com limite de requisições por minuto e vetores de 3072 dimensões no padrão), Pinecone / Qdrant / Weaviate como banco vetorial, LlamaIndex / Haystack como orquestração.

## Pré-requisitos

- Python 3.11 ou superior
- Docker Desktop (ou Docker Engine + Compose) **em execução**
- Git
- Uma chave de API da OpenAI com crédito

## Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/Cleber-Xavier/mba-ia-desafio-ingestao-busca.git
cd mba-ia-desafio-ingestao-busca
```

### 2. Criar e ativar o ambiente virtual

Crie o `venv` **dentro da pasta do projeto**.

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
> Se o PowerShell bloquear a ativação ("execução de scripts desabilitada"), rode antes:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

```bash
cp .env.example .env              # Linux / macOS
Copy-Item .env.example .env       # Windows
```

Abra o `.env` e preencha **apenas** a `OPENAI_API_KEY`. Os demais valores já vêm prontos para o ambiente local:

| Variável | Valor padrão | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | *(vazio)* | Sua chave da OpenAI. **Nunca faça commit deste valor.** |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Modelo de embeddings |
| `OPENAI_CHAT_MODEL` | `gpt-6-luna` | Modelo que responde as perguntas |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` | Conexão com o banco do Docker Compose |
| `PG_VECTOR_COLLECTION_NAME` | `MBA` | Nome da collection no pgVector |
| `PDF_PATH` | `document.pdf` | Caminho do PDF, relativo à raiz do projeto |

O `.env` está no `.gitignore` e não é enviado ao GitHub.

## Execução

Todos os comandos são executados **a partir da raiz do projeto**, com o `venv` ativo.

### 1. Subir o banco de dados

```bash
docker compose up -d
```

Verifique se a extensão `vector` foi criada:

```bash
docker exec -it postgres_rag psql -U postgres -d rag -c "\dx"
```

A lista deve conter `vector`.

### 2. Executar a ingestão do PDF

```bash
python src/ingest.py
```

Saída esperada:

```
Páginas carregadas: 34
Chunks criados: 67
Ingestão concluída
```

Confira no banco (o total deve ser igual ao número de chunks):

```bash
docker exec -it postgres_rag psql -U postgres -d rag -c "SELECT count(*) FROM langchain_pg_embedding;"
```

### 3. Rodar o chat

🚧 Em desenvolvimento.

```bash
python src/chat.py
```

## Decisões técnicas

- **Chunks de 1000 caracteres com overlap de 150** (exigência do desafio). O overlap garante que uma linha cortada na borda de um chunk apareça inteira em pelo menos um deles. Na prática, o PDF de 34 páginas gera 67 chunks (cerca de 2 por página), porque o splitter divide cada página separadamente.
- **Ingestão idempotente (`pre_delete_collection=True`).** A ingestão apaga a collection antes de gravar. Sem isso, rodar o script duas vezes duplicava os chunks (134 em vez de 67) e a busca passava a devolver trechos repetidos.
- **Metadados em JSONB (`use_jsonb=True`).** Origem e número da página de cada chunk ficam num formato JSON pesquisável do Postgres.
- **`localhost` na conexão.** O script roda na máquina host, e o Compose publica a porta 5432 do container em `localhost:5432`. O host `postgres` só existe dentro da rede interna do Docker (é usado pelo serviço `bootstrap_vector_ext`).
- **Caminho do PDF relativo à raiz.** Por isso os scripts devem ser executados a partir da raiz do projeto (`python src/ingest.py`).
- **Troca de modelo de embeddings.** Modelos diferentes geram vetores de dimensões diferentes. Ao trocar o modelo, apague o volume do banco (`docker compose down -v`) e refaça a ingestão.

## Correção no `docker-compose.yml`

O serviço `bootstrap_vector_ext` original terminava com sucesso (`Exited (0)`), mas **não criava a extensão `vector`**. Com o `command` escrito como texto, o Docker Compose dividia o comando em vários argumentos, e o `sh -c` executava só o primeiro (`PGPASSWORD=postgres`), ignorando o `psql`.

A correção foi transformar o `command` numa lista com um único item, para que o comando inteiro chegue como um só argumento ao `sh -c`:

```yaml
    command:
      - >
        PGPASSWORD=postgres
        psql "postgresql://postgres@postgres:5432/rag" -v ON_ERROR_STOP=1
        -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Diagnóstico: `docker inspect --format "{{json .Config.Cmd}}" <container>` mostrava uma lista de 7 argumentos. Após a correção, mostra 1.

## Estrutura do projeto

```
├── docker-compose.yml    # PostgreSQL + pgVector e criação da extensão
├── requirements.txt      # Dependências
├── .env.example          # Modelo das variáveis de ambiente
├── src/
│   ├── ingest.py         # Ingestão do PDF
│   ├── search.py         # Busca semântica + LLM
│   └── chat.py           # Chat no terminal
├── document.pdf          # PDF para ingestão
└── README.md
```