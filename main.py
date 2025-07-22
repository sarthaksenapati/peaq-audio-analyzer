# main.py

from ui_interface import display_main_menu, route_user

def main():
    while True:
        choice = display_main_menu()
        route_user(choice)
        again = input("\n🔁 Run another mode? (y/n): ").strip().lower()
        if again != 'y':
            break

if __name__ == "__main__":
    main()
