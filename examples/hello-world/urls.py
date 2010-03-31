from tipfy import Rule

def get_rules():
    rules = [
        Rule('/', endpoint='hello/world', handler='handlers.HelloWorldHandler'),
        Rule('/hello-jinja', endpoint='hello/jinja', handler='handlers.HelloJinjaHandler'),
        Rule('/hello-json', endpoint='hello/json', handler='handlers.HelloJsonHandler'),
        Rule('/hello-ajax', endpoint='hello/ajax', handler='handlers.HelloAjaxHandler'),
    ]

    return rules
