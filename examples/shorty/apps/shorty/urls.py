from tipfy import Rule

def get_rules():
    rules = [
        Rule('/', endpoint='shorty/new', handler='apps.shorty.handlers.NewUrlHandler'),
        Rule('/view/<url_name>', endpoint='shorty/view', handler='apps.shorty.handlers.ViewUrlHandler'),
        Rule('/u/<url_name>', endpoint='shorty/link', handler='apps.shorty.handlers.LinkHandler'),
        Rule('/list', endpoint='shorty/list', handler='apps.shorty.handlers.ListHandler'),
        Rule('/list/<cursor>', endpoint='shorty/list', handler='apps.shorty.handlers.ListHandler'),
    ]

    return rules
