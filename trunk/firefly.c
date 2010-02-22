#include "firefly.h"

static void move_fflies(ffly_population *pop, const ffly_population *pop_old, 
                double alpha, double gamma, point min, point max);
static void fix_positions(ffly_population *pop, point min, point max);
static void output_points(ffly_population *pop, const char *fname);
static void sort_flies(ffly_population *pop, int left, int right);
static size_t partition(ffly_population *pop, int left, int right, int pivot);
static void swap(double *, double *);
static void print_fflies(ffly_population *pop);


/*
	This creates our firefly population and assigns random positions.
*/
ffly_population*
init_fflies(size_t ncount, point min, point max)
{
	register unsigned int i = 0;
	double xrange, yrange;
	ffly_population *pop = NULL;
	
	//create memory chunks for values
	pop = malloc(sizeof(ffly_population));
	pop->nfflies = ncount;
	pop->x_values = calloc(ncount, sizeof(double));
	pop->y_values = calloc(ncount, sizeof(double));
	pop->light_values = calloc(ncount, sizeof(double));
	
	//get range
	xrange = max.x - min.x;
	yrange = max.y - min.y;
	
	//init random positions and zero out light value
	for (i=0; i < ncount; i++)
	{
		pop->x_values[i] = my_rand()*xrange + min.x;
		pop->y_values[i] = my_rand()*yrange + min.y;
		pop->light_values[i] = 0.0;
	}
	
	return pop;	
};

/*
	This is called to free up the population
*/
void
destroy_fflies(ffly_population *pop)
{
	free(pop->x_values);
	free(pop->y_values);
	free(pop->light_values);
	free(pop);

	return;
};

point
ffa(size_t nfireflies, size_t niteration, point min, point max, obj_func f)
{
	register unsigned int i = 0;
	unsigned register int j = 0;
	point p;
	double lmin = FLT_MAX;
	size_t size = 0;
	ffly_population *fflies = NULL;
	ffly_population *fflies_old = NULL;

	double alpha = 0.2; //randomness step
	double gamma = 1.0; //absorption coefficient
	
	//initialize our RNG
	srand(time(NULL));
	
	//initialize our firefly array
	fflies = init_fflies(nfireflies, min, max);
	
	//initialize our old firefly array
	fflies_old = init_fflies(nfireflies, min, max);
	
	size = sizeof(double) * nfireflies;
	
	output_points(fflies, "start.dat");
	for (i=0; i < niteration; i++)
	{
		//keep another copy for move function
		memcpy(fflies_old->x_values, fflies->x_values, size);
		memcpy(fflies_old->y_values, fflies->y_values, size);
		memcpy(fflies_old->light_values, fflies->light_values, size);
		
		//evaluate intensity/attractiveness
		(*f)(fflies);
        
        //rank our flies
        //sort_flies(fflies, 0, fflies->nfflies);
        
        //move the flies based on attractiveness
		move_fflies(fflies, fflies_old, alpha, gamma, min, max);
	}
	output_points(fflies, "end.dat");
	
	return p;
};

/*
    Use this to just print values of the population
*/
void
print_fflies(ffly_population *pop)
{
    unsigned register int i = 0;
    
    for (i = 0; i < pop->nfflies; i ++)
    {
        printf("X: %.2lf, Y: %.2lf, Z: %.2lf\n", pop->x_values[i], pop->y_values[i], pop->light_values[i]);
    }
    return;
};

/* 
	This is what moves our fireflies towards the most attractive flies
*/
static void
move_fflies(ffly_population *pop, const ffly_population *pop_old, double alpha, double gamma, point min, point max)
{
	register int i = 0, j = 0;
	const double beta0 = 1.0;
	double beta = 0.0;
	double r = 0.0;
	int nflies = pop->nfflies;
	
	for (i=0; i < nflies; i++)
	{		
	    #pragma parallel for private(i)
		for (j = 0; j < nflies; j++)
		{
		    if (j == i)
		        continue;
		        
			if (pop->light_values[i] < pop_old->light_values[j])
			{
				//i'th firefly should be attracted to the j'th firefly
				double xdist = pop->x_values[i] - pop_old->x_values[j];
				double ydist = pop->y_values[i] - pop_old->y_values[j];
				
				//get the distance to the other fly
				r = sqrt((xdist * xdist) + (ydist * ydist));
				
				//determine attractiveness with air density [gamma]
				beta = beta0 * exp((-gamma) * (r * r));
				
				//adjust position with a small random step
				pop->x_values[i] = ((1 - beta) * pop->x_values[i]) + (beta * pop_old->x_values[j]) + (alpha * (my_rand() - .5));
				pop->y_values[i] = ((1 - beta) * pop->y_values[i]) + (beta * pop_old->y_values[j]) + (alpha * (my_rand() - .5));
			}
		}
	}
	
	//fix boundaries overstepped by random step
	fix_positions(pop, min, max);
};

/* 
	This should correct our positions that have past the boundries from random steps
 */
static void
fix_positions(ffly_population *pop, point min, point max)
{
	unsigned register int i = 0;
	
	for (i=0; i < pop->nfflies; i++)
	{
		if (pop->x_values[i] < min.x) pop->x_values[i] = min.x;
		if (pop->x_values[i] > max.x) pop->x_values[i] = max.x;
		if (pop->y_values[i] < min.y) pop->y_values[i] = min.y;
		if (pop->y_values[i] > max.y) pop->y_values[i] = max.y;
	}
	return;
};

static void
output_points(ffly_population *pop, const char *fname)
{
    unsigned register int i = 0;
    FILE *file;
    
    
    file = fopen(fname, "wt");
    if (file != NULL)
    {
        for (i = 0; i < pop->nfflies; i++)
        {
            fprintf(file, "%.2lf %.2lf\n", pop->x_values[i], pop->y_values[i]);
        }
    }
    fclose(file);
};

static void
sort_flies(ffly_population *pop, int left, int right)
{
    if (right > left)
    {
        size_t pivot = (left+right)/ 2;
        pivot = partition(pop, left, right, pivot);
        sort_flies(pop, left, pivot - 1);
        sort_flies(pop, pivot + 1, right);
    }
};

static size_t
partition(ffly_population *pop, int left, int right, int pivot)
{
    unsigned register int i = 0;
    size_t idx;
    double intensity = pop->light_values[pivot];
    
    //swap values
    swap(&(pop->light_values[pivot]), &(pop->light_values[right]));
    swap(&(pop->x_values[pivot]), &(pop->x_values[right]));
    swap(&(pop->y_values[pivot]), &(pop->y_values[right]));
    
    idx = left;
    
    for (i = left; i < right; i++)
    {
        if (pop->light_values[i] <= intensity)
        {            
            swap(&(pop->light_values[i]), &(pop->light_values[idx]));
            swap(&(pop->x_values[i]), &(pop->x_values[idx]));
            swap(&(pop->y_values[i]), &(pop->y_values[idx]));
            idx++;
        }
    } 
    
    swap(&(pop->light_values[idx]), &(pop->light_values[right]));
    swap(&(pop->x_values[idx]), &(pop->x_values[right]));
    swap(&(pop->y_values[idx]), &(pop->y_values[right]));
    return idx;
};

static void
swap(double *d1, double *d2)
{
    double temp = *d1;
    *d1 = *d2;
    *d2 = temp;
};
