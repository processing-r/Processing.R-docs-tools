import logging
import os
import jinja2
import click
import tempfile
from subprocess import call
import string
import time

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

# TODO: Refactor
template_dir = '/home/ist/code/Processing.R-docs/templates'
output_dir = '/home/ist/code/Processing.R-docs/generated'

class Generator(object):
    def __init__(self, root, env, jar):
        self.root_dir = root
        self.env = env
        self.jar_path = jar
        self.output_img_dir = os.path.join(output_dir, 'img')
        if not os.path.exists(self.output_img_dir):
            os.makedirs(self.output_img_dir)
        self.output_html_dir = output_dir
        self.reference_dir = self.root_dir + '/examples/reference'
        self.reference_items = []

    def parse_reference(self):
        for filename in os.listdir(self.reference_dir):
            item = ReferenceItem(
                self.reference_dir, filename, self.jar_path, self.output_img_dir)
            self.reference_items.append(item)

    def render_reference_items(self):
        for item in self.reference_items:
            reference_template = self.env.get_template('reference_item_template.jinja')
            with open(os.path.join(output_dir, ('%s.html' % item.name)), 'w+') as f:
                f.write(reference_template.render(item=item))

class ReferenceItem(object):
    def __init__(self, root, name, jar, output_img_dir):
        self.name = name
        self.jar_path = jar
        self.output_img_dir = output_img_dir
        self.item_dir = os.path.join(root, name)
        self.examples = []
        for filename in os.listdir(self.item_dir):
            sketchFile = '%s/%s/%s.rpde' % (self.item_dir, filename, filename)
            with open(sketchFile, 'r') as f:
                code = f.read()
                img_path = os.path.join(self.output_img_dir, ('%s.png' % filename))
                self.generate_image(code, img_path)
                self.examples.append({
                    'code': code,
                    'path': sketchFile,
                    'image': img_path
                })

    def generate_image(self, code, to):
        footer = ''
        actual_code = ''

        # Insert into draw function if draw exists.
        if 'draw <- function' in code:
            pos = code.index('draw <- function')
            for i in range(pos, len(code) - 1):
                if code[i] is '\n' and code[i + 1] is '}':
                    footer = '\n    processing$saveFrame("%s")\n    processing$exit()\n' % to
                    actual_code = code[:i] + footer + code[i+1:]
        else:
            footer = 'processing$saveFrame("%s")\nprocessing$exit()\n' % to
            actual_code = '%s\n%s' % (code, footer)

        # I don't know why temp file could not be written directly. It must be open() and written.
        temp_file = tempfile.NamedTemporaryFile(prefix='Processing.R.', suffix='.tmp.rpde')
        temp_file.write(bytes(actual_code, 'utf-8'))
        print(temp_file.name)
        temp_file.seek(0)
        print(temp_file.read())
        retcode = call(['java', '-jar', self.jar_path, temp_file.name])
        if retcode is not 0:
            logging.error('retcode of runner.jar: %d', retcode)

@click.command()
@click.option('--core', default='', help='The location of Processing.R source code.')
@click.option('--jar', default='', help='The location of runner.jar')
def generate(core, jar):
    '''Generate Processing.R web reference.'''
    if core is '' or jar is '':
        click.echo('There is no core or jar.')
        exit(1)
    click.echo('The location of Processing.R source code:%s' % core)
    click.echo('The location of Processing.R runner.jar: %s' % jar)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), trim_blocks='true')

    generator = Generator(core, env, jar)
    generator.parse_reference()
    generator.render_reference_items()

if __name__ == '__main__':
    generate()
