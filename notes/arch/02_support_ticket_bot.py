"""Support Ticket Triage & Resolution Bot — RAG, MCP tools, Lambda, MSK."""
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS
from diagrams.aws.ml import Bedrock
from diagrams.onprem.queue import Kafka
from diagrams.aws.integration import SNS

with Diagram(
    "Support Ticket Triage & Resolution Bot",
    filename="02_support_ticket_bot",
    show=False,
    direction="TB",
):
    user = User("Agent / User")

    with Cluster("Event stream (MSK)"):
        with Cluster("Amazon MSK"):
            ticket_created = Kafka("ticket.created")
            ticket_enriched = Kafka("ticket.enriched")

    with Cluster("Processing"):
        ingest_lambda = Lambda("Ticket ingest Lambda")
        triage_lambda = Lambda("Triage Lambda\n(RAG + MCP)")
        bedrock = Bedrock("Bedrock\n(KB + tools)")
        kb = RDS("RDS + pgvector\n(KB, past tickets)")

    with Cluster("API & notifications"):
        api = APIGateway("API Gateway")
        sns = SNS("SNS\n(notify, escalate)")

    # New ticket -> MSK
    user >> Edge(label="New ticket") >> ingest_lambda
    ingest_lambda >> Edge(label="produce") >> ticket_created

    # Consume, triage, enrich
    ticket_created >> Edge(color="firebrick", style="dashed", label="consume") >> triage_lambda
    triage_lambda >> Edge(label="retrieve similar") >> kb
    triage_lambda >> Edge(label="classify, suggest") >> bedrock
    bedrock >> triage_lambda
    triage_lambda >> Edge(label="produce") >> ticket_enriched
    triage_lambda >> Edge(label="notify / escalate") >> sns
    sns >> user

    # Optional: query from API
    user >> Edge(label="Query / actions") >> api >> triage_lambda
