import inspect


def get_concrete_subclasses(cls):
	return {
		subclass.get_agent_name(): subclass
		for subclass in _get_all_subclasses(cls)
		if not inspect.isabstract(subclass)
	}


def _get_all_subclasses(cls):
	return [
		subclass
		for child in cls.__subclasses__()
		for subclass in [child, *_get_all_subclasses(child)]
	]

