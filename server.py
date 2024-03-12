#TODO: Login, List, logout, who, Lookup, Deposit, Shutdown
#This is file for all server operatons
import socket
#Use sqlite3 library to create simple db for stocks
import sqlite3

import select

from concurrent.futures import ThreadPoolExecutor

import threading



# Connect to SQLite database
with sqlite3.connect('stock_trading_system.db') as conn:
    cursor = conn.cursor() #create a cursor object to execute SQL commands
    
    #RESET THE DATA OF DB (KEEP CODE COMMENTED UNLESS YOU WANT TO RESET DATA)
    #Drop existing tables

    #cursor.execute('DROP TABLE IF EXISTS stocks;') 
    #cursor.execute('DROP TABLE IF EXISTS users;')


    # Create users table (from professors example)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,  
            email VARCHAR(255) NOT NULL,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            user_name VARCHAR(255) NOT NULL,
            password VARCHAR(255),
            usd_balance DOUBLE NOT NULL
        )
    ''')

     # Create stocks table (From professors example)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_symbol VARCHAR(4) NOT NULL,
            stock_name VARCHAR(20) NOT NULL,
            stock_balance DOUBLE,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (ID)
        )
    ''')

    conn.commit()

#INITIAL DATA LOADING, COMMENT THIS OUT ONCE DB IS CREATED ONCE

#Adding initial data to db
    
#cursor = conn.cursor()

# Insert initial data for users
    
# cursor.executescript("""
# INSERT INTO users (email, first_name, last_name, user_name, password, usd_balance) VALUES
# ('root@example.com', 'root', 'root', 'root', 'root123', 120.00),
# ('john.doe@example.com', 'John', 'Doe', 'johndoe', 'password123', 1000.00),
# ('jane.smith@example.com', 'Jane', 'Smith', 'janesmith', 'password123', 1500.00),
# ('alex.jones@example.com', 'Alex', 'Jones', 'alexjones', 'password123', 5.00);
# """)

#insert initial data for stocks
    
# cursor.executescript("""
# INSERT INTO stocks (stock_symbol, stock_name, stock_balance, user_id) VALUES
# ('AAPL', 'Apple Inc.', 10, 1),
# ('GOOGL', 'Alphabet Inc.', 5, 2),
# ('MSFT', 'Microsoft Corp.', 8, 1),
# ('TSLA', 'Tesla Inc.', 3, 2);
# """)

# conn.commit()
# print("Initial data added successfully")

 #TODO: maybe not require user_id in buy command   
#Souad
def buy_command(conn, command):
    _, stock_symbol, stock_amount, price_per_stock, user_id= command.split()

    #converting strings into float or int
    stock_amount = float(stock_amount)
    price_per_stock = float(price_per_stock)
    user_id = int(user_id)

    #initialize new stock balance
    new_stock_balance = 0

    cursor = conn.cursor()

    #check to see if user exists in db
    cursor.execute("SELECT usd_balance FROM users WHERE ID = ?", (user_id,))
    result = cursor.fetchone()

    #if user isn't in db
    if result is None:
        return "Error: User Does Not Exist!!\n"
    
    usd_balance = result[0]
    total_price = stock_amount *price_per_stock

    #check if user has enough balance
    if usd_balance <total_price:
        return "Error: Not Enough Balance!!\n"
    
    #Deduct price from user balance
    new_usd_balance = usd_balance - total_price
    #update the table 
    cursor.execute("UPDATE users SET usd_balance = ? WHERE ID = ?", (new_usd_balance, user_id))

    #grab data from the stock table
    cursor.execute("SELECT stock_balance FROM stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
    stock_result = cursor.fetchone()

    if stock_result: #if the user already owns some of this stock
        new_stock_balance = stock_result[0] +stock_amount
        #update table 
        cursor.execute("UPDATE stocks SET stock_balance = ? WHERE user_id = ? AND stock_symbol = ?", (new_stock_balance, user_id, stock_symbol))
    
    else: #user doesnt own any of this stock previously
        new_stock_balance = stock_amount
        cursor.execute("INSERT INTO stocks (stock_symbol, stock_name, stock_balance, user_id) VALUES (?, ?, ?, ?)", (stock_symbol, stock_symbol, stock_amount, user_id))


    #Commit all changes to the Database!
    conn.commit()

    return f"200 OK\nBOUGHT: New balance: {new_stock_balance} {stock_symbol}. USD balance ${new_usd_balance}"


#TODO: maybe not require user_id in sell command
#Brooklyn
def sell_command(conn, command):
    _, stock_symbol, stock_amount, price_per_stock, user_id = command.split()

    stock_amount = float(stock_amount)
    price_per_stock = float(price_per_stock)
    user_id = int(user_id)

    cursor = conn.cursor()

    cursor.execute("SELECT usd_balance FROM users WHERE ID = ?", (user_id,))
    result = cursor.fetchone()

    #if user isn't in db
    if result is None:
        return "Error: User Does Not Exist!!"

    usd_balance = result[0]
    total_price = stock_amount * price_per_stock
    
    #Add price to user balance
    new_usd_balance = usd_balance + total_price
    #update the table
    cursor.execute("UPDATE users SET usd_balance = ? WHERE ID = ?", (new_usd_balance, user_id))

    #grab data from the stock table
    cursor.execute("SELECT stock_balance FROM stocks WHERE user_id = ? AND stock_symbol = ?", (user_id, stock_symbol))
    stock_result = cursor.fetchone()

    if stock_result and stock_result[0] >= stock_amount: #if the user already owns some of this stock
        new_stock_balance = stock_result[0] - stock_amount
        #update table 
        cursor.execute("UPDATE stocks SET stock_balance = ? WHERE user_id = ? AND stock_symbol = ?", (new_stock_balance, user_id, stock_symbol))
    elif stock_result and stock_result[0] < stock_amount: #if user owns some stock but not enough to sell
       # print(f"Debug Message: Not enough stock to sell")
        return "ERROR: Not enough stock to sell\n"
    else: 
        return "ERROR: You don't own any of this stock\n"
     #Commit all changes to the Database!
    conn.commit()

    return f"200 OK\nSOLD: New balance: {new_stock_balance} {stock_symbol}. USD balance ${new_usd_balance}"

#Souad
def list_command(conn, address, client_login_status):

    #parts = command.split() 
    #if user provided user id, use it, else defualt user id is 1
   # user_id = parts[1] if len(parts) > 1 else '1'

    cursor = conn.cursor()

    #determine if user is root
    is_root = client_login_status[address]['user_name'] =='root'
    user_id = client_login_status[address]['user_id']

    #Fetch data based on user permissions
    if is_root:
        cursor.execute("SELECT ID, stock_symbol, stock_balance, user_id FROM stocks")
        response_prefix ="The list of records in the Stock Database:\n"
    else:
        cursor.execute("SELECT ID, stock_symbol, stock_balance, user_id FROM stocks WHERE user_id = ?", (user_id,))
        response_prefix = f"The list of records in the Stocks Database for user {user_id}:\n"
    
    stocks = cursor.fetchall()

    if not stocks:
        return f"200 OK\n" + ("No stocks found." if is_root else f"No stocks found for user {user_id}")

    #creating response string
    response = f"200 OK\n" + response_prefix
    for stock in stocks:
        stock_id, symbol, balance, user_id = stock
        #if is root, then include user id to the response, else don't need to
        user_info = f" {user_id}" if is_root else ""
        response += f"{stock_id} {symbol} {balance} {user_info}\n"

    return response
   

#Brooklyn
def balance_command(conn, command):
    _, user_id = command.split()

    #should user number be read in or set? right now its read in
    user_id = int(user_id)

    cursor = conn.cursor()

    #grab balance from the user table
    cursor.execute("SELECT usd_balance FROM users WHERE ID = ?", (user_id,))
    result = cursor.fetchone()

    #if user isn't in db
    if result is None:
        return "Error: User Does Not Exist!!"

    usd_balance = result[0]

    cursor.execute("SELECT first_name, last_name FROM users WHERE ID = ?", (user_id,))
    name = cursor.fetchone()

    return f"200 OK\nBalance for {name} is ${usd_balance} " #grab first name and last name from user through user_id

#Souad
def shutdown_command(clientsocket, serversocket, conn):
    #send confirmation msg to client
    response = "200 OK\nSERVER SHUTDOWN\n"
    clientsocket.sendall(response.encode())

    #added this code so we know to close all clients if flag is set
    global shutdown_event
    shutdown_event.set()

    #close client socket
    #clientsocket.close()

    #close server socket
    #serversocket.close()

    #close db connection
    conn.close()

    #exit program
    exit(0)

#Brooklyn
def quit_command(clientsocket, address):

    global client_login_status

    #remove login status
    if address in client_login_status:
        del client_login_status[address]

    #send confirmation msg to client
    response = "200 OK\n"
    clientsocket.sendall(response.encode())

    #close client socket
    clientsocket.close()

#method for login
def login_command(clientsocket, address, command, conn):

    global client_login_status

    _, username, password = command.split() #split up command
    cursor = conn.cursor()
    #check to see if user exists in user database
    cursor.execute("SELECT user_name, password, ID FROM users WHERE user_name = ? AND password = ?", (username, password))
    result = cursor.fetchone()

    #maybe have lock for concurrency IDK**
    if result:
        username,_,user_id = result
        client_login_status[address] = {'logged_in': True, 'user_name': username, 'user_id': user_id, 'IP': address[0]}
        response = "200 Ok"
    else:
        response = "403 Wrong Username or Password"
    
    return response


#method for logout
def logout_command(address, client_login_status):
    if address in client_login_status:
        #remove user login status
        del client_login_status[address]
        response = "200 OK"
    else:
        response = "403 Unable to logout"
    
    return response
    

#method for who
def who_command(client_login_status):
    response = "200 OK\nThe list of active users:\n"

    for addr, info in client_login_status.items():
        if info.get('logged_in'):
            response += f"{info.get('user_name')} {info.get('IP')}\n"

    return response

#lookup method
def lookup_command(clientsocket, address, command, conn, client_login_status):
    if address not in client_login_status or not client_login_status[address]['logged_in']:
        return "403 Please login first"
    _, stock_name = command.split(maxsplit = 1)
    cursor = conn.cursor()

    #get all records from logged in user matching stock name
    cursor.execute("SELECT * FROM stocks WHERE user_id = ? AND stock_name LIKE ?", (client_login_status[address]['user_id'], f'%{stock_name}%'))
    results = cursor.fetchall()

    if results:
        response = "200OK\n Found {len(results)} Match(es)\n"
    for result in results:
        response += ' '.join(str(item) for item in result) + "\n"
    else: 
        response = "404 no records found"
    return response
    

#deposit command





#defining method to recieve data from client

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
        except BlockingIOError: #added exception
            if not data:
                continue
            else:
                break
        except OSError: #added another exception to prevent OSError when shutting everything down
            if shutdown_event.is_set():
                # Expected during shutdown, treat as normal
                break
        #Join all chunks into a string and remove delimiter
        return ''.join(data).rstrip(delimiter)


#variables for login

root_client = None #keeps track of root client
client_login_status = {} #use dictionary to keep track of logins



#defining method to handle clients (need to handle multiple clients)
def handle_clients(clientsocket, address):

    global root_client  
    global client_login_status #use this to keep track if client is logged in or not 

    print(f"Connection from {address} has been established")
    conn = sqlite3.connect('stock_trading_system.db')
    cursor = conn.cursor
    


    while not shutdown_event.is_set():
        client_message = recv_all(clientsocket)
        if not client_message:
            break #no message recieved, client is disconnected

        print(f"Received command from client: {client_message}")
   	 
        if client_message.startswith("LOGIN"):
            response = login_command(clientsocket, address, client_message, conn)
        elif client_message.startswith("LOGOUT"):
            response = logout_command(address, client_login_status)
        elif client_message.startswith("BUY"):
            response = buy_command(conn, client_message)
        elif client_message.startswith("SELL"):
            response = sell_command(conn, client_message)
        elif client_message.startswith("BALANCE"):
            response = balance_command(conn, client_message)

        elif client_message.startswith("LOOKUP"):
            response = lookup_command(clientsocket, address, client_message, conn, client_login_status)
            
        elif client_message.startswith("LIST"):

            #make sure they're logged in before list
            if address in client_login_status and client_login_status[address]['logged_in']:
                response = list_command(conn, address, client_login_status)
            else:
                response = "403 Please login first \n"

        elif client_message.startswith("SHUTDOWN"):
            if address in client_login_status and client_login_status[address]['user_name'] == 'root': #checks if client is root
                response = shutdown_command(clientsocket, server_socket, conn)
            else: 
                response = "Error: only root can execute shutdown"
        elif client_message.startswith("QUIT"):
            quit_command(clientsocket, address)
            if clientsocket in sockets_list:
                sockets_list.remove(clientsocket) #Added this to remove socket from list immediately to prevent ValueError
            break
        elif client_message.startswith("WHO"):
            if address in client_login_status and client_login_status[address]['user_name'] =='root': #check if client is root
                response = who_command(client_login_status)
            else:
                response = "Error: only root can use WHO command"

        else:
         response = "Error 400: Invalid command.\n"

    
    
        
        #send response to client
        clientsocket.sendall(response.encode())
    
    conn.close
    #close connection
    clientsocket.close()
    print(f"Connection with {address} closed.")




#creating socket object which is ipv4 & uses TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

server_socket.bind(('0.0.0.0', 2323)) #changed from socket.gethostname() to '0.0.0.0'(allows clients from any machine)
server_socket.listen()
server_socket.setblocking(False)

print("Server is listening on port 2323")

#create global event for shutdown!! to close all clients (cause it wasn't doing so before)
shutdown_event = threading.Event() #global event flag for shutdown

sockets_list = [server_socket]
try:
    while True:

        if shutdown_event.is_set():
            #SHUTDOWN EVENT RECIEVED, START CLEANUP PROCESS
            break

        #Use select to wait for event on any of the sockets in our list to monitor
        #includes sockets that we are reading/sending messages to as well as exceptions (which monitor for errors)
        try:
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
        except ValueError:
            print("Debug msg: Client is closed.\n")
            continue

        #Process sockets that are ready to be read (either new connections or incoming data on a client socket)
        for notified_socket in read_sockets:

            #check if new connection request
            if notified_socket == server_socket:

                #accecpt request
                client_socket, client_address = server_socket.accept()

                #REMOVE THIS
                #if root_client is None:
               #     root_client = client_socket #assigns first client connected as root

                print(f"Accepted new connection from {client_address}")

                #add new client socket to list of sockets
                sockets_list.append(client_socket)

                # Start a new thread to handle communication with this client.
                # The client_socket and client_address are passed as arguments to the handle_client function.
                threading.Thread(target=handle_clients, args=(client_socket, client_address)).start()

        #if sockets have an error
        for notified_socket in exception_sockets:
            #remove socket from list
            sockets_list.remove(notified_socket)

            #close socket
            notified_socket.close()
finally:
    # Cleanup code before exiting
    for socket in sockets_list[1:]:  # Skip the server socket
        try:
            socket.sendall("SERVER SHUTDOWN".encode())
            socket.close()
        except:
            print(f"Error in closing socket.")
    #close server socket at the end
    server_socket.close()
    print("Server Shutdown Cleanly!")













# #this loop runs until a connection is established

# while True:
#     clientsocket, address = s.accept() 

    
#     print(f"Connection from {address} Successfully Established")#message to check if connection worked
#     #sending string to client
    
#     message_welcome = "Welcome to this Stock Trading Program\n"
#     clientsocket.send(message_welcome.encode())
    
#     #Receive a command from the client
     
#     while True:
#         client_message = recv_all(clientsocket)
#         print(f"Received command from client: {client_message}")
   	 
#         if client_message.startswith("BUY"):
#             response = buy_command(conn, client_message)
#         elif client_message.startswith("SELL"):
#             response = sell_command(conn, client_message)
#         elif client_message.startswith("BALANCE"):
#             response = balance_command(conn, client_message)
#         elif client_message.startswith("LIST"):
#             response = list_command(conn, client_message)
#         elif client_message.startswith("SHUTDOWN"):
#             shutdown_command(clientsocket, s, conn)
#         elif client_message.startswith("QUIT"):
#             quit_command(clientsocket)
#             break
#         else:
#          response = "Error 400: Invalid command.\n"
#          #print(f"Sending response to client: {response}")  # Debug print
   	 

#         # Send the response to the client
#         clientsocket.sendall(response.encode())

#     #close connection
#     clientsocket.close()
    