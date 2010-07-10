from mako.lookup import TemplateLookup

from tipfy import Tipfy


def get_mako_env():
    app = Tipfy.app
    dirs = app.get_config('tipfy.ext.mako', 'templates_dir')
    if isinstance(dirs, basestring):
        dirs = [dirs]

    return TemplateLookup(directories=dirs, output_encoding='utf-8',
        encoding_errors='replace')
