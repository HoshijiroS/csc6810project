""" This module contains the Population class and Firefly class for
    continuous optimization problems"""
import random
import math
from multiprocessing import Pool
from functions import *

def write_coords(filename, pop):
    """ This function will output the points for each fly in the population """

    with open(filename, 'w') as outputfile:
        for fly in pop.pop:
            for coord in fly.coords:
                outputfile.write(str(coord) + " ")
            outputfile.write("\n")

class Population:
    """ The Population class is responsible for maintaining the fireflies and
        running the rounds of optimization"""

    NORMAL = 1
    HYBRID = 2
    EPSILON = 0.00001

    __funcs = {"dejung" : DeJung }

    def __init__(self, gen, size, dim, alpha, beta, gamma, func_name, style=NORMAL):

        """ Setup sets the initialization parameters 
            for the population"""

        self.gen = gen
        self.alpha = self.alpha0 = alpha
        self.beta0 = beta
        self.gamma = gamma
        self.func = self.__funcs[func_name](dim)
        self.style = style
        self.rand = random.Random()
        self.rand.seed()
        self.pop = self.__generate_pop(size, dim)
        self.oldpop = self.__generate_pop(size, dim)

    def run(self):
        """ Run begins the optimization based 
            on the initialization parameters given """
        
        if self.style == Population.NORMAL:
            self.__npop()
        else:
            self.__hpop()

        self.pop.sort()
        return self.pop[0]

    def test(self):
        """ Runs the Firefly algorithm until the mean delta of
            the values is less than EPSILON """

        if self.style == Population.NORMAL:
            self.__test_population()
        else:
            self.__hybrid_test_population()

        self.pop.sort()
        return self.pop[0]

    def __generate_pop(self, size, dim):
        """ initializes our population """
        return [FireFly(self.func, self, dim)  for i in xrange(size)]

    def __npop(self):
        """ __npop runs the normal firefly algorithm """

        pool = Pool()
        for i in xrange(self.gen):
            #copy our population over to old one as well
            self.__copy_pop()
            #map our current population to a new one
            self.pop = pool.map(map_fly, self.pop)

    def __test_population(self):
        """ runs the optimization until the mean values of change are 
            less than a given epsilon """

        pool = Pool()
        oldavg = self.__mean()

        while True:
            #copy our population over to old one as well
            self.__copy_pop()
            #map our current population to a new one
            self.pop = pool.map(map_fly, self.pop)

            #calculate the delta of the means
            avg = self.__mean()
            val = math.fabs(avg - oldavg)

            if val < Population.EPSILON:
                break
            
            oldavg = avg

    def __hybrid_test_population(self):
        """ runs the optimization until the mean values of change are
            less than a given epsilon """
        pool = Pool()
        i = 2.0

        oldavg = self.__mean()
        while True:
            #calculate our new alpha value based on the annealing schedule
            #this may change to allow for a user chosen schedule
            self.alpha = self.alpha0 / math.log(i)
            
            #copy our population over to old one as well
            self.__copy_pop()
            #map our current population to a new one
            self.pop = pool.map(hybrid_map_fly, self.pop)

            #calculate the delta of the means
            avg = self.__mean()
            val = math.fabs(avg - oldavg)

            i += 1
            if val < Population.EPSILON:
                break
            
            oldavg = avg

    def __hpop(self):
        """ __hpop runs the hybrid firefly algorithm """

        pool = Pool()
        #start at 2 for the log function. do same amount of steps
        for i in xrange(2, self.gen + 2):
            #calculate our new alpha value based on the annealing schedule
            #this may change to allow for a user chosen schedule
            self.alpha = self.alpha0 / math.log(i)
            
            #copy our population over to old one as well
            self.__copy_pop()
            #map our current population to a new one
            self.pop = pool.map(hybrid_map_fly, self.pop)

    def __copy_pop(self):
        """ copies the population coords to oldpopulation coords """
        for i in xrange(len(self.pop)):
            self.oldpop[i].copy(self.pop[i])

    def __mean(self):
        """ calculates the mean value of the population """
        meanval = 0.0
        for fly in self.pop:
            meanval += fly.val

        return meanval / float(len(self.pop))

class FireFly:
    """ A FireFly is a point in hyperdimensional space """

    def __init__(self, objfunc, population, dim):
        self.func = objfunc
        self.pop = population
        self.coords = [(self.pop.rand.random()*(self.func.maxs[x] - self.func.mins[x]) + self.func.mins[x]) for x in xrange(dim)]
        self.val = self.func.eval(self.coords)
        self.moved = False

    def __cmp__(self, fly):
        if isinstance(fly, FireFly):
            return cmp(self.val, fly.val)
        else:
            return cmp(self.val, fly)

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return str(self.val)

    def eval(self):
        """ eval evaluates the firefly given its current coordinates """

        self.val = self.func.eval(self.coords)

    def copy(self, fly):
        """ copy the coordinates and val from fly to this """

        self.val = fly.val
        for i in xrange(len(fly.coords)):
            self.coords[i] = fly.coords[i]

    def map(self):
        """ nmap maps a firefly to its new position """
        reduce(flyfold, self.pop.oldpop, self)
        self.eval()

    def hybrid_map(self):
        """ hybrid_map maps a firefly to its new 
            position using the hybrid technique """

        self.moved = False
        reduce(flyfold, self.pop.oldpop, self)
        if not self.moved:
            self.move_random()
        self.eval()

    def nfoldf(self, fly):
        """ our fold function to use over a list of flies """

        if self.val > fly.val:
            #calculate the distance
            dist = self.__calculate_dist(fly)
            #calculate the attractiveness beta
            beta = self.__calculate_beta(dist, self.pop.beta0, self.pop.gamma)
            #move towards fly
            self.move(self.pop.alpha, beta, self.pop.rand, fly)

    def move(self, alpha, beta, rand, fly):
        """ moves towards another fly based on the 
            values of alpha and beta """

        for i in xrange(len(self.coords)):
            # calc the temp value to set as coord
            tval = ((1 - beta) * fly.coords[i]) + \
                    (beta * self.coords[i]) + (alpha * (rand.random() - 0.5))
            # set as coord if within bounds
            self.coords[i] = self.func.mins[i] if tval < self.func.mins[i] \
                    else self.func.maxs[i] if tval > self.func.maxs[i] else tval
        #we moved
        self.moved = True

    def move_random(self):
        """ moves a little random bit"""
        alpha = self.pop.alpha
        rand = self.pop.rand

        for i in xrange(len(self.coords)):
            # calc the temp value to set as coord
            tval = self.coords[i] + (alpha * (rand.random() - 0.5))
            # set as coord if within bounds
            self.coords[i] = self.func.mins[i] if tval < self.func.mins[i] \
                    else self.func.maxs[i] if tval > self.func.maxs[i] else tval

    def __calculate_dist(self, fly):
        """ calculates the euclidean distance between flies """
        totalsum = 0.0
        for i in xrange(len(self.coords)):
            totalsum += (self.coords[i] - fly.coords[i])**2

        return math.sqrt(totalsum)

    def __calculate_beta(self, dist, beta0, gamma):
        """ calculates the value of beta, or attraction """
        return beta0 * math.exp((-gamma) * (dist**2))


#These functions just help with the higher order functions
def flyfold(fly, otherfly):
    """ this is the function used for folding over a list of flies """
    fly.nfoldf(otherfly)
    return fly

def map_fly(fly):
    """ this is a weird workaround to be able to use the pool """
    fly.map()
    return fly

def hybrid_map_fly(fly):
    """ this is a weird workaround to be able to use the pool """
    fly.hybrid_map()
    return fly
