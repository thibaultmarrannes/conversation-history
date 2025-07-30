
import os
from neo4j import GraphDatabase


def get_driver():
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


from datetime import datetime

def summarize_user_history(user_id: int, call_openai_func):
    """
    1. Ensure a Summary node exists for the user.
    2. Find all questions/answers for this user that have isSummarized=False or missing.
    3. Get the current summary content.
    4. Send summary + new Q/As to ChatGPT to extend the summary.
    5. Update the Summary node and mark Q/As as summarized.
    6. Return the updated summary.
    """
    driver = get_driver()
    with driver.session() as session:
        # 1. Ensure Summary node exists
        session.run(
            """
            MERGE (u:User {user_id: $user_id})
            MERGE (u)-[:HAS_SUMMARY]->(s:Summary)
            ON CREATE SET s.content = "", s.updated = datetime()
            """,
            user_id=user_id
        )

        # 2. Find unsummarized Q/As
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(sess:Session)-[:HAS_MESSAGE]->(q:Question)
            OPTIONAL MATCH (q)-[:HAS_ANSWER]->(a:Answer)
            WHERE coalesce(q.isSummarized, false) = false OR coalesce(a.isSummarized, false) = false
            RETURN q, a
            ORDER BY q.timestamp
            """,
            user_id=user_id
        )
        new_items = []
        for record in result:
            q = record["q"]
            a = record["a"]
            if q and (not q.get("isSummarized", False)):
                new_items.append(f"User: {q['text']}")
            if a and (not a.get("isSummarized", False)):
                new_items.append(f"Assistant: {a['text']}")

        # 3. Get current summary
        summary_result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_SUMMARY]->(s:Summary)
            RETURN s.content AS content
            """,
            user_id=user_id
        )
        summary_content = ""
        for rec in summary_result:
            summary_content = rec["content"] or ""

        # 4. If there are new items, extend summary with ChatGPT
        if new_items:
            prompt = (
                "Here is a running summary of the user's chat history. "
                "Please extend or update the summary to include any new relevant information that could help in understanding the user better. and optimising answers to make it more personal "
                "Keep the summary concise and factual.\n\n"
                "Do not add an intro and outro to you message, just return the updated summary. in markdown format\n\n"
                "goal here is to build a profile about me, only add necessary information.\n\n"
                f"Current summary:\n{summary_content}\n\n"
                f"New questions/answers:\n" + "\n".join(new_items)
            )
            new_summary = call_openai_func(prompt)
            # 5. Update the summary node
            session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:HAS_SUMMARY]->(s:Summary)
                SET s.content = $content, s.updated = datetime()
                """,
                user_id=user_id, content=new_summary
            )
            # 6. Mark Q/As as summarized
            session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(sess:Session)-[:HAS_MESSAGE]->(q:Question)
                OPTIONAL MATCH (q)-[:HAS_ANSWER]->(a:Answer)
                WHERE coalesce(q.isSummarized, false) = false OR coalesce(a.isSummarized, false) = false
                SET q.isSummarized = true
                SET a.isSummarized = true
                """,
                user_id=user_id
            )
            summary_content = new_summary
        # 7. Return the summary
        return summary_content
    driver.close()

    

def ensure_user_and_session(tx, user_id: str, session_id: str):
    tx.run(
        """
        MERGE (u:User {user_id: $user_id})
        MERGE (s:Session {session_id: $session_id})
        MERGE (u)-[:HAS_SESSION]->(s)
        """,
        user_id=user_id, session_id=session_id
    )

def log_question(tx, user_id: str, session_id: str, prompt: str, timestamp: str):
    # Create Question node, link to session, maintain order, update LAST_MESSAGE
    tx.run(
        """
        MATCH (s:Session {session_id: $session_id})
        OPTIONAL MATCH (s)-[:LAST_MESSAGE]->(lastMsg)
        CREATE (q:Question {text: $prompt, timestamp: $timestamp})
        MERGE (s)-[:HAS_MESSAGE]->(q)
        WITH s, q, lastMsg
        OPTIONAL MATCH (s)-[r:LAST_MESSAGE]->(lastMsg)
        DELETE r
        FOREACH (_ IN CASE WHEN lastMsg IS NOT NULL THEN [1] ELSE [] END |
            MERGE (lastMsg)-[:NEXT]->(q)
        )
        MERGE (s)-[:LAST_MESSAGE]->(q)
        """,
        session_id=session_id, prompt=prompt, timestamp=timestamp
    )

def log_answer(tx, session_id: str, answer: str, timestamp: str):
    # Create Answer node, link to last Question, and update relationships
    tx.run(
        """
        MATCH (s:Session {session_id: $session_id})-[:LAST_MESSAGE]->(q:Question)
        CREATE (a:Answer {text: $answer, timestamp: $timestamp})
        MERGE (q)-[:HAS_ANSWER]->(a)
        """,
        session_id=session_id, answer=answer, timestamp=timestamp
    )


def log_question_only(user_id: str, session_id: str, prompt: str):
    timestamp = datetime.utcnow().isoformat()
    driver = get_driver()
    with driver.session() as session:
        session.write_transaction(ensure_user_and_session, user_id, session_id)
        session.write_transaction(log_question, user_id, session_id, prompt, timestamp)
    driver.close()

def log_answer_only(session_id: str, answer: str):
    timestamp = datetime.utcnow().isoformat()
    driver = get_driver()
    with driver.session() as session:
        session.write_transaction(log_answer, session_id, answer, timestamp)
    driver.close()

def fetch_session_history(session_id: str):
    driver = get_driver()
    """
    Returns a list of dicts: [{type: 'question'/'answer', text: ..., timestamp: ...}, ...] in order for the session.
    """
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Session {session_id: $session_id})-[:HAS_MESSAGE]->(first:Question)
            OPTIONAL MATCH path = (first)-[:NEXT*0..]->(q:Question)
            WITH s, nodes(path) AS questions
            UNWIND questions AS q
            OPTIONAL MATCH (q)-[:HAS_ANSWER]->(a:Answer)
            RETURN q.text AS question, q.timestamp AS q_time, a.text AS answer, a.timestamp AS a_time
            ORDER BY q.timestamp
            """,
            session_id=session_id
        )
        history = []
        seen = set()
        for record in result:
            q_key = ("question", record["question"], record["q_time"])
            if q_key not in seen:
                history.append({
                    "type": "question",
                    "text": record["question"],
                    "timestamp": record["q_time"]
                })
                seen.add(q_key)
            if record["answer"]:
                a_key = ("answer", record["answer"], record["a_time"])
                if a_key not in seen:
                    history.append({
                        "type": "answer",
                        "text": record["answer"],
                        "timestamp": record["a_time"]
                    })
                    seen.add(a_key)
    driver.close()
    return history
