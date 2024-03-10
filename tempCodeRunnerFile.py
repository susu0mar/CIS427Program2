 # #MY ATTEMPT TO FIX VALUE ERROR FOR SHUTDOWN AND QUIT
        # #clean up any closed/broken sockets from the list before select() statement
        # for sock in list(sockets_list):
        #     if sock == server_socket:
        #         continue #skip the server socket
        #     try:
        #         #check socket status
        #         sock.getpeername()
        #     except socket.error:
        #         #if there is a failure/exception, remove server from list
        #         sockets_list.remove(sock)
        #         print(f"Removed/closed socket: {sock}")