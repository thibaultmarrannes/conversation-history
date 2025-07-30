

# main.py

from dotenv import load_dotenv
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
import uvicorn

from graph import log_question_only, log_answer_only, fetch_session_history, summarize_user_history, get_relevant_context
from llm import call_openai

# Ensure vector indexes exist in Neo4j at startup
try:
    from init import ensure_vector_indexes
    ensure_vector_indexes()
except Exception as e:
    print(f"[WARNING] Could not ensure Neo4j vector indexes: {e}")

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


# Endpoint to fetch session history for the chat UI
@app.get("/history")
async def get_history(session_id: int):
    history = fetch_session_history(session_id)
    return JSONResponse({"history": history})

@app.get("/sessions")
async def get_sessions(user_id: int):
    from graph import get_driver
    driver = get_driver()
    sessions = []
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(s:Session)
            OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(q:Question)
            WITH s, q
            ORDER BY s.session_id, q.timestamp DESC
            WITH s.session_id AS session_id, collect(q.text)[0] AS last_question
            RETURN session_id, last_question
            ORDER BY session_id
            """,
            user_id=user_id
        )
        for record in result:
            # Truncate question to 60 chars, remove newlines
            title = (record["last_question"] or "(no question)").replace("\n", " ")
            if len(title) > 60:
                title = title[:57] + "..."
            sessions.append({"session_id": record["session_id"], "title": title})
    driver.close()
    return {"sessions": sessions}




class PromptRequest(BaseModel):
    user_id: int
    session_id: int
    prompt: str

@app.post("/echo")
async def echo_prompt(request: PromptRequest):
    # 1. Store the question
    log_question_only(request.user_id, request.session_id, request.prompt)
    # 2. Fetch session history
    history = fetch_session_history(request.session_id)
    # Fetch user summary and add to context window
    summary = summarize_user_history(request.user_id, call_openai)
    # Fetch highly relevant content and add to context window
    relevant_context = get_relevant_context(request.user_id, request.prompt)
    # Debug: log length and content of history
    print(f"[DEBUG] History length: {len(history)}")
    for idx, msg in enumerate(history):
        print(f"[DEBUG] {idx}: {msg}")

    # Deduplicate consecutive identical messages (by type and text)
    deduped_history = []
    prev = None
    for msg in history:
        if prev is None or (msg["type"], msg["text"]) != (prev["type"], prev["text"]):
            deduped_history.append(msg)
        prev = msg

    # 3. Build prompt for OpenAI as per user instructions
    # 1. This is the question
    prompt_sections = [f"This is the question:\n{request.prompt.strip()}"]

    # 2. IF it helps, this is some context regarding the conversation
    if deduped_history:
        context_lines = []
        for msg in deduped_history:
            prefix = "User:" if msg["type"] == "question" else "Assistant:"
            context_lines.append(f"{prefix} {msg['text']}")
        prompt_sections.append("If it helps, this is some context regarding the conversation so far:\n" + "\n".join(context_lines))

    # 3. Add most relevant context for this query
    if relevant_context:
        rel_lines = []
        for item in relevant_context:
            rel_lines.append(f"User: {item['question']}")
            if item['answer']:
                rel_lines.append(f"Assistant: {item['answer']} (score: {item['score']:.2f})")
        prompt_sections.append("These are the most relevant questions and answers from the past for this query:\n" + "\n".join(rel_lines))

    # 4. Some extra context is this summary that I have about the user. Only use it if it helps to answer the question
    if summary:
        prompt_sections.append("Some extra context is this summary that I have about the user. Only use it if it helps to answer the question:\n" + summary.strip())

    full_prompt = "\n\n".join(prompt_sections)
    # Log the relevant context, prompt, and answer to history.log
    answer = call_openai(full_prompt)
    with open("history.log", "a") as log_file:
        log_file.write(f"user_id={request.user_id}, session_id={request.session_id}\n")
        if relevant_context:
            rel_lines = []
            for item in relevant_context:
                rel_lines.append(f"User: {item['question']}")
                if item['answer']:
                    rel_lines.append(f"Assistant: {item['answer']} (score: {item['score']:.2f})")
            log_file.write("Most relevant questions and answers for this query (vector search):\n" + "\n".join(rel_lines) + "\n")
        log_file.write(f"PROMPT TO LLM:\n{full_prompt}\n")
        log_file.write(f"Assistant: {answer}\n")
        log_file.write(f"{'-'*40}\n")
    # 5. Store the answer
    log_answer_only(request.session_id, answer)
    # 6. Return the answer
    return {"answer": answer}

if __name__ == "__main__":

    # Start FastAPI app for manual testing
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
