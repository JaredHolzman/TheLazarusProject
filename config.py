#!/usr/bin/env python3
import os
import re

# Directives to match on
# file_extension: (target_path, prepend_to_file, append_to_file)
directives = {
    'symh': ('$HOME', '.', ''),
    'symc': ('$HOME/.config', '', '')
}

def build_directive_dict():
    return {key: [] for key in directives}

def find_directive_matches():
    exclude = {'.git'}
    # Dictionary to add files/dirs to by their respecitive directives
    matches = build_directive_dict()
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude]
        # Here we are matching on any files/directories that end in a directive
        # and adding them to matches. Something to note, this applies to all
        # sub-directories as well, so you can have a directory matching one
        # directive and it's child matching another.
        for key in matches:
            matches[key] += [d for d in dirs if re.fullmatch(".*\.{0}".format(key), d) is not None]
            matches[key] += [f for f in files if re.fullmatch(".*\.{0}".format(key), f) is not None]
    return matches

# Meat and potatoes of the operation, here we are symlinking all our configs
# based on their directive
def symlink_directives(directives_files):
    for direc in directives:
        (path, prepend, append) = directives[direc]
        base_path = os.path.expandvars(path)
        for f in directives_files[direc]:
            file_name = re.split("\.{0}".format(direc),
                                 "{0}{1}{2}".format(prepend,f,append))[0]
            target_path = os.path.join(base_path, file_name)
            print(target_path)


def main():
    matches = find_directive_matches()
    symlink_directives(matches)


if __name__ == "__main__":
    main()
