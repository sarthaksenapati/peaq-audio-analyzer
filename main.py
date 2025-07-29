# main.py


from settings import main as settings_main
from ui_interface import display_main_menu, route_user

def main():
    # Ensure device is set up before proceeding
    settings_main()
    while True:
        choice = display_main_menu()
        route_user(choice)
        again = input("\n🔁 Run another mode? (y/n): ").strip().lower()
        if again != 'y':
            break

if __name__ == "__main__":
    main()
