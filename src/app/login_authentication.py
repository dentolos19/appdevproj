import shelve

class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

# add new user
def add_user(username, email, password):

    # open storage file
    with shelve.open('accounts') as db:
        
        # checking first if user exists already
        if username in db:
            print("User already exists! Click below to login")
        
        else:
            new_user = User(username, email, password)
            db[username] = new_user
            print(f"Account created for {username}")

# authentication for login
def login(username, password):
    
    with shelve.open("accounts") as db:
        if username in db:
            user = db[username]

            if user.password == password:
                print(f"Welcome back {username}")
            
            else:
                print("Incorrect password. Try again!")
        
        else:
            print("User not found!")
        
# testing

# if __name__ == "__main__":

#     add_user("zuhair123", "zuhair.gmail.com", "password")
    
#     login("zuhair123", "password")
    
#     login("zuhair123", "wrongpassword")
    
#     login("buddy", "password456")

        