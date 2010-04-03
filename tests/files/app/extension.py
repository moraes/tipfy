def setup(app):
    app.hooks.add('pre_run_app', pre_run_app)
    app.hooks.add('post_make_app', post_make_app)


def pre_run_app(app):
    pass


def post_make_app(app):
    pass
