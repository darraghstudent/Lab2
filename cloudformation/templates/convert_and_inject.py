import yaml
import json
import os

# Custom constructor to handle AWS-specific tags like !ImportValue
def custom_constructor(loader, tag_suffix, node):
    return f"{tag_suffix} {node.value}"

# Add support for !ImportValue
yaml.add_multi_constructor('!', custom_constructor, Loader=yaml.FullLoader)

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

def convert_and_inject(task_def_file, output_file):
    # Load the YAML file (assumes CloudFormation-style input)
    with open(task_def_file, 'r') as yaml_file:
        cf_template = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # Extract the TaskDefinition resource from the CloudFormation template
    task_definition = cf_template.get("Resources", {}).get("FlaskAppTaskDefinition", {}).get("Properties", {})

    # Validate the task_definition dictionary
    if not task_definition:
        raise ValueError("Task definition is missing or incorrectly formatted.")

    # Convert keys to ECS-specific case
    ecs_task_def = convert_keys_to_ecs_case(task_definition)

    # Replace placeholders with actual environment variables dynamically
    for container in ecs_task_def.get("containerDefinitions", []):  # Note: PascalCase preserved
        for env_var in container.get("environment", []):  # Note: PascalCase preserved
            name = env_var.get("name")
            if name == "db_password":
                env_var["value"] = os.getenv("DB_PASSWORD", "default-password")  # GitHub Secret or default
            elif name == "vpc_id":
                env_var["value"] = os.getenv("VPC_ID", "")
            elif name == "task_exec_role_arn":
                env_var["value"] = os.getenv("TASK_EXEC_ROLE", "")
            elif name == "subnet_id":
                env_var["value"] = os.getenv("SUBNET_ID", "")
            elif name == "aws_region":
                env_var["value"] = os.getenv("AWS_REGION", "us-west-1")  # Default region if not set
            elif name == "db_host":
                env_var["value"] = os.getenv("DB_HOST", "localhost")  # Default host if not set
            elif name == "db_port":
                env_var["value"] = os.getenv("DB_PORT", "5432")  # Default port if not set

    # Write the final ECS task definition to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(ecs_task_def, json_file, indent=2)

if __name__ == "__main__":
    task_def_file = os.getenv('TASK_DEF_FILE', 'cloudformation/templates/Task_def.yml')
    output_file = 'Task_def.json'
    convert_and_inject(task_def_file, output_file)

if __name__ == "__main__":
    task_def_file = os.getenv('TASK_DEF_FILE', 'cloudformation/templates/Task_def.yml')
    output_file = 'Task_def.json'
    convert_and_inject(task_def_file, output_file)
