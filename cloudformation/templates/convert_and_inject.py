import yaml
import json
import os

# Custom constructor to handle AWS-specific tags like !ImportValue
def custom_constructor(loader, tag_suffix, node):
    return f"{tag_suffix} {node.value}"

# Add support for !ImportValue
yaml.add_multi_constructor('!', custom_constructor, Loader=yaml.FullLoader)

def convert_and_inject(task_def_file, output_file):
    # Load the YAML file (assumes CloudFormation-style input)
    with open(task_def_file, 'r') as yaml_file:
        cf_template = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # Extract the TaskDefinition resource from the CloudFormation template
    task_definition = cf_template.get("Resources", {}).get("FlaskAppTaskDefinition", {}).get("Properties", {})

    # Ensure required ECS fields exist
    if "Family" not in task_definition or "ContainerDefinitions" not in task_definition:
        raise ValueError("Task definition is missing required fields: 'Family' or 'ContainerDefinitions'")

    # Transform fields to match ECS CLI expectations
    ecs_task_def = {
        "family": task_definition.get("Family"),
        "networkMode": task_definition.get("NetworkMode", "awsvpc"),
        "requiresCompatibilities": task_definition.get("RequiresCompatibilities", []),
        "cpu": task_definition.get("Cpu"),
        "memory": task_definition.get("Memory"),
        "executionRoleArn": task_definition.get("ExecutionRoleArn"),
        "taskRoleArn": task_definition.get("TaskRoleArn"),
        "containerDefinitions": task_definition.get("ContainerDefinitions", [])
    }

    # Replace placeholders with actual environment variables dynamically
    for container in ecs_task_def["containerDefinitions"]:
        for env_var in container.get("Environment", []):
            name = env_var.get("Name")
            if name == "DB_PASSWORD":
                env_var["Value"] = os.getenv("DB_PASSWORD", "default-password")  # GitHub Secret or default
            elif name == "VPC_ID":
                env_var["Value"] = os.getenv("VPC_ID", "")
            elif name == "TASK_EXEC_ROLE_ARN":
                env_var["Value"] = os.getenv("TASK_EXEC_ROLE", "")
            elif name == "SUBNET_ID":
                env_var["Value"] = os.getenv("SUBNET_ID", "")
            elif name == "AWS_REGION":
                env_var["Value"] = os.getenv("AWS_REGION", "us-west-1")  # Default region if not set
            elif name == "DB_HOST":
                env_var["Value"] = os.getenv("DB_HOST", "localhost")  # Default host if not set
            elif name == "DB_PORT":
                env_var["Value"] = os.getenv("DB_PORT", "5432")  # Default port if not set

    # Write the final ECS task definition to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(ecs_task_def, json_file, indent=2)

if __name__ == "__main__":
    task_def_file = os.getenv('TASK_DEF_FILE', 'cloudformation/templates/Task_def.yml')
    output_file = 'Task_def.json'
    convert_and_inject(task_def_file, output_file)
