#!/bin/env python3

import json
import os
import re
import sys
import yaml
from os.path import isdir
from os.path import isfile
from os.path import join as p_join


def usage():
    msg = ['usage: {} in_dir out_file'.format(__file__),
           '    in_dir - directory where to find webhook config dirs',
           '    out_file - where to write the generated json file']
    print('\n'.join(msg))


def read_text_file(file_path, format_data):
    lines = []
    try:
        for line in open(file_path):
            if format_data:
                lines.append(line.format(**format_data))
            else:
                lines.append(line)
    except OSError:
        return None

    return ''.join(lines)


def parse_yaml_or_json_file(file_path, format_data=None):
    try_files = [{'type': 'yaml', 'path': file_path + '.yaml'},
                 {'type': 'yaml', 'path': file_path + '.yml'},
                 {'type': 'json', 'path': file_path + '.json'}]

    for entry in try_files:
        if not isfile(entry['path']):
            continue

        file_text = read_text_file(entry['path'], format_data)

        if file_text is None:
            return None

        if entry['type'] == 'yaml':
            return yaml.load(file_text)

        else:
            return json.loads(file_text)


def handle_hook_dir(hook_path, base_name):
    id_expr = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    if not re.match(id_expr, base_name):
        msg = 'hook {!r} must match regular expression {!r}'
        raise ValueError(msg.format(base_name, id_expr))

    secrets_file = p_join(hook_path, 'secrets')
    hook_file = p_join(hook_path, 'hook')

    secrets_data = parse_yaml_or_json_file(secrets_file)
    hook_data = parse_yaml_or_json_file(hook_file, format_data=secrets_data)

    if hook_data is None:
        msg = 'no yml or json file founr for hook {!r}'.format(base_name)
        raise TypeError(msg)

    hook_data['id'] = base_name
    hook_data['execute-command'] = '/data/trigger_hook.sh'
    hook_data['pass-arguments-to-command'] = [{'source': 'string',
                                               'name': base_name}]

    return hook_data


def main(hooks_dir, out_json):
    hooks_config = []

    for entry in os.listdir(hooks_dir):
        full_path = p_join(hooks_dir, entry)

        if isdir(full_path):
            hooks_config.append(handle_hook_dir(full_path, entry))

    with open(out_json, 'w') as fd:
        fd.write(json.dumps(hooks_config, indent=4, sort_keys=True))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
