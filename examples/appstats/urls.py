from tipfy import Rule

def get_rules():
    return [
        Rule('/', endpoint='home', handler='handlers.HomeHandler')
    ]
