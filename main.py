#!/usr/bin/env python3

import argparse
from collections import OrderedDict
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
    print(dest)

    if (not path.exists(src)):
        create = input("Source file '{0}' does not exist in the layer.\n"
                       .format(src) + "Would you like to create it? [Y/n]: ")
        if (create == 'n'):
            return None
        print("Creating '{0}'".format(src))
        os.makedirs(src)

    action = None
    if path.exists(dest):
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
    elif path.islink(dest):
        remove_broken = input("{0} appears to be a broken link.\n".format(dest)
                              + 'Would you like to remove it? [Y/n]: ')
        if remove_broken == 'n':
            return None
        remove(dest)
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

def handle_directive(command, args, layer_path, run, link):
    if command.startswith('run'):
        if run:
            if args.startswith('"') and args.endswith('"'):
                handle_run_directive(command, args)
            else:
                handle_run_directive(command, path.join(layer_path, args))
    elif command == 'link':
        if link:
            link_args = args.split(' ')
            validated_args = validate_link(link_args, layer_path)
            if validated_args is not None:
                handle_link_directive(validated_args[0], validated_args[1],
                                      action=validated_args[2])
    elif command == 'depends':
        if args not in installed_layers:
            dependant_layer_path = find_layer(args)
            parse_caravan(dependant_layer_path, args, run, link, dependant=True)
    else:
        print(bcolors.FAIL + "Directive '{0}' not recognized.".format(command))

# [(directive, [lines])]
def parse_caravan(layer_name, layer_path):
    layer_caravan_path = path.join(layer_path, 'caravan')
    if not os.path.exists(layer_caravan_path):
        print(bcolors.FAIL + "Error: No caravan file in '{0}' layer."
              .format(layer_name))
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
            elif command != '':
                command_lines.append(line.strip())
            else:
                print(bcolors.FAIL + "Error: caravan file for '{0}' layer"
                      .format(layer_name) + ' malformed.')
                return None
        if command != '' and len(command_lines) > 0:
            directives.append((command, command_lines))
            command = line.strip()
    return directives

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
        print("{0} layer not found!".format(layer_name))
        return None
    elif len(matches) > 1:
        print("There appears to be duplicate layers:\n{0}\n".format(matches)
              + "Please make all layer names unique and try again.")
        return None
    return matches[0]

# [(layer_name, layer_path)]
def read_caravan_layers():
    layers = []
    with open('caravan.layers') as layers_file:
        for line in layers_file:
            layer_name = line.strip()
            layer_path = find_layer(layer_name.strip())
            if layer_path is None:
                print(bcolors.FAIL + "Error: layer '{0}' could not be found"
                      .format(layer_name))
                return None
            layers.append((layer_name, layer_path))
    return layers

def build_caravan_layer_graph():
    root_layers = read_caravan_layers()
    if root_layers is None:
        return None

    print(root_layers)

    layers_directives = OrderedDict()
    for (layer_name, layer_path) in root_layers:
        parsed_caravan = parse_caravan(layer_name, layer_path)
        if parse_caravan is None:
            return None
        layers_directives[layer_name] = parsed_caravan

    print(layers_directives)
    for layer_name in layers_directives:
        directives = layers_directives[layer_name]
        if (len(directives) > 0 and directives[0][0] == 'depends'):
            print(directives)

def main():
    parser = argparse.ArgumentParser(description='caravan - system setup and '
                                     + ' configuration made easy')
    parser.add_argument('--run', action='store_true',
                        help='Handle all install directives')
    parser.add_argument('--link', action='store_true',
                        help='Handle all link directives')

    # Show help message if no arguments are passed
    if len(sys.argv[1:])==0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    # read_caravan_layers(args.run, args.link)
    build_caravan_layer_graph()

if __name__ == "__main__":
    main()
