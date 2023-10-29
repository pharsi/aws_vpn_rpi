RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

deps_check_passed=false
check_deps(){

    # Check if python 3.9 is available, else install it
    if command -v python3.9 >/dev/null 2>&1 ; then
    echo -e "${GREEN}python3.9 found ${NC}"
    deps_check_passed=true

    else
        sudo -- bash -c 'apt-get update && apt-get install python3.9 -y >/dev/null 2>&1'
    fi
    
    # Check if pip is available, else install it
    if command -v pip >/dev/null 2>&1 ; then
        echo -e "${GREEN}pip found"
        deps_check_passed=true
    else
       echo -e "${RED}pip not found, installing pip ${NC}"
       sudo -- bash -c 'apt-get update && apt-get install python3-pip -y >/dev/null 2>&1'
    fi

    # Check if git is available, else install it
    if command -v git >/dev/null 2>&1 ; then
        echo -e "${GREEN}git found"
        deps_check_passed=true
    else
       echo -e "${RED}git not found, installing git ${NC}"
       sudo -- bash -c 'apt-get update && apt-get install git -y >/dev/null 2>&1'
    fi

    # Check if boto3 is available, else install it
    python -c "import boto3" >/dev/null 2>&1
    check_import_boto3=$?

    if [ $check_import_boto3 -eq 0 ]; then
        echo -e "${GREEN}boto3 found"
        deps_check_passed=true
    else
       echo -e "${RED}boto3 not found, installing boto3 ${NC}"
       python3.9 -m pip install boto3
    fi
}

check_deps

if $deps_check_passed
then
    echo -e "${GREEN}Dependency checks passed${NC}"
    echo -e "Provisioning an EC2 instance with an OpenVPN server"
    python3.9 provision_ec2.py
else
     echo -e "${RED} Dependency checks failed${NC}"
fi