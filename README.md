This is a fork of [https://github.com/ctrl-z-bg/gav](ctrl-z-bg/gav)

# GAV RL

Welcome to GAV, a GPL rendition of the popular Arcade Volleyball.

In addition to the original game, GAV RL implements an AI agent based on Deep
Q-Learning. It uses
[stable-baselines3](https://stable-baselines3.readthedocs.io/en/master/) as RL
framework and includes a neural network visualization tool for live demos.

# Building

The game is based on SDL version 1. The easiest way to get it is to install SDL-compat (to SDL2 or 3)
and [SDL-image version 1.2](https://github.com/libsdl-org/SDL_image/tree/SDL-1.2).

Edit the file `CommonHeader` if necessary with the path with SDL libraries. Then, run `make`.

### RL agent

Enter the directory `RL` and run:

```
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For the neural network visualization based on the 
[AzDelivery 4x64 led matrix](https://www.az-delivery.de/en/products/4-x-64er-led-matrix-display?variant=6015286214683), flash
the Arduino firmware in `RL/arduino/azdel_4x64_ledmatrix`.

# Running

1. Activate the environment

```
cd RL/
source .venv/bin/activate
```

2. Run the DQN service

```
python DQNservice_predict.py
```

3. run the game:

```
cd ..
./gav
```

and select `AI RL` for `Player 2`

# Author

Filippo Bergamasco, Ca'Foscari University of Venice

# License

```
GAV RL, a fork of GAV (https://github.com/ctrl-z-bg/gav)

Copyright (c) 2016 Original Authors (see ctrl-z-bg/gav)
Copyright (c) 2026 Ca'Foscari University of Venice

GAV RL is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

GAV RL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
