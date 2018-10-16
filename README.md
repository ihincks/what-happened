# What Happened

Merges logs of multiple git repositories and sorts by date to figure out what you did in the past while.

## Usage

Write a file `config.yaml` containing at least:
```yaml
repos:
  - /path/to/first/repo
  - /path/to/second/repo
  - /and/so/on
```

Make the `whathappened` file executable (or alternatively run with `python whathappened`) and use
```bash
./whathappened
```

which will print commit logs of all specified repos, ordered by commit date:

```
2018-10-15  Ian Hincks  what-happened  Initial commit
2018-10-15  Ian Hincks  what-happened  initial commit
                                        * script works but is pretty ugly in places
2018-10-15  Ian Hincks  what-happened  simplified gitignore
2018-10-16  Ian Hincks  what-happened  design improvements
                                        * - added argparse - repos are now specified in a config
                                          yaml - get rid of regex with better git log call
2018-10-16  Ian Hincks  what-happened  further clean-up of code

                                        * including auto-width and body width specifiers
2018-10-16  Ian Hincks  what-happened  improved body formatting
2018-10-16  Ian Hincks  what-happened  improved subject formatting
2018-10-16  Ian Hincks  what-happened  added shebang
2018-10-16  Ian Hincks  what-happened  renamed file
```

If `config.yaml` is located in a different folder than `whathappened`, specify its location with 
```bash
./whathappened other/location/config.yaml
```

## Command Line Arguments

Use `whathappened --help` to see command line arguments.
For instance, we can control line wrapping with

```
./whathappened --width 60
```

or reverse the order with 

```
./whathappened --reverse
```

If we specify a user, then only commits from that author are shown, with the author column not printed:

```
./whathappened --user Ian
```

## YAML config file arguments

All command line arguments are valid yaml keywords in the config file. 
Command line arguments override values set in the yaml file.

```yaml
repos:
  - /path/to/first/repo
  - /path/to/second/repo
  - /and/so/on
reverse: True
user: Ian
width: 88
```
