#!/bin/bash
set -e

echo "🎨 DHCS Dashboard AWS Deployment"
echo "================================="

AWS_REGION="us-west-2"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="dhcs-bht-demo"
DASHBOARD_ECR_REPO="dhcs-bht-dashboard"
API_ALB_DNS="dhcs-bht-demo-alb-398486025.us-west-2.elb.amazonaws.com"

# Get existing infrastructure IDs
CLUSTER_NAME="${PROJECT_NAME}-cluster"
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=${PROJECT_NAME}-vpc" --query 'Vpcs[0].VpcId' --output text --region ${AWS_REGION} 2>/dev/null || echo "")

if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
  echo "Getting default VPC..."
  VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region ${AWS_REGION})
fi

SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --query 'Subnets[*].SubnetId' --output text --region ${AWS_REGION})
SUBNET1=$(echo $SUBNETS | awk '{print $1}')
SUBNET2=$(echo $SUBNETS | awk '{print $2}')

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text --region ${AWS_REGION})
ALB_DNS=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-alb --query 'LoadBalancers[0].DNSName' --output text --region ${AWS_REGION})

echo "Using existing infrastructure:"
echo "  VPC: ${VPC_ID}"
echo "  Subnets: ${SUBNET1}, ${SUBNET2}"
echo "  ALB: ${ALB_DNS}"

# Create target group for dashboard (port 8501)
echo ""
echo "Creating target group for dashboard..."
TG_ARN=$(aws elbv2 create-target-group \
  --name ${PROJECT_NAME}-dashboard-tg \
  --protocol HTTP \
  --port 8501 \
  --vpc-id ${VPC_ID} \
  --target-type ip \
  --health-check-path /_stcore/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region ${AWS_REGION} \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text 2>/dev/null || \
  aws elbv2 describe-target-groups --names ${PROJECT_NAME}-dashboard-tg --query 'TargetGroups[0].TargetGroupArn' --output text --region ${AWS_REGION})

echo "Target Group ARN: ${TG_ARN}"

# Create listener rule for dashboard (port 80, path /dashboard/*)
echo ""
echo "Creating ALB listener rule for dashboard..."
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn ${ALB_ARN} --query 'Listeners[?Port==`80`].ListenerArn' --output text --region ${AWS_REGION})

# Create rule for /dashboard path
aws elbv2 create-rule \
  --listener-arn ${LISTENER_ARN} \
  --priority 10 \
  --conditions Field=path-pattern,Values='/dashboard*' \
  --actions Type=forward,TargetGroupArn=${TG_ARN} \
  --region ${AWS_REGION} 2>/dev/null || echo "Listener rule already exists"

# Also create default rule for port 8501
echo "Creating listener on port 8501..."
ALB_SG=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-alb --query 'LoadBalancers[0].SecurityGroups[0]' --output text --region ${AWS_REGION})

# Add port 8501 to security group
aws ec2 authorize-security-group-ingress \
  --group-id ${ALB_SG} \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0 \
  --region ${AWS_REGION} 2>/dev/null || echo "Port 8501 already allowed"

# Create listener on port 8501
aws elbv2 create-listener \
  --load-balancer-arn ${ALB_ARN} \
  --protocol HTTP \
  --port 8501 \
  --default-actions Type=forward,TargetGroupArn=${TG_ARN} \
  --region ${AWS_REGION} 2>/dev/null || echo "Listener on 8501 already exists"

# Create ECS task definition for dashboard
echo ""
echo "Creating ECS task definition..."
TASK_ROLE_ARN=$(aws iam get-role --role-name ${PROJECT_NAME}-task-execution-role --query 'Role.Arn' --output text --region ${AWS_REGION} 2>/dev/null)

cat > /tmp/dashboard-task-def.json <<EOF
{
  "family": "${PROJECT_NAME}-dashboard-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "${TASK_ROLE_ARN}",
  "containerDefinitions": [
    {
      "name": "dashboard",
      "image": "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${DASHBOARD_ECR_REPO}:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_BASE_URL",
          "value": "http://${API_ALB_DNS}"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${PROJECT_NAME}-dashboard",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "dashboard",
          "awslogs-create-group": "true"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
  --cli-input-json file:///tmp/dashboard-task-def.json \
  --region ${AWS_REGION}

# Get security group for ECS tasks
TASK_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-task-sg" --query 'SecurityGroups[0].GroupId' --output text --region ${AWS_REGION})

# Create ECS service for dashboard
echo ""
echo "Creating ECS service for dashboard..."
aws ecs create-service \
  --cluster ${CLUSTER_NAME} \
  --service-name ${PROJECT_NAME}-dashboard-service \
  --task-definition ${PROJECT_NAME}-dashboard-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNET1},${SUBNET2}],securityGroups=[${TASK_SG}],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=${TG_ARN},containerName=dashboard,containerPort=8501" \
  --region ${AWS_REGION} 2>/dev/null || \
  aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${PROJECT_NAME}-dashboard-service \
    --force-new-deployment \
    --region ${AWS_REGION}

echo ""
echo "✅ Dashboard deployment initiated!"
echo ""
echo "=========================================="
echo "Access Dashboard UI:"
echo "  http://${ALB_DNS}:8501"
echo ""
echo "Monitor deployment:"
echo "  aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${PROJECT_NAME}-dashboard-service --region ${AWS_REGION}"
echo "=========================================="
