
import functools
import pathlib
import inspect
import json


# Idea is to be able to cache data from a function to speed up the process

# There are different cases
# Case 1: A function has a long calculation time, cache the input argument and keyword arguments to a hash and store in a dictionary.


def file_cache(to_target=None):
    if callable(to_target):
        user_function, to_target = to_target, _set_cache_target(None)
        wrapper = use_cache(user_function,to_target)
        return functools.update_wrapper(wrapper,user_function)
    else:
        to_target = _set_cache_target(to_target)

    def decorating_function(user_function):
        wrapper = use_cache(user_function,to_target)
        return functools.update_wrapper(wrapper,user_function)
    
    return decorating_function

def _set_cache_target(to_target):
    if to_target is None:
        to_target = pathlib.Path.home().joinpath(".pyfilecache")
    else:
        to_target = pathlib.Path(to_target)

    if to_target.is_dir():
        to_target = to_target.joinpath(".pyfilecache")
    elif to_target.is_file():
        pass
    else:
        if to_target.parent.is_dir():
            to_target.touch()
        else:
            raise NotADirectoryError(to_target.parent.absolute())
    return to_target
    


def use_cache(func,cache_path):  
    @functools.wraps(func)
    def inner(*args,**kwargs):
        cache_dict = dict()
        try:
            with open(cache_path.absolute(),'r') as from_file:
                cache_dict = json.load(from_file)
        except:
            print("Exception")
            result = func(*args,**kwargs)
            cache_dict['args'] = _convert_classes_to_names(args)
            cache_dict['kwargs'] = _convert_classes_to_names(kwargs)
            cache_dict['result'] = result
            with open(cache_path.absolute(),'w') as to_file:
                json.dump(cache_dict,to_file,indent=4)
            print("printed", cache_dict)
        else:
            if all([expected_key in cache_dict.keys() for expected_key in ['args','kwargs','result']]) \
            and _check_args(cache_dict['args'],*args) is True \
            and _check_kwargs(cache_dict['kwargs'],**kwargs) is True:
                pass 
            else:
                result = func(*args,**kwargs)
                cache_dict['args'] = _convert_classes_to_names(args)
                cache_dict['kwargs'] = _convert_classes_to_names(kwargs)
                cache_dict['result'] = result
                with open(cache_path.absolute(),'w') as to_file:
                    json.dump(cache_dict,to_file,indent=4)
        finally:
            return cache_dict['result']
    return inner

def _convert_classes_to_names(args):
    if isinstance(args,(list,tuple)):
        converted_args = list()
        for arg in args:
            if inspect.isclass(arg):
                converted_args.append(f"class: {arg.__module__}.{arg.__name__}")
            else:
                converted_args.append(arg)
        return converted_args
    elif isinstance(args,dict):
        converted_args = dict()
        for key,value in args.items():
            if inspect.isclass(value):
                converted_args[key] = f"class: {value.__module__}.{value.__name__}"
            else:
                converted_args[key] = value
        return converted_args

def _check_args(cached_args,*new_args):
    new_args = _convert_classes_to_names(new_args)
    if new_args is not None \
        and cached_args is not None \
        and len(new_args) == len(cached_args):
        for arg, cached_arg in zip(new_args,cached_args):
            if arg != cached_arg:
                return False
        return True
    else:
        return False

def _check_kwargs(cached_kwargs,**new_kwargs):
    new_kwargs = _convert_classes_to_names(new_kwargs)
    if new_kwargs is not None \
        and cached_kwargs is not None \
        and len(new_kwargs.keys()) == len(cached_kwargs.keys()):
        for (key,value),(cached_key,cached_value) in zip(new_kwargs.items(),cached_kwargs.items()):
            if key != cached_key or value != cached_value:
                return False
        return True
    else:
        return False

