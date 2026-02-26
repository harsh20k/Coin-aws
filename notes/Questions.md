Are we using hard drives and/or EBS / instance store in our architecture?
What kind of block-level storage are we using for our EC2 instance, and where is it specified in our architecture?
What IAM roles are we attaching to our EC2 instance, and what is the user data script on our EC2?
Why are we are installing AWS CLI to the instance using user data script.
What is our instance type of EC2, and what is the AMI we are using?
Does our EC2 instance have separate storage and root volume?
Are we adding tags to our EC2 instance or any other resources for future filtering, automation, cost allocation, or access control?
What is the security group for our EC2, and what are its permissions?
Where are we starting? Which line of code is actually provisioning an EC2 instance and starting the EC2 instance?
Are we stopping hibernating or just terminating our EC2 every time?
How many concurrent users can our architecture handle?
For our EC2 instances, are we using SSD or HDD?

What kinds of API gateways are we using in our architecture, and who is interacting with that API gateway?


Do we have an internet gateway, and what traffic is being inbound if we have an internet gateway?
