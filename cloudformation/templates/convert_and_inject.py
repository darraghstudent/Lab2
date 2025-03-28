import json
import os
import yaml

# Custom constructor to handle AWS-specific tags like !ImportValue
def custom_constructor(loader, tag_suffix, node):
    return f"{tag_suffix} {node.value}"

# Add support for !ImportValue
def custom_constructor(loader, tag_suffix, node):
    # Resolve ImportValue placeholders using environment variables or mappings
    return os.getenv(node.value, f"{tag_suffix} {node.value}")

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
            if name == "DB_PASSWORD":
                env_var["value"] = os.getenv("DB_PASSWORD", "default-password")  # GitHub Secret or default
            elif name == "VpcId":
                env_var["value"] = os.getenv("VPC_ID", "")
            elif name == "TaskExecutionRoleArn":
                env_var["value"] = os.getenv("TASK_EXEC_ROLE", "")
            elif name == "PublicSubnetId":
                env_var["value"] = os.getenv("PublicSubnetId", "")
            elif name == "RDSInstanceEndpoint":
                env_var["value"] = os.getenv("DB_HOST", "localhost")  # Default host if not set
            elif name == "MyECSClusterName":
                env_var["value"] = os.getenv("ECS_CLUSTER", "")
            elif name == "ECRRepositoryURI":
                env_var["value"] = os.getenv("ECR_REPOSITORY", "")
            elif name == "MyTaskExecutionRoleExportName":
                env_var["value"] = os.getenv("TASK_ROLE", "")
            elif name == "FlaskEnv":
                env_var["value"] = os.getenv("FlaskEnv", "")
            elif name == "AWS_REGION":
                env_var["value"] = os.getenv("AWS_REGION", "")
            elif name == "MySecurityGroup":
                env_var["value"] = os.getenv("MySecurityGroup", "")
     

    # Write the final ECS task definition to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(ecs_task_def, json_file, indent=2)

if __name__ == "__main__":
    task_def_file = os.getenv('TASK_DEF_FILE', 'cloudformation/templates/Task_def.yml')
    output_file = 'Task_def.json'
    convert_and_inject(task_def_file, output_file)
