import boto3
import sys
from botocore.config import Config
import urllib.request



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

userDataScript = '''#!/bin/bash
mkdir /home/ubuntu/openvpn
cd /home/ubuntu/openvpn
curl https://raw.githubusercontent.com/angristan/openvpn-install/master/openvpn-install.sh -o openvpn-install.sh
chmod +x openvpn-install.sh
sed -i '284s/1194/443/' /home/ubuntu/openvpn/openvpn-install.sh
sed -i '902s/3/10/' /home/ubuntu/openvpn/openvpn-install.sh
sudo bash -c 'export AUTO_INSTALL=y && export APPROVE_INSTALL=y && export APPROVE_IP=y && export IPV6_SUPPORT=n && export PORT_CHOICE=1 && export PROTOCOL_CHOICE=2 && export DNS=9 && export COMPRESSION_ENABLED=n && export CUSTOMIZE_ENC=n && export CLIENT=client1 && export PASS=1 && ./openvpn-install.sh'
mv /root/client1.ovpn /home/ubuntu/openvpn/client1.ovpn
python3 -m http.server 8080
'''

# Get VPC ID of the default VPC
vpc_response = ec2_client.describe_vpcs(Filters = [
    {'Name':'isDefault','Values': ['true']}
])

vpcId = vpc_response['Vpcs'][0]['VpcId']

# Get a subnet ID from the default VPC ID

subnet_response = ec2_client.describe_subnets(
    Filters=[
        {
            'Name': 'vpc-id',
            'Values': [vpcId]
        },
    ]
)


subnetID = subnet_response['Subnets'][0]['SubnetId']

# Create a security group without an ingress rule
security_group_response = ec2_client.create_security_group(
    Description='This security group controls incoming traffic from the public IP address of Raspberry Pi',
    GroupName='openvpn_sg',
    VpcId=vpcId,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'openvpn_sg'
                },
            ]
        },
    ],

)
securityGroup_Id = security_group_response['GroupId']

# Add an ingress rule for TCP/443 and TCP/22 to the security group
public_ip_rpi = urllib.request.urlopen('https://ident.me').read().decode('utf8')


authorize_security_group_ingress_response = ec2_client.authorize_security_group_ingress(

    GroupId = securityGroup_Id,
     IpPermissions=[
        {
            'FromPort': 443,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': public_ip_rpi+'/32',
                    'Description': 'RPi public IP address in CIDR format'
                },
            ],
            'ToPort': 443,
        },
        {
            'FromPort': 8080,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': public_ip_rpi+'/32',
                    'Description': 'Allow port 8080 for RPi to pull OpenVPN client config'
                },
            ],
            'ToPort': 8080,
        },
        {
            'FromPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': [
                {
                    'CidrIp': public_ip_rpi+'/32',
                    'Description': 'Allow SSH from public IP address of RPi'
                },
            ],
            'ToPort': 22,
        },
    ],
     TagSpecifications=[
        {
            'ResourceType': 'security-group-rule',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'Allow traffic to VPN server running on port 443 from RPi'
                },
            ]
        },
    ]

)


# Create EC2 instance and install OpenVPN server package

ec2_response = ec2_client.run_instances(
    ImageId='ami-0df4b2961410d4cff',
    InstanceType='t3.small',
    KeyName='vpn',
    MaxCount=1,
    MinCount=1,
    SecurityGroupIds=[securityGroup_Id],
    SubnetId=subnetID,
    UserData= userDataScript,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'vpn'
                },
            ]
        },
    ],
)

instanceId = ec2_response["Instances"][0]["InstanceId"]
waiter = ec2_client.get_waiter('instance_status_ok')

# Wait for the instance to pass the status checks
waiter.wait(InstanceIds=[instanceId])

# Once the instance is running we can now attach an Elastic IP address or allocate one
addresses_dict = ec2_client.describe_addresses(
     Filters=[
        {
            'Name': 'tag:Name',
            'Values': [
                'rpi',
            ]
        },
          {
            'Name': 'tag:Type',
            'Values': [
                'vpn',
            ]
        },
    ],
)

if addresses_dict["Addresses"] == []:
  allocate_address_response = ec2_client.allocate_address(Domain='vpc',  TagSpecifications=
    [{
      'ResourceType': 'elastic-ip',
      'Tags':[{
                'Key': 'Name',
                'Value': 'rpi'
            },
            {
                'Key': 'Type',
                'Value': 'vpn'
            }]
    }]
)
  elastic_ip = allocate_address_response['PublicIp']
  associate_address_response = ec2_client.associate_address(
    InstanceId=instanceId,
    PublicIp=elastic_ip
)
else:
  elastic_ip = addresses_dict["Addresses"][0]["PublicIp"]
  associate_address_response = ec2_client.associate_address(
    InstanceId=instanceId,
    PublicIp=elastic_ip
)

sys.stdout.write(elastic_ip)
sys.stdout.flush()
sys.exit(0)