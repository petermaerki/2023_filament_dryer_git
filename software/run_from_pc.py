import mp
import mp.micropythonshell

if __name__ == "__main__":
    shell = mp.micropythonshell.MicropythonShell(str_port=None)  # 'COM9')
    files_to_skip = ["config_secrets.py", "config_secrets.py.gpg"]
    # files_to_skip = ["config_secrets.py.gpg"]
    shell.sync_folder(directory_local="micropython", files_to_skip=files_to_skip)
    shell.repl(start_main=True)
    shell.close()
