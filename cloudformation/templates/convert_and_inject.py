import os
import yaml
import json

def custom_constructor(loader, tag_suffix, node):
    """
    Custom constructor to resolve CloudFormation-style tags like !ImportValue.
    Dynamically replaces tags with environment variables or defaults.
    """
    return os.getenv(node.value, f"{tag_suffix} {node.value}")

# Add support for !ImportValue in YAML files
yaml.add_multi_constructor('!', custom_constructor, Loader=yaml.FullLoader)

def convert_yaml_to_json_with_outputs(task_def_file, output_file, outputs_file):
    """
    Converts YAML Task Definition to JSON and generates Outputs (CloudFormation-style).
    """
    # Load YAML file
    with open(task_def_file, 'r') as yaml_file:
        cf_template = yaml.safe_load(yaml_file)

    # Extract the TaskDefinition resource
    task_definition = cf_template.get("Resources", {}).get("FlaskAppTaskDefinition", {}).get("Properties", {})
    if not task_definition:
        raise ValueError("Task definition is missing or incorrectly formatted in YAML file.")

    # Convert keys to ECS-specific case
    ecs_case_mapping = {
        "Family": "family",
        "NetworkMode": "networkMode",
        "RequiresCompatibilities": "requiresCompatibilities",
        "Cpu": "cpu",
        "Memory": "memory",
        "ExecutionRoleArn": "executionRoleArn",
        "TaskRoleArn": "taskRoleArn",
        "ContainerDefinitions": "containerDefinitions",
        "Environment": "environment",
        "Name": "name",
        "Value": "value",
        "PortMappings": "portMappings",
        "ContainerPort": "containerPort",
        "Protocol": "protocol",
        "LogConfiguration": "logConfiguration",
        "LogDriver": "logDriver",
        "Options": "options",
        "Essential": "essential",
        "Image": "image"
    }

    def convert_keys_to_ecs_case(data):
        if isinstance(data, dict):
            return {ecs_case_mapping.get(key, key): convert_keys_to_ecs_case(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [convert_keys_to_ecs_case(item) for item in data]
        else:
            return data

    ecs_task_def = convert_keys_to_ecs_case(task_definition)

    # Replace placeholders with actual environment variables dynamically
    for container in ecs_task_def.get("containerDefinitions", []):
        for env_var in container.get("environment", []):
            name = env_var["name"]
            if name == "DB_PASSWORD":
                env_var["value"] = os.getenv("DB_PASSWORD", "default-password")  # GitHub Secret or default
            elif name == "TaskExecutionRoleArn":
                env_var["value"] = os.getenv("TASK_EXEC_ROLE", "")
            elif name == "RDSInstanceEndpoint":
                env_var["value"] = os.getenv("DB_HOST", "localhost")  # Default host if not set
            elif name == "ECRRepositoryURI":
                env_var["value"] = os.getenv("ECR_REPOSITORY", "")
            elif name == "MyTaskExecutionRoleExportName":
                env_var["value"] = os.getenv("TASK_ROLE", "")
            elif name == "FlaskEnv":
                env_var["value"] = os.getenv("FlaskEnv", "")
            elif name == "AWS_REGION":
                env_var["value"] = os.getenv("AWS_REGION", "")


    # Save the Task Definition JSON
    with open(output_file, 'w') as json_file:
        json.dump(ecs_task_def, json_file, indent=2)

    # Generate Outputs (simulate CloudFormation-style export)
    task_def_arn = f"arn:aws:ecs:{os.getenv('AWS_REGION', 'us-east-1')}:{os.getenv('AWS_ACCOUNT_ID', '123456789012')}:task-definition/{ecs_task_def['family']}"
    outputs = {
        "FlaskAppTaskDefinition": {
            "Description": "The ARN of the Flask App Task Definition",
            "Value": task_def_arn,
            "ExportName": "FlaskAppTaskDefinition"
        }
    }

    # Save Outputs to JSON file
    with open(outputs_file, 'w') as outputs_json_file:
        json.dump(outputs, outputs_json_file, indent=2)

    return ecs_task_def, outputs


if __name__ == "__main__":
    # File paths
    task_def_file = os.getenv("TASK_DEF_FILE", "cloudformation/templates/Task_def.yml")
    output_file = "Task_def.json"
    outputs_file = "Task_def_outputs.json"

    # Convert YAML and generate outputs
    try:
        task_definition, outputs = convert_yaml_to_json_with_outputs(task_def_file, output_file, outputs_file)
        print("Task Definition JSON and Outputs generated successfully.")
        print("Outputs:")
        print(json.dumps(outputs, indent=2))
    except Exception as e:
        print(f"Error: {e}")
