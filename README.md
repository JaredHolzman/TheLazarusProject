# Caravan

Caravan makes system setup and configuration easy. By operating on a system of directives, Caravan is generic enough to work out the box for most use cases and easy enough to extend to support more.

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

## Configuration
Most of your configuration should be done in the `caravan.config` file. 
* To add or edit any directive, modify `LINK_DIRECTIVES` and `INSTALL_DIRECTIVES`. 
* To specifiy directories to be ignored, modify `EXCLUDE`

## Usage
```
git clone https://github.com/JaredHolzman/caravan.git
cd caravan
./main.py
```

```
usage: main.py [-h] [--install] [--dotfiles]

caravan - system setup and configuration made easy

optional arguments:
  -h, --help  show this help message and exit
  --install   Handle all install directives
  --link  Handle all link directives
```
Install directives will always be handles before any link directives.

## Next steps
* Improve output formatting and add colors
* Add a `bin` directive for symlinking to `/usr/bin`
* Glob pattern matching support for EXCLUDE entries
* Add os specific directives (e.g. maybe something like 'mac.install' would only run when `uname -s == 'darwin'`)

