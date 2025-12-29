import SockServer

def main():
    # Create the server
    server = SockServer.SockServer(host='0.0.0.0')
    running = True

    try:
        while running:
            # 1. Wait for a client
            print("Waiting for clients...")
            server.wait_for_connection()

            print("Connected!")
            # 2. Simple loop to echo data
            while True:
                # Receive the payload
                status = server.recv_status()
                
                if status is None:
                    print("Client disconnected.")
                    break

                
                """
                Game status:
                0: playing 
                1: win
                2: lose
                3: ball hit the player
                 """
                game_status = status[0]

                #float game_data[6] = { px,py,bx,by,bvx,bvy };
                game_data = status[1:]

                print("-----------")
                print("Game status: ", game_status )
                print("  Game data: ", game_data )


                """
                ACTION MAPPING 
                0: do nothing
                1: move forward
                2: move backward
                3: jump center
                4: jump forward
                5: jump backward
                """
    
                action_to_send = 3
                server.send_action( action_to_send )

    except KeyboardInterrupt:
        running = False
    finally:
        print("\nStopping server...")
        server.close()

if __name__ == "__main__":
    main()
