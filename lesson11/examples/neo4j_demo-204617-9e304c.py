import os
from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def erase_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def build_knowledge_graph(tx):
    # small toy graph: people, companies, tech, cities
    tx.run("""
        CREATE
            (alice:Person {name: 'Alice', role: 'ML Engineer'}),
            (bob:Person {name: 'Bob', role: 'Data Scientist'}),
            (carol:Person {name: 'Carol', role: 'CTO'}),
            (dave:Person {name: 'Dave', role: 'Researcher'}),

            (neuro:Company {name: 'NeuroTech', founded: 2019}),
            (forge:Company {name: 'DataForge', founded: 2017}),
            (graph:Company {name: 'GraphLabs', founded: 2021}),

            (python:Technology {name: 'Python', category: 'language'}),
            (neo4j:Technology {name: 'Neo4j', category: 'database'}),
            (llm:Technology {name: 'Transformers', category: 'ml'}),
            (rag:Technology {name: 'RAG', category: 'ml'}),

            (berlin:City {name: 'Berlin', country: 'Germany'}),
            (london:City {name: 'London', country: 'UK'}),
            (sf:City {name: 'San Francisco', country: 'USA'}),

            (alice)-[:WORKS_AT {since: 2021}]->(neuro),
            (bob)-[:WORKS_AT {since: 2018}]->(forge),
            (carol)-[:WORKS_AT {since: 2021}]->(graph),
            (carol)-[:FOUNDED]->(graph),
            (dave)-[:WORKS_AT {since: 2020}]->(neuro),

            (alice)-[:KNOWS]->(bob),
            (bob)-[:KNOWS]->(carol),
            (dave)-[:KNOWS]->(alice),

            (alice)-[:KNOWS_TECH]->(python),
            (alice)-[:KNOWS_TECH]->(llm),
            (alice)-[:KNOWS_TECH]->(rag),
            (bob)-[:KNOWS_TECH]->(python),
            (bob)-[:KNOWS_TECH]->(neo4j),
            (carol)-[:KNOWS_TECH]->(neo4j),
            (carol)-[:KNOWS_TECH]->(rag),
            (dave)-[:KNOWS_TECH]->(llm),

            (neuro)-[:LOCATED_IN]->(berlin),
            (forge)-[:LOCATED_IN]->(london),
            (graph)-[:LOCATED_IN]->(sf),
            (neuro)-[:USES]->(llm),
            (neuro)-[:USES]->(rag),
            (forge)-[:USES]->(python),
            (forge)-[:USES]->(neo4j),
            (graph)-[:USES]->(neo4j),
            (graph)-[:USES]->(rag)
        """)


def show(session, title, cypher):
    print("\n---", title)
    print(cypher.strip())
    for row in session.run(cypher):
        print(dict(row))


def run_demo():
    with driver.session(database=NEO4J_DATABASE) as session:
        session.execute_write(erase_graph)
        session.execute_write(build_knowledge_graph)
        print("graph built")

        # basic match
        show(session, "all people", """
            MATCH (p:Person)
            RETURN p.name AS name, p.role AS role
            ORDER BY name
        """)

        # pattern with a relationship
        show(session, "who works at NeuroTech", """
            MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: 'NeuroTech'})
            RETURN p.name AS employee, p.role AS role
        """)

        # filter on relationship property
        show(session, "joined in 2020 or later", """
            MATCH (p:Person)-[r:WORKS_AT]->(c:Company)
            WHERE r.since >= 2020
            RETURN p.name AS employee, c.name AS company, r.since AS since
            ORDER BY since
        """)

        # two hops
        show(session, "tech used at Alice's company", """
            MATCH (p:Person {name: 'Alice'})-[:WORKS_AT]->(c:Company)-[:USES]->(t:Technology)
            RETURN c.name AS company, collect(t.name) AS technologies
        """)

        # variable-length path
        show(session, "path Alice -> Carol via KNOWS", """
            MATCH path = (a:Person {name: 'Alice'})-[:KNOWS*1..3]->(c:Person {name: 'Carol'})
            RETURN [n IN nodes(path) | n.name] AS chain, length(path) AS hops
        """)

        # aggregation
        show(session, "headcount per company", """
            MATCH (p:Person)-[:WORKS_AT]->(c:Company)
            RETURN c.name AS company, count(p) AS headcount
            ORDER BY headcount DESC
        """)

        # negative pattern
        show(session, "knows RAG, not at GraphLabs", """
            MATCH (p:Person)-[:KNOWS_TECH]->(:Technology {name: 'RAG'})
            WHERE NOT (p)-[:WORKS_AT]->(:Company {name: 'GraphLabs'})
            RETURN p.name AS name, p.role AS role
        """)


if __name__ == "__main__":
    run_demo()
    driver.close()
