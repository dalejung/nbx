import github
from mock import Mock

hub = None
try:
    import GithubCredentials
    login = GithubCredentials.login
    password = GithubCredentials.password
    hub = github.Github(login, password, user_agent="nbx")
except:
   #hub = Mock()
   pass

def require_github(func):
    if hub is None:
        return lambda s: None
    return func
