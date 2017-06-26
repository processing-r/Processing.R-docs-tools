import logging
import os
import jinja2
import click
import tempfile
from subprocess import call
import string
import time
import shutil
import yaml
import datetime

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

img_dir = 'img'
property_dir = '.property.yml'

class Generator(object):
    def __init__(self, root, env, jar):
        self.root_dir = root
        self.env = env
        self.jar_path = jar
        self.output_img_dir = os.path.join(output_dir, img_dir)
        if not os.path.exists(self.output_img_dir):
            os.makedirs(self.output_img_dir)
        self.output_html_dir = output_dir
        self.reference_dir = self.root_dir + '/examples/reference'
        self.reference_items = []

    def generate(self):
        self.parse_reference()
        self.render_reference_items()
        self.render_reference_index()

    def parse_reference(self):
        for filename in os.listdir(self.reference_dir):
            item = ReferenceItem(
                self.reference_dir, filename, self.jar_path, self.output_img_dir)
            self.reference_items.append(item)

    def render_reference_items(self):
        for item in self.reference_items:
            reference_template = self.env.get_template('reference_item_template.jinja')
            with open(os.path.join(output_dir, ('%s.html' % item.name)), 'w+') as f:
                f.write(reference_template.render(item=item, today=datetime.datetime.now().ctime()))

    def render_reference_index(self):
        categories = dict()
        for item in self.reference_items:
            path = (item.category, item.subcategory)
            # print(item.category, item.category)
            if item.category is '':
                # print(item.category)
                path = (item.category, '')
            if path == ('', ''): continue
            # Fields and Methods aren't included in the index
            if path[1] in ('Method', 'Field'): continue
            if path not in categories:
                categories[path] = list()
            categories[path].append(item)
        category_order = [
            ('Structure', ''),
            ('Environment', ''),
            ('Data', 'Conversion'),
            ('Control', 'Relational Operators'),
            ('Control', 'Iteration'),
            ('Control', 'Conditionals'),
            ('Control', 'Logical Operators'),
            ('Shape', ''),
            ('Shape', '2D Primitives'),
            ('Shape', 'Curves'),
            ('Shape', '3D Primitives'),
            ('Shape', 'Attributes'),
            ('Shape', 'Vertex'),
            ('Shape', 'Loading & Displaying'),
            ('Input', 'Mouse'),
            ('Input', 'Keyboard'),
            ('Input', 'Files'),
            ('Input', 'Time & Date'),
            ('Output', 'Text Area'),
            ('Output', 'Image'),
            ('Output', 'Files'),
            ('Transform', ''),
            ('Lights, Camera', 'Lights'),
            ('Lights, Camera', 'Camera'),
            ('Lights, Camera', 'Coordinates'),
            ('Lights, Camera', 'Material Properties'),
            ('Color', 'Setting'),
            ('Color', 'Creating & Reading'),
            ('Image', ''),
            ('Image', 'Loading & Displaying'),
            ('Image', 'Textures'),
            ('Image', 'Pixels'),
            ('Rendering', ''),
            ('Rendering', 'Shaders'),
            ('Typography', ''),
            ('Typography', 'Loading & Displaying'),
            ('Typography', 'Attributes'),
            ('Typography', 'Metrics'),
            ('Math', ''),
            ('Math', 'Operators'),
            ('Math', 'Bitwise Operators'),
            ('Math', 'Calculation'),
            ('Math', 'Trigonometry'),
            ('Math', 'Random'),
            ('Constants', ''),
        ]
        # assert set(category_order) == set(categories.keys()), \
        #         "category order and category keys are different. " + \
        #         str(set(category_order) - set(categories.keys())) + " *** " + \
        #         str(set(categories.keys()) - set(category_order))
        elements = list()
        current_cat = None
        current_subcat = None
        for path in category_order:
            cat, subcat = path
            if cat != current_cat:
                if current_cat is not None:
                    elements.append({'type': 'end-category', 'content': None})
                elements.append({'type': 'start-category', 'content': cat})
                current_cat = cat
            if subcat != current_subcat:
                if current_subcat is not None:
                    elements.append({'type': 'end-subcategory', 'content': None})
                elements.append({'type': 'start-subcategory', 'content': subcat})
                current_subcat = subcat
            elements.append({'type': 'start-list', 'content': None})
            # For demo.
            if path not in categories:
                continue
            for item in sorted(categories[path], key=lambda x: x.name):
                elements.append({'type': 'link', 'content': item})
            elements.append({'type': 'end-list', 'content': None})
        elements.append({'type': 'end-subcategory', 'content': None})
        elements.append({'type': 'end-category', 'content': None})

        index_template = self.env.get_template('reference_index_template.jinja')
        with open(os.path.join(output_dir, 'index.html'), 'w+') as f:
            f.write(index_template.render(elements=elements))

class ReferenceItem(object):
    def __init__(self, root, name, jar, output_img_dir):
        self.name = name
        self.path = '%s.html' % name
        self.jar_path = jar
        self.output_img_dir = output_img_dir
        self.item_dir = os.path.join(root, name)
        self.examples = []

        self.parse_reference_item()
        self.parse_property()
    
    def parse_property(self):
        file_name = os.path.join(self.item_dir, property_dir)
        with open(file_name) as f:
            raw_yaml_doc = f.read()
            yaml_obj = yaml.load(raw_yaml_doc)
            self.category = yaml_obj['category']
            if 'subcategory' in yaml_obj:
                if yaml_obj['subcategory'] is None:
                    self.subcategory = ''
                else:
                    self.subcategory = yaml_obj['subcategory']
            if 'description' in yaml_obj:
                self.description = yaml_obj['description']
            if 'syntax' in yaml_obj:
                self.syntax = yaml_obj['syntax']
            if 'parameters' in yaml_obj:
                self.parameters = []
                for parameter in yaml_obj['parameters']:
                    self.parameters.append({
                        'label': parameter['label'],
                        'description': parameter['description']
                    })
            if 'related' in yaml_obj:
                self.related = []
                for related_function in yaml_obj['related']:
                    self.related.append({
                        'path': './%s.html' % related_function,
                        'name': related_function
                    })

    def parse_reference_item(self):
        for filename in os.listdir(self.item_dir):
            sketchFile = '%s/%s/%s.rpde' % (self.item_dir, filename, filename)
            if os.path.isfile(os.path.join(self.item_dir, filename)):
                continue
            with open(sketchFile, 'r') as f:
                code = f.read()
                img_path = os.path.join(self.output_img_dir, ('%s.png' % filename))
                self.generate_image(code, img_path)
                self.examples.append({
                    'code': code,
                    'path': sketchFile,
                    'image': os.path.join(img_dir, ('%s.png' % filename))
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
        temp_file.seek(0)
        retcode = call(['java', '-jar', self.jar_path, temp_file.name])
        if retcode is not 0:
            logging.error('retcode of runner.jar: %d', retcode)

@click.command()
@click.option('--core', default='', help='The location of Processing.R source code.')
@click.option('--jar', default='', help='The location of runner.jar')
@click.option('--docs-dir', default='', help='The location of Processing.R docs')
def generate(core, jar, docs_dir):
    '''Generate Processing.R web reference.'''
    # BUG: Fail to exit.
    if core is None or jar is None:
        click.echo('There is no core or jar.')
        exit(1)
    click.echo('The location of Processing.R source code:%s' % core)
    click.echo('The location of Processing.R runner.jar: %s' % jar)
    click.echo('The location of Processing.R docs:       %s' % docs_dir)

    template_dir_short = 'templates'
    output_dir_short = 'docs'
    content_dir_short = 'content'

    global template_dir
    global output_dir
    global content_dir

    template_dir = os.path.join(docs_dir, template_dir_short)
    output_dir = os.path.join(docs_dir, output_dir_short)
    content_dir = os.path.join(docs_dir, content_dir_short)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), trim_blocks='true')

    generator = Generator(core, env, jar)
    generator.generate()

if __name__ == '__main__':
    generate()
