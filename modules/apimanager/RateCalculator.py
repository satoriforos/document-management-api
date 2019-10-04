import time


class RateCalculatorOverLimitError(Exception):
    pass


class RateCalculator:

    S_TO_YEAR = 3600*365
    S_TO_MONTH = 3600*24*30
    S_TO_WEEK = 3600*24*7
    S_TO_DAY = 3600*24
    S_TO_HOUR = 3600
    S_TO_MINUTE = 60
    S_TO_MS = 1/1000

    YEAR_TO_S = 1/(3600*365)
    MONTH_TO_S = 1/(3600*24*30)
    WEEK_TO_S = 1/(3600*24*7)
    DAY_TO_S = 1/(3600*24)
    HOUR_TO_S = 1/3600
    MINUTE_TO_S = 1/60
    MS_TO_S = 1000

    num_transactions_per_tick = 0
    tick_length_s = 100
    total_transactions = 0
    last_tick = 0
    num_transactions_since_tick = None

    def __init__(
        self,
        num_transactions_per_tick,
        tick_length_s,
        total_transactions,
        last_tick
    ):
        self.num_transactions_per_tick = num_transactions_per_tick
        self.tick_length_s = tick_length_s
        self.total_transactions = total_transactions
        self.last_tick = last_tick
        self.get_num_transactions_since_tick()

    def __iter__(self):
        exclusions = [
            'YEAR_TO_S',
            'MONTH_TO_S',
            'WEEK_TO_S',
            'DAY_TO_S',
            'HOUR_TO_S',
            'MINUTE_TO_S',
            'MS_TO_S',
            'S_TO_YEAR',
            'S_TO_MONTH',
            'S_TO_WEEK',
            'S_TO_DAY',
            'S_TO_HOUR'
            'S_TO_MINUTE',
            'S_TO_MS'
        ]
        for property, value in vars(self).items():
            if property not in exclusions:
                yield(property, value)

    def get_num_transactions_since_tick(self):
        if self.num_transactions_since_tick is not None:
            return self.num_transactions_since_tick
        else:
            current_time_s = time.time()
            if self.did_tick_expire(current_time_s) is True:
                self.num_transactions_since_tick = 0
            else:
                self.num_transactions_since_tick = self.total_transactions
        return self.num_transactions_since_tick

    def did_tick_expire(self, current_time_s=None):
        if current_time_s is None:
            current_time_s = time.time()
        did_timer_expire = False
        if current_time_s - self.last_tick > self.tick_length_s:
            did_timer_expire = True
        return did_timer_expire

    def can_increment_transactions(self):
        can_increment_transactions = False
        if self.num_transactions_per_tick == 0:
            can_increment_transactions = True
        else:
            if self.did_tick_expire() is True:
                can_increment_transactions = True
            else:
                if self.num_transactions_since_tick < self.num_transactions_per_tick:
                    can_increment_transactions = True
        return can_increment_transactions

    def increment_transactions(self):
        current_time_s = time.time()
        did_tick_expire = self.did_tick_expire(current_time_s)
        if did_tick_expire is True:
            self.last_tick = round(current_time_s)
            self.num_transactions_since_tick = 0
        can_increment_transactions = self.can_increment_transactions()
        if can_increment_transactions is True:
            self.num_transactions_since_tick += 1
            self.total_transactions += 1
        else:
            raise RateCalculatorOverLimitError
        return self.num_transactions_since_tick
