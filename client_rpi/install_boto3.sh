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
    publicIP=`python3.9 provision_ec2.py`
    echo -e "${GREEN}OpenVPN server is live at $publicIP"
    echo -e "${NC}Fetching client configuration from OpenVPN server at $publicIP ${NC}"
    sudo curl -s --interface eth0 http://$publicIP:8080/client1.ovpn -o /etc/openvpn/client1.conf
    echo -e "Starting OpenVPN service using systemctl interface"
    sudo systemctl start openvpn@client1.service
    systemctl_start_openvpn_client_status=$?
    if [ $systemctl_start_openvpn_client_status -eq 0 ]; then
        echo -e "${GREEN}OpenVPN service started successfully"
        deps_check_passed=true
    else
       echo -e "${RED}Failed to start OpenVPN client service ${NC}"
    fi
    echo -e "${NC}Setting up iptables to forward all traffic from wlan0 to tun0"
    sudo sed -i 's/eth0/tun0/g' /etc/iptables.ipv4.nat
    sudo iptables-legacy-restore < /etc/iptables.ipv4.nat
    iptables_restore_status=$?
    if [ $iptables_restore_status -eq 0 ]; then
        echo -e "${NC}Successfully set up iptables to forward all traffic from wlan0 to tun0"
        echo -e "${NC}Ready to use the VPN"
    else
        echo -e "${RED}Failed to setup iptables"
    fi
else
    echo -e "${RED} Dependency checks failed${NC}"
fi