#!/bin/bash
#java -Xmx5000m -jar target/assignment4-jabeja-1.0-jar-with-dependencies.jar $@

java -Xmx5000m -jar jabeja.jar -rounds 500 -graph ./graphs/3elt.graph -temp 2 -alpha 0.99