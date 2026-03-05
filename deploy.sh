#!/bin/bash
set -e

# Load variables from .env
export $(grep -v '^#' .env | xargs)

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"

echo "🔑 Logging in AWS ECR with profile $AWS_PROFILE ..."
AWS_PROFILE=$AWS_PROFILE aws ecr get-login-password --region $AWS_REGION \
    | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "🏷️  Tagging image: $LOCAL_IMAGE -> $ECR_URI:latest ..."
docker tag $LOCAL_IMAGE:latest $ECR_URI:latest

echo "📤 Pushing image to $ECR_URI ..."
docker push $ECR_URI:latest

echo "✅ Published image successfully in ECR"
