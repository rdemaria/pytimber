def check_kerberos():
    import subprocess
    ret=subprocess.run(["klist"], stdout=subprocess.PIPE)
    if len(ret.stdout)==0:
        import getpass
        user=getpass.getuser()
        mypass=getpass.getpass(f"Type the password for `{user}`:")
        subprocess.run(["kinit"],input=mypass.encode())

