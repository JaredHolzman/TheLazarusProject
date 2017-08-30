# Caravan

Caravan make system setup and configuration easy. By operating on a system of directives, Caravan is generic enough to work out the box for most use cases and easy to extend to support more.

## Layout
Caravan is organized around layers. Group all your setup scripts and dotfiles into a single logical directory and you can use directives to link all of your configs wherever they need to go on your system.

## Directives
Directives are what allows you easily manage all of your dotfiles and setup scripts. Directives can easily be added or changed by modifying the `LINK_DIRECTIVES` and `INSTALL_DIRECTIVES` in `config.py`. Any link directives are stripped at the time of symlinking.
Here are the ones that exist by default:
### Link Directives
* **.symh**: Any file ending in `.symh` will be symlinked to your `$HOME` directory as a hidden file.
* **.symc**: Any file ending in `.symc` will be symlinked to your `$HOME/.config` directory. 
### Install Directives
* **.install**: Any file ending in `.install` will be run using `sh -c`. Files with this directive must be executable and have a command string at the top of the file (e.g. `#!/usr/bin/env bash`)
