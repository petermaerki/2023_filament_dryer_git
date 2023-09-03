import mp
import mp.micropythonshell

if __name__ == "__main__":
    shell = mp.micropythonshell.MicropythonShell(str_port=None) # 'COM9')
    shell.sync_folder(directory_local='micropython')
    shell.repl(start_main=True)
    shell.close()
