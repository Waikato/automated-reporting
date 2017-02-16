def null_empty_cells(row):
    """
    Sets all value in the dictionary to None if empty
    :param row: the dictionary to process
    :type row: dict
    """
    for k in row.keys():
        if row[k] == "":
            row[k] = None

def truncate_strings(row, max):
    """
    Truncates strings to the maximum length.

    :param row: the dicationary to process
    :type row: dict
    :param max: the maximum length
    :type max: int
    """
    for k in row.keys():
        if len(row[k]) > max:
            row[k] = row[k][:max]
