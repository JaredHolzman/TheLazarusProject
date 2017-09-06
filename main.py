#!/usr/bin/env python3

import argparse
import os
from os import path
import re
import shutil
import sys
import uuid

# Hacky way to import config file
exec(open('caravan.config').read())

CWD = os.getcwd()
skip_all, remove_all, backup_all = False, False, False

def dict_from_keys(keys):
    return {key: [] for key in keys}

def find_pattern_matches(patterns, exclude, layer):
    # Dictionary to add files/dirs to by their respecitive directives
    matches = dict_from_keys(patterns)
    for root, dirs, files in os.walk(layer):
        dirs[:] = [d for d in dirs if d not in exclude]
        # Here we are matching on any files/directories that end in a directive
        # and adding them to matches. Something to note, this applies to all
        # sub-directories as well, so you can have a directory matching one
        # directive and it's child matching another.
        for key in matches:
            # Directories
            matches[key] += [os.path.join(root, d) for d in dirs
                             if re.fullmatch(".*\.{0}".format(key), d)
                             is not None]
            # Files
            matches[key] += [os.path.join(root, f) for f in files
                             if re.fullmatch(".*\.{0}".format(key), f)
                             is not None]
    return matches

def remove (file_path):
    print(file_path)
    if os.path.islink(file_path):
        print("Removing link {0}".format(file_path))
        os.remove(file_path)
    elif os.path.isdir(file_path):
        print("Removing directory {0}".format(file_path))
        shutil.rmtree(file_path)
    elif os.path.isfile(file_path):
        print("Removing file {0}".format(file_path))
        os.remove(file_path)
    else:
        print("File {0} doesn't exist!".format(file_path))

def backup (file_path):
    file_name = os.path.split(file_path)[1]
    backup_base_path = os.path.join(CWD, 'backups')
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
def handle_link_directive(src, dest, layer, action=None):
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

def validate_link(link_args, layer):
    if not len(link_args) == 2:
        print('The link directive takes two arguments,'
              + ' a source and destination.')
        return None
    link_args[0] = path.join(layer, link_args[0])
    [src, dest] = [path.abspath(path.expandvars(path.expanduser(link)))
                      for link in link_args]
    if (not path.exists(src)):
        create = input("Config file '{0}' does not exist.\n".format(src)
                       + "Would you like to create it? [Y/n]: ")
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
    return (src, dest, action)

def handle_install_directive(install_file_path):
    if not os.access(install_file_path, os.X_OK):
        print(bcolors.FAIL + "\"{0}\": Install file not executable!"
              .format(install_file_path) + bcolors.ENDC)
        return False
    command_string = "sh -c {0}".format(install_file_path)
    print("Running {0}:".format(command_string))
    print(bcolors.HEADER + ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
          + bcolors.ENDC)
    os.system(command_string)
    print(bcolors.HEADER + "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
          + bcolors.ENDC)

def handle_directive(command, args, layer):
    if command == 'run':
        handle_install_directive(path.abspath(path.join(layer, args)))
    elif command == 'link':
        link_args = args.split(' ')
        validated_args = validate_link(link_args, layer)
        if validated_args is not None:
            handle_link_directive(validated_args[0], validated_args[1],
                                  layer, validated_args[2])
    else:
        print("Unknown command: {0}".format(command))

def parse_caravan(layer):
    if not os.path.exists(os.path.join(layer, 'caravan')):
        print("No caravan file in {0} layer, skipping.".format(layer))
        return
    with open("{0}/caravan".format(layer)) as caravan:
        command = ''
        for line in caravan:
            if line.strip()[-1] == ':':
                command = line.strip()
            elif command != '':
                handle_directive(command[:-1], line.strip(), layer)
            else:
                print('Error')
                break

def read_caravan_layers():
    with open('caravan.layers') as layers_file:
        for layer in layers_file:
            print(bcolors.OKBLUE
                  + "----------- Layer: {0} -----------".format(layer.strip())
                  + bcolors.ENDC)
            parse_caravan(layer.strip())

def main():
    parser = argparse.ArgumentParser(description='caravan - system setup and '
                                     + ' configuration made easy')
    parser.add_argument('--install', action='store_true',
                        help='Handle all install directives')
    parser.add_argument('--link', action='store_true',
                        help='Handle all link directives')

    # Show help message if no arguments are passed
    if len(sys.argv[1:])==0:
        parser.print_help()
        # parser.print_usage() # for just the usage line
        parser.exit()

    args = parser.parse_args()

    # layers = readLayers()
    # if (args.install):
    #     installs(layers)
    # if (args.link):
    #     dotfiles(layers)

    read_caravan_layers()


if __name__ == "__main__":
    main()
