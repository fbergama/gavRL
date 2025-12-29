/* -*- C++ -*- */
/*
  GAV - Gpl Arcade Volleyball
  
  Copyright (C) 2002
  GAV team (http://sourceforge.net/projects/gav/)

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

#ifndef __MENUITEMPLAYER_H__
#define __MENUITEMPLAYER_H__

#include <stdio.h>
#include <SDL.h>
#include "MenuItem.h"
#include "globals.h"

enum { TEAM_LEFT = 0, TEAM_RIGHT};

class MenuItemPlayer: public MenuItem {
 private:
  std::string prefix;
  int team;
  int index;

public:
  MenuItemPlayer(int tm, int idx) {
    team = tm;
    index = idx;
    char numb[10];
    snprintf(numb, 10, "%d", idx*2 + tm + 1);
    prefix = std::string("Player ") + std::string(numb) + std::string(": ");
    resetLabel();
  }

  void resetLabel() {
    int *src =
      (team == TEAM_LEFT)?configuration.left_players:configuration.right_players;
    
    std::string postfix = std::string("");
    switch ( src[index] ) {
    case PLAYER_NONE:
      postfix = std::string("None");
      break;
    case PLAYER_COMPUTER:
      postfix = std::string("Computer / Net");
      break;
    case PLAYER_RL:
      postfix = std::string("AI RL");
      break;
    case PLAYER_HUMAN:
      postfix = std::string("Keyboard / Joy");
      break;
    }

    label = prefix + postfix;
  }

  int execute(std::stack<Menu *> &s) {
    int *src =
      (team == TEAM_LEFT)?configuration.left_players:configuration.right_players;
    int& src_n =
      (team == TEAM_LEFT)?configuration.left_nplayers:configuration.right_nplayers;


    switch ( src[index] ) 
    {
        case PLAYER_NONE:
          src[index] = PLAYER_HUMAN;
          src_n=1;
          break;
        case PLAYER_HUMAN:
          src[index] = PLAYER_COMPUTER;
          src_n=1;
          break;
        case PLAYER_COMPUTER:
          src[index] = PLAYER_RL;
          src_n=1;
          break;
        case PLAYER_RL:
          src[index] = PLAYER_NONE;
          src_n=0;
          break;
    }

    std::cout << "MenuItemPlayer::execute() " << src[index] << " nplayers: " << src_n << std::endl;

    #if 0
      if ( team == TEAM_LEFT )
	configuration.left_nplayers++;
      else
	configuration.right_nplayers++;
      break;
    case PLAYER_HUMAN:
      src[index] = PLAYER_COMPUTER;
      break;
    case PLAYER_COMPUTER:
      src[index] = PLAYER_RL;
      break;
    

      if ( index ) {
	src[index] = PLAYER_NONE;
	if ( team == TEAM_LEFT )
	  configuration.left_nplayers--;
	else
	  configuration.right_nplayers--;
      } else
	src[index] = PLAYER_HUMAN;
      break;
    case PLAYER_RL:
      if ( index ) {
	src[index] = PLAYER_NONE;
	if ( team == TEAM_LEFT )
	  configuration.left_nplayers--;
	else
	  configuration.right_nplayers--;
      } else
	src[index] = PLAYER_HUMAN;
      break;
    }
    #endif

    resetLabel();
    return(0);
  }
};

#endif
