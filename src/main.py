
from persist import data_add_refresh, persist_data_from_files
from threading import Thread
from api import create_app
import uvicorn

# if data is to be added start and join the below thread
# we need to add the data before starting the server, o.w there could be multiple threads
# trying to access the db and one of them could time out because the db was locked by another thread

# data_persist_thread = Thread(target=persist_data_from_files)
# data_persist_thread.start()
# data_persist_thread.join()

# starting a thread for refreshing every hour
# making it a daemon thread so that when server stops the refresh thread also stops
Thread(target=data_add_refresh, daemon=True).start()

# creating the api
app = create_app()

if __name__ == "__main__":
    
    uvicorn.run("main:app", host="127.0.0.1", port=8081, log_level="debug", reload=False)