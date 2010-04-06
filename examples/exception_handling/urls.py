from tipfy import Rule

def get_rules():
    rules = [
        Rule('/', endpoint='home', handler='handlers.HomeHandler'),
        Rule('/example-1', endpoint='example-1', handler='handlers.Example1Handler'),
        Rule('/example-2', endpoint='example-2', handler='handlers.Example2Handler'),
        Rule('/example-3', endpoint='example-3', handler='handlers.Example3Handler'),
    ]

    return rules
