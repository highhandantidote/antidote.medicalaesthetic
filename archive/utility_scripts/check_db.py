from main import app
from models import Thread, Procedure, Community, CommunityReply, User
from app import db

with app.app_context():
    print(f'Threads: {Thread.query.count()}')
    print(f'Procedures: {Procedure.query.count()}')
    print(f'Community posts: {Community.query.count()}')
    print(f'Community replies: {CommunityReply.query.count()}')
    print(f'Users: {User.query.count()}')
    
    # Check if we have any threads with the required structure
    thread = Thread.query.first()
    if thread:
        print(f"\nSample Thread: {thread.id}")
        print(f"Title: {thread.title}")
        try:
            print(f"Keywords: {thread.keywords if thread.keywords else 'None'}")
        except Exception as e:
            print(f"Error getting keywords: {str(e)}")
        
        try:
            # Check if procedure exists
            if thread.procedure_id:
                procedure = Procedure.query.get(thread.procedure_id)
                print(f"Procedure: {procedure.procedure_name if procedure else 'Not found'}")
            else:
                print("No procedure associated with this thread")
        except Exception as e:
            print(f"Error getting procedure: {str(e)}")
    else:
        print("\nNo threads found in the database")
    
    # Check all tables
    print("\nDatabase Tables:")
    tables = db.engine.table_names()
    for table in tables:
        print(f"- {table}")