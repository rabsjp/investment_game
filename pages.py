import math
from ._builtin import Page, WaitPage

from datetime import timedelta
from operator import concat
from functools import reduce
from .models import parse_config

class Introduction(Page):

    def is_displayed(self):
        return self.round_number == 1


class DecisionWaitPage(WaitPage):

    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True
    #after_all_players_arrive = 'set_initial_decisions'

    def is_displayed(self):
        return self.subsession.config is not None


class Decision(Page):

    def is_displayed(self):
        return self.subsession.config is not None

    def vars_for_template(self):
        return {
            'tiempo': self.group.period_length(),
            'nadie': self.group.z_value(),
            'alguien': self.group.y_value(),
            'voluntario': self.group.y_value() - self.group.cost()

        }

class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    after_all_players_arrive = 'set_payoffs'

    def is_displayed(self):
        return self.subsession.config is not None


class Results(Page):

    timeout_seconds = 30

    def is_displayed(self):
        return self.subsession.config is not None

    def vars_for_template(self):

        payoffs = []

        for i in range(1, self.round_number + 1):
            payoffs.append({'index': i, 'payoff': self.player.in_round(i).payoff,
                            'group_inv': 'yes' if self.group.in_round(i).invested != -1 else 'no',
                            'you_inv': 'yes' if self.group.in_round(i).invested == self.player.in_round(i).id_in_group else 'no'})
        
        print(payoffs)

        return {
            'payoffs': payoffs,
        }

class Payment(Page):

    def is_displayed(self):
        return self.round_number == self.subsession.num_rounds()
    
    def vars_for_template(self):
        return {
            'payoff': self.participant.payoff #.to_real_world_currency(self.session),
        }

page_sequence = [
    Introduction,
    DecisionWaitPage,
    Decision,
    ResultsWaitPage,
    Results,
    Payment
]
