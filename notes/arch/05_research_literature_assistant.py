"""Research / Literature Assistant — RAG, MCP tools, Lambda, MSK."""
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.aws.database import RDS
from diagrams.aws.ml import Bedrock
from diagrams.onprem.queue import Kafka

with Diagram(
    "Research / Literature Assistant",
    filename="05_research_literature_assistant",
    show=False,
    direction="TB",
):
    user = User("Researcher")

    with Cluster("Ingestion (event-driven)"):
        bucket = S3("Papers / sources")
        ingest_lambda = Lambda("Ingest Lambda")
        with Cluster("Amazon MSK"):
            ingest_topic = Kafka("literature.ingested")
        index_lambda = Lambda("Index Lambda")
        vector_db = RDS("RDS + pgvector\n(papers, notes)")

    with Cluster("Query & tools"):
        api = APIGateway("API Gateway")
        query_lambda = Lambda("Query Lambda")
        bedrock = Bedrock("RAG + MCP tools\n(search, cite, save)")

    # Ingestion
    user >> Edge(label="Upload / bulk import") >> bucket
    bucket >> Edge(color="darkgreen", style="dashed", label="event") >> ingest_lambda
    ingest_lambda >> Edge(label="produce") >> ingest_topic
    ingest_topic >> Edge(color="firebrick", style="dashed", label="consume") >> index_lambda
    index_lambda >> Edge(label="chunk, embed") >> vector_db

    # Query + MCP (e.g. search API, save list, BibTeX)
    user >> Edge(label="Ask / search / save") >> api
    api >> query_lambda
    query_lambda >> Edge(label="retrieve") >> vector_db
    query_lambda >> Edge(label="answer + tools") >> bedrock
    bedrock >> Edge(label="response") >> query_lambda >> api >> user
