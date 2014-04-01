NBX command line tool
====================

## USAGE

```
usage: nbx [-h] [--host HOST] [--port PORT] [action] [target]

positional arguments:
  action
  target
```

## Actions

### list

`nbx`/`nbx list`

Output a list of running notebook kernels. 

```
$ nbx list
Active Kernels:
====================
[0] panel shift.ipynb
[1] Untitled1.ipynb
```

### attach

`nbx attach $1`

Startup an `IPython` terminal console attached to the chosen notebook's kernel.

```
$ nbx attach 0
================================================================================
Attaching to panel shift.ipynb
================================================================================
Python 2.7.2 (default, Feb 23 2012, 15:27:35)
Type "copyright", "credits" or "license" for more information.
...
In [1]:
```

### cd/pwd

`nbx cd $1`/`nbx pwd $1`

`cd` to or `pwd` the notebook kernel's current working directory. The use of cd requires a shell function. A `zsh` example is below.

```
$ nbx cd 0
$ pwd
~/python/apps/notebooks/bundle_test/panel shift.ipynb
```

## SETUP

Wrapping nbx to allow `cd`. This is required because a child process cannot change the `cwd` of the parent.

```
#.zshrc

nbx()
{
  if [[ $1 == 'cd' ]]; then
    cd "`$VIRTUAL_ENV/bin/nbx pwd $2`"
  else
    $VIRTUAL_ENV/bin/nbx $*
  fi
}
```
