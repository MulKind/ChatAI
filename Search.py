import shelve
with shelve.open('verification_codes.db') as db:
    print(db['phone_numbers'])