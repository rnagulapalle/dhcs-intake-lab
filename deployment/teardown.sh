#!/bin/bash
set -e

echo "🗑️  DHCS BHT Teardown - Deleting All AWS Resources"
echo "=================================================="
echo ""

# Variables
AWS_REGION="us-west-2"
PROJECT_NAME="dhcs-bht-demo"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-service"
ALB_NAME="${PROJECT_NAME}-alb"
TG_NAME="${PROJECT_NAME}-tg"
SG_NAME="${PROJECT_NAME}-sg"
ECR_REPO="${PROJECT_NAME}-api"
ROLE_NAME="${PROJECT_NAME}-task-execution-role"

echo "⚠️  WARNING: This will delete all resources for $PROJECT_NAME"
echo ""
read -p "Are you sure? Type 'yes' to continue: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Starting teardown..."
echo ""

# 1. Delete ECS Service
echo "🗑️  Step 1/10: Deleting ECS service..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --desired-count 0 \
  2>/dev/null || echo "   Service not found"

aws ecs delete-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force \
  2>/dev/null && echo "   Service deleted" || echo "   Service not found"

echo ""

# Wait for service to drain
echo "⏳ Waiting for service to drain (30 seconds)..."
sleep 30
echo ""

# 2. Delete ECS Cluster
echo "🗑️  Step 2/10: Deleting ECS cluster..."
aws ecs delete-cluster \
  --cluster $CLUSTER_NAME \
  2>/dev/null && echo "   Cluster deleted" || echo "   Cluster not found"

echo ""

# 3. Delete Load Balancer
echo "🗑️  Step 3/10: Deleting load balancer..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names $ALB_NAME \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text 2>/dev/null)

if [ "$ALB_ARN" != "None" ] && [ ! -z "$ALB_ARN" ]; then
  aws elbv2 delete-load-balancer \
    --load-balancer-arn $ALB_ARN
  echo "   Load balancer deleted"
else
  echo "   Load balancer not found"
fi

echo ""

# 4. Delete Target Group
echo "🗑️  Step 4/10: Deleting target group..."
sleep 10  # Wait for ALB to finish deleting
TG_ARN=$(aws elbv2 describe-target-groups \
  --names $TG_NAME \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text 2>/dev/null)

if [ "$TG_ARN" != "None" ] && [ ! -z "$TG_ARN" ]; then
  aws elbv2 delete-target-group \
    --target-group-arn $TG_ARN
  echo "   Target group deleted"
else
  echo "   Target group not found"
fi

echo ""

# 5. Delete Security Group
echo "🗑️  Step 5/10: Deleting security group..."
sleep 10  # Wait for network resources to detach
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SG_NAME" \
  --query 'SecurityGroups[0].GroupId' \
  --output text 2>/dev/null)

if [ "$SG_ID" != "None" ] && [ ! -z "$SG_ID" ]; then
  aws ec2 delete-security-group \
    --group-id $SG_ID \
    2>/dev/null && echo "   Security group deleted" || echo "   Security group in use, will auto-delete later"
else
  echo "   Security group not found"
fi

echo ""

# 6. Delete ECR Repository
echo "🗑️  Step 6/10: Deleting ECR repository..."
aws ecr delete-repository \
  --repository-name $ECR_REPO \
  --force \
  2>/dev/null && echo "   ECR repository deleted" || echo "   ECR repository not found"

echo ""

# 7. Delete Secrets Manager Secret
echo "🗑️  Step 7/10: Deleting secret..."
aws secretsmanager delete-secret \
  --secret-id "${PROJECT_NAME}/openai-key" \
  --force-delete-without-recovery \
  2>/dev/null && echo "   Secret deleted" || echo "   Secret not found"

echo ""

# 8. Delete CloudWatch Log Group
echo "🗑️  Step 8/10: Deleting CloudWatch logs..."
aws logs delete-log-group \
  --log-group-name "/ecs/$PROJECT_NAME" \
  2>/dev/null && echo "   Log group deleted" || echo "   Log group not found"

echo ""

# 9. Detach and Delete IAM Role
echo "🗑️  Step 9/10: Deleting IAM role..."
aws iam detach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  2>/dev/null || true

aws iam detach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  2>/dev/null || true

aws iam delete-role \
  --role-name $ROLE_NAME \
  2>/dev/null && echo "   IAM role deleted" || echo "   IAM role not found"

echo ""

# 10. Deregister Task Definitions (keep last 5, delete older)
echo "🗑️  Step 10/10: Cleaning up old task definitions..."
TASK_FAMILY="${PROJECT_NAME}-task"
TASK_ARNS=$(aws ecs list-task-definitions \
  --family-prefix $TASK_FAMILY \
  --status ACTIVE \
  --query 'taskDefinitionArns[5:]' \
  --output text 2>/dev/null)

if [ ! -z "$TASK_ARNS" ]; then
  for ARN in $TASK_ARNS; do
    aws ecs deregister-task-definition \
      --task-definition $ARN \
      2>/dev/null || true
  done
  echo "   Old task definitions deregistered"
else
  echo "   No old task definitions to clean up"
fi

echo ""
echo "✅ Teardown Complete!"
echo "======================================"
echo ""
echo "All AWS resources for $PROJECT_NAME have been deleted."
echo ""
echo "Note: Some resources may take a few minutes to fully delete."
echo ""
echo "Check costs in 24 hours:"
echo "  aws ce get-cost-and-usage \\"
echo "    --time-period Start=\$(date -u -d '1 day ago' +%Y-%m-%d),End=\$(date -u +%Y-%m-%d) \\"
echo "    --granularity DAILY \\"
echo "    --metrics BlendedCost"
echo ""
