#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${AWS_REGION:-}" || -z "${AWS_ACCOUNT_ID:-}" || -z "${ECR_REPOSITORY:-}" || -z "${ECS_CLUSTER:-}" || -z "${ECS_SERVICE:-}" ]]; then
  echo "Set AWS_REGION, AWS_ACCOUNT_ID, ECR_REPOSITORY, ECS_CLUSTER, and ECS_SERVICE."
  exit 1
fi

IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"

aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
docker build -t "${ECR_REPOSITORY}:latest" .
docker tag "${ECR_REPOSITORY}:latest" "${IMAGE_URI}"
docker push "${IMAGE_URI}"

TASK_DEF_FILE="deploy/aws/ecs-task-definition.json"
TEMP_FILE="$(mktemp)"
sed "s|810448722017.dkr.ecr.ap-south-1.amazonaws.com/taskflow-pro:latest|${IMAGE_URI}|g" "${TASK_DEF_FILE}" > "${TEMP_FILE}"

aws ecs register-task-definition --cli-input-json "file://${TEMP_FILE}" >/dev/null
aws ecs update-service --cluster "${ECS_CLUSTER}" --service "${ECS_SERVICE}" --force-new-deployment >/dev/null

echo "Deployment triggered for ${IMAGE_URI}"
