def null_empty_cells(row):
    """
    Sets all value in the dictionary to None if empty
    :param row: the dictionary to process
    :type row: dict
    """
    for k in row.keys():
        if row[k] == "":
            row[k] = None

def truncate_strings(row, max, enc='utf-8'):
    """
    Truncates strings to the maximum length.

    :param row: the dictionary to process
    :type row: dict
    :param max: the maximum length
    :type max: int
    :param enc: the encoding to use
    :type enc: str
    """
    for k in row.keys():
        if len(row[k]) > max:
            row[k] = row[k][:max]

def encode_strings(row, enc='utf-8'):
    """
    Encodes strings (bytes objects) with the specified encoding.

    :param row: the dictionary to process
    :type row: dict
    :param enc: the encoding to use
    :type enc: str
    """
    for k in row.keys():
        if len(row[k]) > 0:
            if not isinstance(row[k], str):
                row[k] = row[k].decode(enc)

def string_cell(row, names, defvalue=None):
    """
    Returns a string cell from the row dictionary, using a list of aliases for the value.

    :param row: the (eg CSV) row dictionary
    :type row: dict
    :param names: the list of alias names
    :type names: list of str
    :param defvalue: the default value
    :type defvalue: str
    :return: the value if any of the aliases was found, otherwise the default value
    :rtype: str
    """
    result = defvalue
    for name in names:
        if name in row:
            if not isinstance(row[name], str):
                return row[name].decode('utf-8')
            else:
                return row[name]
    return result

def int_cell(row, names, defvalue=None):
    """
    Returns an int value from the row dictionary, using a list of aliases for the value.

    :param row: the (eg CSV) row dictionary
    :type row: dict
    :param names: the list of alias names
    :type names: list of str
    :param defvalue: the default value
    :type defvalue: int
    :return: the value if any of the aliases was found, otherwise the default value
    :rtype: int
    """
    result = defvalue
    for name in names:
        if name in row:
            if row[name] != '':
                return int(row[name])
    return result

def float_cell(row, names, defvalue=None):
    """
    Returns a float value from the row dictionary, using a list of aliases for the value.

    :param row: the (eg CSV) row dictionary
    :type row: dict
    :param names: the list of alias names
    :type names: list of str
    :param defvalue: the default value
    :type defvalue: float
    :return: the value if any of the aliases was found, otherwise the default value
    :rtype: float
    """
    result = defvalue
    for name in names:
        if name in row:
            if row[name] != '':
                return float(row[name].replace(",", ""))
    return result
