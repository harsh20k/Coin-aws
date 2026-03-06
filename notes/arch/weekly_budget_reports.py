from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import User

from diagrams.aws.integration import Eventbridge, SQS
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.engagement import SES
from diagrams.aws.management import Cloudwatch


with Diagram(
    "Weekly Budget & Forecast – Event-driven",
    filename="weekly_budget_reports",
    show=False,
    direction="LR",
):
    user = User("CoinBaby user")

    with Cluster("Scheduling"):
        rule = Eventbridge("Weekly schedule rule")
        scheduler_lambda = Lambda("Scheduler Lambda")
        cw = Cloudwatch("Metrics & logs")

    with Cluster("Work queue"):
        queue = SQS("Weekly report jobs")

    with Cluster("Workers"):
        worker_lambda = Lambda("Report worker Lambda")
        db = RDS("PostgreSQL (budgets, txns)")
        mailer = SES("SES (email)")

    # Time-based trigger
    user >> Edge(label="Configured preference") >> rule
    rule >> Edge(color="darkgreen", style="dashed", label="cron (weekly)") >> scheduler_lambda
    scheduler_lambda >> Edge(label="1 msg / user") >> queue
    scheduler_lambda >> cw

    # Fan-out processing of per-user jobs
    queue >> Edge(color="firebrick", style="dashed", label="batch of jobs") >> worker_lambda
    worker_lambda >> Edge(label="read history") >> db
    worker_lambda >> Edge(label="summary + forecast") >> mailer
    mailer >> Edge(label="weekly email") >> user

