# Caravan

Caravan makes system setup and configuration easy. By operating on a system of directives, Caravan is generic enough to work out the box for most use cases and easy enough to extend to support more.

## Layers
Caravan is organized around layers. Group all your setup scripts and dotfiles into a single logical directory and you can use directives to link all of your configs wherever they need to go on your system. You can specifiy which layers you'd like installed via the `caravan.layers` file.

## Directives
Directives are what allow you easily manage all of your dotfiles and setup scripts. Each layer has its own `caravan` file which give instructions to caravan on what to do with the files inside it. Here is a simple example
```
run:
  install_1
  install_2
link:
  random_file ~/.random_file
  different_rando_file ~/.config/thing/rando_file
  executable_i_like /usr/bin/do_a_thing
```
`caravan` files are read and executed in order and you are not limited to using each directive only once. For example, if you need to run something, link a file, and the run another file, that is totally fine.
### Run Directive
* Files specified by this directive must be executable and have a command string at the top of the file (e.g. `#!/usr/bin/env bash`)
### Link Directive
* This directive requires two arguments:
** The file in the layer you want to symlink
** The destination on the filesystem where you want to put that link
## Usage
```
git clone https://github.com/JaredHolzman/caravan.git
cd caravan
./main.py
```

```
usage: main.py [-h] [--run] [--dotfiles]

caravan - system setup and configuration made easy

optional arguments:
  -h, --help  show this help message and exit
  --run   Handle all install directives
  --link  Handle all link directives
```

## Next steps
* Add support for a *depends* directive so that layers can be stacked
* Improve output formatting and add colors
* Add a `bin` directive for symlinking to `/usr/bin`
* Glob pattern matching support for EXCLUDE entries
* Add os specific directives (e.g. maybe something like `*.mac.install` would only run when `uname -s == 'darwin'`)

