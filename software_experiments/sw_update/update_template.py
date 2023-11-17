list_files = ()


def install():
    import os, rp2, machine

    for f in os.listdir("/"):
        # if f != "update.py":
        print(f"unlink('{f}')")
        os.unlink(f)

    if False:
        print("Flash A")
        flash = rp2.Flash()
        os.umount("/")
        os.VfsLfs2.mkfs(flash)
        os.mount(flash, "/")
        print("Flash B")

    if False:
        f = open("/x.py", "w")
        f.write("Hallo")
        f.close()
        for f in os.listdir("/"):
            print(f)
        print("Flash C")

    if True:
        for filename, data in list_files:
            print(f"Write {filename}")
            f = open(filename, "w")
            print("a")
            f.write(data)
            # f.write("Hallo")
            print("b")
            f.close()
            print("c")

    print("Write done")
    for f in os.listdir("/"):
        print(f)

    # machine.soft_reset()


if __name__ == "__main__":
    install()
