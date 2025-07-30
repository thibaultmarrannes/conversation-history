# Conversation History LLM

This project is a conversational AI web application that allows users to chat with an LLM (Large Language Model) and keeps a persistent history of all conversations. Each session is stored, and you can view, switch, and manage multiple chat sessions. The backend is built with FastAPI (Python), and conversation history is stored in a Neo4j graph database. The frontend is a simple HTML/JS interface.

## Features
- Chat with an LLM and get responses in real time
- Persistent conversation history per session
- Sidebar to switch between sessions, each titled with the last question
- Markdown rendering for assistant responses
- Session management and history endpoints

## Requirements
- Python 3.8+
- Neo4j (local or remote)
- OpenAI API key (or compatible LLM API)

## Setup
1. **Clone the repository**
2. **Install dependencies** (see requirements.txt)
3. **Configure your `.env` file** (see below)
4. **Start Neo4j**: You can use the free [Neo4j Desktop app](https://neo4j.com/download/) for local development.
5. **Run the FastAPI server**
6. **Open `static/chat.html` in your browser**

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

## Notes
- You can download the free Neo4j Desktop app from [here](https://neo4j.com/download/) to run a local database for testing and development.
- Make sure your Neo4j instance is running and accessible before starting the FastAPI server.
- The `.env` file should be placed in the project root and will be ignored by git.

## License
MIT
  
## Graph Database Schema

This project uses Neo4j to store conversation history as a graph. Here’s how the main entities (nodes) and their relationships are structured:

### Node Types
- **User**: Represents a user of the chat system.
- **Session**: Represents a chat session (a conversation thread).
- **Question**: A message from the user (prompt to the LLM).
- **Answer**: A message from the assistant (LLM response).
- **Summary**: (Optional) A summary node for a session or part of a session.

### Relationships
- `(:User)-[:HAS_SESSION]->(:Session)`
  - Each user can have multiple sessions.
- `(:Session)-[:HAS_QUESTION]->(:Question)`
  - Each session contains multiple user questions.
- `(:Question)-[:HAS_ANSWER]->(:Answer)`
  - Each question has a corresponding assistant answer.
- `(:Session)-[:HAS_SUMMARY]->(:Summary)`
  - (Optional) A session can have one or more summary nodes for context compression or quick review.

### Example Graph Structure
```
(:User {user_id: 1})-[:HAS_SESSION]->(:Session {session_id: 1})
  -[:HAS_QUESTION]->(:Question {text: "How are you?"})
    -[:HAS_ANSWER]->(:Answer {text: "I'm just a program..."})
  -[:HAS_QUESTION]->(:Question {text: "What is Python?"})
    -[:HAS_ANSWER]->(:Answer {text: "Python is a programming language..."})
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
