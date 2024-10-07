#export a module that launches an ec2 instance
import os
import time

import boto3

def launch_instance(image_id, region, instance_type, key_name, instance_name, security_group, user_data):
    ec2 = boto3.resource('ec2', region_name=region)
    ec2_instance = ec2.create_instances(
        ImageId=image_id,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        SecurityGroupIds=[security_group],
        KeyName=key_name,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': instance_name
                    }
                ]
            }
        ],
        UserData=user_data)
    ec2_instance[0].wait_until_running()
    #wait until instance is initialized
    while ec2_instance[0].public_ip_address is None:
        ec2_instance[0].reload()
    #check if user_data is executed, httpd should be running
    counter = 0
    while counter < 10:
        #check if httpd is running
        response = os.system("curl -s " + ec2_instance[0].public_ip_address)
        if response == 0:
            break
        counter += 1
        #wait for 10 seconds
        time.sleep(10)
    return ec2_instance[0]

def get_instance_by_name(name, region, running):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            for tag in instance['Tags']:
                if tag['Key'] == 'Name' and tag['Value'] == name:
                    if running:
                        if instance['State']['Name'] == 'running':
                            return instance
                    else:
                        return instance
    return None

def create_security_group(name, region, desc, vpc_id, ip_permissions):
    ec2 = boto3.resource('ec2', region_name=region)
    security_group = ec2.create_security_group(
        GroupName=name,
        Description=desc,
        VpcId=vpc_id
    )
    security_group.authorize_ingress(
        IpPermissions=ip_permissions
    )
    print("Security Group Created, ID: ", security_group.id)
    return security_group

def create_key_pair(name, region):
    ec2 = boto3.client('ec2', region_name=region)
    key_pair = ec2.create_key_pair(KeyName=name)
    with open(f"{name}.pem", "w") as file:
        file.write(key_pair['KeyMaterial'])
    print("Key Pair Created, Name: ", name)
    return

def key_pair_exists(name, region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_key_pairs()
    for key_pair in response['KeyPairs']:
        if key_pair['KeyName'] == name:
            return True
    return False

def security_group_exists(name, region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_security_groups()
    for security_group in response['SecurityGroups']:
        if security_group['GroupName'] == name:
            return True
    return False

def get_security_group_id(name, region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_security_groups()
    for security_group in response['SecurityGroups']:
        if security_group['GroupName'] == name:
            return security_group['GroupId']
    return None

def get_vpc_id(region):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_vpcs()
    print("VPC ID: ", response['Vpcs'][0]['VpcId'])
    return response['Vpcs'][0]['VpcId']


def delete_key_pair(key_name, region):
    ec2 = boto3.client('ec2', region_name=region)
    ec2.delete_key_pair(KeyName=key_name)
    print("Key Pair Deleted, Name: ", key_name)
    return


def terminate_instance(instance_id, region):
    ec2 = boto3.client('ec2', region_name=region)
    ec2.terminate_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=[instance_id])
    print("Instance Terminated, ID: ", instance_id)
    return