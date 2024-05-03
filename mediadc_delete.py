from webdav3.client import Client
from webdav3.exceptions import RemoteResourceNotFound,ResponseErrorCode
import argparse
import json
import pathlib

parser = argparse.ArgumentParser(
                    prog='MediaDC - Mass deleter',
                    description='Takes the json export from MediaDC and massively delete all replicates',
                    )

parser.add_argument('--exclude',type=str,nargs='+',
                    help='Do not delete files whose path contains this (if size is similar)')
parser.add_argument('--dry-run',action='store_true',default=False,
                    help='Do not actually delete files')

parser.add_argument('--different-path-only',action='store_true',default=False,
                    help='Only delete files in different path (to avoid deleting pictures just a bit similar)')

parser.add_argument('--host',type=str,required=True,
                    help='WebDav full URL as given in the bottom left of the root URL')
parser.add_argument('--login',type=str,required=True,
                    help='Login')
parser.add_argument('--password',type=str,required=True,
                    help='Password')
parser.add_argument('--verify-ssl',action='store_true',default=False,
                    help='Do verify SSL certificate')


parser.add_argument('json',type=str,
                    help='Path to the json file')


args = parser.parse_args()
if args.exclude is None:
    args.exclude = []
if args.include is None:
    args.include = []

# Connect to webdav
options = {
 'webdav_hostname': args.host,
 'webdav_login':    args.login,
 'webdav_password': args.password,
}


client = Client(options)
client.verify = args.verify_ssl

def remove(path):
    """
    Actually removes a remote file given its path
    """
    if path.startswith("files/"):
        path=path[6:]

    assert(path) # Just to be sure we won't delete everything
    try:
        if args.dry_run:
            print("Would delete : ",client.info(path))
        else:
            client.clean(path)
    except RemoteResourceNotFound:
        print(f"  {path} does not exist anymore...")
    except ResponseErrorCode as e:
        print(f"  error {e} while deleting {path}")

dc = json.load(open(args.json))
for result in dc["Results"]:
    all_files=result["files"]
    files = []
    for f in all_files:
        if f['filepath'].startswith("files_trashbin"):
            continue
        files.append(f)
    if len(files) >= 2:

        files.sort(key=lambda x : x["filesize"], reverse=True)
        
        kept_file = files[0]

        if files:
            files.remove(files[0])

        print(f"Keeping {kept_file['filename']} {kept_file['filepath']} {kept_file['filesize']}")
        if files:
            for duplicate in files:

                if args.different_path_only and \
                pathlib.Path(kept_file["filepath"]).parent.resolve() == pathlib.Path(duplicate["filepath"]).parent.resolve():
                    print(f"Ignoring files in the same folder : {kept_file['filepath']} {duplicate['filepath']}")
                    continue

                print(f"Deleting {duplicate['filename']} {duplicate['filepath']} {duplicate['filesize']}")
                try:
                    remove(duplicate['filepath'])
                except Exception as e:
                    print(f"ERROR while deleting {duplicate['filename']}")

