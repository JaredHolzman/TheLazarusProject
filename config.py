#!/usr/bin/env python3
import os
import shutil
import re
import uuid

# Directives to match on
# file_extension: (target_path, hidden)
directives = {
    'symh': ('$HOME/test', True),
    'symc': ('$HOME/test/.config', False)
}

CWD = os.getcwd()

def build_directive_dict():
    return {key: [] for key in directives}

def find_directive_matches():
    exclude = {'.git'}
    # Dictionary to add files/dirs to by their respecitive directives
    matches = build_directive_dict()
    for root, dirs, files in os.walk(CWD):
        dirs[:] = [d for d in dirs if d not in exclude]
        # Here we are matching on any files/directories that end in a directive
        # and adding them to matches. Something to note, this applies to all
        # sub-directories as well, so you can have a directory matching one
        # directive and it's child matching another.
        for key in matches:
            matches[key] += [os.path.join(root, d) for d in dirs if re.fullmatch(".*\.{0}".format(key), d) is not None]
            matches[key] += [os.path.join(root, f) for f in files if re.fullmatch(".*\.{0}".format(key), f) is not None]
    return matches

def remove (file_path):
    if os.file_path.isdir(file_path):
        print("Removing directory {0}".format(file_path))
        os.rmdir(file_path)
    elif os.file_path.isfile(file_path):
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

def perform_action(action, target_path):
    if action == 'S':
        skip_all = True
        print('Skipping {0}'.format(target_path))
        return False
    elif action == 's':
        print('Skipping {0}'.format(target_path))
        return False
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
    return True 

# Meat and potatoes of the operation, here we are symlinking all our configs
# based on their directive
def symlink_directives(directives_files):
    skip_all, remove_all, backup_all = False, False, False
    for direc in directives:
        (path, hidden) = directives[direc]
        base_path = os.path.expandvars(path)
        for f in directives_files[direc]:
            file_name = os.path.split(f)[1]
            target_file_name = re.split(
                "\.{0}".format(direc),
                "{0}{1}".format('.' if hidden else '', file_name)
            )[0]
            target_path = os.path.join(base_path, target_file_name)
            if (os.path.exists(target_path)):
                # Checks inode to see if same file
                # if (os.path.samefile(f, target_path)):
                #     print("Symlink {0} -> {1} already exists. Skipping"
                #           .format(target_path, f))
                #     continue
                if skip_all: action = 's'
                elif remove_all: action = 'o'
                elif backup_all: action = 'b'
                else:
                    action = input(
                        "Target {0} already exists, what do you want to do?\n"
                        .format(target_path)
                        + "[s]kip, [S]kip all, [r]emove, [R]emove all, "
                        + "[b]ackup, [B]ackup all: "
                    )

                if (not perform_action(action, target_path)):
                    continue

            # It's symlinking time!
            print("Symlinking {0} -> {1}".format(target_path, f))
            os.symlink(f, target_path)

def validate_directives():
    for direc in directives:
        (direc_path, hidden) = directives[direc]
        path = os.path.expandvars(direc_path)
        if (len(directives[direc]) != 2):
            print("Uh-oh, your directives appear to be malformed.")
            return False

        if (not os.path.exists(path)):
            create = input("{0} does not exist.\n".format(path)
                  + " Would you like to create it? [Y/n]: ")
            if (create == 'n'):
                return False
            print("Creating {0}".format(path))
            os.makedirs(path)
        elif (os.path.isfile(path)):
            print("{0} is a file, but directives must specify a directory"
                  .format(path))
            return False
    return True


def main():
    if (not validate_directives()):
        return
    matches = find_directive_matches()
    symlink_directives(matches)


if __name__ == "__main__":
    main()
