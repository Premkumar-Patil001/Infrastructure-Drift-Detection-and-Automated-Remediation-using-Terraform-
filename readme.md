#  Infrastructure Drift Detection and Automated Remediation using Terraform and AWS Lambda

> A production-style Cloud Automation project that solves a problem every growing engineering team eventually faces — someone makes a "quick" console change that bypasses Terraform, and suddenly nobody knows what the infrastructure actually looks like anymore.

![AWS](https://img.shields.io/badge/AWS-Cloud%20Automation-orange?style=flat-square&logo=amazon-aws)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple?style=flat-square&logo=terraform)
![Lambda](https://img.shields.io/badge/Lambda-Serverless-green?style=flat-square&logo=aws-lambda)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)
![Author](https://img.shields.io/badge/Author-Premkumar%20Patil-blue?style=flat-square)

---

##  Project Preview

>  **CloudWatch Logs** showing the complete automated cycle in action — drift detected, remediation triggered, infrastructure restored. No human touched anything.

![alt text](img/155.png)
![alt text](img/156.png)
![alt text](img/157.png)
![alt text](img/160.png)
![alt text](img/162.png)
![alt text](img/165.png)

---

##  Introduction

Here is a scenario that happens more often than most teams want to admit.

It's 11 PM and there's a production incident. An engineer needs to open a port to unblock things quickly. They log into the AWS Console, make the change in 30 seconds, and the incident is resolved. Everyone goes back to sleep.

The port never gets closed.

Weeks later, during an audit, the team finds that the AWS environment no longer matches the Terraform configuration in Git. The change isn't in the commit history because it was never made through code — it went straight into the AWS Console. At that point, it's often unclear who made the change, why it was made, or exactly when it happened.

This is configuration drift. What starts as a quick operational change can eventually become a security, governance, and audit problem.

This project is designed to address that problem with an automated system that continuously monitors AWS resources, detects when something deviates from the expected Terraform-managed state, and automatically corrects it — while maintaining a clear audit trail in CloudWatch of what changed, when it changed, and what action was taken.

No one has to manually catch every change or follow a runbook when drift occurs. The system detects the change, triggers remediation, and logs the full process automatically.


---

##  Project Overview

| What | Details |
|---|---|
| Type | Infrastructure Drift Detection + Automated Remediation |
| Role | Cloud Automation Engineer |
| Resources monitored | EC2 Instance, Security Group, S3 Bucket |
| Drift types handled | Unauthorized inbound rules, EC2 tag violations |
| Remediation | Lambda automatically revokes bad rules and restores tags |
| Audit trail | CloudWatch Logs records every event with timestamps |
| Region | us-east-1 (N. Virginia) |

---

##  Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Cloud (us-east-1)                      │
│                                                                 │
│  Terraform ──────► EC2 Instance      ◄──── Manual Console      │
│  (approved         Security Group          Change (drift)        │
│   state)           S3 Bucket                                    │
│                         │                                       │
│                         │ configuration change detected         │
│                         ▼                                       │
│                    AWS Config                                   │
│                    (continuous monitoring)                      │
│                         │                                       │
│                         │ NON_COMPLIANT event fired             │
│                         ▼                                       │
│                    Amazon EventBridge                           │
│                    (routes the event to Lambda)                 │
│                         │                                       │
│                         │ triggers                              │
│                         ▼                                       │
│                    Lambda Function                              │
│                    drift-auto-remediate                         │
│                     ├── revokes unauthorized SG rules           │
│                     └── logs every action taken                 │
│                         │                                       │
│                         ▼                                       │
│                    CloudWatch Logs                              │
│                    (permanent audit trail)                      │
│                         │                                       │
│                         ▼                                       │
│                    Infrastructure Restored ✅                   │
│                    (back to Terraform approved state)           │
└────────────────────────────────────────────────────────────────

```
![Drift Detection Architecture](img/Architecture.png)

---

## 🔄 The Automated Flow — End to End

Here is exactly what happens from the moment someone makes an unauthorized console change to the moment it is fixed:

```
1.  Engineer manually adds port 80 via AWS Console
2.  AWS Config detects the configuration change
3.  Config Rule evaluates → marks Security Group NON_COMPLIANT
4.  EventBridge receives the compliance change event
5.  EventBridge triggers the Lambda function automatically
6.  Lambda identifies the unauthorized port 80 rule
7.  Lambda calls revoke_security_group_ingress via boto3
8.  Port 80 rule is removed — approved state restored
9.  CloudWatch Logs records every step with timestamps
10. Zero human intervention required throughout
```

The whole thing from detection to remediation takes between 2 and 15 minutes depending on how AWS Config evaluation timing lines up. For demos, triggering a manual re-evaluate in Config drops that to under 30 seconds.

---

##  Services Used

| Service | Role |
|---|---|
| **Terraform** | Defines the approved state — EC2, Security Group, S3 |
| **AWS Config** | Continuously watches resources and evaluates compliance |
| **Amazon EventBridge** | Routes NON_COMPLIANT events from Config to Lambda |
| **AWS Lambda** | The brain — auto-remediates drift when triggered |
| **CloudWatch Logs** | Records everything — the permanent audit trail |
| **IAM** | Scoped role that gives Lambda exactly the permissions it needs |

---

##  Technologies and Tools

```
Terraform       Infrastructure as Code — provisions and defines approved state
Python 3.12     Lambda function runtime
boto3           AWS SDK for Python — makes the actual EC2 API calls
AWS Config      Drift detection and compliance evaluation engine
EventBridge     Serverless event routing between Config and Lambda
Lambda          Serverless auto-remediation — no servers to manage
CloudWatch      Audit logging and monitoring
IAM             Permission management — least privilege throughout
```

---

##  Project Structure

```
drift-detection-project/
│
├── terraform/
│   ├── provider.tf          ← AWS provider and version constraints
│   ├── main.tf              ← EC2, Security Group, S3 resources
│   ├── variables.tf         ← Your IP and configurable values
│   └── outputs.tf           ← Resource IDs and ARNs as output
│
├── lambda/
│   └── lambda_function.py   ← Auto-remediation logic
│
├── image/                   ← All 18 project screenshots
│   ├── 01-terraform-apply-output.png
│   ├── 02-aws-resources-created.png
│   └── ... (all screenshots)
│
└── README.md
```

---

## 🚀 Step-by-Step Deployment

---

### Phase 1 — Provision Infrastructure with Terraform

Terraform creates the three AWS resources that form the approved baseline. Every resource gets a `ManagedBy = Terraform` tag — this is how AWS Config knows which resources belong to this project.

#### provider.tf

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

#### main.tf

```hcl
resource "aws_security_group" "app_sg" {
  name        = "drift-demo-sg"
  description = "SG managed by Terraform - drift detection demo"

  ingress {
    description = "SSH from authorized IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.your_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "drift-demo-sg"
    ManagedBy   = "Terraform"
    Environment = "lab"
  }
}

resource "aws_instance" "app_server" {
  ami             = "ami-0c101f26f147fa7fd"
  instance_type   = "t2.micro"
  security_groups = [aws_security_group.app_sg.name]

  tags = {
    Name        = "drift-demo-ec2"
    ManagedBy   = "Terraform"
    Environment = "lab"
  }
}

resource "aws_s3_bucket" "drift_bucket" {
  bucket = "drift-demo-bucket-prem-lab"

  tags = {
    Name      = "drift-demo-bucket"
    ManagedBy = "Terraform"
  }
}
```

#### variables.tf

```hcl
variable "your_ip" {
  description = "Your authorized IP address for SSH"
  type        = string
  default     = "YOUR_IP/32"
}
```

#### Run it

```bash
terraform init
terraform plan
terraform apply -auto-approve
```

After apply completes, you have your baseline. Three resources, all tagged, all matching the Terraform definition exactly. This is the approved state everything will be compared against.

![alt text](img/17.png)
![alt text](img/18.png)

![alt text](img/1.png)
![alt text](img/2.png)
![alt text](img/3.png)

---

### Phase 2 — Simulate Configuration Drift

Now for the fun part — breaking things on purpose to prove the system catches it.

These two manual changes simulate exactly what happens in real engineering teams under pressure. Someone adds a rule "temporarily." Someone updates a tag "just to test something." Neither change makes it into the Terraform code. Drift is born.

#### Drift 1 — Unauthorized Security Group Rule

```
AWS Console → EC2 → Security Groups → drift-demo-sg
→ Edit inbound rules → Add rule

Type:        HTTP
Port:        80
Source:      0.0.0.0/0
Description: temp-manual-change

→ Save rules
```

#### Drift 2 — EC2 Tag Violation

```
AWS Console → EC2 → Instances → drift-demo-ec2
→ Tags → Manage tags → Add tag

Key:   Owner
Value: manually-added-not-in-terraform

→ Save
```

#### Confirm drift with terraform plan

```bash
terraform plan

# You should see:
# ~ aws_security_group.app_sg will be updated
#   ingress rules differ from approved state
# ~ aws_instance.app_server will be updated
#   tags differ from approved state
```

The `terraform plan` output is your evidence that drift exists. Terraform can see the gap between its state file and what AWS actually has right now.

![alt text](img/5.png)
![alt text](img/6.png)
![alt text](img/7.png)
![alt text](img/11.png)
![alt text](img/12.png)
![alt text](img/13.png)
![alt text](img/14.png)

---

### Phase 3 — AWS Config Drift Detection

AWS Config is the continuous monitoring layer. It records a snapshot every time a resource configuration changes — and evaluates those snapshots against compliance rules you define.

#### Enable AWS Config Recording

```
AWS Config → Settings → Edit

Resource types to record:
  AWS::EC2::Instance
  AWS::EC2::SecurityGroup
  AWS::S3::Bucket

Delivery method: S3 bucket → config-delivery-prem-lab
Service role: Create new → AWSServiceRoleForConfig

→ Save
```
![alt text](img/62.png)

#### Create Config Rule

```
AWS Config → Rules → Add rule

Managed rule: vpc-sg-open-only-to-authorized-ports
Rule name:    terraform-drift-sg-rule2

Parameters:
  authorizedTcpPorts: 22

Trigger: When configuration changes
Scope:   EC2 SecurityGroup

→ Add rule
```
![alt text](img/54.png)
![alt text](img/55.png)
![alt text](img/56.png)
![alt text](img/57.png)
![alt text](img/58.png)
![alt text](img/60.png)


This rule is simple but powerful — it marks any Security Group NON_COMPLIANT the moment a port other than 22 has an inbound rule. The moment port 80 was added in Phase 2, this rule will fire.

#### IAM Role for Lambda

```
IAM → Roles → Create role

Trusted entity: Lambda
Policies:
  ✓ AWSConfigRulesExecutionRole
  ✓ AmazonEC2FullAccess
  ✓ CloudWatchLogsFullAccess

Role name: drift-remediation-lambda-role
```
![alt text](img/76.png)
![alt text](img/77.png)
![alt text](img/82.png)
![alt text](img/83.png)
![alt text](img/84.png)




> ⚠️ `AmazonEC2FullAccess` is used here for lab simplicity. In production this would be scoped down to only `ec2:DescribeSecurityGroups`, `ec2:RevokeSecurityGroupIngress`, `ec2:DescribeInstances`, `ec2:CreateTags`, and `ec2:DeleteTags`. Always apply least privilege before production deployment.

![alt text](img/73.png)
![alt text](img/65.png)

---

### Phase 4 — Lambda Auto-Remediation Function

This is the core of the project. When EventBridge fires the Lambda, it figures out exactly what drifted and uses boto3 to put it back the way Terraform defined it.

One design decision worth calling out — the `is_rule_approved()` function validates port, protocol, AND source CIDR together. An earlier version only checked port numbers, which would incorrectly approve `port 22 open to 0.0.0.0/0` because the port matched. That is a worse security posture than the drift it was trying to fix.

#### lambda_function.py

```python
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')

# Approved rules — port, protocol AND cidr must all match
APPROVED_RULES = [
    {
        'port':     22,
        'protocol': 'tcp',
        'cidr':     'YOUR_IP/32'
    }
]

APPROVED_TAGS = {
    'Name':        'drift-demo-ec2',
    'ManagedBy':   'Terraform',
    'Environment': 'lab'
}


def lambda_handler(event, context):
    try:
        logger.info(f"Event received: {json.dumps(event)}")

        detail        = event.get('detail', {})
        resource_id   = detail.get('resourceId', '')
        resource_type = detail.get('resourceType', '')

        compliance = (
            detail.get('newEvaluationResult', {})
                  .get('complianceType', '')
        )

        logger.info(f"Resource: {resource_type} | ID: {resource_id}")
        logger.info(f"Compliance status: {compliance}")

        if compliance != 'NON_COMPLIANT':
            logger.info("Resource is compliant. No action needed.")
            return {'statusCode': 200, 'body': 'No action needed'}

        if resource_type == 'AWS::EC2::SecurityGroup':
            remediate_security_group(resource_id)
        elif resource_type == 'AWS::EC2::Instance':
            remediate_ec2_tags(resource_id)
        else:
            logger.info(f"No handler for resource type: {resource_type}")

        return {'statusCode': 200, 'body': 'Remediation complete'}

    except Exception as e:
        logger.error(f"Lambda handler failed: {str(e)}")
        raise


def is_rule_approved(rule):
    """
    Validates port, protocol AND cidr — not just port.
    A rule is only approved when ALL three match an approved entry.
    This prevents port 22 open to 0.0.0.0/0 from passing as approved.
    """
    from_port = rule.get('FromPort', -1)
    to_port   = rule.get('ToPort', -1)
    protocol  = rule.get('IpProtocol', '').lower()
    cidrs     = [ip.get('CidrIp', '') for ip in rule.get('IpRanges', [])]

    for approved in APPROVED_RULES:
        port_ok     = (from_port == approved['port'] and
                       to_port   == approved['port'])
        protocol_ok = (protocol  == approved['protocol'])
        cidr_ok     = (approved['cidr'] in cidrs)

        if port_ok and protocol_ok and cidr_ok:
            return True

    return False


def remediate_security_group(sg_id):
    try:
        logger.info(f"Checking SG inbound rules: {sg_id}")
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        sg = response['SecurityGroups'][0]
        current_rules = sg['IpPermissions']

        unauthorized = []
        for rule in current_rules:
            if not is_rule_approved(rule):
                from_port = rule.get('FromPort', 'ALL')
                cidrs = [ip.get('CidrIp') for ip in rule.get('IpRanges', [])]
                unauthorized.append(rule)
                logger.warning(
                    f"DRIFT DETECTED: Unauthorized rule — "
                    f"port={from_port}, cidrs={cidrs} on {sg_id}"
                )

        if unauthorized:
            ec2.revoke_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=unauthorized
            )
            logger.info(
                f"REMEDIATED: Removed {len(unauthorized)} "
                f"unauthorized inbound rules from {sg_id}"
            )
        else:
            logger.info(f"All inbound rules are approved on {sg_id}")

    except Exception as e:
        logger.error(f"Error in remediate_security_group: {e}")
        raise


def remediate_ec2_tags(instance_id):
    try:
        logger.info(f"Checking EC2 tags: {instance_id}")
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        current_tags = {
            t['Key']: t['Value']
            for t in instance.get('Tags', [])
        }

        approved_keys     = set(APPROVED_TAGS.keys())
        current_keys      = set(current_tags.keys())
        unauthorized_keys = current_keys - approved_keys

        if unauthorized_keys:
            ec2.delete_tags(
                Resources=[instance_id],
                Tags=[{'Key': k} for k in unauthorized_keys]
            )
            logger.info(
                f"REMEDIATED: Removed unauthorized tags "
                f"{unauthorized_keys} from {instance_id}"
            )

        wrong_tags = {
            k: v for k, v in APPROVED_TAGS.items()
            if current_tags.get(k) != v
        }

        if wrong_tags:
            ec2.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': k, 'Value': v} for k, v in wrong_tags.items()]
            )
            logger.info(
                f"REMEDIATED: Restored changed tags "
                f"{list(wrong_tags.keys())} on {instance_id}"
            )

    except Exception as e:
        logger.error(f"Error in remediate_ec2_tags: {e}")
        raise
```
![alt text](img/85.png)
![alt text](img/86.png)
![alt text](img/87.png)
![alt text](img/91.png)
![alt text](img/93.png)
![alt text](img/94.png)
![alt text](img/95.png)

#### Deploy Lambda

```bash
zip function.zip lambda_function.py

# AWS Console:
Lambda → Create function
  Function name:    drift-auto-remediate
  Runtime:          Python 3.12
  Execution role:   Use existing → drift-remediation-lambda-role
  Timeout:          30 seconds   ← important, default 3s is too short

→ Upload function.zip → Deploy
```
![alt text](img/97.png)
![alt text](img/98.png)
![alt text](img/99.png)
![alt text](img/100.png)
![alt text](img/101.png)
![alt text](img/157.png)
![alt text](img/159.png)
![alt text](img/160.png)

#### Create EventBridge Rule

```
EventBridge → Rules → Create rule
Mode: Advanced builder

Name: config-noncompliant-trigger

Event pattern (Custom pattern):
{
  "source": ["aws.config"],
  "detail-type": ["Config Rules Compliance Change"],
  "detail": {
    "newEvaluationResult": {
      "complianceType": ["NON_COMPLIANT"]
    }
  }
}

Target: Lambda function → drift-auto-remediate
→ Create rule
```

The EventBridge rule is what connects Config to Lambda. Config does not call Lambda directly — it fires an event, EventBridge catches it and routes it. This decoupling means you can later add more targets to the same event (a Slack notification, a DynamoDB audit record) without touching either Config or Lambda.

![alt text](img/112.png)
![alt text](img/115.png)
![alt text](img/116.png)
![alt text](img/117.png)
![alt text](img/118.png)
![alt text](img/119.png)
![alt text](img/120.png)
![alt text](img/122.png)
![alt text](img/124.png)
![alt text](img/125.png)
![alt text](img/127.png)
![alt text](img/128.png)

---

### Phase 5 — End-to-End Test and Verification

Time to prove the whole system works together, not just in isolation.

```bash
# Step 1: Add drift via console
# AWS Console → drift-demo-sg → Edit inbound rules
# Add: HTTP, port 80, source 0.0.0.0/0 → Save

# Step 2: Force Config to evaluate immediately
# AWS Config → Rules → terraform-drift-sg-rule
# → Actions → Re-evaluate
# (Otherwise you wait up to 15 minutes for automatic evaluation)

# Step 3: Check the Security Group 30 seconds later
# EC2 → Security Groups → drift-demo-sg
# Port 80 should be gone — automatically
```

The moment Config marks the rule NON_COMPLIANT, EventBridge fires, Lambda runs, and the unauthorized rule is revoked. No ticket raised. No engineer paged. No runbook followed.

![alt text](img/153.png)
![alt text](img/155.png)
![alt text](img/156.png)
![alt text](img/159.png)
![alt text](img/161.png)
![alt text](img/160.png)
![alt text](img/162.png)

---

### Phase 6 — CloudWatch Logs Audit Trail

Every step of the remediation cycle is logged in CloudWatch. This is what you hand to a compliance auditor — a timestamped record of what drifted, when, and exactly what was done about it.

![alt text](img/163.png)
![alt text](img/165.png)

#### What the logs look like

```
[INFO]    Checking SG inbound rules: sg-0d59147aaa97318d9
[WARNING] DRIFT DETECTED: Unauthorized rule — port=80, cidrs=['0.0.0.0/0'] on sg-0d59147aaa97318d9
[INFO]    REMEDIATED: Removed 1 unauthorized inbound rules from sg-0d59147aaa97318d9
```

Four log lines. Complete story. Timestamp on every entry. This is the audit trail that makes compliance teams happy and keeps security teams informed.

---

##  Drift Types This System Handles

| Drift Type | Example | How It Is Detected | How It Is Fixed |
|---|---|---|---|
| Unauthorized inbound rule | Port 80 added via console | Config rule flags NON_COMPLIANT | Lambda revokes the rule |
| Wrong source CIDR | Port 22 changed to 0.0.0.0/0 | Config rule flags NON_COMPLIANT | Lambda revokes and the approved rule stays |
| Unauthorized EC2 tag | Owner tag added manually | Config change event fires | Lambda deletes the unauthorized tag |
| Changed tag value | Environment changed from lab to production | Config change event fires | Lambda restores the original value |

---

## 🔧 Key Design Decisions

### Why AWS Config instead of a scheduled Terraform plan

I chose AWS Config because it can detect configuration changes as they happen instead of waiting for the next scheduled Terraform plan.

For example, if someone changes a Security Group at midnight, a scheduled `terraform plan` might not detect it until its next run. With AWS Config, the change can be evaluated shortly after it happens.

For security-sensitive resources such as Security Groups, detecting the change quickly gives us a better chance of correcting it before it becomes a bigger issue.

### Why `is_rule_approved()` checks both port and CIDR

Initially, the function only checked the port number. That created a serious problem.

For example, if port 22 was allowed in the approved configuration, a rule allowing `22` from `0.0.0.0/0` could also be treated as approved, even though it exposes SSH to the entire internet.

The check therefore needs to validate the complete rule — including the port, protocol, and source CIDR. This makes sure that a rule is considered valid only when it actually matches the expected configuration.

### Why EventBridge sits between Config and Lambda

AWS Config doesn't need to call the Lambda function directly. Instead, Config generates an event when a resource becomes `NON_COMPLIANT`, and EventBridge receives and routes that event to Lambda.

This also keeps the components separate. If I later want the same event to trigger an SNS notification, store an audit record in DynamoDB, or send a Slack notification, I can add another EventBridge target without having to change the Config rule or the Lambda function.

This makes it easier to extend the system as the project grows.

### Why the Lambda timeout is set to 30 seconds

The default Lambda timeout is 3 seconds. For this project, that can be a little tight because the function needs to make AWS API calls such as `describe_security_groups` and `revoke_security_group_ingress`.

If multiple unauthorized rules need to be removed, or if an AWS API call takes longer than expected, a 3-second timeout could cause the function to stop before the remediation is completed.

I set the timeout to 30 seconds to give the function enough time to complete the remediation without making the timeout unnecessarily long.


---

## ⏱ How Long Does Remediation Take

| Trigger Method | Time to Remediate |
|---|---|
| Lambda Test button — manual | 5–10 seconds |
| Config → Re-evaluate → EventBridge → Lambda | 2–5 minutes |
| Config on configuration changes (automatic) | 5–15 minutes |
| Config periodic evaluation (1 hour cycle) | Up to 1 hour |

For demos, click **Config → Actions → Re-evaluate** to force immediate evaluation without waiting for the periodic cycle. For end-to-end validation, the automatic flow is more impressive — add the rule, wait a few minutes, and watch it disappear on its own.

---

### 💡 What I Learned

Configuration drift isn't only a technical problem — it's also a governance problem. The port 80 rule itself wasn't the biggest issue. The real problem was that someone bypassed the normal code review process, so there was no second pair of eyes on the change, nothing in Git, and no clear way to know it happened until someone noticed the difference or an auditor found it.

One thing that surprised me was how different Terraform state and AWS Config are when it comes to tracking changes. Terraform knows the state of the infrastructure it manages, but it doesn't keep a complete history of every change made between applies. AWS Config does provide that historical view, including timestamps for configuration changes. You can use it to look back at what a Security Group looked like at a particular point in time and see what changed. That's especially useful when investigating drift or dealing with audit requirements.

I also got the remediation logic wrong on my first pass. My initial `is_rule_approved()` function only checked port numbers. That meant SSH on port 22 could have been treated as approved even if it was open to `0.0.0.0/0`, simply because the port matched. I had to change the logic to validate the port, protocol, and source CIDR together. Otherwise, the system could have marked an insecure rule as valid and missed the actual drift.

Routing everything through EventBridge instead of connecting Config directly to Lambda felt like extra complexity at first. But it gives the system more flexibility. I can add another target later — such as an SNS notification, Slack integration, or another Lambda function — without changing the existing Config or remediation logic.

I also learned that Lambda's default 3-second timeout can be too short for a remediation workflow. The function timed out once while making the required AWS API calls, leaving the Security Group only partially fixed. Increasing the timeout gave the function enough time to complete the remediation reliably.

These were small details individually, but they made a big difference in how I approached the final design of the system.

---

## 📌 Project Summary

This project started with a simple observation: telling engineers not to touch the AWS Console directly works fine — until there's a production incident and someone needs to make a quick change to fix it.

That's where drift creeps in.

Here's what the system does when that happens: someone manually opens a port in a Security Group, AWS Config detects the change, EventBridge routes the event to Lambda, and Lambda checks whether the change matches the approved configuration. If it doesn't, the system automatically reverts it. CloudWatch logs the entire process — what changed, when it changed, and what action was taken.

I'm not trying to prevent emergency console changes altogether. Sometimes they're genuinely necessary, especially during a production incident. The goal is to prevent those temporary changes from quietly becoming permanent without anyone noticing.

That's the gap this project is designed to close.

---

## 🧹 Cleanup Order

```
1. Disable AWS Config recording          → Settings → Edit → turn off
2. Delete EventBridge rule               → config-noncompliant-trigger
3. Delete Lambda function                → drift-auto-remediate
4. Delete IAM Role                       → drift-remediation-lambda-role
5. Delete AWS Config rule                → terraform-drift-sg-rule
6. Terraform destroy                     → terraform destroy -auto-approve
7. Empty Config delivery S3 bucket       → then delete the bucket
8. Delete CloudWatch Log Group           → /aws/lambda/drift-auto-remediate
```

> ⚠️ Run `terraform destroy` before manually deleting resources. Deleting resources from the console first puts Terraform state out of sync and makes the destroy fail.

---

## 👨‍💻 Author

**Premkumar Keshav Patil**
Cloud & DevOps Enthusiast | Learning AWS, Terraform, and Cloud Automation

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https:www.linkedin.com/in/premkumar-patil-bb9471253)
[![Medium](https://img.shields.io/badge/Medium-Follow-black?style=flat-square&logo=medium)](https://medium.com/@premkpatil9423)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-grey?style=flat-square&logo=github)](https://github.com/Premkumar-Patil001)

---

## 📌 Tags

`AWS` `Terraform` `Lambda` `AWS Config` `EventBridge` `CloudWatch` `IAM` `Python` `boto3` `Infrastructure as Code` `Drift Detection` `Auto Remediation` `Cloud Automation` `DevOps` `Compliance` `Security` `EC2` `Security Groups`