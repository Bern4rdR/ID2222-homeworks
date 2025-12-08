#!/bin/bash
# java -Xmx5000m -jar target/assignment4-jabeja-1.0-jar-with-dependencies.jar $@

# java -Xmx5000m -ea -jar jabeja.jar -rounds 5001 -graph ./graphs/ws-250.graph -temp 2 -alpha 1 -delta 0.05 -ap exp -tp default
java -Xmx5000m -ea -jar jabeja.jar -rounds 5001 -graph ./graphs/3elt.graph -temp 2 -alpha 1 -delta 0.003 -ap exp -tp default -fn "exp5k2part.txt" -numPartitions=2
# java -Xmx5000m -ea -jar jabeja.jar -rounds 1001 -graph ./graphs/3elt.graph -temp 2 -alpha 1 -delta 0.003 -ap exp -tp default -fn "exp.txt" 
# java -Xmx5000m -ea -jar jabeja.jar -rounds 1001 -graph ./graphs/3elt.graph -temp 2 -alpha 1 -delta 0.003 -ap exp -tp log -fn "log.txt" 

# java -Xmx5000m -ea -jar jabeja.jar -rounds 5001 -graph ./graphs/3elt.graph -temp 2 -alpha 1 -delta 0.003 -ap exp -tp log -fn "3eltDynamic5klog0d1.txt"
# java -Xmx5000m -ea -jar jabeja.jar -rounds 5001 -graph ./graphs/3elt.graph -temp 2 -alpha 1 -delta 0.003 -ap exp -tp default -fn "3eltDynamic5k0d1.txt"
#java -Xmx5000m -ea -jar jabeja.jar -rounds 1001 -graph ./graphs/add20.graph -temp 2 -alpha 1 -delta 0.003 -ap default -tp default
#java -Xmx5000m -ea -jar jabeja.jar -rounds 101 -graph ./graphs/twitter.graph -temp 2 -alpha 1 -delta 0.003 -ap default -tp default
# java -Xmx5000m -ea -jar jabeja.jar -rounds 101 -graph ./graphs/facebook.graph -temp 2 -alpha 1 -delta 0.003 -ap default -tp default