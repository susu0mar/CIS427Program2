#This file is for all client operations
import socket
import select
import threading
import queue

#(**Had issues with timing of asking for commands and recieving response from server so added event handeling)
#Event object used to control the timing of user inputs
input_event = threading.Event()

# Set the event for the first time to allow initial user input
input_event.set()

def input_handler(cmd_queue):
     while True:
          input_event.wait() #wait for the event to be set before asking for input 
          

          cmd = input("Enter command (BUY, SELL, BALANCE, LIST, SHUTDOWN, QUIT): ").strip()
          cmd_queue.put(cmd)
          if cmd.upper() =="QUIT":
                break
          input_event.clear() # Clear the event after getting user input, wait for server response

#TODO: QUIT AND SHUTDOWN DON'T WORK, KEEP GETTING VALUE ERROR
def recv_all(sock, delimiter = '\n'):
    #have empty list to hold all chunks of data
    data = []


    #read data from socket
    while True:
        try:
            #recieve data in chunks
            chunk =sock.recv(4096).decode()

            #check if delimiter is in the chunk
            if delimiter in chunk:
                data.append(chunk)
                break #exit loop once delimiter is done
            elif not chunk:
                #if empty, then assume connection is closed
                break
            else:
                #no delimiter encountered, keep gathering chunks
                data.append(chunk)
        except BlockingIOError: #added exception!
             break
        
    #Join all chunks into a string and remove delimiter
    return ''.join(data).rstrip(delimiter)




#creating socket object
cs= socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Chose random port number
cs.connect((socket.gethostname(), 2323))
cs.setblocking(False) #set socket to non-blocking mode

cmd_queue = queue.Queue() #create a queue for thread-safe communication

#create separate thread to handle user input
threading.Thread(target=input_handler, args=(cmd_queue,), daemon=True).start()


#welcome_message = cs.recv(4096).decode()

#print(welcome_message)


try:
    should_close = False
    while not should_close:
            while not cmd_queue.empty():
                    
                #grab command from queue
                command = cmd_queue.get_nowait()

                if command:
                    # Send the command to the server
                    cs.sendall(command.encode())

                    if command.upper() == "QUIT":
                         print ("Exiting client :)") 
                         should_close = True #to exit the loop and end the client

            #check for server messages
            readable, _, _ = select.select([cs], [], [], 0.1)

            if cs in readable:
                 response = recv_all(cs)
                 print(f"Server response: {response}")

                 if "SERVER SHUTDOWN" in response:
                    print("Server shutting down. Exiting client.")
                    should_close = True
                    continue

                    
                # Set the event after the server response is processed 
                # to allow the next input prompt for the user
                 input_event.set()
            
                
finally:
     #close connection
     cs.close()
     print("Connection closed.")
                               
