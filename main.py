#!/usr/bin/env python3

import argparse
from collections import OrderedDict, defaultdict
import os
from os import path
import platform
import re
import shutil
import sys
import uuid

# Colors used for output messages
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

skip_all, remove_all, backup_all = False, False, False
installed_layers = set()

def remove (file_path):
    if os.path.islink(file_path) or os.path.isfile(file_path):
        print("Removing file {0}".format(file_path))
        try:
            os.remove(file_path)
        except PermissionError:
            os.system("sudo rm -f {0}".format(file_path))
    elif os.path.isdir(file_path):
        print("Removing directory {0}".format(file_path))
        try:
            shutil.rmtree(file_path)
        except PermissionError:
            os.system("sudo rm -rf {0}".format(file_path))
    else:
        print("File {0} doesn't exist!".format(file_path))

def backup (file_path):
    file_name = os.path.split(file_path)[1]
    backup_base_path = path.abspath('backups')
    uid = uuid.uuid4().hex[:5]
    # We are backing up files that were in possibly different directories
    # now into one, so there are potential naming conflicts here.
    # Rather than address the problem in a legitimate way, Imma just throw a
    # uuid in there.
    backup_path = os.path.join(backup_base_path,
                               "{0}_{1}_backup".format(file_name, uid))
    if (not os.path.exists(backup_base_path)):
        os.makedirs(backup_base_path)
    print("Backing up {0} -> {1}".format(file_path, backup_path))
    shutil.move(file_path, backup_path)

# Meat and potatoes of the operation, here we are symlinking all our dotfiles
# based on their directive
def handle_link_directive(src, dest, action=None):
    global skip_all
    global remove_all
    global backup_all
    if action == 'S':
        skip_all = True
        print('Skipping {0}'.format(dest))
        return None
    elif action == 's':
        print('Skipping {0}'.format(dest))
        return None
    elif action == 'R':
        remove_all = True
        remove(dest)
    elif action == 'r':
        remove(dest)
    elif action == 'B':
        backup_all = True
        backup(dest)
    elif action is not None:
        backup(dest)

    # It's symlinking time!
    print("Symlinking {0} -> {1}".format(src, dest))
    try:
        os.symlink(src, dest)
    except PermissionError:
        os.system("sudo ln -s {0} {1}".format(src, dest))

def validate_link(link_args, layer_path):
    if not len(link_args) == 2:
        print('The link directive takes two arguments,'
              + ' a source and destination.')
        return None

    src = path.join(layer_path, link_args[0])
    dest = path.expandvars(path.expanduser(link_args[1]))

    if (not path.exists(src)):
        create = input("Source file '{0}' does not exist in the layer.\n"
                       .format(src) + "Would you like to create it? [Y/n]: ")
        if (create == 'n'):
            return None
        print("Creating '{0}'".format(src))
        os.makedirs(src)

    action = None
    if (path.exists(dest)):
        # Checks inode to see if same file
        if path.samefile(src, dest) or skip_all:
            action = 's'
        elif remove_all:
            action = 'r'
        elif backup_all:
            action = 'b'
        else:
            action = input(
                "Target '{0}' already exists, what do you want to do?\n"
                .format(dest)
                + "[s]kip, [S]kip all, [r]emove, [R]emove all, "
                + "[b]ackup, [B]ackup all: "
            )
    # path.exists follows symlinks, so if the path does not exist, but 'dest'
    # is a link, then it is a broken link
    elif (path.islink(dest)):
        remove_broken = input("{0} appears to be a broken link.\n".format(dest)
                              + 'Would you like to remove it? [Y/n]: ')
        if remove_broken == 'n':
            return None
        remove(dest)
    elif (not path.exists(path.dirname(dest))):
        os.makedirs(path.dirname(dest))
        
    return (src, dest, action)

def handle_run_directive(command, install_file_path):
    if command == 'run-mac' and platform.uname().system != 'Darwin':
        return False
    if command == 'run-ubuntu' and platform.linux_distribution()[0] != 'Ubuntu':
        return False
    # Hacky way to determine if platform is Arch where checking if
    # linux_distribution fails. Bettery was would be to parse '/etc/os-release'
    # or /etc/lsb-release
    if (command == 'run-arch' and
        (platform.linux_distribution()[0] != ''
         or platform.uname().system != 'Linux')):
            return False

    if install_file_path.startswith('"') and install_file_path.endswith('"'):
        command_string = "echo {0} | bash".format(install_file_path)
    else:
        if not os.access(install_file_path, os.X_OK):
            print(bcolors.FAIL + "\"{0}\": Install file not executable!"
                  .format(install_file_path) + bcolors.ENDC)
            return False
        command_string = "sh -c {0}".format(install_file_path)
    print("Running {0}:".format(install_file_path))
    print(bcolors.HEADER + ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
          + bcolors.ENDC)
    os.system(command_string)
    print(bcolors.HEADER + "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
          + bcolors.ENDC)
    return True

def handle_directive(layer_name, command, args):
    layer_path = find_layer(layer_name)
    if layer_path is None:
        return False
    if command.startswith('run'):
        if args.startswith('"') and args.endswith('"'):
            handle_run_directive(command, args)
        else:
            handle_run_directive(command, path.join(layer_path, args))
    elif command == 'link':
        link_args = args.split(' ')
        validated_args = validate_link(link_args, layer_path)
        if validated_args is not None:
            handle_link_directive(validated_args[0], validated_args[1],
                                  action=validated_args[2])
    elif command == 'depends':
        print(bcolors.FAIL + "Error: 'depends' directive must come first."
              .format(command) + bcolors.ENDC)
        return False
    else:
        print(bcolors.FAIL + "Error: Directive '{0}' not recognized."
              .format(command) + bcolors.ENDC)
        return False
    return True

def find_layer(layer_name):
    # Set of directories to be ignored
    exclude = {'.git'}
    matches = []
    for root, dirs, files in os.walk(os.getcwd()):
        # Modifies dirs in place to ignore directories in exclude
        dirs[:] = [d for d in dirs if d not in exclude]
        matches += [os.path.join(root, d) for d in dirs
                    if d == layer_name and not d.startswith('+')]
    if len(matches) == 0:
        print(bcolors.FAIL + "Error: layer '{0}' could not be found"
              .format(layer_name) + bcolors.ENDC)
        return None
    elif len(matches) > 1:
        print(bcolors.WARNING + "There appears to be duplicate layers:\n{0}\n"
              .format(matches) + 'Please make all layer names unique and'
              + ' try again.' + bcolors.ENDC)
        return None
    return matches[0]

# [(directive, [lines])]
def parse_caravan(layer_name):
    layer_path = find_layer(layer_name)
    if layer_path is None:
        return None
    layer_caravan_path = path.join(layer_path, 'caravan')
    if not os.path.exists(layer_caravan_path):
        print(bcolors.FAIL + "Error: No caravan file in '{0}' layer."
              .format(layer_name) + bcolors.ENDC)
        return None
    directives = []
    with open(layer_caravan_path) as caravan:
        command = ''
        command_lines =[]
        for line in caravan:
            if line.strip()[-1] == ':':
                if command != '' and len(command_lines) > 0:
                    directives.append((command, command_lines))
                command = line.strip()[:-1]
                command_lines = []
            elif command != '':
                command_lines.append(line.strip())
            else:
                print(bcolors.FAIL + "Error: caravan file for '{0}' layer"
                      .format(layer_name) + ' malformed.' + bcolors.ENDC)
                return None
        if command != '' and len(command_lines) > 0:
            directives.append((command, command_lines))
            command = line.strip()
    return directives

def install_layer(layer_name):
    print(bcolors.OKBLUE
              + "----------- Layer: {0} -----------".format(layer_name)
              + bcolors.ENDC)
    directives = parse_caravan(layer_name)
    if directives is None:
        return False
    if (len(directives) > 0 and directives[0][0] == 'depends'):
        directives = directives[1:]
    for directive in directives:
        for lines in directive[1]:
            no_errors = handle_directive(layer_name, directive[0], lines)
            if (not no_errors):
                return False
    return True
    
def read_caravan_layers():
    layers = []
    with open('caravan.layers') as layers_file:
        layers = [layer.strip() for layer in layers_file.readlines()]
    return layers

def get_deps(layer_name):
    directives = parse_caravan(layer_name)
    if directives is None:
        return None
    if (len(directives) > 0 and directives[0][0] == 'depends'):
        return directives[0][1]
    return []

def build_caravan_layer_graph():
    root_layers = read_caravan_layers()
    dependency_graph = defaultdict(set)
    stack = []
    visited = set()

    stack.extend(root_layers)
    while (len(stack) > 0):
        layer = stack.pop()
        if layer not in dependency_graph:
            dependency_graph[layer] = set()
        dependencies = get_deps(layer)
        if (dependencies is None):
            return None
        for dependeny in dependencies:
            dependency_graph[dependeny].add(layer)
        if (layer not in visited):
            visited.add(layer)
            stack.extend(dependencies)
    return dependency_graph

def topological_sort(graph):
    ordered = []
    visited = set()
    fully_explored = set()
    layers = list(graph.keys())
    while (len(layers) > 0):
        layer = layers.pop()
        is_dag = visit(layer, None, graph, ordered, visited, fully_explored)
        if (not is_dag):
            return None
    return ordered

def visit(layer, parent_layer, graph, ordered, visited, fully_explored):
    if (layer in fully_explored):
        return True
    if (layer in visited):
        print(bcolors.FAIL + "Error: Circular Dependeny between {0} and {1}"
              .format(layer, parent_layer) + bcolors.ENDC)
        return False
    visited.add(layer)
    is_dag = True
    for dependency in graph[layer]:
        is_dag = is_dag and visit(dependency, layer, graph, ordered, visited,
                                  fully_explored)

    fully_explored.add(layer)
    ordered.insert(0, layer)
    return is_dag

def main():
    graph = build_caravan_layer_graph()
    if (graph is None):
        return
    ordered = topological_sort(graph)
    if (ordered is None):
        return None
    # stuff = [parse_caravan(thing) for thing in ordered]
    for layer_name in ordered:
        no_errors = install_layer(layer_name)
        if (not no_errors):
            return False

if __name__ == "__main__":
    main()
