import json
import os
import re
from collections import defaultdict
from typing import List, Dict

## Update project setup
root_path = '/Users/pskd73/some/another'
project = 'service/loan_operator'
project_path = os.path.join(root_path, project)
ignored_packages = [
    'lambda_core', 'pyluca', 'json', 'uuid', 'pandas', 'typing', 'datetime',
    'base64', 'mongoengine', 'math', 'pickle', 'io', 'calendar', 'dateutil',
    'boto3', 'copy', 'botocore', 'os', 'requests', 'enum', 'abc', 're'
]
file_prefix = 'loan_operator.'


def read_ignored_regex(path: str) -> List[str]:
    if not os.path.isfile(os.path.join(path, '.gitignore')):
        return []
    with open(os.path.join(path, '.gitignore')) as f:
        res = [r for r in f.read().split('\n') if not r.startswith('#')]
        return [r for r in res if len(r)]


def is_path_ignored(path: str, ignored_res: List[str]):
    for _re in ignored_res:
        _re = _re.replace('*', '.*')
        if not _re.endswith('/'):
            _re = f'{_re}$'
        if re.search(_re, path):
            return True
    return False


def is_dep_ignored(dep: str, ignored: List[str]):
    for package in ignored:
        if dep.startswith(package):
            return True
    return False


def get_dependencies(path: str, ignore: List[str]):
    with open(path) as f:
        content = f.read()
        dependencies = []
        for m in re.findall(r'^import (.*)$', content, flags=re.MULTILINE):
            m = re.sub(r' as .*', '', m)
            if not is_dep_ignored(m, ignore):
                dependencies.append(m)
        for m in re.findall(r'^from (.*) import .*$', content, flags=re.MULTILINE):
            if not is_dep_ignored(m, ignore):
                dependencies.append(m)
        return dependencies


def path_to_package(path: str):
    path = path.replace(project_path, '')
    if path.startswith('/'):
        path = path[1:]
    if path.endswith('.py'):
        path = path[:-3]
    return path.replace('/', '.')


def get_package_group(package: str):
    return package.split('.')[0]


def travel_dir(path: str, ignored_res: List[str], dependencies: dict):
    for f in os.listdir(path):
        if not is_path_ignored(os.path.join(path, f), ignored_res):
            if os.path.isfile(os.path.join(path, f)):
                if f.endswith('.py'):
                    full_path = os.path.join(path, f)
                    dependencies[f'{file_prefix}{path_to_package(full_path)}'] = get_dependencies(full_path, ignored_packages)
            else:
                travel_dir(os.path.join(path, f), ignored_res, dependencies)


def group_by_package(dependencies: List[str]):
    packages = defaultdict(list)
    for dep in dependencies:
        packages[get_package_group(dep)].append(dep)
    return packages


def get_all_files(dependencies: Dict[str, list]):
    return list(set(list(dependencies.keys()) + [dep for sublist in list(dependencies.values()) for dep in sublist]))


def get_package_dependencies(dependencies: Dict[str, list]):
    package_deps = []
    for source, deps in dependencies.items():
        for dep in deps:
            source_package = get_package_group(source)
            dep_package = get_package_group(dep)
            if source_package != dep_package:
                package_deps.append(f'{get_package_group(source)}:{get_package_group(dep)}')
    return [tuple(dep.split(':')) for dep in list(set(package_deps))]


def main():
    ignored_res = read_ignored_regex(root_path)
    ignored_res.append('tests')
    dependencies = {}
    travel_dir(project_path, ignored_res, dependencies)
    package_dependencies = get_package_dependencies(dependencies)
    with open('chart/data.json', 'w+') as f:
        f.write(json.dumps({'all': dependencies, 'package': package_dependencies}))


main()
