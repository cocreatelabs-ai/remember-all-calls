#!/bin/bash

set -e

PROJECT_NAME="call-analyzer"
AWS_REGION="us-east-1"
AWS_PROFILE="call-analyzer"

echo "Building webapp Docker image..."
docker build --platform linux/amd64 -t $PROJECT_NAME-webapp ./webapp

echo "Getting ECR login..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE).dkr.ecr.$AWS_REGION.amazonaws.com

echo "Getting webapp ECR repository URI..."
WEBAPP_ECR_URI=$(aws ecr describe-repositories --repository-names $PROJECT_NAME-webapp --region $AWS_REGION --profile $AWS_PROFILE --query 'repositories[0].repositoryUri' --output text)

echo "Tagging and pushing webapp image..."
docker tag $PROJECT_NAME-webapp:latest $WEBAPP_ECR_URI:latest
docker push $WEBAPP_ECR_URI:latest

echo "Applying Terraform changes..."
cd terraform && terraform apply -auto-approve

echo "Updating webapp ECS service..."
aws ecs update-service --cluster $PROJECT_NAME --service $PROJECT_NAME-webapp --force-new-deployment --region $AWS_REGION --profile $AWS_PROFILE

echo "Webapp deployment complete!"