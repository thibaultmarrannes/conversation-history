import os
from neo4j import GraphDatabase

VECTOR_INDEX_QUES = "question_embedding_index"
VECTOR_INDEX_ANS = "answer_embedding_index"
VECTOR_DIM = 1536
SIM_FUNCTION = "cosine"

def get_driver():
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def ensure_vector_indexes():
    driver = get_driver()
    with driver.session() as session:
        # Question vector index
        session.run(f'''
            CREATE VECTOR INDEX {VECTOR_INDEX_QUES} IF NOT EXISTS
            FOR (q:Question)
            ON (q.embedding)
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: {VECTOR_DIM},
                `vector.similarity_function`: '{SIM_FUNCTION}'
              }}
            }}
        ''')
     
    driver.close()

if __name__ == "__main__":
    ensure_vector_indexes()
