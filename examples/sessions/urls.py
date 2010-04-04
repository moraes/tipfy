from tipfy import Rule

def get_rules():
    rules = [
        Rule('/', endpoint='home', handler='handlers.BasicSessionHandler'),
        Rule('/cart', endpoint='sessions/cart', handler='handlers.ShoppingCartHandler'),
        Rule('/delete-session', endpoint='sessions/delete', handler='handlers.DeleteSessionHandler'),
    ]

    return rules
