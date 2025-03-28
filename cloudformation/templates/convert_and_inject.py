import yaml
import json
import os

# Custom constructor to handle AWS-specific tags like !ImportValue
def custom_constructor(loader, tag_suffix, node):
    return f"{tag_suffix} {node.value}"

# Add support for !ImportValue
yaml.add_multi_constructor('!', custom_constructor, Loader=yaml.FullLoader)

def convert_and_inject(task_def_file, output_file):
    # Load the YAML file
    with open(task_def_file, 'r') as yaml_file:
        task_def = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # Replace the 'DB_PASSWORD' placeholder with the actual secret value
    for container in task_def.get('ContainerDefinitions', []):
        for env_var in container.get('Environment', []):
            if env_var.get('Name') == 'DB_PASSWORD':
                env_var['Value'] = os.getenv('DB_PASSWORD')  # Using GitHub Secret via the environment

    # Convert to JSON and save it
    with open(output_file, 'w') as json_file:
        json.dump(task_def, json_file, indent=2)

if __name__ == "__main__":
    task_def_file = os.getenv('TASK_DEF_FILE', 'cloudformation/templates/Task_def.yml')
    output_file = 'Task_def.json'
    convert_and_inject(task_def_file, output_file)
