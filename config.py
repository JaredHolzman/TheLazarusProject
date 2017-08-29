#!/usr/bin/env python3
import os
import re

directives = {
    'symh': '$HOME',
    'symc': '$HOME/.config'
}

def build_directive_dict():
    return {key: [] for key in directives}

def walk_layers():
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
        
    print(matches)

def main():
    walk_layers()


if __name__ == "__main__":
    main()
