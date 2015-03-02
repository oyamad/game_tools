"""
Filename: fictplay.py

Authors: Daisuke Oyama

Fictitious play model.

"""
from __future__ import division

import numpy as np
from game_tools import NormalFormGame, pure2mixed


class FictitiousPlay(object):
    """
    Fictitious play with two players

    Parameters
    ----------
    data : array_like(float) or NormalFormGame


    Attributes
    ----------
    g : NormalFormGame

    players : list(Player)  # tuple

    nums_actions : tuple(int)

    current_beliefs : tuple(ndarray(float, ndim=1))

    """
    def __init__(self, data):
        if isinstance(data, NormalFormGame):
            if data.N != 2:
                raise ValueError('input game must be a two-player game')
            self.g = data
        else:  # data must be array_like
            payoffs = np.asarray(data)
            if not (payoffs.ndim in [2, 3]):
                raise ValueError(
                    'input data must be a square matrix or a bimatrix'
                )
            self.g = NormalFormGame(payoffs)

        self.N = self.g.N  # Must be 2
        self.players = self.g.players
        self.belief_sizes = tuple(
            self.g.nums_actions[1-i] for i in range(self.N)
        )

        # Create instance variable `current_belief` for self.players
        for player, belief_size in zip(self.players, self.belief_sizes):
            player.current_belief = np.empty(belief_size)
        self.set_init_beliefs()  # Initialize `current_belief`

        self.current_actions = np.zeros(self.N, dtype=int)

        self.step_size = lambda t: 1 / (t+2)

    def __repr__(self):
        msg = "Fictitious play for "
        g_repr = self.g.__repr__()
        msg += g_repr
        return msg

    def __str__(self):
        return self.__repr__()

    @property
    def current_beliefs(self):
        return tuple(player.current_belief for player in self.players)

    def set_init_beliefs(self, init_beliefs=None):
        """
        Set the initial beliefs of the players.

        Parameters
        ----------
        init_beliefs : array_like

        """
        if init_beliefs is None:
            init_beliefs = [
                np.random.dirichlet(np.ones(belief_size))
                for belief_size in self.belief_sizes
            ]

        for i, player in enumerate(self.players):
            player.current_belief[:] = init_beliefs[i]

    def play(self):
        for i, player in enumerate(self.players):
            self.current_actions[i] = \
                player.best_response(player.current_belief)

    def update_beliefs(self, step_size):
        for i, player in enumerate(self.players):
            # x[i] = x[i] + step_size * (a[1-i] - x[i])
            #      = (1-step_size) * x[i] + step_size * a[1-i]
            # where x[i] = player's current_belief,
            #       a[1-i] = opponent's current_action.
            player.current_belief *= 1 - step_size
            player.current_belief[self.current_actions[1-i]] += step_size

    def simulate(self, ts_length, init_beliefs=None):
        belief_sequences = tuple(
            np.empty((ts_length, belief_size))
            for belief_size in self.belief_sizes
        )
        beliefs_iter = self.simulate_iter(ts_length, init_beliefs)

        for t, beliefs in enumerate(beliefs_iter):
            for i, belief in enumerate(beliefs):
                belief_sequences[i][t] = belief

        return belief_sequences

    def simulate_iter(self, ts_length, init_beliefs=None):
        self.set_init_beliefs(init_beliefs)

        for t in range(ts_length):
            yield self.current_beliefs
            self.play()
            self.update_beliefs(self.step_size(t))

    def replicate(self, T, num_reps, init_beliefs=None):
        """
        Returns
        -------
        out : tuple(ndarray(float, ndim=2))

        """
        out = tuple(
            np.empty((num_reps, belief_size))
            for belief_size in self.belief_sizes
        )

        for j in range(num_reps):
            beliefs_iter = self.simulate_iter(T+1, init_beliefs)
            for beliefs in beliefs_iter:
                x = beliefs
            for belief_array, belief in zip(out, x):
                belief_array[j] = belief

        return out
