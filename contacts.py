contacts = {}

def add_contact(name, phone):
    contacts[name] = phone

def search_contact(name):
    return contacts.get(name, "not found")

if __name__ == '__main__':
    add_contact("Arun", "9876543210")
    add_contact("Priya","9123456780")
    print("Arun's number:", search_contact("Arun"))
    print("Kabir's number:", search_contact("Kabir"))