def dump_methods(obj):
    method_list = [func for func in dir(obj) if callable(getattr(obj, func))]
    print(method_list)