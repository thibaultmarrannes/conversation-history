
# Graph Database Schema (Updated)

This project uses Neo4j to store conversation history as a graph, with advanced features for retrieval-augmented generation (RAG) and vector search.

## Node Types
- **User**: Represents a user of the chat system.
- **Session**: Represents a chat session (a conversation thread).
- **Question**: A message from the user (prompt to the LLM). Stores a combined Q&A embedding after the answer is created.
- **Answer**: A message from the assistant (LLM response).
- **Summary**: (Optional) A summary node for a session or part of a session.

## Relationships
- `(:User)-[:HAS_SESSION]->(:Session)`
  - Each user can have multiple sessions.
- `(:Session)-[:HAS_MESSAGE]->(:Question)`
  - Each session contains multiple user questions (ordered via `:NEXT` relationships).
- `(:Question)-[:HAS_ANSWER]->(:Answer)`
  - Each question has a corresponding assistant answer.
- `(:Session)-[:HAS_SUMMARY]->(:Summary)`
  - (Optional) A session can have one or more summary nodes for context compression or quick review.

## Vector Embeddings & Retrieval
- **Combined Q&A Embedding**: After an answer is created, the embedding for the concatenated Q&A (`Q: ...\nA: ...`) is stored on the `Question` node as the `embedding` property.
- **Vector Search**: The system uses the Neo4j GDS plugin to perform vector similarity search on `Question.embedding` to retrieve the most relevant Q&A pairs for a new user query.
- **Cypher for Retrieval**:
  ```cypher
  MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(:Session)-[:HAS_MESSAGE]->(q:Question)
  MATCH (q)-[:HAS_ANSWER]->(a:Answer)
  WHERE q.embedding IS NOT NULL AND size(coalesce(q.embedding, [])) > 0
  WITH q, a, gds.similarity.cosine(q.embedding, $query_embedding) AS score
  RETURN q.text AS question, a.text AS answer, score
  ORDER BY score DESC
  LIMIT 5
  ```

## Example Graph Structure
```
(:User {user_id: 1})-[:HAS_SESSION]->(:Session {session_id: 1})
  -[:HAS_MESSAGE]->(:Question {text: "How are you?", embedding: [...]})
    -[:HAS_ANSWER]->(:Answer {text: "I'm just a program..."})
  -[:HAS_MESSAGE]->(:Question {text: "What is Python?", embedding: [...]})
    -[:HAS_ANSWER]->(:Answer {text: "Python is a programming language..."})
  -[:HAS_SUMMARY]->(:Summary {text: "User asked about Python and greetings..."})
```

## Visual Overview
- **User**
  - HAS_SESSION → **Session**
    - HAS_MESSAGE → **Question**
      - HAS_ANSWER → **Answer**
    - HAS_SUMMARY → **Summary**

## Notes
- Each session is a separate conversation thread for a user.
- Questions and answers are always paired and linked in order.
- Each `Question` node only gets an embedding after its answer is created.
- Vector search only uses Q&A pairs with both a question, answer, and valid embedding.
- Summaries are optional and can be used for context window management or quick overviews.

---

You can copy this section into your README or reference it for understanding and extending the graph structure.
