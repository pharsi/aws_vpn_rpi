import boto3
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

ec2_client = boto3.client('ec2', config=my_config, aws_access_key_id = accessKeyId, aws_secret_access_key = secretAccessKey)

userDataScript = '''#!/bin/bash
mkdir /home/ubuntu/openvpn
cd /home/ubuntu/openvpn
curl https://raw.githubusercontent.com/angristan/openvpn-install/master/openvpn-install.sh -o openvpn-install.sh
chmod +x openvpn-install.sh
sed -i '284s/1194/443/' ~/openvpn/openvpn-install.sh
sudo bash -c 'export AUTO_INSTALL=y && export APPROVE_INSTALL=y && export APPROVE_IP=y && export IPV6_SUPPORT=n && export PORT_CHOICE=1 && export PROTOCOL_CHOICE=2 && export DNS=9 && export COMPRESSION_ENABLED=n && export CUSTOMIZE_ENC=n && export CLIENT=client1 && export PASS=1 && ./openvpn-install.sh'
mv /root/client1.ovpn /home/ubuntu/openvpn/client1.ovpn
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

ec2_resonse = ec2_client.run_instances(
    # BlockDeviceMappings=[
    #     {
    #         'DeviceName': '/dev/sda',
    #         'Ebs': {
    #             'DeleteOnTermination': True,
    #             # 'Iops': 123,
    #             'VolumeSize': 8,
    #             'VolumeType': 'gp3',
    #             # 'KmsKeyId': 'string',
    #             # 'Throughput': 123,
    #             # 'OutpostArn': 'string',
    #             'Encrypted': False
    #         },
    #     },
    # ],
    ImageId='ami-0df4b2961410d4cff',
    InstanceType='t2.micro',
    # Ipv6AddressCount=123,
    # Ipv6Addresses=[
    #     {
    #         'Ipv6Address': 'string',
    #         'IsPrimaryIpv6': True|False
    #     },
    # ],
    # KernelId='string',
    KeyName='vpn',
    MaxCount=1,
    MinCount=1,
    # Monitoring={
    #     'Enabled': False
    # },
    # Placement={
    #     'AvailabilityZone': 'string',
    #     'Affinity': 'string',
    #     'GroupName': 'string',
    #     'PartitionNumber': 123,
    #     'HostId': 'string',
    #     'Tenancy': 'default',
    #     'SpreadDomain': 'string',
    #     # 'HostResourceGroupArn': 'string',
    #     'GroupId': 'string'
    # },
    # RamdiskId='string',
    SecurityGroupIds=[securityGroup_Id],
    # SecurityGroups=['openvpn_sg',],
    SubnetId=subnetID,
    UserData= userDataScript,
    # AdditionalInfo='string',
    # ClientToken='string',
    # DisableApiTermination=False,
    # EbsOptimized=True,
    # IamInstanceProfile={
    #     'Arn': 'string',
    #     'Name': 'string'
    # },
    # InstanceInitiatedShutdownBehavior='terminate',
    # NetworkInterfaces=[
    #     {
    #         'AssociatePublicIpAddress': True|False,
    #         'DeleteOnTermination': True|False,
    #         'Description': 'string',
    #         'DeviceIndex': 123,
    #         'Groups': [
    #             'string',
    #         ],
    #         'Ipv6AddressCount': 123,
    #         'Ipv6Addresses': [
    #             {
    #                 'Ipv6Address': 'string',
    #                 'IsPrimaryIpv6': True|False
    #             },
    #         ],
    #         'NetworkInterfaceId': 'string',
    #         'PrivateIpAddress': 'string',
    #         'PrivateIpAddresses': [
    #             {
    #                 'Primary': True|False,
    #                 'PrivateIpAddress': 'string'
    #             },
    #         ],
    #         'SecondaryPrivateIpAddressCount': 123,
    #         'SubnetId': 'string',
    #         'AssociateCarrierIpAddress': True|False,
    #         'InterfaceType': 'string',
    #         'NetworkCardIndex': 123,
    #         'Ipv4Prefixes': [
    #             {
    #                 'Ipv4Prefix': 'string'
    #             },
    #         ],
    #         'Ipv4PrefixCount': 123,
    #         'Ipv6Prefixes': [
    #             {
    #                 'Ipv6Prefix': 'string'
    #             },
    #         ],
    #         'Ipv6PrefixCount': 123,
    #         'PrimaryIpv6': True|False
    #     },
    # ],
    # PrivateIpAddress='string',
    # ElasticGpuSpecification=[
    #     {
    #         'Type': 'string'
    #     },
    # ],
    # ElasticInferenceAccelerators=[
    #     {
    #         'Type': 'string',
    #         'Count': 123
    #     },
    # ],
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
    # LaunchTemplate={
    #     'LaunchTemplateId': 'string',
    #     'LaunchTemplateName': 'string',
    #     'Version': 'string'
    # },
    # InstanceMarketOptions={
    #     'MarketType': 'spot',
    #     'SpotOptions': {
    #         'MaxPrice': 'string',
    #         'SpotInstanceType': 'one-time'|'persistent',
    #         'BlockDurationMinutes': 123,
    #         'ValidUntil': datetime(2015, 1, 1),
    #         'InstanceInterruptionBehavior': 'hibernate'|'stop'|'terminate'
    #     }
    # },
    # CreditSpecification={
    #     'CpuCredits': 'string'
    # },
    # CpuOptions={
    #     'CoreCount': 123,
    #     'ThreadsPerCore': 123,
    #     'AmdSevSnp': 'enabled'|'disabled'
    # },
    # CapacityReservationSpecification={
    #     'CapacityReservationPreference': 'open'|'none',
    #     'CapacityReservationTarget': {
    #         'CapacityReservationId': 'string',
    #         'CapacityReservationResourceGroupArn': 'string'
    #     }
    # },
    # HibernationOptions={
    #     'Configured': True|False
    # },
    # LicenseSpecifications=[
    #     {
    #         'LicenseConfigurationArn': 'string'
    #     },
    # ],
    # MetadataOptions={
    #     'HttpTokens': 'optional'|'required',
    #     'HttpPutResponseHopLimit': 123,
    #     'HttpEndpoint': 'disabled'|'enabled',
    #     'HttpProtocolIpv6': 'disabled'|'enabled',
    #     'InstanceMetadataTags': 'disabled'|'enabled'
    # },
    # EnclaveOptions={
    #     'Enabled': True|False
    # },
    # PrivateDnsNameOptions={
    #     'HostnameType': 'ip-name'|'resource-name',
    #     'EnableResourceNameDnsARecord': True|False,
    #     'EnableResourceNameDnsAAAARecord': False
    # },
    # MaintenanceOptions={
    #     'AutoRecovery': 'disabled'|'default'
    # },
    # DisableApiStop=True|False,
    # EnablePrimaryIpv6=False
)