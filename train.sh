#!/bin/sh
set -e

mkdir -p models
SNAKE="python3 snake -visual off"

$SNAKE -sessions 1   -save models/1sess.txt
$SNAKE -sessions 10  -save models/10sess.txt
$SNAKE -sessions 100 -save models/100sess.txt

$SNAKE -load models/100sess.txt  -sessions 900  -save models/1000sess.txt
$SNAKE -load models/1000sess.txt -sessions 2000 -save models/3000sess.txt
$SNAKE -load models/3000sess.txt -sessions 5000 -save models/8000sess.txt
