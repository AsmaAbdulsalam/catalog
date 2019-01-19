from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Bookstore, Base, StoreItem, User

engine = create_engine('sqlite:///bookstorelistwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/' +
             '18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Menu for Jarir
bookstore1 = Bookstore(user_id=1, name="Jarir")

session.add(bookstore1)
session.commit()

menuItem2 = StoreItem(user_id=1, name="Spark Joy",
                      description="An Illustrated " +
                      "Guide To The Life Changing Kon Mari Method",
                      price="$795.00", category="Novel",
                      bookstore=bookstore1)

session.add(menuItem2)
session.commit()

menuItem1 = StoreItem(user_id=1, name="Kate Spade",
                      description="Journal 164339 Yellow A Likely Story",
                      price="$972.99", category="Journal",
                      bookstore=bookstore1)

session.add(menuItem1)
session.commit()

# Menu for Virgin Megastore
bookstore2 = Bookstore(user_id=1, name="Virgin Megastore")

session.add(bookstore2)
session.commit()

menuItem1 = StoreItem(user_id=1, name="book1",
                      description="With your choice of noodles " +
                      "vegetables and sauces",
                      price="$7.99", category="Entree",
                      bookstore=bookstore2)

session.add(menuItem1)
session.commit()

menuItem2 = StoreItem(user_id=1, name="book2",
                      description=" A famous duck dish " +
                      " from Beijing[1] that has ",
                      price="$25", category="Entree",
                      bookstore=bookstore2)

session.add(menuItem2)
session.commit()

print "added menu items!"
