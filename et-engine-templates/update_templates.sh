#!/bin/bash

# Define your S3 bucket name
BUCKET_NAME="et-engine-templates"

# Define the base directory where your CDK projects are located
BASE_CDK_DIR=$(pwd)

# List of your CDK project directories, relative to the base directory
CDK_PROJECTS=("efs-basic")

# Loop through each project
for PROJECT_DIR in "${CDK_PROJECTS[@]}"; do
    echo "Processing template: $PROJECT_DIR"

    # Navigate to project directory
    cd "$BASE_CDK_DIR/$PROJECT_DIR"

    # Synthesize CloudFormation template
    TEMPLATE_FILE="${PROJECT_DIR}.yaml"
    cdk synth > "$TEMPLATE_FILE"
    
    # Here you could include any steps to programmatically edit the template file
    # e.g., sed -i 's/original_text/replacement_text/g' "$TEMPLATE_FILE"

    # Upload the template to S3
    aws s3 cp "$TEMPLATE_FILE" "s3://$BUCKET_NAME/$TEMPLATE_FILE"
done
