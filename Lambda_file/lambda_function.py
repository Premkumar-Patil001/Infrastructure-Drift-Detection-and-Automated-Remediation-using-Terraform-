import boto3
import json
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')

# Approved rules — both port AND cidr must match

APPROVED_RULES = [
    {
        'port':     22,
        'protocol': 'tcp',
        'cidr':     '103.171.55.124/32'  # IP from Terraform
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
    Fix 1: Check port, protocol AND cidr — not just port.
    A rule is approved only if ALL 3 match an entry
    in APPROVED_RULES.
    """
    from_port = rule.get('FromPort', -1)
    to_port   = rule.get('ToPort', -1)
    protocol  = rule.get('IpProtocol', '').lower()

    # Collect all CIDRs in this rule
    cidrs = [ip.get('CidrIp', '') for ip in rule.get('IpRanges', [])]

    for approved in APPROVED_RULES:
        port_ok     = (from_port == approved['port'] and
                       to_port   == approved['port'])
        protocol_ok = (protocol  == approved['protocol'])
        cidr_ok     = (approved['cidr'] in cidrs)

        if port_ok and protocol_ok and cidr_ok:
            return True  # this rule exactly matches an approved rule

    return False  # no approved rule matched → unauthorized


def remediate_security_group(sg_id):
    """
    Fix 1 + 5 + 6: Checks inbound rules against
    port, protocol AND cidr — not just port number.
    """
    try:
        logger.info(f"Checking SG inbound rules: {sg_id}")
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        sg = response['SecurityGroups'][0]

        
        # Note: outbound (IpPermissionsEgress) check is
        # out of scope for this lab project
        current_rules = sg['IpPermissions']

        unauthorized = []
        for rule in current_rules:
            if not is_rule_approved(rule):
                from_port = rule.get('FromPort', 'ALL')
                cidrs = [ip.get('CidrIp') for ip in
                         rule.get('IpRanges', [])]
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

    except ec2.exceptions.ClientError as e:
        
        logger.error(f"AWS API error in remediate_security_group: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in remediate_security_group: {e}")
        raise


def remediate_ec2_tags(instance_id):
    """
    Tag remediation — this part was already correct.
    Added try/except for robustness.
    """
    try:
        logger.info(f"Checking EC2 tags: {instance_id}")

        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = (response['Reservations'][0]['Instances'][0])
        current_tags = {
            t['Key']: t['Value']
            for t in instance.get('Tags', [])
        }

        # Remove tags that should not exist
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

        # Restore tags whose values were changed
        wrong_tags = {
            k: v for k, v in APPROVED_TAGS.items()
            if current_tags.get(k) != v
        }

        if wrong_tags:
            ec2.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': k, 'Value': v}
                      for k, v in wrong_tags.items()]
            )
            logger.info(
                f"REMEDIATED: Restored changed tags "
                f"{list(wrong_tags.keys())} on {instance_id}"
            )

        if not unauthorized_keys and not wrong_tags:
            logger.info(f"All tags are correct on {instance_id}")

    except ec2.exceptions.ClientError as e:
        logger.error(f"AWS API error in remediate_ec2_tags: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in remediate_ec2_tags: {e}")
        raise