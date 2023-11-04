import boto3
from botocore.config import Config

my_config = Config(
    region_name = 'ap-southeast-2',
    signature_version = 'v4',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
    },
)
with open("/home/rpi/openvpn/keysFile") as file:
  [accessKeyId, secretAccessKey] = file.readlines()

accessKeyId = accessKeyId.strip()
secretAccessKey = secretAccessKey.strip()

ec2_client = boto3.client('ec2', config=my_config, aws_access_key_id = accessKeyId, aws_secret_access_key = secretAccessKey)

describe_instances_response = ec2_client.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'vpn',
            ]
        },
        {
          'Name': 'instance-state-name',
          'Values': ['running']
        }
    ],
)
instance_id = describe_instances_response["Reservations"][0]["Instances"][0]["InstanceId"]
# print(describe_instances_response)
ec2_client.terminate_instances(InstanceIds=[instance_id])
waiter = ec2_client.get_waiter('instance_terminated')
waiter.wait(InstanceIds=[instance_id])
print(f"Instance {instance_id} has been terminated.")

security_group_name = 'openvpn_sg'

# Find the security group by name
response = ec2_client.describe_security_groups(
    Filters=[
        {
            'Name': 'group-name',
            'Values': [security_group_name]
        }
    ]
)

# Check if the security group exists
if response['SecurityGroups']:
    # Extract the ID of the security group
    security_group_id = response['SecurityGroups'][0]['GroupId']
    
    # Delete the security group
    ec2_client.delete_security_group(GroupId=security_group_id)
    
    print(f"Security group '{security_group_name}' with ID '{security_group_id}' has been deleted.")
else:
    print(f"Security group '{security_group_name}' not found.")