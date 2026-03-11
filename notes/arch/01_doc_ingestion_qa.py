"""Document Ingestion + Q&A Assistant — RAG, MCP tools, Lambda, MSK."""
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.aws.database import RDS
from diagrams.aws.ml import Bedrock
from diagrams.onprem.queue import Kafka

with Diagram(
    "Document Ingestion + Q&A Assistant",
    filename="01_doc_ingestion_qa",
    show=False,
    direction="TB",
):
    user = User("User")

    with Cluster("Ingestion (event-driven)"):
        bucket = S3("Document bucket")
        ingest_lambda = Lambda("Ingest Lambda")
        with Cluster("Amazon MSK"):
            msk = Kafka("doc.ingested")
        index_lambda = Lambda("Index Lambda")
        vector_db = RDS("RDS + pgvector\n(RAG index)")

    with Cluster("Q&A (API)"):
        api = APIGateway("API Gateway")
        query_lambda = Lambda("Query Lambda")
        bedrock = Bedrock("RAG + MCP tools")

    # Ingestion flow
    user >> Edge(label="Upload docs") >> bucket
    bucket >> Edge(color="darkgreen", style="dashed", label="S3 event") >> ingest_lambda
    ingest_lambda >> Edge(label="produce") >> msk
    msk >> Edge(color="firebrick", style="dashed", label="consume") >> index_lambda
    index_lambda >> Edge(label="chunk, embed") >> vector_db

    # Query flow
    user >> Edge(label="Ask question") >> api
    api >> query_lambda
    query_lambda >> Edge(label="retrieve") >> vector_db
    query_lambda >> Edge(label="generate + tools") >> bedrock
    bedrock >> Edge(label="answer") >> query_lambda >> api >> user
