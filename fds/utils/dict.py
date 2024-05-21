from fds.utils.log import log_and_raise


def compare_two_dicts(test_dict: dict, blueprint: dict):
    """The two dictionaries have a set of keys, the test_dict one must be a subset of the blueprint one. Moreover,
    each key corresponds to a dictionary, and keys of this dictionary must be the same as the blueprint one.
    """
    _check_if_dict(blueprint, "blueprint")
    _check_if_dict(test_dict, "test_dict")

    for key in test_dict.keys():
        if key not in blueprint.keys():
            msg = f"Dictionary key {key} is not in default config key {blueprint.keys()}"
            log_and_raise(ValueError, msg)
        if isinstance(blueprint[key], dict):
            _check_if_dict(test_dict[key], f"test_dict[{key}]")
            _check_if_same_keys(key, blueprint, test_dict)


def _check_if_same_keys(key: str, blueprint: dict, test_dict: dict):
    sub_blueprint = blueprint[key]
    sub_config = test_dict[key]
    if set(sub_blueprint.keys()) != set(sub_config.keys()):
        # Find the difference between the two sets
        diff_blueprint = set(sub_blueprint.keys()) - set(sub_config.keys())
        diff_config = set(sub_config.keys()) - set(sub_blueprint.keys())
        if len(diff_blueprint) == 0:
            msg = f"Keys of test_dict {key} are not the same as blueprint {key}: " \
                  f"test_dict has additional keys: {diff_config}"
        elif len(diff_config) == 0:
            msg = f"Keys of test_dict {key} are not the same as blueprint {key}: " \
                  f"blueprint has additional keys: {diff_blueprint}"
        else:
            msg = f"Keys of test_dict {key} are not the same as blueprint {key}: " \
                  f"test_dict has additional keys: {diff_config}, blueprint has additional keys: {diff_blueprint}"
        log_and_raise(ValueError, msg)


def _check_if_dict(value: dict, name: str):
    if not isinstance(value, dict):
        msg = f"Invalid type {type(value)} for {name}"
        log_and_raise(ValueError, msg)
