"""Internal DevOps / Runbook Assistant — RAG, MCP tools, Lambda, MSK."""
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS
from diagrams.aws.ml import Bedrock
from diagrams.onprem.queue import Kafka
from diagrams.aws.management import Cloudwatch

with Diagram(
    "Internal DevOps / Runbook Assistant",
    filename="04_devops_runbook_assistant",
    show=False,
    direction="TB",
):
    user = User("Engineer")

    with Cluster("Event stream (MSK)"):
        with Cluster("Amazon MSK"):
            action_events = Kafka("assistant.actions")

    with Cluster("Runbook & RAG"):
        vector_db = RDS("RDS + pgvector\n(runbooks, docs)")
        api = APIGateway("API Gateway")
        assistant_lambda = Lambda("Assistant Lambda")
        bedrock = Bedrock("RAG + MCP tools")

    with Cluster("MCP tools (read-only + actions)"):
        cw = Cloudwatch("CloudWatch\n(metrics, logs)")

    with Cluster("Consumers"):
        audit_lambda = Lambda("Audit Lambda")

    # User asks -> RAG + tool calls
    user >> Edge(label="e.g. How do I roll back X?") >> api
    api >> assistant_lambda
    assistant_lambda >> Edge(label="retrieve runbooks") >> vector_db
    assistant_lambda >> Edge(label="answer + tools") >> bedrock
    bedrock >> assistant_lambda
    assistant_lambda >> Edge(label="describe / get logs") >> cw
    assistant_lambda >> Edge(label="emit action") >> action_events
    action_events >> Edge(color="firebrick", style="dashed", label="audit / approval") >> audit_lambda
