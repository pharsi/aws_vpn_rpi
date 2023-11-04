# Setting up
## SSH key
- Create a key pair and name it ```vpn``` through the AWS Management Console
- Download this SSH key as this key will be used to access the VPN server (if needed)
## AWS Credentials
- Create an IAM user with EC2 permissions
- Download credentials for this IAM user
- Extract the access key ID and secret access key for this user
- Place both of these keys inside RPi at this location
```/home/rpi/openvpn/keysFile```
The contents of the ```keysFile``` file will be as follows
```
AKIAEXAMPLEACCESSKEYID
someRandomSecretAccessKey
```

# Running the code
- When powered up, RPi will pull the code from dev branch of this repo and will run the ```client_rpi/install_boto3.sh``` script
- When powered off (through the command-line ```¯\_(ツ)_/¯```) RPi will terminate the EC2 instance and deletes the SG only, it will not release the Elastic IP address for next run