from matplotlib import pyplot as plt
#%matplotlib inline
import seaborn as sns
import numpy as np
import pandas as pd

import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


__version__ = "0.3.20230609"

class Locked: 
    
    def __init__(
            self, amount=10_000, startday=date.today(), name="no name",
            verbose=True,
            tasso=.025, # .025 means 2.5% tasso lordo
            duration=72, # months
            quarter=3, # use quarter=12 to calculate interests annually
        ):
        
        try:
            assert quarter in [3, 12]
        except:
            raise TypeError("3 and 12 are the only values allowed for 'quarter'")
        
        # TODO: what's this for? comment, I already forgot
        if quarter == 3:
            self.adjust = 4
        else:
            self.adjust = 1
               
        self.initial_amount = amount
        self.name = name
        self.verbose = verbose
        self.quarter = quarter
        
        self.duration = duration # investment duration, in months
        self.startday = startday
        self.endday = startday + relativedelta(months=duration)
        self.maxticks = (self.endday - startday).days
        self.expired = False
        
        # == the following WILL BE MODIFIED during the simulation ==
        self.currday = startday # <date>
        self.amount = amount # <int>
        self.totalticks = 0
        self.nextquarter = startday + relativedelta(months=self.quarter)
        
        # these require the idea of months and quarters (relative to the amount)
        self.totalquarters = 0
        self.paid_this_tick = 0
        self.gain_this_tick = 0
        
        self.totalpaid = 0
        self.totalgain = 0

        # == constants ==
        
        # 26% di tasse sul guadagno sull'interesse guadagnato, ogni volta
        # che ti accreditano un interesse 
        self.TASSE = .26
        
        # alla fine dell'anno, devi sottrarre il 2 per mille dell'intero valore
        # dei soldi presenti sul conto il 31/12
        self.FINEANNO = .002
        
        # il tasso a cui abbiamo vincolato i picci
        self.TASSO = tasso
        
        if verbose:
            print(f"Starting with {amount} € on",
                  f"{startday.day}/{startday.month}/{startday.year}"
            )
    
    def say(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)
    

    def tick(self): # 1 tick = 1 day
        
        # this reset needs to happen before any check. The Wallet
        # pulls these values to decide if something happened in this tick
        # for this Locked, and this may require a full tick to clear.
        self.paid_this_tick = 0
        self.gain_this_tick = 0
        money_at_beginning = self.amount
        
        # we can continue ticking, but we just keep returning None
        if not self.expired:
            self.totalticks += 1
        else:
            return None
        
        if self.totalticks > self.maxticks:
            self.expired = True
            return None
        
        self.currday += relativedelta(days=1)
        # TODO: add here calculation to check if three months have passed

        if self.currday == self.nextquarter:
            self.totalquarters += 1
            # now we need to get some cash (and pay taxes on it)        
            quarter_gain = (self.amount * self.TASSO) / self.adjust
            quarter_tax = quarter_gain * self.TASSE
            quarter_net_gain = quarter_gain - quarter_tax
            self.amount += quarter_net_gain

            self.paid_this_tick += quarter_tax
            self.totalpaid += quarter_tax
            self.gain_this_tick += quarter_gain
            self.totalgain += quarter_gain

            self.say(
                f"+{round(quarter_gain, 2)} €\tgross gain Q{self.totalquarters} '{self.name}' on {self.currday}",
                f"-{round(quarter_tax, 2)} €\ttax on gain Q{self.totalquarters} '{self.name}' on {self.currday}",
                #f"net gain {round(quarter_net_gain, 2)} €",
                sep="\n"
            )
            
            money_at_the_end = self.amount
            quarter_delta = money_at_the_end - money_at_beginning
            perc_quarter_delta = (quarter_delta / money_at_beginning) * 100

            #self.say(f"From {round(money_at_beginning, 2)}€ to {round(money_at_the_end, 2)}€",
            #      f"({round(perc_quarter_delta, 2)}%)"
            #     )
            #
            #self.say()
            #self.say("=" * 20)
            
            if self.currday < self.endday:
                self.nextquarter = self.currday + relativedelta(months=self.quarter)
            else:
                return None # maybe this is the first spot where we.. spot it
            
            if (delta := (self.endday - self.nextquarter).days) < 0:
                print(
                    f"Warning: {self.name} locked for" ,
                    f"{delta} other days but won't gain interests. ",
                    "\n",
                    f"Today: {self.currday}\tEnd day: {self.endday}",
                    sep="",
                )

        # in the case that the quarter ends this very day, first we earn
        # money, then we pay this tax (conservative estimate)
        # TODO: make these dates selectable
        if self.currday.day == 31 and self.currday.month == 12:
            # Yearly taxes (not BOLLO. Bollo is paid in the Wallet)
            duepermille = self.amount * self.FINEANNO
            self.paid_this_tick += duepermille
            self.totalpaid += duepermille
            self.amount -= duepermille
            self.say(f"-{round(duepermille, 2)} €\tEnd of year: 2‰ tax on {self.currday} '{self.name}'")
    
    
    # TODO: da rifare sto schifo
    def info(self):
        """Bad-looking info in text format
        """
        
        print(f"Report for locked sum '{self.name}'")
        print("=" * 80)
        print(f"Days total: {self.totaldays},",
              f"started on day {self.startday} -",
              f"{self.totalticks} quarters ({self.totalticks / self.adjust} years) ago."
        )
        print(f"{self.initial_amount} €\t- initial amount")
        print(f"{self.amount} €\t- current amount, {(self.amount / self.initial_amount)*100}%")
        
    
    def make_ticks(self, ticks=1):
        for _ in range(ticks):
            self.tick()
    
    
    def mature(self):
        # TODO: reset the start date when called
        """This completely matures the locked sum."""
        original_verbosity = self.verbose
        self.verbose = False
        for _ in range(self.maxticks):
            self.tick()
        self.verbose = original_verbosity
        
        print(f"Start date: {self.startday.day}/{self.startday.month}/{self.startday.year}",
              f"- end date: {self.currday.day}/{self.currday.month}/{self.currday.year}")
        print(f"{round(self.initial_amount, 2)} €\tInitial amount")
        print(f"{round(self.amount, 2)} €\tFinal amount")
        print(f"-{round(self.totalpaid, 2)} €\tTotal taxes paid")


class Wallet:
    
    def __init__(
            self, startday=date.today(), bollo=34.20, verbose=True,
            taxday=31, taxmonth=12, # this decides when BOLLO is applied
        ):
        
        # L'imposta di bollo è pari a 34,20€ annuali e la paghi sulla
        #  base della periodicità con cui ricevi l'estratto conto.
        self.BOLLO = bollo
        self.wallet = []        
        self.startday = startday
        self.verbose = verbose
        self.taxday = taxday
        self.taxmonth = taxmonth
        self.df = None
        
        # == the following WILL BE MODIFIED during the simulation ==
        self.currday = startday # <date>
        self.amount = 0 # <int>
        self.totalticks = 0
        
        self.paid_this_tick = 0
        self.gain_this_tick = 0
        
        self.totalpaid = 0
        self.totalgain = 0
    

    def say(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)
    
    
    def add_locked(self, locked):
        # TODO: fix
        #if not isinstance(locked, Locked):
        #    raise TypeError("Only <Locked> objects can be added to the wallet.")
        if len(self.wallet) > 0:
            for elem in self.wallet:
                if elem.name == locked.name:
                    raise TypeError(
                        f"Can't add Locked sums with the same name: '{locked.name}'"
                    )  
        
        self.wallet.append(locked)
        
    
    # new on 8/6/23
    def rm_locked(self, locked_name):
        """ Remove a Locked sum by its name (can't have duplicate Locked names)
        """
        for i, elem in enumerate(self.wallet):
            if elem.name == locked_name:
                del self.wallet[i]

    
    def tick(self):
        
        self.totalticks += 1
        self.currday += relativedelta(days=1)
                
        self.paid_this_tick = 0
        self.gain_this_tick = 0
        
        # pagamento del bollo
        if self.currday.day == self.taxday \
        and self.currday.month == self.taxmonth\
        and self.amount > 5_000: # legge italiana
            self.paid_this_tick += self.BOLLO
            self.totalpaid += self.BOLLO
            self.amount -= self.BOLLO
            self.say(f"-{self.BOLLO} € \tImposta di bollo on {self.currday}")
            
            data = {
                "name": "wallet operation",
                "operation": -self.BOLLO,
                "currday": self.currday,
                "totalticks": np.nan,
                "wallet ticks": self.totalticks,
                "quarter": np.nan, # Locked quarter (this is no Locked operation)
                "totalpaid": np.nan, # Locked totalpaid (this is no Locked operation)
                "totalgain": np.nan, # Locked totalgain (this is no Locked operation)
                "totalpaid wallet": self.totalpaid,
                "totalgain wallet": self.totalgain,
                "wallet amount": self.amount,
            }
            df = pd.DataFrame(data, columns=data.keys(), index=range(1))
            self.df = pd.concat([self.df, df])
                
        for locked in self.wallet:
            if locked.expired:
                # TODO: remove locked from wallet
                continue
            
            if locked.currday > self.currday:
                # the locked has been preloaded into the wallet,
                # but it has not started yet. Skipping
                continue
            
            locked.tick()
            
            if locked.totalticks == 1:
                self.say(f"Adding locked '{locked.name}' on {self.currday}")
                self.amount += locked.amount
                
                data = {
                    "name": "wallet operation",
                    "operation": locked.amount,
                    "currday": self.currday,
                    "totalticks": locked.totalticks, #1?
                    "wallet ticks": self.totalticks,
                    "quarter": locked.totalquarters,
                    "totalpaid": locked.totalpaid,
                    "totalgain": locked.totalgain,
                    "totalpaid wallet": self.totalpaid,
                    "totalgain wallet": self.totalgain,
                    "wallet amount": self.amount,
                }
                df = pd.DataFrame(data, columns=data.keys(), index=range(1))
                self.df = pd.concat([self.df, df])
            
            # updating the wallet stats with what has happened in the Locked this tick
            self.paid_this_tick += locked.paid_this_tick
            self.totalpaid += locked.paid_this_tick
            self.amount -= locked.paid_this_tick
            
            if locked.paid_this_tick != 0:
                data = {
                    "name": locked.name,
                    "operation": -locked.paid_this_tick,
                    "currday": self.currday,
                    "totalticks": locked.totalticks,
                    "wallet ticks": self.totalticks,
                    "quarter": locked.totalquarters,
                    "totalpaid": locked.totalpaid,
                    "totalgain": locked.totalgain,
                    "totalpaid wallet": self.totalpaid,
                    "totalgain wallet": self.totalgain,
                    "wallet amount": self.amount,
                }
                df = pd.DataFrame(data, columns=data.keys(), index=range(1))
                self.df = pd.concat([self.df, df])

            self.gain_this_tick += locked.gain_this_tick
            self.totalgain += locked.gain_this_tick
            self.amount += locked.gain_this_tick
            
            if locked.gain_this_tick != 0:
                data = {
                    "name": locked.name,
                    "operation": locked.gain_this_tick,
                    "currday": self.currday,
                    "totalticks": locked.totalticks,
                    "wallet ticks": self.totalticks,
                    "quarter": locked.totalquarters,
                    "totalpaid": locked.totalpaid,
                    "totalgain": locked.totalgain,
                    "totalpaid wallet": self.totalpaid,
                    "totalgain wallet": self.totalgain,
                    "wallet amount": self.amount,
                }
                df = pd.DataFrame(data, columns=data.keys(), index=range(1))
                self.df = pd.concat([self.df, df])
                
        # final indexing after all Locked sums have been sifted through
        self.df["op_id"] = range(len(self.df))
        self.df = self.df.set_index(self.df["op_id"])
        del self.df["op_id"]
            
            
    def bruttoreport(self):
        
        print(f"{round(self.totalgain, 2)} €\tTotal Gain")
        print(f"{-round(self.totalpaid, 2)} €\tTotal Paid")
        print(
            f"{round(self.totalgain - self.totalpaid, 2)} € Net Gain in {self.totalticks} days",
            f"from {len(self.wallet)} locked sums.",
        )
    
                       
    def make_ticks(self, ticks=1):
        for _ in range(ticks):
            self.tick()