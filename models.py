from otree.api import (
    models, BaseConstants, BaseSubsession, BasePlayer
)

from django.contrib.contenttypes.models import ContentType
from otree_redwood.models import Event, DecisionGroup
from otree_redwood.models import Group as RedwoodGroup

import csv
import random
import math
import otree.common
import time
import datetime


doc = """
This is a Lines Queueing project
"""

class Constants(BaseConstants):
    name_in_url = 'investment_game'
    players_per_group = None
    num_rounds = 50
    base_points = 0


def parse_config(config_file):
    with open('investment_game/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'round_number': int(row['round_number']),
            'duration': int(row['duration']),
            'shuffle_role': True if row['shuffle_role'] == 'TRUE' else False,
            'players_per_group': int(row['players_per_group']),
            'Y': int(row['Y']),
            'cost': int(row['cost']),
            'Z': int(row['Z']),
        })
    return rounds

class Subsession(BaseSubsession):
    def num_rounds(self):
        return len(parse_config(self.session.config['config_file']))

    def creating_session(self):
        config = self.config
        if not config:
            return

        num_silos = self.session.config['num_silos']
        fixed_id_in_group = not config['shuffle_role']

        players = self.get_players()
        num_players = len(players)
        silos = [[] for _ in range(num_silos)]
        for i, player in enumerate(players):
            if self.round_number == 1:
                player.silo_num = math.floor(num_silos * i/num_players)
            else:
                player.silo_num = player.in_round(1).silo_num
            silos[player.silo_num].append(player)
        group_matrix = []
        for silo in silos:
            silo_matrix = []
            ppg = self.config['players_per_group']
            for i in range(0, len(silo), ppg):
                silo_matrix.append(silo[i:i+ppg])
            group_matrix.extend(otree.common._group_randomly(silo_matrix, fixed_id_in_group))
        self.set_group_matrix(group_matrix)
    
    def set_payoffs(self):
        for g in self.get_groups():
            g.set_payoffs()
                
    @property
    def config(self):
        try:
            return parse_config(self.session.config['config_file'])[self.round_number-1]
        except IndexError:
            return None

class Group(RedwoodGroup):
    invested = models.IntegerField(initial=-1)
    investment_time = models.FloatField()

    def period_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['duration']
    
    def y_value(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['Y']

    def cost(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['cost']
    
    def z_value(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['Z']
    

    def set_payoffs(self):
        for p in self.get_players():
            p.set_payoff(self.invested)

    def _on_invest_event(self, event=None, **kwargs):
        if self.invested == -1:
            self.investment_time = (datetime.datetime.now(datetime.timezone.utc) - self.get_start_time()).total_seconds()
            print("Investment")
            self.invested = int(event.value['id'])
            self.send('invest', event.value)
            self.save()



class Player(BasePlayer):
    silo_num = models.IntegerField()

    def num_players(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['players_per_group']


    def set_payoff(self,invested):
        if invested == -1:
            self.payoff = self.group.z_value()
            print("Noone Invested: ", self.payoff)
        elif invested == self.id_in_group:
            self.payoff = self.group.y_value() - self.group.cost()
            print("I Invested: ", self.payoff)
        else:
            self.payoff = self.group.y_value()
            print("Someoe Invested: ", self.payoff)