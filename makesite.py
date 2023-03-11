#!/usr/bin/python3

# Copyright (c) 2022 Derek Gustafson
# All right reserved.

# The MIT License (MIT)
#
# Copyright (c) 2018 Sunaina Pai
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""Make static website/blog with Python."""


import os
import shutil
import re
import glob
import sys
import json
import datetime


def fread(filename):
    """Read file and close the file."""
    with open(filename, 'r') as f:
        return f.read()


def fwrite(filename, text):
    """Write content to file and close the file."""
    basedir = os.path.dirname(filename)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    with open(filename, 'w') as f:
        f.write(text)


def log(msg, *args):
    """Log message with specified arguments."""
    sys.stderr.write(msg.format(*args) + '\n')


def truncate(text, words=25):
    """Remove tags and truncate text to the specified number of words."""
    return ' '.join(re.sub('(?s)<.*?>', ' ', text).split()[:words])


def read_headers(text):
    """Parse headers in text and yield (key, value, end-index) tuples."""
    for match in re.finditer(r'\s*<!--\s*(.+?)\s*:\s*(.+?)\s*-->\s*|.+', text):
        if not match.group(1):
            break
        yield match.group(1), match.group(2), match.end()


def rfc_2822_format(date_str):
    """Convert yyyy-mm-dd date string to RFC 2822 format date string."""
    d = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return d.strftime('%a, %d %b %Y %H:%M:%S +0000')


def read_content(filename):
    """Read content and metadata from file into a dictionary."""
    # Read file content.
    text = fread(filename)

    # Read metadata and save it in a dictionary.
    date_slug = os.path.basename(filename).split('.')[0]
    match = re.search(r'^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$', date_slug)
    content = {
        'date': match.group(1) or '1970-01-01',
        'slug': match.group(2),
    }

    # Read headers.
    end = 0
    for key, val, end in read_headers(text):
        content[key] = val

    # Separate content from headers.
    text = text[end:]

    # Check that if an image is included for the social media cards, it includes all meta data.
    socialImg = {k:content[k] for k in ('socialImage','socialImageAlt') if k in content}
    if len(socialImg) != 0 and len(socialImg) != 2:
        raise RuntimeError(filename + ": An entry in content must contain all or none of 'socialImage' and 'socialImageAlt'.")

    # Convert Markdown content to HTML.
    if filename.endswith(('.md', '.mkd', '.mkdn', '.mdown', '.markdown')):
        try:
            import commonmark
            text = commonmark.commonmark(text)
        except ImportError as e:
            log('WARNING: Cannot render Markdown in {}: {}', filename, str(e))

    # Convert projectCss into an appropriate URL.
    if 'projectCss' in content:
        content['projectCssUrl'] = '<link rel="stylesheet" href="/assets/{}">'.format(content['projectCss'])

    # Update the dictionary with content and RFC 2822 date.
    content.update({
        'content': text,
        'rfc_2822_date': rfc_2822_format(content['date'])
    })

    return content


def render(template, filename, **params):
    """Replace placeholders in template with values from params."""
    def replace_fn_call(match):
        f = params.get(match.group(1))
        if f is None:
            raise RuntimeError(f'The variable {match.group(1)} is unset for rendering {filename}.')
        return f(filename, match.group(2))

    def replace(match):
        ret = params.get(match.group(1))
        if ret is None:
            raise RuntimeError(f'The variable {match.group(1)} is unset for rendering {filename}.')
        return str(ret)

    template = re.sub(r'{{!\s*([^}\s]+)\s*([^}\s]+)\s*}}', replace_fn_call, template)
    return re.sub(r'{{\s*([^}\s]+)\s*}}', replace, template)


def make_pages(src, dst, layout, **params):
    """Generate pages from page content."""
    items = []

    for src_path in glob.glob(src):
        content = read_content(src_path)

        page_params = dict(params, **content)

        # detect type of socialImage.
        img = page_params['socialImage']
        extension = img[img.rfind('.') + 1:]
        if extension in ('png', 'avif'):
            page_params['socialImageType'] = 'image/' + extension
        elif extension in ('jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp'):
            page_params['socialImageType'] = 'image/png'
        elif extension == 'svg':
            page_params['socialImageType'] = 'image/svg+xml'

        # Populate placeholders in content if content-rendering is enabled.
        if page_params.get('render') == 'yes':
            rendered_content = render(page_params['content'], src_path, **page_params)
            page_params['content'] = rendered_content
            content['content'] = rendered_content

        items.append(content)

        dst_path = render(dst, src_path, **page_params)
        output = render(layout, src_path, **page_params)

        log('Rendering {} => {} ...', src_path, dst_path)
        fwrite(dst_path, output)

    return sorted(items, key=lambda x: x['date'], reverse=True)


# def make_list(posts, dst, list_layout, item_layout, **params):
#     """Generate list page for a blog."""
#     items = []
#     for post in posts:
#         item_params = dict(params, **post)
#         item_params['summary'] = truncate(post['content'])
#         item = render(item_layout, **item_params)
#         items.append(item)
# 
#     params['content'] = ''.join(items)
#     dst_path = render(dst, **params)
#     output = render(list_layout, **params)
# 
#     log('Rendering list => {} ...', dst_path)
#     fwrite(dst_path, output)


def navbar_class(src, link):
    """
    Returns the appropriate classes for the navbar based on the current file
    name and the destination of the link.
    """
    if os.path.basename(src) == link:
        return 'navbar-item active'
    return 'navbar-item'


def main(site_dir='docs'):
    # Create a new site directory from scratch.
    if os.path.isdir(site_dir):
        shutil.rmtree(site_dir)
    shutil.copytree('static', site_dir)

    # Default parameters.
    params = {
        'base_path': '',
        'subtitle': 'The Bogfolk Cafè',
        'site_url': 'https://bogfolk.com',
        'socialImage': 'assets/missy_cup_logo.jpg',
        'socialImageAlt': 'Missy in a cup',
        'current_year': datetime.datetime.now().year,
        'navbar_class': navbar_class,
        'projectCssUrl': ''
    }

    # If params.json exists, load it.
    if os.path.isfile('params.json'):
        params.update(json.loads(fread('params.json')))

    # Load layouts.
    page_layout = fread('layout/page.html')
    '''
    # This code is needed if we decide to add a blog.
    post_layout = fread('layout/post.html')
    list_layout = fread('layout/list.html')
    item_layout = fread('layout/item.html')
    feed_xml = fread('layout/feed.xml')
    item_xml = fread('layout/item.xml')
    '''

    '''
    # This code is needed if we decide to add a blog.
    # Combine layouts to form final layouts.
    post_layout = render(page_layout, content=post_layout)
    list_layout = render(page_layout, content=list_layout)
    '''

    # Create site pages.
    # make_pages('content/_index.html', site_dir + '/index.html',
    #            page_layout, **params)
    make_pages('content/*.html', site_dir + '/{{ slug }}.html',
               page_layout, **params)

    '''
    # This code is needed if we decide to add a blog.
    # Create blogs.
    blog_posts = make_pages('content/blog/*.md',
                            site_dir + '/blog/{{ slug }}/index.html',
                            post_layout, blog='blog', **params)
    make_list(blog_posts, site_dir + '/blog/index.html',
              list_layout, item_layout, blog='blog', title='Blog', **params)
    make_list(blog_posts, site_dir + '/blog/rss.xml',
              feed_xml, item_xml, blog='blog', title='Blog', **params)
    '''




if __name__ == '__main__':
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
