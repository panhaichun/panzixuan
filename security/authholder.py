import threading

__all__ = ['set', 'get', 'principal']

authentication_local = threading.local()

def set(authentication):
    authentication_local.authentication = authentication

def get():
    return authentication_local.authentication

def principal():
    authentication = get()
    return authentication.get_principal() if authentication else None
    