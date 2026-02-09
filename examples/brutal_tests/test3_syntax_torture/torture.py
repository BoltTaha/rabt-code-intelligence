# torture.py - valid but weird Python

def my_func(a, b=lambda x: x + 1):
    return [x for x in range(10) if x > 5]

class Nested:
    class Deeper:
        def method(self):
            pass

def decorator(a=1):
    def wrap(f):
        return f
    return wrap

@decorator(a=1)
def decorated():
    pass
