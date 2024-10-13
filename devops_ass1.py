import EC2
import S3
import subprocess
import os
import argparse

# defaults
name = 'jdemaine'
image_id = 'ami-0ebfd941bbafe70c6'
region = 'us-east-1'
instance_type = 't2.nano'
key_name = 'devops_assignment'
instance_name = 'Devops Assignment'
vpc_id = -1
security_group_name = 'Devops Security Group'
security_group_desc = 'Allow HTTP and SSH traffic'
security_group_id = -1
# https://stackoverflow.com/questions/39021545/how-to-specify-all-ports-in-security-group-cloudformation
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
instance_ip = None


###CHATGPT### prompted with the default variables, ip_permissions is impossible, as it is a list of dictionaries, and user_data is a file.
def parse_args():
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
    return parser.parse_args()
###CHATGPTEND###


# Ensure key pair exists locally or create a new one
def ensure_key_pair_exists(key_name, region):
    if not EC2.key_pair_exists(key_name, region):
        EC2.create_key_pair(key_name, region)
        print(f"Key pair created. Access the instance with the key: {key_name}.pem")
    else:
        if not os.path.exists(key_name + ".pem"):
            # I figured if the file is missing locally, then the key pair is useless, so I delete it and recreate it
            print("Key pair does not exist locally, recreating key pair")
            EC2.delete_key_pair(key_name, region)
            EC2.create_key_pair(key_name, region)


# Ensure security group exists or create a new one
def ensure_security_group_exists(security_group_name, region, security_group_desc, vpc_id, ip_permissions):
    if not EC2.security_group_exists(security_group_name, region):
        security_group = EC2.create_security_group(security_group_name, region, security_group_desc, vpc_id,
                                                   ip_permissions)
        security_group_id = security_group.id
    else:
        security_group_id = EC2.get_security_group_id(security_group_name, region)
        print(f"Using existing security group: {security_group_id}")
    return security_group_id


# Launch or terminate instance based on user input
def launch_or_find_instance(instance_name, region, image_id, instance_type, key_name, security_group_id, user_data):
    instance_dict = EC2.get_instance_by_name(instance_name, region, True)
    if instance_dict:
        instance_ip = instance_dict["PublicIpAddress"]
        print(f"Instance already exists. Access it at: {instance_ip}")
        # This input should ideally be in a loop, but I didn't have time to implement it. Any answer other than 'y' will be treated as 'n'
        terminate = input("Would you like to terminate the instance? (y/n): ")
        if terminate.lower() == 'y':
            EC2.terminate_instance(instance_dict["InstanceId"], region)
            return None
    else:
        instance = EC2.launch_instance(image_id, region, instance_type, key_name, instance_name, security_group_id,
                                       user_data)
        instance_ip = instance.public_ip_address
        print(f"Instance launched. Public IP address: {instance_ip}")
    return instance_ip


# Upload the monitoring script and execute it on the instance
def upload_and_run_monitoring_script(instance_ip, key_name):
    print("Uploading monitoring script to the instance")
    subprocess.run(["scp", "-i", key_name + ".pem", "-o", "StrictHostKeyChecking=no", "monitoring.sh",
                    f"ec2-user@{instance_ip}:"])
    print("Monitoring script uploaded. Making it executable and running it")
    subprocess.run(["ssh", "-i", key_name + ".pem", "-o", "StrictHostKeyChecking=no",
                    f"ec2-user@{instance_ip}", "chmod +x monitoring.sh"])
    subprocess.run(["ssh", "-i", key_name + ".pem", "-o", "StrictHostKeyChecking=no",
                    f"ec2-user@{instance_ip}", "./monitoring.sh"])


# Save instance and bucket URLs to a file
def save_urls_to_file(instance_url, bucket_url):
    file_name = name + "-websites.txt"
    with open(file_name, 'w') as f:
        f.write(f"Instance URL: {instance_url}\n")
        f.write(f"Bucket URL: {bucket_url}\n")
    print(f"URLs saved to {file_name}")


# Main program
def main():
    ###CHATGPT###
    args = parse_args()
    global image_id, region, instance_type, key_name, instance_name, vpc_id, security_group_name, security_group_desc, ip_permissions, user_data
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
    ###CHATGPTEND###

    # Fetch default VPC ID if not provided
    if vpc_id == -1:
        vpc_id = EC2.get_vpc_id(region)
        print(f"Using default VPC: {vpc_id}")

    # Ensure key pair and security group exist
    ensure_key_pair_exists(key_name, region)
    security_group_id = ensure_security_group_exists(security_group_name, region, security_group_desc, vpc_id,
                                                     ip_permissions)

    # Launch or find running instance
    instance_ip = launch_or_find_instance(instance_name, region, image_id, instance_type, key_name, security_group_id,
                                          user_data)
    if instance_ip is None:
        print("Instance terminated. Bucket may not be created. Exiting...")
        exit(0)

    print(f"Instance is running, accessible at: http://{instance_ip}/")

    # Create S3 bucket and upload files
    bucket_url = S3.main(name, region)
    print("The S3 bucket has been created and configured")

    # Save URLs to a file
    instance_url = f"http://{instance_ip}/"
    save_urls_to_file(instance_url, bucket_url)

    # Upload and run monitoring script
    upload_and_run_monitoring_script(instance_ip, key_name)
    print("If the Web Server is not running, httpd is not yet running")
    #Sometimes the instance hasn't had a chance to run the user data script, I should have waited for it to finish before running the monitoring script


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        #I should really have better error handling
        print(f"An error occurred: {e}")
        exit(1)
