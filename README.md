# programods #
A Python package for representing and querying **Pro**babilistic **Gra**phical **Mod**el**s**.

GitHub repository:

    https://github.com/thalespaiva/programods


### Core Philosophy ###
 - Code that is easy to read is favored over efficient code
 - It should help students to visualize and understand Probabilistic Models concepts
 - The dificulties of implementations should be clear, and not delegated to another Python library
 - No use of other libraries for probablistic graphical models (corolary of the above, but equally important)

### Supported Probabilistic Models ###

Currently the following are implemented:

- **Probabilistic Logic**
  - ...
- **Bayesian Networks**
  - ...
- **Markov Networks**
  - ...

### Examples

#### Bayesian Networks ####

We can load the [asia]() network from a BIF file with:
   
```python
asia = BayesNet.init_from_bif_file('examples/bayesnet/asia/asia.bif')
```

To see the network structure, we can call
```python
asia.draw('asia.png')
```
which creates the following PNG image:

![asia_png](https://github.com/thalespaiva/programods/blob/master/examples/bayesnet/asia/graphics/asia.png)

For each node in the above Digraph, there is a variable with the same name. For example, the variable associated with the lung node can be accessed by `asia['lung']`.

The local probabilities are indexed by its main varible name. So, for accessing the local probability of the dysp variable, one can call

**Local Probability (asia)**

|asia = yes|asia = no|
|:-:|:-:|
|0.0100|0.9900|

**Local Probability (smoke)**

|smoke = yes|smoke = no|
|:-:|:-:|
|0.5000|0.5000|

**Local Probability (bronc|smoke)**

| smoke|bronc = yes|bronc = no|
|:-:|:-:|:-:|
|yes| 0.6000| 0.4000|
| no| 0.3000| 0.7000|

**Local Probability (tub|asia)**

| asia|tub = yes|tub = no|
|:-:|:-:|:-:|
|yes| 0.0500| 0.9500|
| no| 0.0100| 0.9900|

**Local Probability (xray|either)**

| either|xray = yes|xray = no|
|:-:|:-:|:-:|
|yes| 0.9800| 0.0200|
| no| 0.0500| 0.9500|

**Local Probability (lung|smoke)**

| smoke|lung = yes|lung = no|
|:-:|:-:|:-:|
|yes| 0.1000| 0.9000|
| no| 0.0100| 0.9900|

**Local Probability (either|lung,tub)**

| lung| tub|either = yes|either = no|
|:-:|:-:|:-:|:-:|
|yes|yes| 1.0000| 0.0000|
|yes| no| 1.0000| 0.0000|
| no|yes| 1.0000| 0.0000|
| no| no| 0.0000| 1.0000|

**Local Probability (dysp|bronc,either)**

| bronc| either|dysp = yes|dysp = no|
|:-:|:-:|:-:|:-:|
|yes|yes| 0.9000| 0.1000|
|yes| no| 0.8000| 0.2000|
| no|yes| 0.7000| 0.3000|
| no| no| 0.1000| 0.9000|



