import os.path

from nbx.nbmanager.bundle.manager import BundleManager
from nbx.nbmanager.gist import GistService, model_to_files
from nbx.config import get_config

def main():
    import argparse
    import os


    parser = argparse.ArgumentParser(description="");

    parser.add_argument('path', help="path to IPython notebook")

    args = parser.parse_args()
    path = os.path.abspath(args.path)
    save_to_gist(path)

def save_to_gist(path):
    service = GistService()
    accounts = get_config()['github_accounts']
    for user, pw in accounts:
        service.login(user, pw)

    os_path, name = os.path.split(path)
    if os.path.isdir(path):
        model = bundle_get_model(name, os_path)
    else:
        raise NotImplementedError("Need to plugin normal file stuff")

    gist_id = model['content']['metadata'].get('gist_id', None)
    if gist_id is None:
        print('No gist_id found in notebook')
        return

    gist = service.get_gist(gist_id)

    files = model_to_files(model)
    gist.save(description=name, files=files)
    msg = "Saved notebook {path} {name} to gist {gist_id}".format(name=name,
                                                        path=path,
                                                        gist_id=gist_id)
    print(msg)

def bundle_get_model(name, path):
    bundler = BundleManager()

    bundle = bundler.get_notebook(name, path)

    model = bundle.get_model(content=True, file_content=True)
    return model
