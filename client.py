#This file is for all client operations
import socket

#creating socket object
cs= socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Chose random port number
cs.connect((socket.gethostname(), 2323))

welcome_message = cs.recv(4096).decode()

print(welcome_message)

#method to recieve all data from server (same definiton in both files!!)
def recv_all(sock, delimiter = '\n'):
    #have empty list to hold all chunks of data
    data = []


    #read data from socket
    while True:
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
        
        
    #Join all chunks into a string and remove delimiter
    return ''.join(data).rstrip(delimiter)



while True:
          # Prompt the user for a command
            command = input("Enter command (BUY, SELL, BALANCE, LIST, SHUTDOWN, QUIT): ").strip()
            

            # Send the command to the server
            cs.sendall(command.encode())

            # Wait for and print the server's response
            response = recv_all(cs)
            print(f"Server response: {response}")

            if command.upper() == "QUIT":  # If user enters QUIT, break the loop
                print("Exiting the client. :)")
                break
            
            #Check to see if response contains the shutdown message (From shutdown function)
            if "SERVER SHUTDOWN" in response:
                print("Exiting the client.")
                break

           

#close connection
cs.close()







