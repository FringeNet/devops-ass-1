import json
import boto3
import random
import string

def generate_bucket_name(name):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)) + '-' + name

def create_bucket(name, region):
    s3 = boto3.resource('s3', region_name='us-east-1')
    #BucketOwnerPreferred is required for the bucket to be publicly accessible, learned this the hard way
    bucket = s3.create_bucket(Bucket=name, ObjectOwnership='BucketOwnerPreferred')
    bucket.wait_until_exists()
    print(f"Bucket created: {bucket.name}")
    return bucket

def upload_file(bucket, region, file_name):
    #upload the file and set the ACL to public-read
    s3 = boto3.resource('s3', region_name=region)
    html = open(file_name, 'r').read()
    bucket.put_object(Key='index.html', Body=html, ContentType='text/html')
    document = s3.Object(bucket.name, 'index.html')
    #ACL was not allowed until I set the bucket policy
    document.Acl().put(ACL='public-read')
    print(f"File uploaded: {file_name}")
    return

def set_bucket_website(bucket_name, region):
    s3 = boto3.resource('s3', region_name=region)
    bucket_website = s3.BucketWebsite(bucket_name)
    bucket_website.put(WebsiteConfiguration={'ErrorDocument': {'Key': 'error.html'}, 'IndexDocument': {'Suffix': 'index.html'}})
    print(f"Bucket website enabled: {bucket_name}")
    return

#https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_public_access_block.html
#This gave me a lot of headaches, I couldn't get the uploaded file to be publicly accessible
def disable_block_public_access(bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': False,
            'IgnorePublicAcls': False,
            'BlockPublicPolicy': False,
            'RestrictPublicBuckets': False
        }
    )
    print(f"Public access enabled for bucket: {bucket_name}")
    return

#https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteAccessPermissionsReqd.html
#I couldn't get the uploaded file to be publicly accessible, I found this on the internet
def set_bucket_policy(bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }]
    }
    bucket_policy = json.dumps(bucket_policy)
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
    print(f"Bucket policy set for public read access: {bucket_name}")
    return

#Check if a bucket already exists, use it if it does
def does_bucket_exist(name, region):
    s3 = boto3.resource('s3', region_name=region)
    for bucket in s3.buckets.all():
        if name in bucket.name:
            return True
    return False

#I should have made a main function for the EC2 instance as well, but I didn't have time
def main(name, region):
    bucket_name = generate_bucket_name(name)
    #Should really ask the user if they want to delete the bucket if it already exists, same as I did for the instance.
    if does_bucket_exist(name, region):
        s3 = boto3.resource('s3', region_name=region)
        bucket_name = [bucket.name for bucket in s3.buckets.all() if name in bucket.name][0]
        print(f"A Bucket already exists: {bucket_name}")
        bucket_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com/"
        print(f"Bucket URL: {bucket_url}")
        return bucket_url
    bucket = create_bucket(bucket_name, region)
    disable_block_public_access(bucket_name, region)
    set_bucket_policy(bucket_name, region)
    upload_file(bucket, region, 'index.html')
    set_bucket_website(bucket_name, region)
    bucket_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com/"
    print(f"Bucket URL: {bucket_url}")
    return bucket_url


