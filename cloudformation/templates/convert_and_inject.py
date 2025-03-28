import yaml
import json
import os

# Custom constructor to handle AWS-specific tags like !ImportValue
def custom_constructor(loader, tag_suffix, node):
    return f"{tag_suffix} {node.value}"  # Handle the tag generically

# Add support for !ImportValue (and other AWS-specific tags if needed)
yaml.add_multi_constructor('!', custom_constructor, Loader=yaml.FullLoader)

# Load the YAML file
with open('cloudformation/templates/Task_def.yml', 'r') as yaml_file:
    task_def = yaml.load(yaml_file, Loader=yaml.FullLoader)

# Inject environment variables into container definitions
for container in task_def.get('containerDefinitions', []):
    container['environment'] = [
        {'name': 'DB_PASSWORD', 'value': os.getenv('DB_PASSWORD')}
    ]

# Convert to JSON and save to file
with open('Task_def.json', 'w') as json_file:
    json.dump(task_def, json_file, indent=2)
