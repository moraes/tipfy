from tipfy import Rule

def get_rules():
    rules = [
        Rule('/', endpoint='home', handler='apps.users.handlers.HomeHandler'),
        Rule('/accounts/signup', endpoint='auth/signup', handler='apps.users.handlers.SignupHandler'),
    ]

    return rules
