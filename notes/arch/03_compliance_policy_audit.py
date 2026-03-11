"""Compliance / Policy Assistant with Audit Trail — RAG, MCP, Lambda, MSK."""
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS
from diagrams.aws.ml import Bedrock
from diagrams.onprem.queue import Kafka
from diagrams.aws.storage import S3

with Diagram(
    "Compliance / Policy Assistant with Audit Trail",
    filename="03_compliance_policy_audit",
    show=False,
    direction="TB",
):
    user = User("Compliance / User")

    with Cluster("Audit event stream (MSK)"):
        with Cluster("Amazon MSK"):
            policy_events = Kafka("policy.updates")
            audit_events = Kafka("audit.trail")

    with Cluster("Policy & RAG"):
        policy_bucket = S3("Policy docs")
        index_lambda = Lambda("Policy index Lambda")
        vector_db = RDS("RDS + pgvector\n(policies)")
        api = APIGateway("API Gateway")
        query_lambda = Lambda("Query Lambda")
        bedrock = Bedrock("RAG + MCP tools")

    with Cluster("Consumers (replay / report)"):
        audit_lambda = Lambda("Audit consumer Lambda")

    # Policy updates -> re-index
    user >> Edge(label="Policy update") >> policy_bucket
    policy_bucket >> Edge(label="event") >> index_lambda
    index_lambda >> Edge(label="produce") >> policy_events
    policy_events >> Edge(label="consume") >> index_lambda
    index_lambda >> Edge(label="embed, index") >> vector_db

    # User query -> RAG + tools -> audit to MSK
    user >> Edge(label="Policy question") >> api
    api >> query_lambda
    query_lambda >> Edge(label="retrieve") >> vector_db
    query_lambda >> Edge(label="answer + tools") >> bedrock
    bedrock >> query_lambda
    query_lambda >> Edge(label="every action") >> audit_events
    audit_events >> Edge(color="firebrick", style="dashed", label="consume") >> audit_lambda
