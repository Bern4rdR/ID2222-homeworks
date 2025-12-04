package se.kth.jabeja;

import org.apache.log4j.Logger;
import se.kth.jabeja.config.Config;
import se.kth.jabeja.config.NodeSelectionPolicy;
import se.kth.jabeja.io.FileIO;
import se.kth.jabeja.rand.RandNoGenerator;

import java.io.File;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

public class Jabeja {
  final static Logger logger = Logger.getLogger(Jabeja.class);
  private final Config config;
  private final HashMap<Integer/*id*/, Node/*neighbors*/> entireGraph;
  private final List<Integer> nodeIds;
  private int numberOfSwaps;
  private int round;
  private float T;
  private boolean resultFileCreated = false;
  private float alpha;
  private float delta;

  //-------------------------------------------------------------------
  public Jabeja(HashMap<Integer, Node> graph, Config config) {
    this.entireGraph = graph;
    this.nodeIds = new ArrayList(entireGraph.keySet());
    this.round = 0;
    this.numberOfSwaps = 0;
    this.config = config;
    this.T = config.getTemperature();
    this.alpha = config.getAlpha();
    this.delta = config.getDelta();
  }


  //-------------------------------------------------------------------
  public void startJabeja() throws IOException {
    for (round = 0; round < config.getRounds(); round++) {
      for (int id : entireGraph.keySet()) {
        sampleAndSwap(id);
      }

      //one cycle for all nodes have completed.
      //reduce the temperature
      saCoolDown();
      report();
    }
  }

  /**
   * Simulated analealing cooling function
   */
  private void saCoolDown(){
    if (config.getTempPolicy().equals("default")) {
      if (T > 1)
        T = T - this.delta;
      if (T < 1)
        T = 1;
    } else if (config.getTempPolicy().equals("log")) {
      T = T * (1 - this.delta); // approaches 0
      if (T < 1) {
        T = 1;
      }
    }
    
  }

  private boolean acceptanceProbabilty(double old_util, double new_util) {
    double delta_ratio = (new_util - old_util)/this.T;
    double acceptance_probability = Math.exp(delta_ratio);
    return Math.random() < acceptance_probability;
  }

  private boolean shouldSwap(float oldBen, float newBen, float highestUtil) {
    return false;
  }

  /**
   * Sample and swap algorith at node p
   * @param nodeId
   */
  private void sampleAndSwap(int nodeId) {
    Node partner = null;
    Node nodep = entireGraph.get(nodeId);
    Node plocal = null;
    Node prandom = null;

    // this was really slow so I updated it; Also, I noticed that it was always selecting the random partner 
    // I verified with assertions (which break the program when it is runnnig)
    // so that is why this is different
    if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID
            || config.getNodeSelectionPolicy() == NodeSelectionPolicy.LOCAL) {
      // swap with random neighbors
      partner = findPartner(nodeId, nodep.getNeighbours().toArray(new Integer[0]));
      plocal = partner;
    }
    if ((config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID && partner == null)
            || config.getNodeSelectionPolicy() == NodeSelectionPolicy.RANDOM) {
      // if local policy fails then randomly sample the entire graph
      int sampleSize = 15; // arbitrary value
      Integer[] nodeSamples = new Integer[sampleSize];
      for(int i = 0; i < sampleSize; i++) {
        int index = (int) Math.floor(Math.random()*this.nodeIds.size());
        nodeSamples[i] = this.nodeIds.get(index);
      }
      partner = findPartner(nodeId, nodeSamples);
      prandom = partner;
    }

    // swap the colors
    if (partner != null) {
      // if (prandom != plocal) {
        // assert(partner != plocal);
      // }
      int pColor = nodep.getColor();
      nodep.setColor(partner.getColor());
      partner.setColor(pColor);
      numberOfSwaps++;
    }
  }

  public Node findPartner(int nodeId, Integer[] nodes){

    Node nodep = entireGraph.get(nodeId);

    Node bestPartner = null;
    double highestUtil = 0; //sorry my old boss was named Ben and this was weirding me out.

    // TODO
    for (int qId : nodes) {
      Node nodeq = entireGraph.get(qId);

      int degpp = (int) nodep.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodep.getColor()).count();
      int degqq = (int) nodeq.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodeq.getColor()).count();
      int oldBen = degpp + degqq;

      int degpq = (int) nodep.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodeq.getColor()).count();
      int degqp = (int) nodeq.getNeighbours().stream().filter(n -> entireGraph.get(n).getColor() == nodep.getColor()).count();
      int newBen = degpq + degqp;

      // the paper's annealing functions -- @Bernard lmk if you think this is incorrect
      // logger.info("Annealing Policy: " + config.getAnnealingPolicy());
      assert(config.getAnnealingPolicy().equals("default") || config.getAnnealingPolicy().equals("exp"));
      if (config.getAnnealingPolicy().equals("default")) {
        double util = (Math.pow(degpq, this.alpha) + Math.pow(degqp, this.alpha)) * this.T - (Math.pow(degpp, this.alpha) + Math.pow(degqq, this.alpha));
        if (util > highestUtil) {
          bestPartner = nodeq;
          highestUtil = util; 
        }
      } else if (config.getAnnealingPolicy().equals("exp")) {
        // no multiply by T here
        double util = (Math.pow(degpq, this.alpha) + Math.pow(degqp, this.alpha)) - (Math.pow(degpp, this.alpha) + Math.pow(degqq, this.alpha));
        if (acceptanceProbabilty(highestUtil, util)) {
          bestPartner = nodeq;
          highestUtil = util;
        }
      }
      
      
    }
    return bestPartner;
  }

  /**
   * The the degreee on the node based on color
   * @param node
   * @param colorId
   * @return how many neighbors of the node have color == colorId
   */
  private int getDegree(Node node, int colorId){
    int degree = 0;
    for(int neighborId : node.getNeighbours()){
      Node neighbor = entireGraph.get(neighborId);
      if(neighbor.getColor() == colorId){
        degree++;
      }
    }
    return degree;
  }

  /**
   * Returns a uniformly random sample of the graph
   * @param currentNodeId
   * @return Returns a uniformly random sample of the graph
   */
  private Integer[] getSample(int currentNodeId) {
    int count = config.getUniformRandomSampleSize();
    int rndId;
    int size = entireGraph.size();
    ArrayList<Integer> rndIds = new ArrayList<Integer>();

    while (true) {
      rndId = nodeIds.get(RandNoGenerator.nextInt(size));
      if (rndId != currentNodeId && !rndIds.contains(rndId)) {
        rndIds.add(rndId);
        count--;
      }

      if (count == 0)
        break;
    }

    Integer[] ids = new Integer[rndIds.size()];
    return rndIds.toArray(ids);
  }

  /**
   * Get random neighbors. The number of random neighbors is controlled using
   * -closeByNeighbors command line argument which can be obtained from the config
   * using {@link Config#getRandomNeighborSampleSize()}
   * @param node
   * @return
   */
  private Integer[] getNeighbors(Node node) {
    ArrayList<Integer> list = node.getNeighbours();
    int count = config.getRandomNeighborSampleSize();
    int rndId;
    int index;
    int size = list.size();
    ArrayList<Integer> rndIds = new ArrayList<Integer>();

    if (size <= count)
      rndIds.addAll(list);
    else {
      while (true) {
        index = RandNoGenerator.nextInt(size);
        rndId = list.get(index);
        if (!rndIds.contains(rndId)) {
          rndIds.add(rndId);
          count--;
        }

        if (count == 0)
          break;
      }
    }

    Integer[] arr = new Integer[rndIds.size()];
    return rndIds.toArray(arr);
  }


  /**
   * Generate a report which is stored in a file in the output dir.
   *
   * @throws IOException
   */
  private void report() throws IOException {
    int grayLinks = 0;
    int migrations = 0; // number of nodes that have changed the initial color
    int size = entireGraph.size();

    for (int i : entireGraph.keySet()) {
      Node node = entireGraph.get(i);
      int nodeColor = node.getColor();
      ArrayList<Integer> nodeNeighbours = node.getNeighbours();

      if (nodeColor != node.getInitColor()) {
        migrations++;
      }

      if (nodeNeighbours != null) {
        for (int n : nodeNeighbours) {
          Node p = entireGraph.get(n);
          int pColor = p.getColor();

          if (nodeColor != pColor)
            grayLinks++;
        }
      }
    }

    int edgeCut = grayLinks / 2;

    logger.info("round: " + round +
            ", edge cut:" + edgeCut +
            ", swaps: " + numberOfSwaps +
            ", migrations: " + migrations);

    saveToFile(edgeCut, migrations);
  }

  private void saveToFile(int edgeCuts, int migrations) throws IOException {
    String delimiter = "\t\t";
    String outputFilePath;

    //output file name
    File inputFile = new File(config.getGraphFilePath());
    outputFilePath = config.getOutputDir() +
            File.separator +
            inputFile.getName() + "_" +
            "NS" + "_" + config.getNodeSelectionPolicy() + "_" +
            "GICP" + "_" + config.getGraphInitialColorPolicy() + "_" +
            "T" + "_" + config.getTemperature() + "_" +
            "D" + "_" + config.getDelta() + "_" +
            "RNSS" + "_" + config.getRandomNeighborSampleSize() + "_" +
            "URSS" + "_" + config.getUniformRandomSampleSize() + "_" +
            "A" + "_" + config.getAlpha() + "_" +
            "R" + "_" + config.getRounds() + ".txt";

    if (!resultFileCreated) {
      File outputDir = new File(config.getOutputDir());
      if (!outputDir.exists()) {
        if (!outputDir.mkdir()) {
          throw new IOException("Unable to create the output directory");
        }
      }
      // create folder and result file with header
      String header = "# Migration is number of nodes that have changed color.";
      header += "\n\nRound" + delimiter + "Edge-Cut" + delimiter + "Swaps" + delimiter + "Migrations" + delimiter + "Skipped" + delimiter + "Temperature" + "\n";
      FileIO.write(header, outputFilePath);
      resultFileCreated = true;
    }

    FileIO.append(round + delimiter + (edgeCuts) + delimiter + numberOfSwaps + delimiter + migrations + delimiter + T + "\n", outputFilePath);
  }
}
