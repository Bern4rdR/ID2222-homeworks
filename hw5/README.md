# Homework 5
December 8

### Authors
Bernard Rumar -- [bernardr@kth.se](mailto:bernardr@kth.se)

Vivienne Curewitz -- [curewitz@kth.se](mailto:curewitz@kth.se)

## Datasets used
- 3elt
- add20

## Soluction
For the main part of the graph partitioning, `sampleAndSwap` takes a node and swaps the color with another node. It selects a sample of nodes based on a selection policy: neighbors or random sample. It then gives the sample to the function `findPartner` which selects the node with the highest utility to swap colors with. Depending on the selection policy, the candidate node will either be selected from the neighbors or a random sample set. The problem with this is that it may achieve a local maximum which may hinder it from finding a better solution. That's why task 2 adds annealing to possibly select a node with worse utility which may avoid falling into a local maximum.

```java
private void sampleAndSwap(int nodeId) {
    Node partner = null;
    Node nodep = entireGraph.get(nodeId);
    Node plocal = null;
    Node prandom = null;

    if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID
            || config.getNodeSelectionPolicy() == NodeSelectionPolicy.LOCAL) {
        // swap with random neighbors
        partner = findPartner(nodeId, nodep.getNeighbours().toArray(new Integer[0]));
        plocal = partner;
    }
    if ((config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID && partner == null)
            || config.getNodeSelectionPolicy() == NodeSelectionPolicy.RANDOM) {
        // if local policy fails then randomly sample the entire graph
        config.setUniformRandSampleSize(15); // arbitrary value
        Integer[] nodeSamples = getSample(nodeId);
        partner = findPartner(nodeId, nodeSamples);
        prandom = partner;
    }

    // swap the colors
    if (partner != null) {
        int pColor = nodep.getColor();
        nodep.setColor(partner.getColor());
        partner.setColor(pColor);
        numberOfSwaps++;
    }
}
```

```java
public Node findPartner(int nodeId, Integer[] nodes){

    Node nodep = entireGraph.get(nodeId);

    Node bestPartner = null;
    double highestUtil = 0;

    for (int qId : nodes) {
        Node nodeq = entireGraph.get(qId);

        int degpp = (int) nodep.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodep.getColor()).count();
        int degqq = (int) nodeq.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodeq.getColor()).count();

        int degpq = (int) nodep.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodeq.getColor()).count();
        int degqp = (int) nodeq.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodep.getColor()).count();
        
        assert(config.getAnnealingPolicy().equals("default") || config.getAnnealingPolicy().equals("exp"));
        if (config.getAnnealingPolicy().equals("default")) {
            double util = (Math.pow(degpq, this.alpha) + Math.pow(degqp, this.alpha)) * this.T - (Math.pow(degpp, this.alpha) + Math.pow(degqq, this.alpha));
            if (util > highestUtil) {
                bestPartner = nodeq;
                highestUtil = util; 
            }
        } else if (config.getAnnealingPolicy().equals("exp")) {
            // no multiply by T here
            double next_util = Math.pow(degpq, this.alpha) + Math.pow(degqp, this.alpha);
            double current_util = Math.pow(degpp, this.alpha) + Math.pow(degqq, this.alpha);
            if (acceptanceProbabilty(Math.max(current_util, highestUtil), next_util)) {
                bestPartner = nodeq;
                highestUtil = next_util;
            }
        }
    }
    return bestPartner;
}
```

## Results
**3elt graph**
![3eld.graph](3elt.png)

**add20 graph**
![add20.graph](add20.png)

**Twitter graph**
![twitter.graph](twitter.png)

**Facebook graph**
![facebook.graph](facebook.png)

## Benchmarks
Running the program through the IntelliJ Profiler gives the following results:

|   Graph  | CPU Time (ms) |
|----------|---------------|
| 3elt     |      3,200    |
| add20    |      3,200    |
| twitter  |    247,400*   |
| facebook |    217,900*   |

**Parameters**
- rounds: 1,000
- temp: 2
- alpha: 1
- delta: 0.003

\*Extrapolation based on 100 rounds