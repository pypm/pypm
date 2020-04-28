# -*- coding: utf-8 -*-
"""
Population: A class that holds the state of a population as it evolves in time
as well as future contributions to the population:
    - t0: start date
    - history: a list containing the population state at each time step.
      The first element of the list corresponds to time = t0.
    - future: a list containing future additions to the population.
      The first element corresponds to the last time step of the history

Currently, the state of the population is recorded as a single number. Note
that a population can be used for tracking expected numbers (reals) or
simulated data (integers).

@author: karlen
"""

from scipy import stats

from Parameter import Parameter

class Population:
    """A class that keeps state information of a population at each time step:
        - population_name : string, short descriptor. Must be unique
        - initial_value : integer, float, or Parameter object
        - description: string, optional - for documentation
        - hidden: don't show in lists of populations when keeping list short
        - color: color to plot
        - show_sim: is it appropriate to show simulated data for this distribution?
        - report_noise: should simulated data include additional noise due to reporting?
        - if True, then supply the lower limit of range [low,1] for which a uniform
          random number is drawn to select the number from today that are reported today
          the remaining will be in tomorrows report (along with some fraction of tomorrows report)
    """

    def __init__(self, population_name, initial_value, description='',
                 hidden=True, color='black', show_sim=False, report_noise=False,
                 report_noise_par=None):
        """
        Constructor

        Parameters
        ----------
        population_name : string, short descriptor
        initial_value : integer, float, or Parameter object

        Returns
        -------
        None.

        """
        self.name = str(population_name)
        self.description = str(description)
        self.history = None
        self.__initialization_by_parameter = False
        if isinstance(initial_value, (float, int)):
            self.history = [initial_value]
        elif isinstance(initial_value, Parameter):
            self.history = [initial_value.get_value()]
            self.__initialization_by_parameter = True
        else:
            raise TypeError('Error setting initial_value to population ('+
                            self.name+') - must be a float, int, or Parameter object')

        self.future = []
        self.initial_value = initial_value
        self.color = color
        self.hidden = hidden
        # identify those populations for which daily contributions are meaningful
        # this is set to False if a subtraction is performed on the population (see Subtractor.py)
        self.monotonic = True
        # identify those populations for which simulated data is appropriate to show 
        self.show_sim = show_sim
        
        self.report_noise = report_noise
        if report_noise and (report_noise_par is None or \
                             not isinstance(report_noise_par, Parameter)):
            raise TypeError('Error setting report_noise_par in population ('+
                            self.name+') - it must be a Parameter object')
        self.report_noise_par = report_noise_par
        self.missed_yesterday = 0

    def __str__(self):
        return self.name

    def do_time_step(self, expectations=True):
        """Perform one step in time by incrementing population number from future.
        After doing so, remove the future element
        
        if we are reporting data (not expectations) and report_noise is true
        then add the missed reports from yesterday and miss some from today
        """
        next_value = 0
        if self.future is not None:
            if expectations or not \
                (hasattr(self,'report_noise') and self.report_noise):
                if len(self.future) > 0:
                    next_value = self.future[0]
            else:
                next_value = self.missed_yesterday
                # how many will be reported from today?
                low_edge = self.report_noise_par.get_value()
                frac_report = stats.uniform.rvs(loc=low_edge, scale=1.-low_edge)
                n_report = stats.binom.rvs(self.future[0], frac_report)
                self.missed_yesterday = self.future[0] - n_report
                next_value += n_report
        self.history.append(self.history[-1] + next_value)
        # don't let the population go negative
        if self.history[-1] < 0:
            self.history[-1] = 0
        # remove the future element
        if self.future is not None:
            if len(self.future) > 0:
                del self.future[0]

    def reset(self):
        """Remove history and future, reinitialize history
        """
        self.future = []
        if isinstance(self.initial_value, Parameter):
            self.history = [self.initial_value.get_value()]
        else:
            self.history = [self.initial_value]
            
        self.missed_yesterday = 0
                
    def remove_history(self):
        """Replace history with array of length 1
        """
        if len(self.history) > 0:
            current_value = self.history[-1]
            self.history = [current_value]
        
    def scale_history(self, scale, expectations=True):
        if len(self.history) > 0:
            for i in range(len(self.history)):
                if expectations:
                    self.history[i] *= scale
                else:
                    nu = self.history[i]*scale
                    self.history[i] = int(round(nu))
        
    def scale_future(self, scale, expectations=True):
        if len(self.future) > 0:
            for i in range(len(self.future)):
                if expectations:
                    self.future[i] *= scale
                else:
                    nu = self.future[i]*scale
                    self.future[i] = int(round(nu))

    def update_future_expectation(self, scale, delay):
        """Include future expections, growing the future array if needed
        """
        for i in range(len(delay.future_expectations)):
            dfe = delay.future_expectations[i] * scale
            if len(self.future) > i:
                self.future[i] += dfe
            else:
                self.future.append(dfe)

    def update_future_data(self, scale, delay):
        """Include future data, growing the future array if needed
        """
        dist = stats.multinomial.rvs(int(scale), delay.future_expectations)
        i = -1
        for n_future in dist:
            i += 1
            if len(self.future) > i:
                self.future[i] += n_future
            else:
                self.future.append(n_future)

    def update_future_fast(self, value):
        """Modify the immediate future
        """
        if len(self.future) > 0:
            self.future[0] += value
        else:
            self.future.append(value)
