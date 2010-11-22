def after_creation(environment):
    environment.filters['ho'] = lambda x: x + ', Ho!'
