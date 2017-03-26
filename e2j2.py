#!/usr/bin/env python
import sys
import os
import re
import json
import jinja2
import click
from colorama import Fore, Style
from base64 import b64decode


def find_j2files(searchlist, j2file_ext):
    return [os.path.join(dirpath, j2file) for searchlist_item in searchlist.split(',')
            for dirpath, dirnames, files in os.walk(searchlist_item)
            for j2file in files if j2file.endswith(j2file_ext)
            ]


def parse_json_string(json_string):
    return json.loads(json_string)


def parse_json_file(json_file):
    with open(json_file) as json_file:
        data = json.load(json_file)
    return data


def parse_base64(value):
    return b64decode(value)


def parse_tag(tag, value):
    # strip tag from value
    value = re.sub(r'^{}'.format(tag), '', value).strip()
    if tag == 'json:':
        return parse_json_string(value)
    elif tag == 'jsonfile:':
        return parse_json_file(value)
    elif tag == 'base64:':
        return parse_base64(value)
    else:
        raise KeyError('tag: {} not implemented')


def j2vars_from_environment():
    tags = ['json:', 'jsonfile:', 'base64:']
    envcontext = {}
    for envvar in os.environ:
        envvalue = os.environ[envvar]
        defined_tag = [tag for tag in tags if envvalue.startswith(tag)]
        envcontext[envvar] = parse_tag(defined_tag[0], envvalue) if defined_tag else envvalue
    return envcontext


def render_template(j2file, j2vars):
    path, filename = os.path.split(j2file)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')).get_template(filename).render(j2vars)


@click.command()
@click.option('--extention', default='.j2', help='Jinja2 file extention')
@click.option('--searchlist', help='Comma separated list of directories to search for jinja2 templates')
@click.option('--noop/--no-noop', default=False, help='Skip writing the rendered template, only render the template')
def e2j2(searchlist, extention, noop):

    if not searchlist and 'E2J2_SEARCHLIST' not in os.environ:
        print('{}Searchlist not specified{}'.format(Fore.RED, Style.RESET_ALL))
        exit(1)

    if not searchlist and 'E2J2_SEARCHLIST' in os.environ:
        searchlist = os.environ['E2J2_SEARCHLIST']

    j2vars = j2vars_from_environment()
    old_directory = ''
    for j2file in find_j2files(searchlist=searchlist, j2file_ext=extention):
        try:
            directory = os.path.dirname(j2file)
            filename = re.sub(r'{}$'.format(extention), '', j2file)

            if directory != old_directory:
                sys.stdout.write('\n{}In: {}{}\n'.format(Fore.GREEN, Fore.WHITE, os.path.dirname(j2file)))

            sys.stdout.write('    {}rendering: {}{:25}{} => '.format(Fore.GREEN, Fore.WHITE,
                                                                  os.path.basename(j2file), Fore.GREEN))
            rendered_file = render_template(j2file=j2file, j2vars=j2vars)
            sys.stdout.write('{}done{:7} => writing: {}{:25}{} => '.format(Fore.LIGHTGREEN_EX, Fore.GREEN, Fore.WHITE,
                                                                           os.path.basename(filename), Fore.GREEN))
            if not noop:
                with open(filename, mode='w') as fh:
                    fh.writelines(rendered_file)
                sys.stdout.write('{}done{}\n'.format(Fore.LIGHTGREEN_EX, Style.RESET_ALL))
            else:
                sys.stdout.write('{}skipped{}\n'.format(Fore.YELLOW, Style.RESET_ALL))
        except Exception as e:
            sys.stdout.write('{}failed{} ({}){}\n'.format(Fore.LIGHTRED_EX, Fore.WHITE, str(e), Style.RESET_ALL))
        finally:
            old_directory = directory
            sys.stdout.flush()


if __name__ == '__main__':
    e2j2()
