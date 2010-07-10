from jinja2 import FileSystemLoader, Environment

from tipfy import Tipfy


def get_jinja2_env():
    app = Tipfy.app
    cfg = app.get_config('tipfy.ext.jinja2')

    loader = FileSystemLoader(cfg.get( 'templates_dir'))

    return Environment(loader=loader)
