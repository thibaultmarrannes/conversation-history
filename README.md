
# Conversation History LLM

This project is a production-ready conversational AI backend and web application. It allows users to chat with an LLM (Large Language Model) and keeps a persistent history of all conversations. Each session is stored, and you can view, switch, and manage multiple chat sessions. The backend is built with FastAPI (Python), and conversation history is stored in a Neo4j graph database. The frontend is a simple HTML/JS interface. Advanced features include retrieval-augmented generation (RAG) using OpenAI embeddings and Neo4j vector search.

## Features
- Chat with an LLM and get responses in real time
- Persistent conversation history per session
- Sidebar to switch between sessions, each titled with the last question
- Markdown rendering for assistant responses
- Session management and history endpoints
- Combined Q&A embeddings for retrieval-augmented generation (RAG)
- Vector search using OpenAI embeddings and Neo4j GDS
- Robust to missing/null embeddings (only valid Q&A pairs are used for retrieval)
- Detailed error logging for debugging

## Requirements
- Python 3.9+
- Neo4j 5.x (with APOC and GDS plugins enabled)
- OpenAI API key (or compatible LLM API)

**Important:**
- The Neo4j database should have the **Graph Data Science (GDS)** plugin and the **APOC** plugin installed and enabled. You can install these from the Neo4j Desktop dashboard (Plugins tab for your database). These plugins are required for advanced graph and vector operations.

## Setup
1. **Clone the repository**
2. **Install dependencies** (see requirements.txt)
3. **Configure your `.env` file** (see below)
4. **Start Neo4j**: You can use the free [Neo4j Desktop app](https://neo4j.com/download/) for local development. Ensure APOC and GDS plugins are enabled.
5. **Run the FastAPI server**

## Example `.env` file
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
OPENAI_API_KEY=your_openai_api_key
```

- `NEO4J_URI`: The connection URI for your Neo4j instance (default for local is `bolt://localhost:7687`)
- `NEO4J_USER`: Your Neo4j username (default is `neo4j`)
- `NEO4J_PASSWORD`: Your Neo4j password
- `OPENAI_API_KEY`: Your OpenAI API key (or compatible LLM API key)

> Place the `.env` file in the project root. It will be ignored by git.


## Endpoints
- `/echo` - Main chat endpoint (POST: user message, session_id)
- `/history` - Get session history (GET: session_id)
- `/sessions` - List all sessions for a user (GET: user_id)

## Graph Schema
See [graph_schema.md](graph_schema.md) for a detailed schema diagram and explanation.

## Vector Search & Embeddings
- After each Q&A pair, a combined embedding is generated using OpenAI's `text-embedding-ada-002` and stored on the `Question` node as the `embedding` property.
- The Neo4j GDS plugin is used to perform vector similarity search for relevant Q&A pairs to provide context to the LLM.
- Only Q&A pairs with valid embeddings are used for retrieval (null or missing embeddings are skipped).

## Error Handling
- All errors are logged to `error.log` with detailed tracebacks for debugging.
- The system is robust to missing or null embeddings and will skip such Q&A pairs during vector search.

## Plugins Required in Neo4j
- APOC (for utility procedures)
- GDS (Graph Data Science, for vector search)

## Example Cypher for Vector Search
```
MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(:Session)-[:HAS_MESSAGE]->(q:Question)
MATCH (q)-[:HAS_ANSWER]->(a:Answer)
WHERE q.embedding IS NOT NULL AND size(coalesce(q.embedding, [])) > 0
WITH q, a, gds.similarity.cosine(q.embedding, $query_embedding) AS score
RETURN q.text AS question, a.text AS answer, score
ORDER BY score DESC
LIMIT 5
```

## License
MIT
  -[:HAS_SUMMARY]->(:Summary {text: "User asked about Python and greetings..."})
```

### Visual Overview
- **User**
  - HAS_SESSION → **Session**
    - HAS_QUESTION → **Question**
      - HAS_ANSWER → **Answer**
    - HAS_SUMMARY → **Summary**

### Notes
- Each session is a separate conversation thread for a user.
- Questions and answers are always paired and linked in order.
- Summaries are optional and can be used for context window management or quick overviews.
