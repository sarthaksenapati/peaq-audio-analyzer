# main.py

from settings import lock

def main():
    # Ensure device is set up before proceeding
    lock()
    # ui_interface will automatically call the correct mode using config
    import ui_interface

if __name__ == "__main__":
    main()
