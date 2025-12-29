/* -*- C++ -*- */
/*
  GAV - Gpl Arcade Volleyball
  
  TODO

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
*/

#include <iostream>
#include <vector>
#include <cstring>      // for memcpy, memset
#include <sys/socket.h> // Socket functions
#include <arpa/inet.h>  // sockaddr_in, inet_addr
#include <unistd.h>     // close()
#include <netinet/tcp.h>
#include "PlayerAI_RL.h"
#include "Ball.h"


#define SERVER_PORT 1809


/**
 * Helper: Convert a float to Network Byte Order (Big Endian).
 * We treat the float bits as a uint32, then swap bytes using htonl.
 */
uint32_t hton_float(float value) {
    uint32_t temp;
    // Use memcpy to avoid strict-aliasing violations
    std::memcpy(&temp, &value, sizeof(float));
    return htonl(temp);
}

PlayerAI_RL::~PlayerAI_RL()
{
    shutdown( sock, SHUT_RDWR);
    close( sock );
}


void PlayerAI_RL::connect_to_rl_service()
{
    const int side = (team())->side();  // -1: left,  1: right
    struct sockaddr_in serv_addr;

    //const char* SERVER_IP = "157.138.24.148";
    const char* SERVER_IP = "127.0.0.1";

    std::cout << "PlayerAI_RL::connect_to_rl_service()" << std::endl;


    // 1. Create Socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        std::cout << "Socket creation error" << std::endl;
        exit(-1);
    }

    // Disable Nagle's Algorithm
    int flag = 1;
    int result = setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, (char *)&flag, sizeof(int));
    if (result < 0) {
        std::cout << "Warning: Could not set TCP_NODELAY" << std::endl;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons( side<0?SERVER_PORT:SERVER_PORT+1 );

    // Convert IPv4 and IPv6 addresses from text to binary form
    if (inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr) <= 0) {
        std::cout << "Invalid address / Address not supported" << std::endl;
        exit(-1);
    }

    // 2. Connect to Server
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        std::cerr << "Connection Failed. Is the RL service running?" << std::endl;
        sock = -1;
        sleep(1);
    }

    action_sequence_num = 99;
    std::cout << "Connected to RL service!" << std::endl;
}


triple_t PlayerAI_RL::planAction() 
{

    triple_t ret;
    ret.left = ret.right = ret.jump = 0;

    if( sock==-1 )
    {
        connect_to_rl_service();
    }

    if( sock==-1 )
    {
        return ret;
    }

    if( _b->scorerSide() == 0 )
        match_ended = false;

    if( match_ended )
        return ret;

    int offset = 0;

    // We need to send 28 bytes total: 4 bytes (int) + 24 bytes (6 * float)
    const int BUFFER_SIZE = 28;
    char send_buffer[BUFFER_SIZE];

    // Buffer for receiving action (4 bytes)
    int action_buffer;

    //std::cout << "PlayerAI_RL::planAction()" << std::endl;
    //


    const int side = (team())->side();  // -1: left,  1: right


    const float px = (side*(float)(x() - (team())->screen_w()/2)/(float)team()->screen_w() ) - (side<0?0.1f:0.0f);
    const float py = 1.0f - (float)y()/(float)(team()->screen_h());

    const float by = (float)((team())->screen_h() - _b->y() - _b->radius() )/(float)team()->screen_h() ;
    const float bvy = _b->spdy()/(float)(team()->screen_h());

    const float bx = (side*(float)(_b->x() - (team())->screen_w()/2)/(float)team()->screen_w() )- (side<0?0.1f:0.0f);
    const float bvx = side*_b->spdx()/(float)(team()->screen_w());

    int game_status = 0;


    if( _b->colliding_with( this ) )
    {
        game_status = 3;
    }

    if( _b->scorerSide() != 0 )
    {
        game_status = _b->scorerSide()==side?1:2;
        match_ended = true;
    }

    /* Game status:
     * 0: playing 
     * 1: win
     * 2: lose
     * 3: ball hit the player
    std::string status_text[4] = {
        std::string("playing"),
        std::string("win"),
        std::string("lose"),
        std::string("ball hit") };

    std::cout << "Game status: " << status_text[game_status] << std::endl;
     */

    float game_data[6] = { px,py,bx,by,bvx,bvy };

    // --- SERIALIZATION (Pack into buffer) ---
    // We manually copy bytes into the buffer to avoid struct padding issues
    // and ensure correct Endianness (Big Endian as defined by Python's '!')


    // 1. Pack Integer (Network Byte Order)
    //
    game_status = (action_sequence_num<<3) | (game_status & 0x7);
    
    uint32_t id_net = htonl(game_status);
    std::memcpy(send_buffer + offset, &id_net, sizeof(id_net));
    offset += sizeof(id_net);

    // 2. Pack 6 Floats
    for (float val : game_data) {
        uint32_t f_net = hton_float(val);
        std::memcpy(send_buffer + offset, &f_net, sizeof(f_net));
        offset += sizeof(f_net);
    }

    // --- SEND ---
    //std::cout << "Sending status with sequence num " << action_sequence_num << std::endl;
    send(sock, send_buffer, BUFFER_SIZE, 0);


    // --- RECEIVE ACTION ---
    // Wait for 4 bytes (int32)

    int bytes_read = read(sock, &action_buffer, sizeof(action_buffer));


    if (bytes_read <= 0) {
        std::cout << "Server closed connection!" << std::endl;
        sock=-1;
        return ret;
    }

    // Deserialize: Network to Host Byte Order
    int action_data = ntohl(action_buffer);

    action_sequence_num = action_data >> 3;
    int action = action_data & 0x7;

    //std::cout << "Received action with sequence num " << action_sequence_num << " action=" << action << std::endl;

    /* ACTION MAPPING 
    *  0: do nothing
    *  1: move forward
    *  2: move backward
    *  3: jump center
    *  4: jump forward
    *  5: jump backward
    */

    switch( action )
    {
        case 1: if(side<0) ret.right=1; else ret.left=1; break;
        case 2: if(side<0) ret.left=1; else ret.right=1; break;
        case 3: ret.jump=1; break;
        //case 3: ret.jump=1; if(side<0) ret.right=1; else ret.left=1; break;
        //case 4: ret.jump=1; if(side<0) ret.left=1; else ret.right=1; break;
    }

    return ret;
}

