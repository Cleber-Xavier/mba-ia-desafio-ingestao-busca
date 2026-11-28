# Ingestão e Busca Semântica com LangChain e Postgres

Desafio técnico do **MBA em Engenharia de Software com IA (Full Cycle)**: um RAG que lê um PDF, guarda seu conteúdo como vetores no PostgreSQL com pgVector e responde perguntas via linha de comando **usando apenas o conteúdo do PDF**.

> Enunciado original: [devfullcycle/mba-ia-desafio-ingestao-busca](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca)

## Status

| Etapa | Situação |
|---|---|
| Banco PostgreSQL + pgVector via Docker Compose | ✅ Concluído |
| Ingestão do PDF (`src/ingest.py`) | ✅ Concluído |
| Busca semântica + LLM (`src/search.py`) | ✅ Concluído |
| Chat no terminal (`src/chat.py`) | ✅ Concluído |
| Testes de comportamento ([`docs/caderno-de-testes.xlsx`](docs/caderno-de-testes.xlsx)) | ✅ 11 casos executados |

## Exemplo de uso

```
$ python src/chat.py
Faça sua pergunta (digite 'sair' para encerrar):

PERGUNTA: Qual é o faturamento da Alfa Energia S.A.?
RESPOSTA: R$ 722.875.391,46

PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

PERGUNTA: sair
Até logo!
```

## Como funciona

```
INGESTÃO (executa 1x)                         CONSULTA (a cada pergunta)
document.pdf                                  pergunta do usuário (chat.py)
  → PyPDFLoader (1 Document por página)         → embedding da pergunta
  → RecursiveCharacterTextSplitter (1000/150)   → busca dos 10 chunks mais próximos (k=10)
  → OpenAIEmbeddings (1 vetor por chunk)        → prompt com o CONTEXTO + LLM
  → PGVector (Postgres + pgVector)              → resposta no terminal
```

O PDF é uma tabela com **1.001 empresas** (nome, faturamento e ano de fundação) em 34 páginas, que geram **67 chunks**.

## Tecnologias e escolhas

| Camada | Escolha | Por quê |
|---|---|---|
| Linguagem | Python 3.13 | Obrigatório no desafio |
| Orquestração | LangChain | Loader, splitter, embeddings e vector store prontos; troca de provedor com mudança mínima |
| Banco vetorial | PostgreSQL 17 + pgVector 0.8 | Vetores e metadados no mesmo banco relacional, consultáveis com SQL |
| Infra local | Docker Compose | Banco idêntico em qualquer máquina, com um comando |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dimensões) | Modelo leve e barato; a ingestão dos 67 chunks custa frações de centavo |
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

> As variáveis `GOOGLE_API_KEY` e `GOOGLE_EMBEDDING_MODEL` foram mantidas no `.env.example` de propósito, para facilitar uma futura troca para o Gemini. O projeto atual usa apenas OpenAI.

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

```bash
python src/chat.py
```

Digite a pergunta e pressione Enter. Para encerrar, digite `sair` ou pressione **Ctrl+C**.

## Testes

Os testes de comportamento estão documentados em [`docs/caderno-de-testes.xlsx`](docs/caderno-de-testes.xlsx), com pergunta, resultado esperado (conferido no PDF), resposta obtida e status de cada caso.

| Bloco | Casos | Resultado |
|---|---|---|
| A. Respostas do PDF (início, meio e fim do documento) | 3 | ✅ 3 aprovados |
| B. Perguntas fora de contexto (as 3 do enunciado) | 3 | ✅ 3 aprovados |
| C. "Meio dentro": assunto do PDF, dado inexistente | 2 | ✅ 2 aprovados |
| D. Agregação | 1 | ❌ 1 reprovado (limitação conhecida, abaixo) |
| E. Robustez do chat (entrada vazia, Ctrl+C) | 2 | ✅ 2 aprovados |
| **Total** | **11** | **10 aprovados, 1 reprovado** |

Destaques:
- **Não confunde dados parecidos (C1, C2):** perguntado sobre o *lucro* e o *número de funcionários* da Alfa Energia S.A., que não existem no PDF, o chat responde a frase padrão em vez de devolver o faturamento ou inventar um número. É o erro mais perigoso de um RAG, e o prompt com as regras do enunciado o evitou.
- **Recupera o fim do documento (A3):** o ano de fundação da Ímpar Turismo Comércio, na última página, veio correto.
- **Tolera variações de grafia:** "ALPHA ENERGIA" (com PH e em maiúsculas) encontrou a Alfa Energia S.A., e "Impar" (sem acento) encontrou a Ímpar Turismo Comércio. A busca semântica compara significados, não letras.

## Limitações conhecidas

**Perguntas de agregação não são respondidas corretamente** ("qual a maior", "quantas", "qual a média").

A busca semântica recupera os **10 chunks mais parecidos com a pergunta**, ou seja, cerca de 15% do PDF (10 de 67). Uma pergunta como "qual a empresa com maior faturamento?" exige comparar **todas** as 1.001 linhas, mas a LLM só vê as que vieram nesses 10 chunks e responde o maior **entre elas**, como se fosse o maior do documento.

Evidência dos testes:

| Pergunta | Resposta do chat | Correto (conferido no PDF) |
|---|---|---|
| "Qual a empresa com maior faturamento?" | Aliança Esportes ME, R$ 4.485.320.049,16 | **Vanguarda Siderurgia Participações, R$ 4.984.749.742,20** (pág. 29) |
| "Empresa maior faturamento" | Bronze Ambiental Holding, R$ 3.609.370.916,29 | idem |

Além de erradas, as respostas **mudam com a redação da pergunta**, porque cada redação gera um embedding diferente e traz outros 10 chunks.

Como resolver fora do escopo deste desafio: extrair a tabela para uma tabela SQL e responder agregações com consultas (`ORDER BY ... LIMIT 1`), ou usar um agente que decide entre a busca semântica e uma consulta SQL conforme o tipo de pergunta.

## Decisões técnicas

- **Chunks de 1000 caracteres com overlap de 150** (exigência do desafio). O overlap garante que uma linha cortada na borda de um chunk apareça inteira em pelo menos um deles. O PDF de 34 páginas gera 67 chunks (cerca de 2 por página), porque o splitter divide cada página separadamente.
- **Ingestão idempotente (`pre_delete_collection=True`).** A ingestão apaga a collection antes de gravar. Sem isso, rodar o script duas vezes duplicava os chunks (134 em vez de 67) e a busca passava a devolver trechos repetidos. A busca (`search.py`) **não** usa esse parâmetro, pois apagaria os dados.
- **Preparar uma vez, responder muitas.** `search_prompt()` cria embeddings, conexão e LLM uma única vez e devolve a função `responder(pergunta)`, que o `chat.py` chama a cada pergunta. Se alguma variável de ambiente faltar, devolve `None` e o chat avisa e encerra.
- **Validação antes de começar.** A ingestão confere as variáveis de ambiente e a existência do PDF e encerra com uma mensagem clara (`SystemExit`, sem traceback) se algo faltar.
- **Metadados em JSONB (`use_jsonb=True`).** Origem e número da página de cada chunk ficam num formato JSON pesquisável do Postgres.
- **`localhost` na conexão.** O script roda na máquina host, e o Compose publica a porta 5432 do container em `localhost:5432`. O host `postgres` só existe dentro da rede interna do Docker (é usado pelo serviço `bootstrap_vector_ext`).
- **Caminho do PDF relativo à raiz.** Por isso os scripts devem ser executados a partir da raiz do projeto (`python src/ingest.py`).
- **Encerramento limpo do chat.** `sair`, Ctrl+C ou Ctrl+Z (fim de entrada) encerram com "Até logo!", sem traceback.
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
├── docker-compose.yml        # PostgreSQL + pgVector e criação da extensão
├── requirements.txt          # Dependências
├── .env.example              # Modelo das variáveis de ambiente
├── src/
│   ├── ingest.py             # Ingestão do PDF
│   ├── search.py             # Busca semântica + LLM
│   └── chat.py               # Chat no terminal
├── docs/
│   └── caderno-de-testes.xlsx  # Casos de teste e resultados
├── document.pdf              # PDF para ingestão
└── README.md
```
