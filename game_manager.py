import numpy as np

class BattleshipManager(object):
    def __init__(self,
                 state=None, n_players=2,
                 grid_size=(10, 10),
                 rollout_limit=1000,
                 random_seed=1999):
        self.n_players = n_players
        self.grid_size = grid_size
        self.random_seed = random_seed
        self.random_state = np.random.RandomState(random_seed)
        self.rollout_limit = rollout_limit
        if state == None:
            state = self.get_init_state()
        self.state = state

    def _random_grid_layout(self, init_grids):
        # do this randomly at first
        """
        pieces

        Aircraft Carrier	5
        Battleship	4
        Submarine	3
        Cruiser	3
        Destroyer	2
        """
        for p in range(self.n_players):
            play_grid = init_grids[self.n_players * p]
            pieces = ["Aircraft Carrier",
                      "Battleship",
                      "Submarine",
                      "Cruiser",
                      "Destroyer"]
            piece_dims = {}
            # default dimensions in UD configuration
            piece_dims["Aircraft Carrier"] = (5, 1)
            piece_dims["Battleship"] = (4, 1)
            piece_dims["Submarine"] = (3, 1)
            piece_dims["Cruiser"] = (3, 1)
            piece_dims["Destroyer"] = (2, 1)

            piece_code = {}
            piece_code["Aircraft Carrier"] = 2.
            piece_code["Battleship"] = 3.
            piece_code["Submarine"] = 4.
            piece_code["Cruiser"] = 5.
            piece_code["Destroyer"] = 6.
            while len(pieces) > 0:
                piece_idx = self.random_state.choice(range(len(pieces)))
                piece = pieces[piece_idx]
                placed = False
                c = self.random_state.randint(0, 2)
                for _ in range(2):
                    xx, yy = np.meshgrid(np.arange(play_grid.shape[1]), np.arange(play_grid.shape[0]))

                    start_coords = [z for z in zip(yy.ravel(), xx.ravel())]
                    while len(start_coords) > 0:
                        try_idx = self.random_state.choice(range(len(start_coords)))
                        try_start_coord = start_coords[try_idx]
                        sc0 = try_start_coord[0]
                        sc1 = try_start_coord[1]

                        sz = piece_dims[piece]

                        if c == 0:
                            if sc0 + sz[0] >= self.grid_size[0]:
                                start_coords.pop(try_idx)
                                continue
                            if sc1 + sz[1] >= self.grid_size[1]:
                                start_coords.pop(try_idx)
                                continue
                            if np.sum(play_grid[sc0:sc0 + sz[0], sc1:sc1 + sz[1]]) == 0.:
                                play_grid[sc0:sc0 + sz[0], sc1:sc1 + sz[1]] = piece_code[piece]
                                placed = True
                                break
                        elif c == 1:
                            # rotated piece
                            if sc0 + sz[1] >= self.grid_size[0]:
                                start_coords.pop(try_idx)
                                continue
                            if sc1 + sz[0] >= self.grid_size[1]:
                                start_coords.pop(try_idx)
                                continue
                            if np.sum(play_grid[sc0:sc0 + sz[1], sc1:sc1 + sz[0]]) == 0.:
                                play_grid[sc0:sc0 + sz[1], sc1:sc1 + sz[0]] = piece_code[piece]
                                placed = True
                                break
                        else:
                            raise ValueError("Invalid configuration index found!")
                            from IPython import embed; embed(); raise ValueError()
                    if placed:
                       break
                    # if none of those worked, try again with the other configuration...
                    c = int(abs(1 - c))
                if placed:
                    pieces.pop(piece_idx)
                else:
                    raise ValueError("Failed to place piece!")
                    from IPython import embed; embed(); raise ValueError()
            #print("finished placing player {}".format(p))
        return init_grids

    def get_init_state(self):
        # personal play grid, targeting grids per player
        grids = [np.zeros(self.grid_size) for i in range(self.n_players + self.n_players * (self.n_players - 1))]
        grids = self._random_grid_layout(grids)
        return grids

    def get_next_state(self, state, actions, player):
        p = player
        pgrids = state[self.n_players * p:self.n_players * (p + 1)]
        shot_grids = pgrids[1:]
        real_grids = [state[self.n_players * i] for i in range(self.n_players) if i != player]

        assert len(actions) == len(shot_grids)
        for n, a in enumerate(actions):
            if real_grids[n].ravel()[a] == 0.:
                shot_grids[n].ravel()[a] = 1.
                real_grids[n].ravel()[a] = -1.
            elif real_grids[n].ravel()[a] != 0.:
                tt = np.where(real_grids[n].ravel() == real_grids[n].ravel()[a])[0]
                if len(tt) <= 1.:
                    # battleship sunk
                    shot_grids[n].ravel()[a] = 3.
                    real_grids[n].ravel()[a] *= -1.
                else:
                    shot_grids[n].ravel()[a] = 2.
                    real_grids[n].ravel()[a] *= -1.
        return state

    def get_current_player(self, state):
        player_counts = []
        for p in range(self.n_players):
            pgrids = state[self.n_players * p:self.n_players * (p + 1)]
            shot_grids = pgrids[1:]
            total_shots = [np.sum(sg > 0.) for sg in shot_grids]
            count = sum(total_shots)
            player_counts.append(count)

        if min(player_counts) == max(player_counts):
            # if everyone has equal shots, player 0 turn
            return 0
        else:
            return 1

    def get_action_space(self):
        return [np.array(range(self.grid_size[0] * self.grid_size[1])) for p in range(self.n_players - 1)]

    def get_valid_actions(self, state, player):
        # return valid actions against each player
        p = player
        pgrids = state[self.n_players * p:self.n_players * (p + 1)]
        shot_grids = pgrids[1:]
        valid_actions = []
        for sg in shot_grids:
            sg_va = np.where(sg.ravel() == 0.)[0]
            valid_actions.append(sg_va)
        return valid_actions

    def _rollout_fn(self, state):
        pass

    def rollout_from_state(self, state):
        pass

    def is_finished(self, state):
        for p in range(self.n_players):
            pgrids = state[self.n_players * p:self.n_players * (p + 1)]
            shot_grids = pgrids[1:]
            my_grid = pgrids[0]
            if any([len(np.where(sg == 0.)[0]) == 0 for sg in shot_grids]):
                #print("no more shots to take for player {} against opponent".format(p))
                # in true multi-player this means game is over guaranteed?
                # for now, if you can't take any more shots you won for sure
                pass

            opponents = [op for op in range(self.n_players) if op != p]
            o_alive = [True for op in opponents]
            for n, o in enumerate(opponents):
                opponent_grid = state[self.n_players * o]
                if len(np.where(opponent_grid > 0.)[0]) > 0.:
                    continue
                else:
                    o_alive[n] = False
            if any(o_alive):
                continue
            else:
                return p, True
        # return -1 for not finished, or player index 0-n if complete
        return -1, False


if __name__ == "__main__":
    # simple example of 2 random agents playing
    rng = np.random.RandomState(12)
    bsm = BattleshipManager(random_seed=rng.randint(10000))
    state = bsm.state
    s = 0
    while True:
        p = bsm.get_current_player(state)
        va = bsm.get_valid_actions(state, p)
        try:
            actions = [rng.choice(vai) for vai in va]
        except:
            print("no actions left")
            from IPython import embed; embed(); raise ValueError()
        next_state = bsm.get_next_state(state, actions, p)
        state = next_state
        winner, end = bsm.is_finished(state)
        if end:
            print("Game over in steps {}, winner {}".format(s, p))
            bsm = BattleshipManager(random_seed=rng.randint(10000))
            state = bsm.state
            s = 0
        else:
            #print("s {}".format(s))
            s += 1
    from IPython import embed; embed(); raise ValueError()
