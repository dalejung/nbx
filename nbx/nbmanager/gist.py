from IPython.nbformat import current
import github

def model_to_files(model):
    """

    Parameters
    __________
    model : dict
        Notebook model as specified by the NotebookManager. There is
        an additional `__files` dict of the form {filename: file_content}

    Returns
    -------
    files : dict
        {filename: github.InputFileContent(file_content)}
    """
    files = {}
    name = model['name']
    content = current.writes(model['content'], format=u'json')
    f = github.InputFileContent(content)
    files[name] = f


    __files = model.get('__files', {})
    for fn, fn_content in __files.iteritems():
        f = github.InputFileContent(fn_content)
        files[fn] = f
    return files
