#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import sys
import uuid

# Hacky way to import config file
exec(open('caravan.config').read())

CWD = os.getcwd()

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
def handle_dotfiles(directives_files):
    skip_all, remove_all, backup_all = False, False, False
    for direc in LINK_DIRECTIVES:
        (path, hidden) = LINK_DIRECTIVES[direc]
        base_path = os.path.expandvars(path)
        for f in directives_files[direc]:
            file_name = os.path.split(f)[1]
            target_file_name = re.split(
                "\.{0}".format(direc),
                "{0}{1}".format('.' if hidden else '', file_name)
            )[0]
            target_path = os.path.join(base_path, target_file_name)
            if (os.path.exists(target_path) or os.path.islink(target_path)):
                # Checks inode to see if same file
                if (os.path.samefile(f, target_path)):
                    print("Symlink {0} -> {1} already exists. Skipping"
                          .format(target_path, f))
                    continue
                if skip_all:
                    action = 's'
                elif remove_all:
                    action = 'r'
                elif backup_all:
                    action = 'b'
                else:
                    action = input(
                        "Target {0} already exists, what do you want to do?\n"
                        .format(target_path)
                        + "[s]kip, [S]kip all, [r]emove, [R]emove all, "
                        + "[b]ackup, [B]ackup all: "
                    )

                if action == 'S':
                    skip_all = True
                    print('Skipping {0}'.format(target_path))
                    continue
                elif action == 's':
                    print('Skipping {0}'.format(target_path))
                    continue
                elif action == 'R':
                    remove_all = True
                    remove(target_path)
                elif action == 'r':
                    remove(target_path)
                elif action == 'B':
                    backup_all = True
                    backup(target_path)
                else:
                    backup(target_path)

            # It's symlinking time!
            print("Symlinking {0} -> {1}".format(target_path, f))
            try:
                os.symlink(f, target_path)
            except PermissionError:
                os.system("sudo ln -s {0} {1}".format(f, target_path))

def validate_link_directives():
    for direc in LINK_DIRECTIVES:
        (direc_path, hidden) = LINK_DIRECTIVES[direc]
        path = os.path.expandvars(direc_path)
        if (len(LINK_DIRECTIVES[direc]) != 2):
            print("Uh-oh, your directives appear to be malformed.")
            return False

        if (not os.path.exists(path)):
            create = input("{0} does not exist.\n".format(path)
                  + "Would you like to create it? [Y/n]: ")
            if (create == 'n'):
                return False
            print("Creating {0}".format(path))
            os.makedirs(path)
        elif (os.path.isfile(path)):
            print("{0} is a file, but directives must specify a directory"
                  .format(path))
            return False
    return True

def handle_installs(install_files):
    for direc in INSTALL_DIRECTIVES:
        (command) = INSTALL_DIRECTIVES[direc]
        for install_file_path in install_files[direc]:
            if not os.access(install_file_path, os.X_OK):
                print(bcolors.FAIL + "\"{0}\": Install file not executable!"
                      .format(install_file_path) + bcolors.ENDC)
                return False
            command_string = ' '.join(command + (install_file_path,))
            print("Running {0}:".format(command_string))
            print(bcolors.HEADER + ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                  + bcolors.ENDC)
            os.system(command_string)
            print(bcolors.HEADER + "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                  + bcolors.ENDC)

def dotfiles(layers):
    if (not validate_link_directives()):
        return
    for layer in layers:

        matches = find_pattern_matches(LINK_DIRECTIVES.keys(), EXCLUDE, layer)
        handle_dotfiles(matches)

def installs(layers):
    for layer in layers:
        print(bcolors.OKBLUE
              + "----------- Layer: {0} -----------".format(layer)
              + bcolors.ENDC)
        installs = find_pattern_matches(
            INSTALL_DIRECTIVES.keys(), EXCLUDE,layer)
        handle_installs(installs)

def readLayers():
    layers = []
    with open('caravan.layers') as layers_file:
        for layer in layers_file:
            layers.append(layer.replace('\n', ''))
    return layers


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

    layers = readLayers()
    if (args.install):
        installs(layers)
    if (args.link):
        dotfiles(layers)



if __name__ == "__main__":
    main()
