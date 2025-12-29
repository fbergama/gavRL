/* -*- C++ -*- */
/*
  GAV - Gpl Arcade Volleyball
  
  *TODO*

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

#ifndef __PLAYERAI_RL_H__
#define __PLAYERAI_RL_H__

#include "Player.h"
#include "ControlsArray.h"

class Ball;

class PlayerAI_RL : public Player 
{
    Ball * _b;

private:
    void connect_to_rl_service();
    int sock;
    int action_sequence_num;
    bool match_ended;


protected:
    int _highestpoint;

public:

    PlayerAI_RL(Team *team, std::string name, 
	     pl_type_t type, int idx, int speed,
	     Ball *b) {
        init(team, name, type, idx, speed);
        _b = b;
        _highestpoint = 0;
        sock = -1;
    }
    virtual ~PlayerAI_RL();
    
    virtual pl_ctrl_t getCtrl() { return PL_CTRL_AI; }
    virtual triple_t planAction();
    
};

#endif
