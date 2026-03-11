"""Netflix-style: content distribution to millions of users (AWS)."""
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.aws.network import Route53, CloudFront
from diagrams.aws.storage import S3
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import Dynamodb

with Diagram(
    "Netflix-style: Content distribution to millions of users",
    filename="06_netflix_content_distribution",
    show=False,
    direction="TB",
):
    users = Users("Millions of\nstreaming users")

    with Cluster("DNS & entry"):
        route53 = Route53("Route 53")

    with Cluster("Edge delivery (CDN)"):
        cloudfront = CloudFront("CloudFront\n(global edge caches)")

    with Cluster("API — auth, catalog, recommendations"):
        api = APIGateway("API Gateway")
        api_lambda = Lambda("API / Auth")
        dynamo = Dynamodb("User / catalog data")

    with Cluster("Origin (source of truth)"):
        s3_origin = S3("S3 — encoded\nvideo & assets")

    # User flow: resolve and stream
    users >> Edge(label="resolve") >> route53
    users >> Edge(label="stream video / UI assets") >> cloudfront
    cloudfront >> Edge(color="darkgreen", style="dashed", label="cache miss") >> s3_origin

    # API flow
    users >> Edge(label="login, catalog, play") >> api
    api >> api_lambda
    api_lambda >> dynamo
