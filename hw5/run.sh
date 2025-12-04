#!/bin/bash
#java -Xmx5000m -jar target/assignment4-jabeja-1.0-jar-with-dependencies.jar $@

java -Xmx5000m -ea -jar jabeja.jar -rounds 1001 -graph ./graphs/ws-250.graph -temp 2 -alpha 2 -delta 0.01 -ap exp -tp log
# java -Xmx5000m -ea -jar jabeja.jar -rounds 1001 -graph ./graphs/3elt.graph -temp 2 -alpha 2 -delta 0.005 -ap default
