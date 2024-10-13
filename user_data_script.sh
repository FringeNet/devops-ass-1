#!/bin/bash
#I couldn't find a way to extract the html into a separate file so I left it in the user data script.
yum install httpd -y
systemctl enable httpd
systemctl start httpd
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/instance-id)
PRIVATE_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4)
INSTANCE_TYPE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/instance-type)
AVAILABILITY_ZONE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
cat <<EOF > /var/www/html/index.html
<!DOCTYPE html>
<html>
<head>
    <title>James Demaine 20093118</title>
</head>
<body>
    <h1>James Demaine 20093118 DevOps Assignment</h1>
    <img src="http://devops.witdemo.net/logo.jpg" alt="WIT Logo">
    <pre>
      Instance ID: $INSTANCE_ID
      Private IP Address: $PRIVATE_IP
      Instance Type: $INSTANCE_TYPE
      Availability Zone: $AVAILABILITY_ZONE
    </pre>
</body>
</html>
EOF
systemctl restart httpd
