import subprocess
import os
import argparse
import EC2

# defaults
image_id = 'ami-0ebfd941bbafe70c6'
region = 'us-east-1'
instance_type = 't2.nano'
key_name = 'devops_assignment'
instance_name = 'Devops Assignment'
vpc_id = -1
security_group_name = 'Devops Security Group'
security_group_desc = 'Allow HTTP and SSH traffic'
security_group_id = -1
ip_permissions = [
    {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    },
    {
        'IpProtocol': 'tcp',
        'FromPort': 80,
        'ToPort': 80,
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
    }
]
user_data_file = 'user_data_script.sh'
user_data = open(user_data_file, 'r').read()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='James Demaine DevOps Assignment 1')
    parser.add_argument('-i', '--image_id', help='The image id to use for the instance')
    parser.add_argument('-r', '--region', help='The region to launch the instance in')
    parser.add_argument('-t', '--instance_type', help='The instance type to launch')
    parser.add_argument('-k', '--key_name', help='The key name to use for the instance')
    parser.add_argument('-n', '--instance_name', help='The name of the instance')
    parser.add_argument('-v', '--vpc_id', help='The vpc id to use for the security group')
    parser.add_argument('-s', '--security_group_name', help='The name of the security group')
    parser.add_argument('-d', '--security_group_desc', help='The description of the security group')
    parser.add_argument('-p', '--ip_permissions', help='The ip permissions to use for the security group')
    parser.add_argument('-u', '--user_data', help='The user data to use for the instance')
    args = parser.parse_args()
    # set the variables to the arguments if they are provided and fetch ids if not provided
    if args.image_id:
        image_id = args.image_id
    if args.region:
        region = args.region
    if args.instance_type:
        instance_type = args.instance_type
    if args.key_name:
        key_name = args.key_name
    if args.instance_name:
        instance_name = args.instance_name
    if args.vpc_id:
        vpc_id = args.vpc_id
    if args.security_group_name:
        security_group_name = args.security_group_name
    if args.security_group_desc:
        security_group_desc = args.security_group_desc
    if args.ip_permissions:
        ip_permissions = args.ip_permissions
    if args.user_data:
        user_data = args.user_data
    if vpc_id == -1:
        vpc_id = EC2.get_vpc_id(region)
        print("Using default VPC:", vpc_id)
    if not EC2.key_pair_exists(key_name, region):
        EC2.create_key_pair(key_name, region)
        print("Key pair created, you can access the instance with the key", key_name + ".pem")
    else:
        if not os.path.exists(key_name + ".pem"):
            print("Key pair does not exist locally, recreating key pair")
            EC2.delete_key_pair(key_name, region)
            EC2.create_key_pair(key_name, region)
    if not EC2.security_group_exists(security_group_name, region):
        security_group = EC2.create_security_group(security_group_name, region, security_group_desc, vpc_id,
                                                   ip_permissions)
        security_group_id = security_group.id
    else:
        security_group_id = EC2.get_security_group_id(security_group_name, region)
        print("Using existing security group:", security_group_id)

    instance_dict = EC2.get_instance_by_name(instance_name, region, True)
    if instance_dict:
        print("Instance already exists, you can access the instance at", instance_dict["PublicIpAddress"])
        terminate = input("Would you like to terminate the instance? (y/n): ")
        if terminate == 'y':
            EC2.terminate_instance(instance_dict["InstanceId"], region)
        exit(0)
    else:
        try:
            instance = EC2.launch_instance(image_id, region, instance_type, key_name, instance_name, security_group_id,
                                           user_data)
            print("The instance's public IP address is ", instance.public_ip_address)
        except Exception as e:
            print(e)
            exit(1)
    print("You can now access the instance at http://" + instance.public_ip_address)
