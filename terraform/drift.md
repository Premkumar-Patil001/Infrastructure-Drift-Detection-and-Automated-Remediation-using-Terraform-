## Drift Event 1 — Security Group Rule
Date: 29/6/2026
Resource: aws_security_group.app_sg (sg-0f9dfa9e2d186bad8)
Change: An inbound rule was added manually through the AWS Console.

Added: TCP port 80 from 0.0.0.0/0
Risk: Port 80 was exposed to the entire internet without going through the normal code review process. This could allow unintended web traffic to reach the instance.

Detection: terraform plan detected the rule in AWS even though it was not defined in the Terraform configuration.

## Drift Event 2 — EC2 Instance Tags
Date: 29/6/2026
Resource: aws_instance.app_server (i-0b7bea92b370bf655)
Change: EC2 tags were modified manually through the AWS Console.

Added: Owner = manually-added-not-in-terraform
Changed: Environment = lab → production

Risk: These changes bypassed the normal Infrastructure as Code workflow, meaning there was no corresponding code change or Git history to review.

Detection: terraform plan detected that the tags on the EC2 instance did not match the values defined in the .tf files.

## Why This Matters
Configuration drift is more than just a difference between AWS and Terraform. If changes are made outside the normal IaC workflow, they can introduce security risks, create compliance issues, and cause unexpected changes during future Terraform deployments.

These examples show how a small manual change in the AWS Console can go unnoticed until it becomes a larger problem.