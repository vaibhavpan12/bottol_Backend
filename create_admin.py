import bcrypt

from app.database.mongodb import admin_collection


email = "admin@pivora.com"
password = "admin123"


existing_admin = admin_collection.find_one({
    "email": email
})

if existing_admin:
    print("Admin already exists")

else:
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    admin_collection.insert_one({
        "email": email,
        "password": hashed_password.decode("utf-8"),
        "role": "admin"
    })

    print("Admin created successfully")