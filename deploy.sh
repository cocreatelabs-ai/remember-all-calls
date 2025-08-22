#!/bin/bash

set -e

PROJECT_NAME="call-analyzer"
AWS_REGION="us-east-1"
AWS_PROFILE="call-analyzer"

echo "Building Docker image..."
docker build --platform linux/amd64 -t $PROJECT_NAME .

echo "Getting ECR login..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text --profile $AWS_PROFILE).dkr.ecr.$AWS_REGION.amazonaws.com

echo "Getting ECR repository URI..."
ECR_URI=$(aws ecr describe-repositories --repository-names $PROJECT_NAME-app --region $AWS_REGION --profile $AWS_PROFILE --query 'repositories[0].repositoryUri' --output text)

echo "Tagging and pushing image..."
docker tag $PROJECT_NAME:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo "Updating ECS service..."
aws ecs update-service --cluster $PROJECT_NAME --service $PROJECT_NAME-app --force-new-deployment --region $AWS_REGION --profile $AWS_PROFILE

echo "Deployment complete!"