# Graph Database Schema

This project uses Neo4j to store conversation history as a graph. Here’s how the main entities (nodes) and their relationships are structured:

## Node Types
- **User**: Represents a user of the chat system.
- **Session**: Represents a chat session (a conversation thread).
- **Question**: A message from the user (prompt to the LLM).
- **Answer**: A message from the assistant (LLM response).
- **Summary**: (Optional) A summary node for a session or part of a session.

## Relationships
- `(:User)-[:HAS_SESSION]->(:Session)`
  - Each user can have multiple sessions.
- `(:Session)-[:HAS_QUESTION]->(:Question)`
  - Each session contains multiple user questions.
- `(:Question)-[:HAS_ANSWER]->(:Answer)`
  - Each question has a corresponding assistant answer.
- `(:Session)-[:HAS_SUMMARY]->(:Summary)`
  - (Optional) A session can have one or more summary nodes for context compression or quick review.

## Example Graph Structure
```
(:User {user_id: 1})-[:HAS_SESSION]->(:Session {session_id: 1})
  -[:HAS_QUESTION]->(:Question {text: "How are you?"})
    -[:HAS_ANSWER]->(:Answer {text: "I'm just a program..."})
  -[:HAS_QUESTION]->(:Question {text: "What is Python?"})
    -[:HAS_ANSWER]->(:Answer {text: "Python is a programming language..."})
  -[:HAS_SUMMARY]->(:Summary {text: "User asked about Python and greetings..."})
```

## Visual Overview
- **User**
  - HAS_SESSION → **Session**
    - HAS_QUESTION → **Question**
      - HAS_ANSWER → **Answer**
    - HAS_SUMMARY → **Summary**

## Notes
- Each session is a separate conversation thread for a user.
- Questions and answers are always paired and linked in order.
- Summaries are optional and can be used for context window management or quick overviews.

---

You can copy this section into your README or reference it for understanding and extending the graph structure.
