from tipfy import Rule

def get_rules():
   rules = [
       Rule('/', endpoint='home', handler='apps.users.handlers.HomeHandler'),
       Rule('/accounts/signup', endpoint='auth/signup', handler='apps.users.handlers.SignupHandler'),
       Rule('/accounts/login', endpoint='auth/login', handler='apps.users.handlers.LoginHandler'),
       Rule('/accounts/logout', endpoint='auth/logout', handler='apps.users.handlers.LogoutHandler'),
   ]

   return rules
