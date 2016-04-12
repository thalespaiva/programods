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
- **Bayesian Networks**
- **Markov Networks**

### Examples

#### Bayesian Networks ####

We can load the [asia](https://github.com/thalespaiva/programods/examples/bayesnet/asia/asia.bif) network from a BIF file with:
   
```python
asia = BayesNet.init_from_bif_file('examples/bayesnet/asia/asia.bif')
```

To see the network structure, we can call
```python
asia.draw('asia.png')
```
which creates the following PNG image:

![asia_png](https://github.com/thalespaiva/programods/blob/master/examples/bayesnet/asia/graphics/asia.png)

For each node in the above Digraph, there is a variable with the same name. For example, the variable associated with the lung node can be accessed by `asia['lung']`, which is an instance of `Variable`.
```python
>>> asia['lung']
Variable<lung>

>>> print(asia['lung'])
[V] Name : lung
    Dom  : ['yes', 'no']
```

The local probabilities are indexed by their main varible name. So, to print the local probability of the dysp variable, one can call:

```python
>>> print(asia.local_probs['lung'])
[+] LocalProbability(dysp|bronc,either)
[ ] Scope: dysp,bronc,either
[ ] yes,yes,yes |  0.9000 
[ ] yes,yes,no  |  0.8000 
[ ] yes,no,yes  |  0.7000 
[ ]  yes,no,no  |  0.1000 
[ ] no,yes,yes  |  0.1000 
[ ]  no,yes,no  |  0.2000 
[ ]  no,no,yes  |  0.3000 
[ ]   no,no,no  |  0.9000 
[.]
```

Addicionally, we can generate the markdown table for that local probability:
```python
asia.local_probs['dysp'].get_markdown_table()
```

Which would give us the code that generated the following table:

**Local Probability (dysp|bronc,either)**

| bronc| either|dysp = yes|dysp = no|
|:-:|:-:|:-:|:-:|
|yes|yes| 0.9000| 0.1000|
|yes| no| 0.8000| 0.2000|
| no|yes| 0.7000| 0.3000|
| no| no| 0.1000| 0.9000|

[Here](github.com/thalespaiva/programods/blob/master/examples/bayesnet/asia/graphics/localprobs_table.md) we have the tables of all the asia network local probabilities.



