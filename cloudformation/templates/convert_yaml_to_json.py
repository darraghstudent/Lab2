import os
import yaml
import json

# Custom constructor for !ImportValue
def import_value_constructor(loader, node):
    """
    Handles !ImportValue tags.
    Dynamically replaces tags with environment variables or a fallback value.
    """
    # Dynamically resolve environment variable based on the value in the tag
    return os.getenv(node.value, f"ImportValue({node.value})")

# Register the custom constructor for !ImportValue
yaml.add_constructor('!ImportValue', import_value_constructor, Loader=yaml.FullLoader)

def convert_keys_to_ecs_case(data):
    """
    Recursively converts keys to the exact case required by AWS ECS CLI.
    """
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

    if isinstance(data, dict):
        return {ecs_case_mapping.get(key, key): convert_keys_to_ecs_case(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_ecs_case(item) for item in data]
    else:
        return data

def convert_yaml_to_json(task_def, output_file):
    """
    Converts YAML Task Definition to JSON.
    """
    # Load YAML file
    with open(task_def, 'r') as yaml_file:
        cf_template = yaml.safe_load(yaml_file)

    # Extract the TaskDefinition resource
    task_definition = cf_template.get("Resources", {}).get("FlaskAppTaskDefinition", {}).get("Properties", {})
    if not task_definition:
        raise ValueError("Task definition is missing or incorrectly formatted in YAML file.")

    # Convert keys to ECS-specific case
    ecs_task_def = convert_keys_to_ecs_case(task_definition)

    # Replace placeholders dynamically in environment variables
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

    return ecs_task_def

if __name__ == "__main__":
    # File paths
    task_def = os.getenv("TASK_DEF", "cloudformation/templates/Task_def.yml")
    output_file = "Task_def.json"

    # Convert YAML to JSON
    try:
        task_definition = convert_yaml_to_json(task_def, output_file)
        print("Task Definition JSON generated successfully.")
    except Exception as e:
        print(f"Error: {e}")
